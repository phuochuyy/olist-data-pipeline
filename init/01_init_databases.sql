-- Executed once by the postgres image on first start (empty volume),
-- connected to POSTGRES_DB (olist_dw).

-- Metadata database used by Airflow (AIRFLOW__DATABASE__SQL_ALCHEMY_CONN)
CREATE DATABASE airflow;

-- Medallion layers written by spark/data_processor.py and dbt
CREATE SCHEMA IF NOT EXISTS raw;      -- bronze
CREATE SCHEMA IF NOT EXISTS staging;  -- silver
CREATE SCHEMA IF NOT EXISTS marts;    -- gold
