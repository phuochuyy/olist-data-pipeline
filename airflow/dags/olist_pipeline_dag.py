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

LAYERS = {'raw': 'bronze', 'staging': 'silver', 'marts': 'gold', 'analytics': 'analytics'}

METRICS_DDL = """
    CREATE SCHEMA IF NOT EXISTS monitoring;
    CREATE TABLE IF NOT EXISTS monitoring.pipeline_metrics (
        id          BIGSERIAL PRIMARY KEY,
        run_id      TEXT        NOT NULL,
        layer       TEXT        NOT NULL,
        table_name  TEXT        NOT NULL,
        row_count   BIGINT      NOT NULL,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
"""


def generate_data_report(**context):
    """Count rows of every pipeline table and store them in monitoring.pipeline_metrics.

    One row per table and DAG run: Grafana plots it, monitoring/production_monitor.py
    uses it for freshness, and a sudden drop between runs is easy to spot.
    """
    hook = PostgresHook(postgres_conn_id='postgres_default')
    hook.run(METRICS_DDL)

    tables = hook.get_records("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema IN ('raw', 'staging', 'marts', 'analytics')
          AND table_type = 'BASE TABLE'
          AND table_name NOT LIKE '%\_backup\_%'
        ORDER BY 1, 2
    """)

    rows = []
    for schema, table in tables:
        count = hook.get_first(f'SELECT COUNT(*) FROM "{schema}"."{table}"')[0]
        rows.append((context['run_id'], LAYERS[schema], f"{schema}.{table}", count))

    hook.insert_rows('monitoring.pipeline_metrics', rows,
                     target_fields=['run_id', 'layer', 'table_name', 'row_count'])

    logging.info("=== DATA PROCESSING REPORT (%s) ===", context['run_id'])
    for _, layer, table, count in rows:
        logging.info("%-8s %-40s %12s rows", layer, table, f"{count:,}")
    return {table: count for _, _, table, count in rows}

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
    # Truncate whatever staging tables exist: Spark (re)creates dim_customers and dim_products,
    # and on the very first run the schema is still empty.
    sql="""
        DO $$
        DECLARE t TEXT;
        BEGIN
            FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'staging' LOOP
                EXECUTE format('TRUNCATE TABLE staging.%I', t);
            END LOOP;
        END $$;
    """,
    dag=dag
)

# Task 3: Run Spark data processing
spark_processing = BashOperator(
    task_id='spark_data_processing',
    # spark-submit runs in this Airflow container (JDK + pyspark are in the image): the driver
    # lives here, executors on spark-worker. No docker exec / docker socket needed.
    bash_command="""
        spark-submit \
        --master spark://spark-master:7077 \
        --conf spark.driver.host=$(hostname -i) \
        --conf spark.jars.ivy=/tmp/.ivy2 \
        --packages org.postgresql:postgresql:42.6.0 \
        --driver-memory 1g \
        --executor-memory 1g \
        /opt/airflow/spark/data_processor.py
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

# Task 5b: Great Expectations suites on the bronze tables (exit code 1 = failed expectation)
great_expectations_validation = BashOperator(
    task_id='great_expectations_validation',
    bash_command='cd /tmp && python /opt/airflow/great_expectations/data_quality.py',
    dag=dag
)

# Task 5c: dbt models + tests (staging view, customer mart, analytics tables).
# Profile from profiles.yml.example (profiles.yml is git-ignored).
dbt_build = BashOperator(
    task_id='dbt_build',
    bash_command="""
        mkdir -p /tmp/dbt && cp /opt/airflow/dbt_project/profiles.yml.example /tmp/dbt/profiles.yml && \
        cd /opt/airflow/dbt_project && \
        dbt deps --profiles-dir /tmp/dbt && \
        dbt build --profiles-dir /tmp/dbt
    """,
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
spark_processing >> [data_quality_check, business_validation, great_expectations_validation]
[data_quality_check, business_validation, great_expectations_validation] >> dbt_build
dbt_build >> update_marts_metadata
update_marts_metadata >> generate_report
generate_report >> backup_marts >> cleanup_old_backups
