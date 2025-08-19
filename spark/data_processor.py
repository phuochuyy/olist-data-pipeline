from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import sys
import os

class DataProcessor:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("OlistDataProcessor") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.jars", "/opt/spark/jars/postgresql-42.6.0.jar") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        
        # Database connection properties
        self.db_properties = {
            "user": "postgres",
            "password": "postgres",
            "driver": "org.postgresql.Driver"
        }
        self.db_url = "jdbc:postgresql://postgres:5432/olist_dw"
    
    def read_csv_with_schema(self, file_path, schema):
        """Read CSV file with predefined schema"""
        return self.spark.read \
            .option("header", "true") \
            .option("multiline", "true") \
            .option("escape", '"') \
            .schema(schema) \
            .csv(file_path)
    
    def define_schemas(self):
        """Define schemas for all CSV files"""
        self.schemas = {
            "customers": StructType([
                StructField("customer_id", StringType(), True),
                StructField("customer_unique_id", StringType(), True),
                StructField("customer_zip_code_prefix", StringType(), True),
                StructField("customer_city", StringType(), True),
                StructField("customer_state", StringType(), True)
            ]),
            
            "orders": StructType([
                StructField("order_id", StringType(), True),
                StructField("customer_id", StringType(), True),
                StructField("order_status", StringType(), True),
                StructField("order_purchase_timestamp", TimestampType(), True),
                StructField("order_approved_at", TimestampType(), True),
                StructField("order_delivered_carrier_date", TimestampType(), True),
                StructField("order_delivered_customer_date", TimestampType(), True),
                StructField("order_estimated_delivery_date", TimestampType(), True)
            ]),
            
            "order_items": StructType([
                StructField("order_id", StringType(), True),
                StructField("order_item_id", IntegerType(), True),
                StructField("product_id", StringType(), True),
                StructField("seller_id", StringType(), True),
                StructField("shipping_limit_date", TimestampType(), True),
                StructField("price", DecimalType(10, 2), True),
                StructField("freight_value", DecimalType(10, 2), True)
            ]),
            
            "products": StructType([
                StructField("product_id", StringType(), True),
                StructField("product_category_name", StringType(), True),
                StructField("product_name_length", IntegerType(), True),
                StructField("product_description_length", IntegerType(), True),
                StructField("product_photos_qty", IntegerType(), True),
                StructField("product_weight_g", IntegerType(), True),
                StructField("product_length_cm", IntegerType(), True),
                StructField("product_height_cm", IntegerType(), True),
                StructField("product_width_cm", IntegerType(), True)
            ])
        }
    
    def extract_and_load_raw(self, data_path="/opt/airflow/data"):
        """Extract data from CSV files and load to raw schema"""
        self.define_schemas()
        
        # File mappings
        files = {
            "customers": "olist_customers_dataset.csv",
            "orders": "olist_orders_dataset.csv",
            "order_items": "olist_order_items_dataset.csv",
            "order_payments": "olist_order_payments_dataset.csv",
            "order_reviews": "olist_order_reviews_dataset.csv",
            "products": "olist_products_dataset.csv",
            "sellers": "olist_sellers_dataset.csv",
            "geolocation": "olist_geolocation_dataset.csv",
            "product_category_translation": "product_category_name_translation.csv"
        }
        
        for table_name, file_name in files.items():
            file_path = f"{data_path}/{file_name}"
            print(f"Processing {table_name} from {file_path}")
            
            try:
                if table_name in self.schemas:
                    df = self.read_csv_with_schema(file_path, self.schemas[table_name])
                else:
                    df = self.spark.read \
                        .option("header", "true") \
                        .option("inferSchema", "true") \
                        .option("multiline", "true") \
                        .option("escape", '"') \
                        .csv(file_path)
                
                # Add created_at timestamp
                df_with_timestamp = df.withColumn("created_at", current_timestamp())
                
                # Write to PostgreSQL
                df_with_timestamp.write \
                    .mode("overwrite") \
                    .jdbc(self.db_url, f"raw.{table_name}", properties=self.db_properties)
                
                print(f"Successfully loaded {df_with_timestamp.count()} records to raw.{table_name}")
                
            except Exception as e:
                print(f"Error processing {table_name}: {str(e)}")
    
    def transform_staging_data(self):
        """Transform raw data to staging layer"""
        
        # Customers dimension
        customers_df = self.spark.read.jdbc(self.db_url, "raw.customers", properties=self.db_properties)
        
        customers_staging = customers_df.select(
            col("customer_id"),
            col("customer_unique_id"),
            col("customer_zip_code_prefix"),
            upper(col("customer_city")).alias("customer_city"),
            upper(col("customer_state")).alias("customer_state"),
            current_timestamp().alias("created_at")
        ).distinct()
        
        customers_staging.write \
            .mode("overwrite") \
            .jdbc(self.db_url, "staging.dim_customers", properties=self.db_properties)
        
        # Products dimension with category translation
        products_df = self.spark.read.jdbc(self.db_url, "raw.products", properties=self.db_properties)
        translation_df = self.spark.read.jdbc(self.db_url, "raw.product_category_translation", properties=self.db_properties)
        
        products_staging = products_df.join(
            translation_df, 
            products_df.product_category_name == translation_df.product_category_name,
            "left"
        ).select(
            products_df.product_id,
            coalesce(translation_df.product_category_name_english, products_df.product_category_name).alias("product_category_name"),
            products_df.product_name_length,
            products_df.product_description_length,
            products_df.product_photos_qty,
            products_df.product_weight_g,
            products_df.product_length_cm,
            products_df.product_height_cm,
            products_df.product_width_cm,
            current_timestamp().alias("created_at")
        ).distinct()
        
        products_staging.write \
            .mode("overwrite") \
            .jdbc(self.db_url, "staging.dim_products", properties=self.db_properties)
        
        print("Staging transformation completed")
    
    def create_marts(self):
        """Create data marts for analytics"""
        
        # Customer metrics mart
        customers_df = self.spark.read.jdbc(self.db_url, "raw.customers", properties=self.db_properties)
        orders_df = self.spark.read.jdbc(self.db_url, "raw.orders", properties=self.db_properties)
        order_items_df = self.spark.read.jdbc(self.db_url, "raw.order_items", properties=self.db_properties)
        products_df = self.spark.read.jdbc(self.db_url, "raw.products", properties=self.db_properties)
        translation_df = self.spark.read.jdbc(self.db_url, "raw.product_category_translation", properties=self.db_properties)
        
        # Join all data for customer metrics
        customer_orders = orders_df.filter(col("order_status") == "delivered") \
            .join(order_items_df, "order_id") \
            .join(customers_df, "customer_id") \
            .join(products_df, order_items_df.product_id == products_df.product_id, "left") \
            .join(translation_df, products_df.product_category_name == translation_df.product_category_name, "left")
        
        customer_metrics = customer_orders.groupBy("customer_id") \
            .agg(
                count("order_id").alias("total_orders"),
                sum("price").alias("total_spent"),
                avg("price").alias("avg_order_value"),
                min("order_purchase_timestamp").cast("date").alias("first_order_date"),
                max("order_purchase_timestamp").cast("date").alias("last_order_date"),
                first(coalesce(col("product_category_name_english"), col("product_category_name"))).alias("favorite_category")
            ).withColumn(
                "customer_lifetime_days",
                datediff(col("last_order_date"), col("first_order_date"))
            ).withColumn("created_at", current_timestamp()) \
            .withColumn("updated_at", current_timestamp())
        
        customer_metrics.write \
            .mode("overwrite") \
            .jdbc(self.db_url, "marts.customer_metrics", properties=self.db_properties)
        
        # Daily sales summary
        daily_sales = orders_df.filter(col("order_status") == "delivered") \
            .join(order_items_df, "order_id") \
            .withColumn("date_key", col("order_purchase_timestamp").cast("date")) \
            .groupBy("date_key") \
            .agg(
                countDistinct("order_id").alias("total_orders"),
                sum("price").alias("total_revenue"),
                avg("price").alias("avg_order_value"),
                countDistinct("customer_id").alias("unique_customers")
            ).withColumn("created_at", current_timestamp()) \
            .withColumn("updated_at", current_timestamp())
        
        daily_sales.write \
            .mode("overwrite") \
            .jdbc(self.db_url, "marts.daily_sales_summary", properties=self.db_properties)
        
        print("Data marts created successfully")
    
    def run_full_pipeline(self):
        """Run the complete data pipeline"""
        print("Starting full data pipeline...")
        
        # Extract and load raw data
        self.extract_and_load_raw()
        
        # Transform to staging
        self.transform_staging_data()
        
        # Create marts
        self.create_marts()
        
        print("Data pipeline completed successfully!")
        
        # Stop Spark session
        self.spark.stop()

if __name__ == "__main__":
    processor = DataProcessor()
    processor.run_full_pipeline()
