import great_expectations as gx
from great_expectations.data_context import FileDataContext
import pandas as pd
import logging

class DataQualityValidator:
    def __init__(self, data_context_path="./great_expectations"):
        self.context = FileDataContext.create(project_root_dir=data_context_path)
        
    def create_expectations_suite(self, suite_name="olist_data_quality"):
        """Create expectations suite for Olist data"""
        
        # Create suite
        suite = self.context.add_or_update_expectation_suite(expectation_suite_name=suite_name)
        
        # Define expectations for customers table
        customer_expectations = [
            {
                "expectation_type": "expect_column_to_exist",
                "kwargs": {"column": "customer_id"}
            },
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "customer_id"}
            },
            {
                "expectation_type": "expect_column_values_to_be_unique",
                "kwargs": {"column": "customer_id"}
            },
            {
                "expectation_type": "expect_column_values_to_match_regex",
                "kwargs": {
                    "column": "customer_state",
                    "regex": r"^[A-Z]{2}$"
                }
            }
        ]
        
        # Define expectations for orders table
        order_expectations = [
            {
                "expectation_type": "expect_column_values_to_not_be_null",
                "kwargs": {"column": "order_id"}
            },
            {
                "expectation_type": "expect_column_values_to_be_unique",
                "kwargs": {"column": "order_id"}
            },
            {
                "expectation_type": "expect_column_values_to_be_in_set",
                "kwargs": {
                    "column": "order_status",
                    "value_set": ["delivered", "shipped", "processing", "canceled", "invoiced", "unavailable"]
                }
            }
        ]
        
        # Define expectations for order_items table
        order_item_expectations = [
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "price",
                    "min_value": 0,
                    "max_value": 10000
                }
            },
            {
                "expectation_type": "expect_column_values_to_be_between",
                "kwargs": {
                    "column": "freight_value",
                    "min_value": 0,
                    "max_value": 1000
                }
            }
        ]
        
        # Add all expectations to suite
        all_expectations = customer_expectations + order_expectations + order_item_expectations
        
        for expectation in all_expectations:
            suite.add_expectation(**expectation)
        
        self.context.save_expectation_suite(suite)
        logging.info(f"Created expectations suite: {suite_name}")
        
        return suite
    
    def validate_data(self, df, table_name, suite_name="olist_data_quality"):
        """Validate dataframe against expectations"""
        
        # Create validator
        validator = self.context.get_validator(
            batch_request=df,
            expectation_suite_name=suite_name
        )
        
        # Run validation
        results = validator.validate()
        
        # Log results
        if results.success:
            logging.info(f"Data validation PASSED for {table_name}")
        else:
            logging.warning(f"Data validation FAILED for {table_name}")
            for result in results.results:
                if not result.success:
                    logging.warning(f"Failed expectation: {result.expectation_config.expectation_type}")
        
        return results
    
    def generate_data_docs(self):
        """Generate data documentation"""
        self.context.build_data_docs()
        logging.info("Data documentation generated successfully")

# Example usage
if __name__ == "__main__":
    validator = DataQualityValidator()
    
    # Create expectations suite
    suite = validator.create_expectations_suite()
    
    # Example validation (would be called from Airflow)
    # df = pd.read_csv("/path/to/customers.csv")
    # results = validator.validate_data(df, "customers")
    
    # Generate documentation
    validator.generate_data_docs()
