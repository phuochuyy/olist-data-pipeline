# Olist Data Pipeline

Data pipeline for Brazilian e-commerce dataset using Medallion Architecture.

## Tech Stack

- **Airflow**: Workflow orchestration
- **Spark**: Data processing
- **PostgreSQL**: Data warehouse
- **Docker**: Containerization
- **Grafana**: Monitoring

## Quick Start

```bash
# Start all services
make start

# Check status
make status

# View logs
make logs
```

## Services

| Service | URL | User | Pass |
|---------|-----|------|------|
| Airflow | http://localhost:8080 | admin | admin |
| Grafana | http://localhost:3000 | admin | admin |
| Jupyter | http://localhost:8888 | - | - |

## Usage

1. Access Airflow at http://localhost:8080
2. Enable `olist_data_pipeline` DAG
3. Trigger manually or wait for schedule
4. Monitor progress in Grafana dashboard

## Data Flow

**Bronze** (Raw CSV) → **Silver** (Cleaned) → **Gold** (Analytics)

- 9 CSV files (~1.4M records)
- Data quality validation
- Customer analytics marts

## Project Structure

```
airflow/dags/          # Pipeline definitions
spark/                 # Data processing scripts
dbt_project/          # Data transformations
monitoring/           # Production monitoring
data/                 # Source CSV files
```

## License

MIT
