.PHONY: help setup start stop restart logs status clean test dbt-run dbt-test spark-shell spark-bash pyspark spark-test psql backup urls

# Default target
help:
	@echo "🚀 Olist Data Engineering Pipeline Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup         - Initial setup of the pipeline"
	@echo "  start         - Start all services"
	@echo "  stop          - Stop all services"
	@echo "  restart       - Restart all services"
	@echo ""
	@echo "Monitoring Commands:"
	@echo "  logs          - Show logs from all services"
	@echo "  status        - Show status of all services"
	@echo ""
	@echo "Development Commands:"
	@echo "  dbt-run       - Run dbt transformations"
	@echo "  dbt-test      - Run dbt tests"
	@echo "  spark-shell   - Open Spark shell"
	@echo "  psql          - Connect to PostgreSQL"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  clean         - Clean up containers and volumes"
	@echo "  test          - Run data quality tests"
	@echo "  backup        - Backup database"

# Setup pipeline
setup:
	@echo "🔧 Setting up Olist Data Pipeline..."
	chmod +x setup.sh
	./setup.sh

# Start services
start:
	@echo "🚀 Starting services..."
	docker compose up -d
	@echo "✅ Services started!"

# Stop services
stop:
	@echo "🛑 Stopping services..."
	docker compose down
	@echo "✅ Services stopped!"

# Restart services
restart: stop start
	@echo "🔄 Services restarted!"

# Show logs
logs:
	@echo "� Showing logs..."
	docker compose logs -f

# Show service status
status:
	@echo "� Service status:"
	docker compose ps

# Run dbt transformations
dbt-run:
	@echo "🔄 Running dbt transformations..."
	docker compose exec airflow-webserver bash -c "cd /opt/airflow/dbt_project && dbt run"

# Run dbt tests
dbt-test:
	@echo "🧪 Running dbt tests..."
	docker compose exec airflow-webserver bash -c "cd /opt/airflow/dbt_project && dbt test"

# Open Spark shell (with instructions due to ivy config issue)
spark-shell:
	@echo "� Spark Shell Setup:"
	@echo ""
	@echo "Due to Bitnami Spark ivy configuration, use manual setup:"
	@echo "1. Run: make spark-bash"
	@echo "2. Inside container run: python3"
	@echo "3. Setup PySpark:"
	@echo "   from pyspark.sql import SparkSession"
	@echo "   spark = SparkSession.builder.appName('Interactive').master('local[*]').getOrCreate()"
	@echo "   spark.range(5).show()  # Test"
	@echo ""
	@make spark-bash

# Access Spark container bash
spark-bash:
	@echo "💻 Opening Spark container bash..."
	@echo "💡 Inside container you can run PySpark commands"
	docker compose exec spark-master bash

# PySpark shell (alias to spark-shell)
pyspark: spark-shell

# Test Spark installation
spark-test:
	@echo "🧪 Testing Spark installation..."
	docker compose exec spark-master python3 -c "import pyspark; print('✅ PySpark version:', pyspark.__version__)"

# Connect to PostgreSQL
psql:
	@echo "🗄️ Connecting to PostgreSQL..."
	docker compose exec postgres psql -U postgres -d olist_dw

# Run data quality tests
test:
	@echo "🧪 Running data quality tests..."
	docker compose exec airflow-webserver python3 /opt/airflow/great_expectations/data_quality.py

# Backup database
backup:
	@echo "💾 Creating database backup..."
	docker compose exec postgres pg_dump -U postgres olist_dw > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup completed!"

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	docker compose down -v
	docker system prune -f
	@echo "✅ Cleanup completed!"

# Show service URLs
urls:
	@echo "🌐 Service URLs:"
	@echo "• Airflow:  http://localhost:8080 (admin/admin)"
	@echo "• Grafana:  http://localhost:3000 (admin/admin)"
	@echo "• Jupyter:  http://localhost:8888"
	@echo "• Spark UI: http://localhost:8081"