# Olist Data Pipeline

Daily batch pipeline for the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (9 CSV files, ~1.5 M rows). Spark loads it into PostgreSQL in three layers, dbt builds reporting tables, quality checks run before anything is published, and Grafana shows the results.

```
CSV --Spark--> bronze (raw) --Spark--> silver (staging) --Spark--> gold (marts)
                   |
                   +-- quality checks: SQL + Great Expectations
                   +-- dbt --> customer mart + analytics tables --> Grafana
Airflow runs all of it daily (11 tasks).
```

**Stack:** Airflow · Spark · PostgreSQL · dbt · Great Expectations · Grafana · Docker Compose

## Run

```bash
# data (public Kaggle dataset, not in git)
curl -L -o olist.zip https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce
unzip olist.zip -d data

docker compose up -d --build
```

Then open Airflow at http://localhost:8080 (admin/admin) and unpause `olist_data_pipeline`. A run takes about 75 seconds. The dashboard is at http://localhost:3000 (admin/admin) -> "Olist overview".

## What happens in a run

1. **Spark** reads the CSVs into `raw.*`, builds dimensions and an order fact table in `staging.*`, and daily sales and customer metrics in `marts.*`.
2. **Quality gates**: null checks, business rules and 15 Great Expectations rules on the raw tables.
3. **dbt** builds the customer mart and three analytics tables (revenue by state, by month, top customers) and runs 30 tests.
4. **Monitoring**: row counts of every table go into `monitoring.pipeline_metrics` and appear in Grafana.

## Two things I learned from the data

- **`customer_id` is not the customer.** Olist creates a new `customer_id` for every order; `customer_unique_id` is the person. Grouped by `customer_id`, nobody ever orders twice. Grouped correctly: 93,358 customers, 2,801 of them repeat buyers.
- **Average order value = revenue / orders.** The items table has one row per item, so a plain average over rows gives the average item price instead.

## Verified

From a clean start (`docker compose down -v && up --build`): DAG 11/11 tasks green, dbt 30/30 tests, Great Expectations 15/15, test suite (`python tests/automated_test_suite.py`) 7/7.

Local demo passwords only (admin/admin, postgres/postgres).
