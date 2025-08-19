# 🚀 Olist Data Engineering Pipeline


Pipeline này được thiết kế theo mô hình **Medallion Architecture** (Bronze-Silver-Gold) với các layers:

- **Bronze Layer (Raw)**: Dữ liệu thô từ CSV files
- **Silver Layer (Staging)**: Dữ liệu đã được làm sạch và chuẩn hóa  
- **Gold Layer (Marts)**: Dữ liệu đã được tổng hợp và sẵn sàng cho analytics

### Công nghệ sử dụng

| Thành phần | Công nghệ | Mục đích |
|------------|-----------|----------|
| **Orchestration** | Apache Airflow | Điều phối và lập lịch pipeline |
| **Data Processing** | Apache Spark | Xử lý dữ liệu quy mô lớn |
| **Data Warehouse** | PostgreSQL | Lưu trữ dữ liệu |
| **Data Transformation** | dbt | Transformation và modeling |
| **Data Quality** | Great Expectations | Kiểm tra chất lượng dữ liệu |
| **Monitoring** | Grafana | Giám sát và visualization |
| **Caching** | Redis | Cache cho hiệu suất |
| **Containerization** | Docker | Container hóa services |
| **Exploration** | Jupyter Lab | Data exploration và analysis |

## 📊 Dataset

Dữ liệu Olist bao gồm 9 bảng chính:

1. **olist_customers_dataset.csv** - Thông tin khách hàng
2. **olist_orders_dataset.csv** - Thông tin đơn hàng
3. **olist_order_items_dataset.csv** - Chi tiết sản phẩm trong đơn hàng
4. **olist_order_payments_dataset.csv** - Thông tin thanh toán
5. **olist_order_reviews_dataset.csv** - Đánh giá của khách hàng
6. **olist_products_dataset.csv** - Catalog sản phẩm
7. **olist_sellers_dataset.csv** - Thông tin người bán
8. **olist_geolocation_dataset.csv** - Dữ liệu địa lý
9. **product_category_name_translation.csv** - Dịch tên danh mục

## 🚀 Hướng dẫn cài đặt

### Cài đặt nhanh

```bash

cd ...

# Chạy script cài đặt
make setup

# Hoặc chạy thủ công
chmod +x data_pipeline/setup.sh
./data_pipeline/setup.sh
```

### Cài đặt từng bước

1. **Khởi động services**:
```bash
make start
```

2. **Kiểm tra trạng thái**:
```bash
make status
```

3. **Xem logs**:
```bash
make logs
```

## 🎯 Sử dụng

### 1. Truy cập các giao diện

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Airflow | http://localhost:8080 | admin | admin |
| Spark UI | http://localhost:8081 | - | - |
| Grafana | http://localhost:3000 | admin | admin |
| Jupyter Lab | http://localhost:8888 | - | - |

### 2. Chạy Pipeline

1. Truy cập Airflow UI (http://localhost:8080)
2. Đăng nhập với admin/admin
3. Tìm DAG `olist_data_pipeline`
4. Enable DAG và trigger chạy

### 3. Giám sát Pipeline

- **Airflow**: Theo dõi task execution và logs
- **Spark UI**: Giám sát Spark jobs và performance
- **Grafana**: Dashboards cho business metrics
- **Jupyter**: Data exploration và analysis



## 🔄 Data Flow

```
CSV Files → Raw Layer (Bronze) → Staging Layer (Silver) → Marts Layer (Gold) → Analytics
    ↓              ↓                    ↓                   ↓              ↓
 Ingestion    Data Quality      Transformation        Aggregation    Visualization
```

### Luồng xử lý chi tiết:

1. **Data Ingestion**: Spark đọc CSV files và load vào raw schema
2. **Data Quality**: Great Expectations kiểm tra chất lượng dữ liệu
3. **Data Transformation**: dbt transform data từ raw → staging → marts
4. **Data Validation**: Kiểm tra business rules và data consistency
5. **Analytics**: Tạo dashboards và reports trong Grafana



## 🔧 Cấu hình

### Environment Variables

Tạo file `.env` trong thư mục `data_pipeline`:

```env
# Database
POSTGRES_DB=olist_dw
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Airflow
AIRFLOW__CORE__FERNET_KEY=your-fernet-key
AIRFLOW__WEBSERVER__SECRET_KEY=your-secret-key

# Spark
SPARK_WORKER_MEMORY=2G
SPARK_WORKER_CORES=2
```

### Scaling

Để scale pipeline cho production:

1. **Tăng Spark workers**:
```yaml
spark-worker:
  deploy:
    replicas: 3
```

2. **Cấu hình Airflow Executor**:
```yaml
AIRFLOW__CORE__EXECUTOR: CeleryExecutor
```

3. **Thêm monitoring**:
- Prometheus metrics
- ELK stack for logging
- Alerting với PagerDuty/Slack


## 🔧 Development & Deployment

### Local Development

1. **Clone repository**:
```bash
git clone https://github.com/your-username/olist-data-pipeline.git
cd olist-data-pipeline
```

2. **Copy environment files**:
```bash
cp .env.example .env
cp dbt_project/profiles.yml.example dbt_project/profiles.yml
```

3. **Run setup**:
```bash
make setup
make up
```



## 📄 License

MIT License - xem file [LICENSE](LICENSE) để biết thêm chi tiết.

