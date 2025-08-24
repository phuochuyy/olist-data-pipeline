#!/bin/bash

# Olist Data Pipeline Setup Script
echo "Setting up Olist Data Engineering Pipeline..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p data_pipeline/airflow/logs
mkdir -p data_pipeline/airflow/plugins
mkdir -p data_pipeline/notebooks
mkdir -p data_pipeline/spark/jars

# Download PostgreSQL JDBC driver for Spark
echo "Downloading PostgreSQL JDBC driver..."
if [ ! -f data_pipeline/spark/jars/postgresql-42.6.0.jar ]; then
    curl -L https://jdbc.postgresql.org/download/postgresql-42.6.0.jar \
         -o data_pipeline/spark/jars/postgresql-42.6.0.jar
fi

# Set proper permissions
echo "Setting permissions..."
chmod -R 755 data_pipeline/airflow
chmod +x setup.sh

# Copy CSV files to data directory (if they exist)
echo "Preparing data files..."
if [ -f olist_customers_dataset.csv ]; then
    echo "Found CSV files in current directory"
else
    echo "CSV files not found in current directory"
    echo "   Please ensure all Olist CSV files are in the project root"
fi

# Build and start services
echo "Starting Docker services..."
cd data_pipeline
docker compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Check service status
echo "Checking service status..."
docker compose ps

echo ""
echo "Setup completed! Services are starting up..."
echo ""
echo "Access URLs:"
echo "   Airflow Web UI: http://localhost:8080 (admin/admin)"
echo "   Spark Master UI: http://localhost:8081"
echo "   Grafana: http://localhost:3000 (admin/admin)"
echo "   Jupyter Lab: http://localhost:8888"
echo ""
echo "Database Connection:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: olist_dw"
echo "   Username: postgres"
echo "   Password: postgres"
echo ""
echo "Next steps:"
echo "   1. Wait for all services to be fully ready (2-3 minutes)"
echo "   2. Access Airflow UI and enable the 'olist_data_pipeline' DAG"
echo "   3. Trigger the DAG to start the data pipeline"
echo "   4. Monitor progress in Airflow and Spark UIs"
echo "   5. View results in Grafana dashboards"
