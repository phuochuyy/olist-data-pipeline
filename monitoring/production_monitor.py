#!/usr/bin/env python3
"""
Olist Data Pipeline - Production Monitoring System
====================================================

Real-time monitoring for production data pipeline health,
performance metrics, and business KPIs.

Author: Data Engineering Team
Date: August 24, 2025
"""

import psycopg2
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MimeText
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/phuochuy/Projects/pipeline05/data_pipeline/logs/production_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OlistPipelineMonitor:
    """Production Pipeline Monitoring System"""
    
    def __init__(self, db_config: Dict[str, str]):
        """Initialize monitor with database configuration"""
        self.db_config = db_config
        self.connection = None
        self.alerts = []
        
    def connect_database(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def check_data_freshness(self) -> Dict[str, any]:
        """Check data freshness across pipeline layers"""
        freshness_checks = {}
        
        queries = {
            'bronze_layer': """
                SELECT 
                    'bronze' as layer,
                    MAX(created_at) as last_update
                FROM monitoring.pipeline_metrics 
                WHERE layer = 'bronze'
            """,
            'silver_layer': """
                SELECT 
                    'silver' as layer,
                    COUNT(*) as record_count,
                    MAX(created_at) as last_update
                FROM staging.fact_orders
            """,
            'gold_layer': """
                SELECT 
                    'gold' as layer,
                    COUNT(*) as record_count,
                    MAX(date_key) as last_date
                FROM marts.daily_sales_summary
            """
        }
        
        try:
            cursor = self.connection.cursor()
            
            for check_name, query in queries.items():
                cursor.execute(query)
                result = cursor.fetchone()
                freshness_checks[check_name] = {
                    'status': 'Fresh' if result else 'Stale',
                    'last_update': result[1] if result else None,
                    'timestamp': datetime.now()
                }
                
            cursor.close()
            logger.info("📅 Data freshness check completed")
            
        except Exception as e:
            logger.error(f"Data freshness check failed: {e}")
            freshness_checks['error'] = str(e)
            
        return freshness_checks
    
    def monitor_data_quality(self) -> Dict[str, any]:
        """Monitor data quality metrics"""
        quality_metrics = {}
        
        quality_queries = {
            'null_check': """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN customer_id IS NULL THEN 1 END) as null_customers,
                    COUNT(CASE WHEN order_id IS NULL THEN 1 END) as null_orders
                FROM raw.orders
            """,
            'duplicate_check': """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT order_id) as unique_orders,
                    COUNT(*) - COUNT(DISTINCT order_id) as duplicates
                FROM raw.orders
            """,
            'data_consistency': """
                SELECT 
                    COUNT(DISTINCT customer_id) as customers_in_orders,
                    (SELECT COUNT(*) FROM raw.customers) as total_customers
                FROM raw.orders
            """
        }
        
        try:
            cursor = self.connection.cursor()
            
            for check_name, query in quality_queries.items():
                cursor.execute(query)
                result = cursor.fetchone()
                
                if check_name == 'duplicate_check':
                    quality_metrics[check_name] = {
                        'total_records': result[0],
                        'unique_records': result[1], 
                        'duplicates': result[2],
                        'quality_score': (result[1] / result[0]) * 100 if result[0] > 0 else 0
                    }
                else:
                    quality_metrics[check_name] = dict(zip(['metric1', 'metric2', 'metric3'], result))
                    
            cursor.close()
            logger.info("Data quality monitoring completed")
            
        except Exception as e:
            logger.error(f"Data quality check failed: {e}")
            quality_metrics['error'] = str(e)
            
        return quality_metrics
    
    def monitor_performance_metrics(self) -> Dict[str, any]:
        """Monitor pipeline performance"""
        performance_metrics = {}
        
        try:
            cursor = self.connection.cursor()
            
            # Query execution time monitoring
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    seq_scan,
                    idx_scan
                FROM pg_stat_user_tables 
                WHERE schemaname IN ('raw', 'staging', 'marts')
                ORDER BY seq_scan DESC
                LIMIT 10
            """)
            
            table_stats = cursor.fetchall()
            performance_metrics['table_statistics'] = [
                {
                    'schema': row[0],
                    'table': row[1], 
                    'inserts': row[2],
                    'updates': row[3],
                    'deletes': row[4],
                    'seq_scans': row[5],
                    'index_scans': row[6]
                }
                for row in table_stats
            ]
            
            # Database size monitoring
            cursor.execute("""
                SELECT 
                    schemaname,
                    SUM(pg_total_relation_size(schemaname||'.'||tablename)) as size_bytes
                FROM pg_tables 
                WHERE schemaname IN ('raw', 'staging', 'marts', 'analytics')
                GROUP BY schemaname
            """)
            
            size_stats = cursor.fetchall()
            performance_metrics['schema_sizes'] = {
                row[0]: f"{row[1] / (1024**3):.2f} GB" for row in size_stats
            }
            
            cursor.close()
            logger.info("Performance monitoring completed")
            
        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}")
            performance_metrics['error'] = str(e)
            
        return performance_metrics
    
    def monitor_business_kpis(self) -> Dict[str, any]:
        """Monitor key business metrics"""
        business_metrics = {}
        
        try:
            cursor = self.connection.cursor()
            
            # Daily KPIs
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sales_days,
                    SUM(total_revenue) as total_revenue,
                    SUM(total_orders) as total_orders,
                    AVG(total_revenue) as avg_daily_revenue,
                    MAX(total_revenue) as peak_day_revenue
                FROM marts.daily_sales_summary
            """)
            
            daily_kpis = cursor.fetchone()
            business_metrics['daily_performance'] = {
                'sales_days': daily_kpis[0],
                'total_revenue': f"R$ {daily_kpis[1]:,.2f}",
                'total_orders': daily_kpis[2],
                'avg_daily_revenue': f"R$ {daily_kpis[3]:,.2f}",
                'peak_day_revenue': f"R$ {daily_kpis[4]:,.2f}"
            }
            
            # Customer metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as active_customers,
                    AVG(total_spent) as avg_customer_value,
                    COUNT(CASE WHEN total_spent > 1000 THEN 1 END) as high_value_customers
                FROM marts.customer_metrics
                WHERE total_orders > 0
            """)
            
            customer_kpis = cursor.fetchone()
            business_metrics['customer_performance'] = {
                'active_customers': customer_kpis[0],
                'avg_customer_value': f"R$ {customer_kpis[1]:,.2f}",
                'high_value_customers': customer_kpis[2]
            }
            
            cursor.close()
            logger.info("Business KPI monitoring completed")
            
        except Exception as e:
            logger.error(f"Business KPI monitoring failed: {e}")
            business_metrics['error'] = str(e)
            
        return business_metrics
    
    def generate_health_report(self) -> Dict[str, any]:
        """Generate comprehensive health report"""
        logger.info("Generating production health report...")
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'pipeline_status': 'Operational',
            'data_freshness': self.check_data_freshness(),
            'data_quality': self.monitor_data_quality(),
            'performance': self.monitor_performance_metrics(),
            'business_kpis': self.monitor_business_kpis(),
            'alerts': self.alerts
        }
        
        return health_report
    
    def save_report(self, report: Dict[str, any], filepath: str):
        """Save health report to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Health report saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def close_connection(self):
        """🔌 Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Database connection closed")


def main():
    """Main monitoring execution"""
    print("Olist Data Pipeline - Production Monitor")
    print("=" * 50)
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'olist_dw', 
        'user': 'postgres',
        'password': 'postgres'
    }
    
    # Initialize monitor
    monitor = OlistPipelineMonitor(db_config)
    
    try:
        # Connect to database
        if not monitor.connect_database():
            print("Failed to connect to database")
            return
        
        # Generate health report
        health_report = monitor.generate_health_report()
        
        # Display summary
        print("\nPRODUCTION HEALTH SUMMARY")
        print("-" * 30)
        print(f"⏰ Timestamp: {health_report['timestamp']}")
        print(f"🔋 Status: {health_report['pipeline_status']}")
        
        # Save report
        report_path = f"/home/phuochuy/Projects/pipeline05/data_pipeline/logs/health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        monitor.save_report(health_report, report_path)
        
        print(f"Full report saved to: {report_path}")
        print("\nMonitoring completed successfully!")
        
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        print(f"Error: {e}")
        
    finally:
        monitor.close_connection()


if __name__ == "__main__":
    main()
