# Olist Data Pipeline

Batch pipeline for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (9 CSV files, ~1.55 M rows), using a medallion layout in PostgreSQL.

```
CSV (./data) ──Spark──▶ raw.*  (bronze) ──Spark──▶ staging.* (silver) ──Spark──▶ marts.* (gold)
                           │
                           └──dbt──▶ public_staging.stg_customers ──▶ public_marts.mart_customer_analytics
Airflow DAG: health check → clean staging → Spark job → quality + business-rule checks → report → backup marts
Grafana reads the warehouse (datasource provisioned).
```

**Stack:** Airflow 2.8 · Spark 3.5 · PostgreSQL 14 · dbt 1.7 · Grafana · Docker Compose

## Run

```bash
# 1. Data (public Kaggle dataset, not stored in git)
curl -L -o olist.zip https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce
unzip olist.zip -d data

# 2. Start everything (first build takes a few minutes)
docker compose up -d --build

# 3. Airflow http://localhost:8080 (admin/admin): unpause and trigger `olist_data_pipeline`

# 4. dbt models and tests
make dbt-run
make dbt-test
```

| Service | URL | Login |
|---|---|---|
| Airflow | http://localhost:8080 | admin / admin |
| Grafana | http://localhost:3000 | admin / admin |
| Spark master | http://localhost:8081 | - |
| Jupyter | http://localhost:8888 | token in `docker compose logs jupyter` |
| PostgreSQL | localhost:5432, db `olist_dw` | postgres / postgres |

Local demo credentials only.

## Verified (2026-11-12, Docker Desktop on Windows 11)

- DAG `olist_data_pipeline`: **9/9 tasks succeeded**, about 50 s per run (the Spark job is ~40 s).
- Spark loaded raw: 99,441 customers · 99,441 orders · 112,650 order items · 103,886 payments · 99,224 reviews · 32,951 products · 3,095 sellers · 1,000,163 geolocation rows · 71 category translations. Gold: 96,478 rows in `marts.customer_metrics`, 612 days in `marts.daily_sales_summary`.
- dbt: 2 models built, **15/15 tests passed** (not_null, unique, relationships, accepted_range).
- Grafana datasource health check: OK.

## Known gaps

- `tests/automated_test_suite.py` (runs against the live DB): 2 of 7 pass. Four tests check objects this pipeline does not build (`analytics` and `monitoring` schemas, `staging.dim_sellers`/`fact_orders`, an `order_items.quantity` column). One shows a real definition mismatch: the Spark mart's `avg_order_value` is the average *item* price, the test expects revenue per *order*.
- `great_expectations/data_quality.py` and `monitoring/production_monitor.py` are standalone scripts, not part of the DAG, and were not verified.
- Grafana has the datasource but no dashboards in this repo yet.

## Layout

```
airflow/dags/       DAG
spark/              Spark job (bronze → silver → gold)
dbt_project/        dbt models and source tests
init/               Postgres init: airflow DB + raw/staging/marts schemas
great_expectations/ data quality script (standalone)
monitoring/         health report script (standalone)
tests/              test suite against the live warehouse
```

## License

MIT
