from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import logging

# Default arguments
default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2)
}

# DAG definition
dag = DAG(
    'olist_data_pipeline',
    default_args=default_args,
    description='Complete Olist E-commerce Data Pipeline',
    schedule_interval=timedelta(days=1),  # Daily execution
    catchup=False,
    max_active_runs=1,
    tags=['olist', 'ecommerce', 'etl', 'data-warehouse']
)

def check_data_quality(**context):
    """
    Data quality validation function
    
    Đây là function mình viết để check xem data có bị lỗi gì không.
    Mình học được rằng data quality rất quan trọng trong data pipeline.
    """
    # Kết nối database bằng Airflow hook (học từ documentation)
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Danh sách các checks mình muốn làm
    # Mình check những column quan trọng không được null
    quality_checks = [
        ("raw.customers", "customer_id", "Customer ID cannot be null"),
        ("raw.orders", "order_id", "Order ID cannot be null"),
        ("raw.order_items", "order_id", "Order ID in items cannot be null"),
        ("raw.products", "product_id", "Product ID cannot be null")
    ]
    
    # Loop qua từng check (học được cách viết maintainable code)
    for table, column, message in quality_checks:
        query = f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL"
        result = hook.get_first(query)[0]
        
        # Nếu có null values thì fail pipeline (fail fast principle)
        if result > 0:
            raise ValueError(f"Data quality check failed: {message}. Found {result} null values.")
    
    logging.info("All data quality checks passed!")

def validate_business_rules(**context):
    """Validate business rules"""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Check for negative prices
    negative_prices = hook.get_first(
        "SELECT COUNT(*) FROM raw.order_items WHERE price < 0"
    )[0]
    
    if negative_prices > 0:
        raise ValueError(f"Found {negative_prices} records with negative prices!")
    
    # Check for future order dates
    future_orders = hook.get_first(
        "SELECT COUNT(*) FROM raw.orders WHERE order_purchase_timestamp > CURRENT_TIMESTAMP"
    )[0]
    
    if future_orders > 0:
        logging.warning(f"Found {future_orders} orders with future dates!")
    
    logging.info("Business rule validation completed!")

def generate_data_report(**context):
    """Generate data processing report"""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Get record counts
    tables = ['customers', 'orders', 'order_items', 'products', 'sellers']
    report = {}
    
    for table in tables:
        count = hook.get_first(f"SELECT COUNT(*) FROM raw.{table}")[0]
        report[table] = count
    
    # Log the report
    logging.info("=== DATA PROCESSING REPORT ===")
    for table, count in report.items():
        logging.info(f"{table}: {count:,} records")
    
    # You could also send this to an external monitoring system
    return report

# Task 1: Health check
health_check = PostgresOperator(
    task_id='health_check_postgres',
    postgres_conn_id='postgres_default',
    sql="SELECT 1;",
    dag=dag
)

# Task 2: Clean previous staging data
clean_staging = PostgresOperator(
    task_id='clean_staging_data',
    postgres_conn_id='postgres_default',
    sql="""
        TRUNCATE TABLE staging.dim_customers;
        TRUNCATE TABLE staging.dim_products;
        TRUNCATE TABLE staging.dim_sellers;
        TRUNCATE TABLE staging.fact_orders;
    """,
    dag=dag
)

# Task 3: Run Spark data processing
spark_processing = BashOperator(
    task_id='spark_data_processing',
    bash_command="""
        docker exec data_pipeline-spark-master-1 spark-submit \
        --master spark://spark-master:7077 \
        --packages org.postgresql:postgresql:42.6.0 \
        --driver-memory 2g \
        --executor-memory 2g \
        /opt/spark/jobs/data_processor.py
    """,
    dag=dag
)

# Task 4: Data quality checks
data_quality_check = PythonOperator(
    task_id='data_quality_check',
    python_callable=check_data_quality,
    dag=dag
)

# Task 5: Business rules validation
business_validation = PythonOperator(
    task_id='business_rules_validation',
    python_callable=validate_business_rules,
    dag=dag
)

# Task 6: Update marts metadata
update_marts_metadata = PostgresOperator(
    task_id='update_marts_metadata',
    postgres_conn_id='postgres_default',
    sql="""
        -- Update customer metrics metadata
        UPDATE marts.customer_metrics 
        SET updated_at = CURRENT_TIMESTAMP 
        WHERE updated_at < CURRENT_DATE;
        
        -- Update product performance metadata
        UPDATE marts.product_performance 
        SET updated_at = CURRENT_TIMESTAMP 
        WHERE updated_at < CURRENT_DATE;
        
        -- Update daily sales summary metadata
        UPDATE marts.daily_sales_summary 
        SET updated_at = CURRENT_TIMESTAMP 
        WHERE updated_at < CURRENT_DATE;
    """,
    dag=dag
)

# Task 7: Generate report
generate_report = PythonOperator(
    task_id='generate_data_report',
    python_callable=generate_data_report,
    dag=dag
)

# Task 8: Data backup
backup_marts = PostgresOperator(
    task_id='backup_marts_data',
    postgres_conn_id='postgres_default',
    sql="""
        -- Create backup tables with timestamp
        CREATE TABLE IF NOT EXISTS marts.customer_metrics_backup_{{ ds_nodash }} AS 
        SELECT * FROM marts.customer_metrics;
        
        CREATE TABLE IF NOT EXISTS marts.daily_sales_backup_{{ ds_nodash }} AS 
        SELECT * FROM marts.daily_sales_summary;
    """,
    dag=dag
)

# Task 9: Cleanup old backups (keep last 7 days)
cleanup_old_backups = PostgresOperator(
    task_id='cleanup_old_backups',
    postgres_conn_id='postgres_default',
    sql="""
        DO $$
        DECLARE
            table_name TEXT;
            cutoff_date TEXT;
        BEGIN
            cutoff_date := TO_CHAR(CURRENT_DATE - INTERVAL '7 days', 'YYYYMMDD');
            
            FOR table_name IN 
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'marts' 
                AND tablename LIKE '%_backup_%'
                AND SUBSTRING(tablename FROM '.*_([0-9]{8})$') < cutoff_date
            LOOP
                EXECUTE 'DROP TABLE IF EXISTS marts.' || table_name;
            END LOOP;
        END $$;
    """,
    dag=dag
)

# Define task dependencies
health_check >> clean_staging >> spark_processing
spark_processing >> [data_quality_check, business_validation]
[data_quality_check, business_validation] >> update_marts_metadata
update_marts_metadata >> generate_report
generate_report >> backup_marts >> cleanup_old_backups
