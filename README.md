# Olist Data Pipeline

Batch pipeline for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (9 CSV files, ~1.55 M rows): Spark loads and models the data in PostgreSQL (bronze → silver → gold), dbt builds the analytics layer, data quality is checked with SQL, Great Expectations and dbt tests, Airflow runs it all daily, Grafana shows the business KPIs and the pipeline's own metrics.

```
                    ┌──────────────────────────── Airflow DAG (daily) ────────────────────────────┐
CSV (./data) ─Spark─▶ raw.*  ─Spark─▶ staging.*            ─Spark─▶ marts.customer_metrics
                      bronze          silver: dim_customers,         marts.daily_sales_summary
                        │             dim_products, dim_sellers,      gold
                        │             dim_geolocation, fact_orders
                        ├─ SQL checks + Great Expectations (15 expectations)
                        └─dbt─▶ staging.stg_customers ─▶ marts.mart_customer_analytics ─▶ analytics.revenue_by_state
                                                                                          analytics.monthly_trends
                                                                                          analytics.top_customers
                    every run: row counts per table ─▶ monitoring.pipeline_metrics ─▶ Grafana
```

**Stack:** Airflow 2.8 · Spark 3.5 · PostgreSQL 14 · dbt 1.7 · Great Expectations 0.18 · Grafana 13 · Docker Compose

## Run

```bash
# 1. Data (public Kaggle dataset, not stored in git)
curl -L -o olist.zip https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce
unzip olist.zip -d data

# 2. Start everything (first build takes a few minutes)
docker compose up -d --build

# 3. Airflow http://localhost:8080 (admin/admin): unpause `olist_data_pipeline`; it runs once, then daily

# 4. Optional checks
python tests/automated_test_suite.py        # needs psycopg2-binary + pandas; uses localhost:5432
python monitoring/production_monitor.py     # health report JSON in ./logs
```

| Service | URL | Login |
|---|---|---|
| Airflow | http://localhost:8080 | admin / admin |
| Grafana, dashboard "Olist overview" | http://localhost:3000 | admin / admin |
| Spark master | http://localhost:8081 | - |
| Jupyter | http://localhost:8888 | token in `docker compose logs jupyter` |
| PostgreSQL | localhost:5432, db `olist_dw` | postgres / postgres |

Local demo credentials only.

## DAG

`health_check_postgres → clean_staging_data → spark_data_processing → [data_quality_check, business_rules_validation, great_expectations_validation] → dbt_build → update_marts_metadata → generate_data_report → backup_marts_data → cleanup_old_backups`

- **spark_data_processing**: `spark-submit` from the Airflow container to the Spark cluster (driver in Airflow, executors on the worker).
- **Quality gates** before anything is built on the data: SQL null checks, business rules, Great Expectations on the bronze tables, then `dbt build` (5 models, 30 tests).
- **generate_data_report**: row counts of every table into `monitoring.pipeline_metrics`.

## Results (fresh `docker compose down -v && up --build`, 2026-11-12)

| Check | Result |
|---|---|
| DAG, first run on empty volumes | 11/11 tasks succeeded, 76 s (Spark 45 s, dbt 15 s, GX 6 s) |
| DAG, re-run on existing data | 11/11 succeeded, 69 s |
| dbt build | 5 models, 30 tests passed |
| Great Expectations | 15/15 expectations passed on 5 bronze tables |
| `tests/automated_test_suite.py` | 7/7 passed (bronze, silver, gold, data quality, analytics, monitoring, performance) |
| `monitoring/production_monitor.py` | runs without errors |
| Grafana | datasource health OK, dashboard with 9 panels, all queries return data |

| Layer | Tables (rows) |
|---|---|
| bronze `raw` | customers 99,441 · orders 99,441 · order_items 112,650 · order_payments 103,886 · order_reviews 99,224 · products 32,951 · sellers 3,095 · geolocation 1,000,163 · product_category_translation 71 |
| silver `staging` | dim_customers 99,441 · dim_products 32,951 · dim_sellers 3,095 · dim_geolocation 19,015 · fact_orders 112,650 |
| gold `marts` | customer_metrics 96,478 · daily_sales_summary 612 · mart_customer_analytics 93,358 |
| `analytics` | revenue_by_state 27 · monthly_trends 23 · top_customers 500 |

## Modelling notes

- **Customer grain.** Olist issues a new `customer_id` for every order; `customer_unique_id` is the person. Grouped by `customer_id`, nobody ever has a second order. The dbt mart and `analytics.top_customers` use `customer_unique_id`: 93,358 customers, 2,801 with more than one delivered order.
- **Average order value** = revenue / distinct orders. `order_items` has one row per item (no quantity column), so an average over item rows is the average item price, not the AOV.
- **Revenue** in the Spark marts and analytics tables is item price of delivered orders; the customer mart's `total_spent` includes freight.
- dbt models in `analytics` are tables, not views: Spark drops and recreates its tables on each run, and a view on top would block that. Raw tables are reloaded with TRUNCATE for the same reason (the dbt staging view reads them).

## Layout

```
airflow/dags/        DAG
spark/               Spark job (bronze → silver → gold)
dbt_project/         dbt models (staging, marts, analytics) and tests
great_expectations/  GX suites on the bronze tables
config/grafana/      datasource + dashboard provisioning
init/                Postgres init: airflow DB + raw/staging/marts schemas
monitoring/          health report script
tests/               test suite against the live warehouse
```

## License

MIT
