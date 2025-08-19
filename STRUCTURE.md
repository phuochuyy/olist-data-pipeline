# 📁 Project Structure

```
📦 data_pipeline/
├── 📁 airflow/                 # Apache Airflow configurations
│   ├── 📁 dags/               # DAG definitions
│   ├── 📁 logs/               # Airflow logs (gitignored)
│   └── 📁 plugins/            # Custom Airflow plugins
├── 📁 config/                 # Configuration files
│   └── 📁 grafana/           # Grafana datasources config
├── 📁 data/                   # 🆕 CSV data files
│   ├── olist_customers_dataset.csv
│   ├── olist_orders_dataset.csv
│   ├── olist_order_items_dataset.csv
│   ├── olist_order_payments_dataset.csv
│   ├── olist_order_reviews_dataset.csv
│   ├── olist_products_dataset.csv
│   ├── olist_sellers_dataset.csv
│   ├── olist_geolocation_dataset.csv
│   └── product_category_name_translation.csv
├── 📁 dbt_project/            # dbt transformations
│   ├── 📁 models/            # dbt models
│   │   ├── 📁 sources/       # Source definitions
│   │   ├── 📁 staging/       # Staging models
│   │   └── 📁 marts/         # Business marts
│   ├── dbt_project.yml       # dbt project config
│   ├── profiles.yml          # dbt connection profiles
│   └── packages.yml          # 🆕 dbt package dependencies
├── 📁 great_expectations/     # Data quality tests
├── 📁 init/                   # Database initialization scripts
├── 📁 spark/                  # Apache Spark jobs
│   └── data_processor.py     # Main data processing script
├── 📄 docker-compose.yml      # Docker services definition
├── 📄 Dockerfile.airflow      # 🆕 Custom Airflow image with dbt
├── 📄 Makefile               # Project commands
├── 📄 README.md              # Project documentation
├── 📄 requirements.txt       # Python dependencies
├── 📄 setup.sh              # Setup script
└── 📄 .gitignore            # 🆕 Git ignore rules
```

## 🗑️ Files Removed During Cleanup

### ❌ Removed Files:
- `simple_data_loader.py` - Temporary data loading script
- `data_pipeline/` - Duplicate directory structure
- `dbt_project/target/` - Generated dbt files
- `dbt_project/logs/` - dbt log files
- `dbt_project/.user.yml` - User-specific dbt config
- `airflow/dags/__pycache__/` - Python cache files

### 📝 New Files:
- `.gitignore` - Git ignore rules for generated files
- `STRUCTURE.md` - This documentation

## 🔧 Path Updates Made:
- Data files moved to `/data/` directory
- Docker volume mounts updated to use `./data/` instead of `../`
- Spark data processor path updated to `/opt/airflow/data`

## 🎯 Benefits of Cleanup:
- ✅ Cleaner project structure
- ✅ No duplicate files or directories  
- ✅ Proper gitignore to avoid committing generated files
- ✅ Organized data files in dedicated directory
- ✅ Consistent path mappings across services
