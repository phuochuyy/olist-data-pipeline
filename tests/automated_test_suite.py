#!/usr/bin/env python3
"""
Olist Data Pipeline - Automated Testing Suite
===============================================

Comprehensive test suite for production data pipeline validation,
including data quality, business logic, and performance tests.

Author: Data Engineering Team
Date: August 24, 2025
"""

import unittest
import psycopg2
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OlistPipelineTestSuite(unittest.TestCase):
    """Comprehensive test suite for Olist data pipeline"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.db_config = {
            'host': 'localhost',
            'port': '5432', 
            'database': 'olist_dw',
            'user': 'postgres',
            'password': 'postgres'
        }
        
        try:
            cls.connection = psycopg2.connect(**cls.db_config)
            cls.cursor = cls.connection.cursor()
            logger.info("Test database connection established")
        except Exception as e:
            logger.error(f"Test setup failed: {e}")
            raise
    
    @classmethod 
    def tearDownClass(cls):
        """Clean up test environment"""
        if hasattr(cls, 'connection'):
            cls.connection.close()
            logger.info("🔌 Test database connection closed")
    
    def test_bronze_layer_data_integrity(self):
        """🥉 Test Bronze Layer - Raw data integrity"""
        logger.info("Testing Bronze Layer data integrity...")
        
        # Test 1: Check all expected tables exist
        self.cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'raw'
            ORDER BY table_name
        """)
        
        raw_tables = [row[0] for row in self.cursor.fetchall()]
        expected_tables = [
            'customers', 'geolocation', 'order_items', 'order_payments',
            'order_reviews', 'orders', 'products', 'sellers', 'product_category_translation'
        ]
        
        for table in expected_tables:
            self.assertIn(table, raw_tables, f"Missing table: raw.{table}")
        
        # Test 2: Check data volumes
        volume_tests = {
            'customers': 90000,  # Expected minimum records
            'orders': 90000,
            'order_items': 100000,
            'products': 30000
        }
        
        for table, min_count in volume_tests.items():
            self.cursor.execute(f"SELECT COUNT(*) FROM raw.{table}")
            actual_count = self.cursor.fetchone()[0]
            self.assertGreater(actual_count, min_count, 
                             f"Insufficient data in raw.{table}: {actual_count} < {min_count}")
        
        logger.info("Bronze Layer integrity tests passed")
    
    def test_silver_layer_transformations(self):
        """🥈 Test Silver Layer - Data transformations"""
        logger.info("Testing Silver Layer transformations...")
        
        # Test 1: Check staging tables exist and have data
        staging_tables = ['dim_customers', 'dim_products', 'dim_sellers', 
                         'dim_geolocation', 'fact_orders']
        
        for table in staging_tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM staging.{table}")
            count = self.cursor.fetchone()[0]
            self.assertGreater(count, 0, f"Empty staging table: {table}")
        
        # Test 2: Data quality checks
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(customer_key) as non_null_keys,
                COUNT(DISTINCT customer_key) as unique_keys
            FROM staging.dim_customers
        """)
        
        result = self.cursor.fetchone()
        total, non_null, unique = result
        
        # All records should have non-null keys
        self.assertEqual(total, non_null, "Found NULL customer keys in staging")
        # All keys should be unique
        self.assertEqual(non_null, unique, "Found duplicate customer keys in staging")
        
        # Test 3: Foreign key relationships
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM staging.fact_orders f
            LEFT JOIN staging.dim_customers c ON f.customer_key = c.customer_key
            WHERE c.customer_key IS NULL
        """)
        
        orphaned_orders = self.cursor.fetchone()[0]
        self.assertEqual(orphaned_orders, 0, "Found orphaned orders in fact table")
        
        logger.info("Silver Layer transformation tests passed")
    
    def test_gold_layer_business_logic(self):
        """🥇 Test Gold Layer - Business logic validation"""
        logger.info("Testing Gold Layer business logic...")
        
        # Test 1: Customer metrics accuracy
        self.cursor.execute("""
            SELECT 
                customer_id,
                total_orders,
                total_spent,
                avg_order_value
            FROM marts.customer_metrics 
            WHERE total_orders > 0
            LIMIT 5
        """)
        
        for row in self.cursor.fetchall():
            customer_id, total_orders, total_spent, avg_order_value = row
            
            # Verify avg_order_value calculation
            expected_avg = total_spent / total_orders
            self.assertAlmostEqual(avg_order_value, expected_avg, places=2,
                                 msg=f"Incorrect avg_order_value for customer {customer_id}")
        
        # Test 2: Daily sales summary consistency
        self.cursor.execute("""
            SELECT 
                date_key,
                total_orders,
                total_revenue,
                avg_order_value
            FROM marts.daily_sales_summary
            WHERE total_orders > 0
            ORDER BY date_key DESC
            LIMIT 5
        """)
        
        for row in self.cursor.fetchall():
            date_key, total_orders, total_revenue, avg_order_value = row
            
            # Verify avg_order_value calculation
            expected_avg = total_revenue / total_orders
            self.assertAlmostEqual(avg_order_value, expected_avg, places=2,
                                 msg=f"Incorrect daily avg_order_value for {date_key}")
        
        # Test 3: Revenue calculations
        self.cursor.execute("""
            SELECT SUM(total_revenue) 
            FROM marts.daily_sales_summary
        """)
        marts_revenue = self.cursor.fetchone()[0]
        
        self.cursor.execute("""
            SELECT SUM(price * quantity) 
            FROM raw.order_items oi
            JOIN raw.orders o ON oi.order_id = o.order_id
            WHERE o.order_status = 'delivered'
        """)
        raw_revenue = self.cursor.fetchone()[0]
        
        # Allow 1% tolerance for rounding differences
        self.assertAlmostEqual(marts_revenue, raw_revenue, delta=raw_revenue * 0.01,
                              msg="Revenue mismatch between raw and marts layers")
        
        logger.info("Gold Layer business logic tests passed")
    
    def test_data_quality_rules(self):
        """Test data quality rules"""
        logger.info("Testing data quality rules...")
        
        # Test 1: No duplicate orders
        self.cursor.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT order_id) as duplicates
            FROM raw.orders
        """)
        duplicates = self.cursor.fetchone()[0]
        self.assertEqual(duplicates, 0, "Found duplicate orders in raw data")
        
        # Test 2: Valid order statuses
        self.cursor.execute("""
            SELECT DISTINCT order_status 
            FROM raw.orders
            WHERE order_status NOT IN (
                'delivered', 'shipped', 'processing', 'canceled', 
                'unavailable', 'invoiced', 'created', 'approved'
            )
        """)
        invalid_statuses = self.cursor.fetchall()
        self.assertEqual(len(invalid_statuses), 0, f"Found invalid order statuses: {invalid_statuses}")
        
        # Test 3: Positive prices and quantities
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM raw.order_items 
            WHERE price <= 0 OR quantity <= 0
        """)
        invalid_amounts = self.cursor.fetchone()[0]
        self.assertEqual(invalid_amounts, 0, "Found non-positive prices or quantities")
        
        # Test 4: Valid date ranges
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM raw.orders 
            WHERE order_purchase_timestamp < '2016-01-01' 
               OR order_purchase_timestamp > CURRENT_DATE
        """)
        invalid_dates = self.cursor.fetchone()[0]
        self.assertEqual(invalid_dates, 0, "Found orders with invalid dates")
        
        logger.info("Data quality rules tests passed")
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        logger.info("Testing performance benchmarks...")
        
        import time
        
        # Test 1: Customer metrics query performance
        start_time = time.time()
        self.cursor.execute("""
            SELECT customer_id, total_spent, total_orders
            FROM marts.customer_metrics
            WHERE total_spent > 1000
            ORDER BY total_spent DESC
            LIMIT 100
        """)
        self.cursor.fetchall()
        query_time = time.time() - start_time
        
        self.assertLess(query_time, 2.0, f"Customer metrics query too slow: {query_time:.2f}s")
        
        # Test 2: Daily sales aggregation performance
        start_time = time.time()
        self.cursor.execute("""
            SELECT 
                date_key,
                SUM(total_revenue) as revenue,
                COUNT(*) as order_count
            FROM marts.daily_sales_summary
            WHERE date_key >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY date_key
            ORDER BY date_key DESC
        """)
        self.cursor.fetchall()
        query_time = time.time() - start_time
        
        self.assertLess(query_time, 3.0, f"Daily sales query too slow: {query_time:.2f}s")
        
        logger.info("Performance benchmark tests passed")
    
    def test_analytics_views(self):
        """Test analytics views"""
        logger.info("Testing analytics views...")
        
        # Test 1: Revenue by state view
        self.cursor.execute("SELECT COUNT(*) FROM analytics.revenue_by_state")
        state_count = self.cursor.fetchone()[0]
        self.assertGreater(state_count, 20, "Insufficient states in analytics view")
        
        # Test 2: Monthly trends view
        self.cursor.execute("SELECT COUNT(*) FROM analytics.monthly_trends")
        month_count = self.cursor.fetchone()[0]
        self.assertGreater(month_count, 10, "Insufficient months in trends view")
        
        # Test 3: Top customers view
        self.cursor.execute("""
            SELECT COUNT(*), AVG(total_revenue) 
            FROM analytics.top_customers
        """)
        result = self.cursor.fetchone()
        customer_count, avg_revenue = result
        
        self.assertGreater(customer_count, 100, "Insufficient top customers")
        self.assertGreater(avg_revenue, 500, "Low average revenue for top customers")
        
        logger.info("Analytics views tests passed")
    
    def test_monitoring_infrastructure(self):
        """Test monitoring infrastructure"""
        logger.info("Testing monitoring infrastructure...")
        
        # Test 1: Monitoring schema exists
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.schemata 
            WHERE schema_name = 'monitoring'
        """)
        schema_exists = self.cursor.fetchone()[0]
        self.assertEqual(schema_exists, 1, "Monitoring schema missing")
        
        # Test 2: Pipeline metrics table exists
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'monitoring' 
            AND table_name = 'pipeline_metrics'
        """)
        table_exists = self.cursor.fetchone()[0]
        self.assertEqual(table_exists, 1, "Pipeline metrics table missing")
        
        logger.info("Monitoring infrastructure tests passed")


def run_test_suite():
    """Run complete test suite"""
    print("\nOlist Data Pipeline - Automated Test Suite")
    print("=" * 55)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(OlistPipelineTestSuite)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=None)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 55)
    print("TEST RESULTS SUMMARY")
    print("-" * 25)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"⏱️ Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception: ')[-1].split('\\n')[0]}")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_test_suite()
    exit(0 if success else 1)
