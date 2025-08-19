.PHONY: help setup start stop restart logs clean test dbt-run dbt-test

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
	@echo "📋 Showing logs..."
	docker compose logs -f

# Show service status
status:
	@echo "📊 Service status:"
	docker compose ps

# Run dbt transformations
dbt-run:
	@echo "🔄 Running dbt transformations..."
	docker compose exec airflow-webserver bash -c "cd /opt/airflow/dbt_project && dbt run"

# Run dbt tests
dbt-test:
	@echo "🧪 Running dbt tests..."
	docker compose exec airflow-webserver bash -c "cd /opt/airflow/dbt_project && dbt test"

# Open Spark shell
spark-shell:
	@echo "🔥 Opening Spark shell..."
	docker compose exec spark-master spark-shell

# Connect to PostgreSQL
psql:
	@echo "🗄️ Connecting to PostgreSQL..."
	docker compose exec postgres psql -U postgres -d olist_dw

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	docker compose down -v
	docker system prune -f
	@echo "✅ Cleanup completed!"

# Run tests
test:
	@echo "🧪 Running data quality tests..."
	docker compose exec airflow-webserver python /opt/airflow/great_expectations/data_quality.py

# Backup database
backup:
	@echo "💾 Creating database backup..."
	mkdir -p backups
	docker compose exec postgres pg_dump -U postgres olist_dw > ../backups/olist_dw_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup created in backups/ directory"

# Show pipeline URLs
urls:
	@echo "🌐 Pipeline Access URLs:"
	@echo "   Airflow Web UI: http://localhost:8080"
	@echo "   Spark Master UI: http://localhost:8081"
	@echo "   Grafana: http://localhost:3000"
	@echo "   Jupyter Lab: http://localhost:8888"
