# 🚀 Quick Start Guide

## One-command setup

```bash
# Clone and setup the entire pipeline
git clone https://github.com/your-username/olist-data-pipeline.git
cd olist-data-pipeline
make setup && make up
```

## What this includes

🏗️ **Complete data engineering stack**:
- Apache Airflow (Orchestration)
- Apache Spark (Processing) 
- PostgreSQL (Data Warehouse)
- dbt (Transformations)
- Grafana (Monitoring)
- Jupyter (Analysis)
- Redis (Caching)
- Great Expectations (Data Quality)

📊 **1.5M+ records processed** from 9 CSV files

🧪 **15 data quality tests** all passing

📈 **Ready-to-use dashboards** for customer analytics

## Access points

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Airflow | http://localhost:8080 | admin | admin |
| Grafana | http://localhost:3000 | admin | admin |
| Jupyter | http://localhost:8888 | - | - |
| Spark UI | http://localhost:8081 | - | - |

## First steps

1. **Open Airflow**: http://localhost:8080
2. **Enable DAG**: Toggle `olist_pipeline_dag` 
3. **Trigger run**: Click play button
4. **Monitor progress**: Watch tasks complete
5. **View results**: Check Grafana dashboards

## Need help?

- 📖 [Full Documentation](README.md)
- 🤝 [Contributing Guide](CONTRIBUTING.md)
- 🐛 [Report Issues](https://github.com/your-username/olist-data-pipeline/issues)

---
⭐ **Star this repo** if it helped you learn data engineering!
