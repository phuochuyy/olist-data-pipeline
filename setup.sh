#!/bin/bash

# Olist Data Pipeline Setup Script
echo "Setting up Olist Data Engineering Pipeline..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose (v2 plugin) is installed
if ! docker compose version &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Always run from the repository root (where docker-compose.yml lives)
cd "$(dirname "$0")"

# Create necessary directories
echo "Creating directories..."
mkdir -p airflow/logs
mkdir -p airflow/plugins
mkdir -p data
mkdir -p spark/jars

# Download PostgreSQL JDBC driver for Spark
echo "Downloading PostgreSQL JDBC driver..."
if [ ! -f spark/jars/postgresql-42.6.0.jar ]; then
    curl -L https://jdbc.postgresql.org/download/postgresql-42.6.0.jar \
         -o spark/jars/postgresql-42.6.0.jar
fi

# Set proper permissions
echo "Setting permissions..."
chmod -R 755 airflow
chmod +x setup.sh

# Check that the Olist CSV files are in ./data (mounted into the containers)
echo "Preparing data files..."
if [ -f data/olist_customers_dataset.csv ]; then
    echo "Found Olist CSV files in ./data"
else
    echo "Olist CSV files not found in ./data"
    echo "   Download https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
    echo "   and extract all 9 CSV files into ./data"
fi

# Build and start services
echo "Starting Docker services..."
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
