# 🚀 Olist Data Engineering Pipeline

Một pipeline data engineering hiện đại và toàn diện cho việc xử lý và phân tích dữ liệu thương mại điện tử Olist (Brazil).

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-017CEE?style=for-the-badge&logo=apache-airflow&logoColor=white)](https://airflow.apache.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white)](https://spark.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![dbt](https://img.shields.io/badge/dbt-FF694B?style=for-the-badge&logo=dbt&logoColor=white)](https://www.getdbt.com/)

> **Note**: Đây là một dự án demo để minh họa kiến trúc data engineering pipeline hiện đại. Code được tối ưu hóa cho môi trường học tập và phát triển.

## 🏗️ Kiến trúc

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

### Yêu cầu hệ thống

- Docker & Docker Compose
- 8GB RAM trở lên
- 10GB dung lượng trống

### Cài đặt nhanh

```bash
# Clone repository và di chuyển vào thư mục dự án
cd /home/phuochuy/Projects/pipeline05

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
- **Jupyter**: Data exploration và ad-hoc analysis

## 📋 Các lệnh hữu ích

```bash
# Khởi động pipeline
make start

# Dừng pipeline
make stop

# Restart pipeline
make restart

# Chạy dbt transformations
make dbt-run

# Chạy dbt tests
make dbt-test

# Kết nối PostgreSQL
make psql

# Mở Spark shell
make spark-shell

# Backup database
make backup

# Dọn dẹp
make clean

# Hiển thị URLs
make urls
```

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

## 📊 Analytics & Reports

### Customer Analytics
- Customer segmentation (VIP, Premium, Regular, New)
- Customer lifetime value
- Purchase behavior analysis
- Geographic distribution

### Product Analytics  
- Best-selling products và categories
- Product performance metrics
- Inventory insights
- Pricing analysis

### Business Metrics
- Daily/Monthly sales trends
- Revenue analytics
- Order fulfillment metrics
- Customer satisfaction scores

## 🧪 Data Quality

Pipeline tích hợp nhiều layers kiểm tra chất lượng dữ liệu:

1. **Schema Validation**: Kiểm tra cấu trúc dữ liệu
2. **Data Profiling**: Phân tích thống kê dữ liệu
3. **Business Rules**: Kiểm tra logic nghiệp vụ
4. **Completeness**: Kiểm tra tính đầy đủ
5. **Accuracy**: Kiểm tra tính chính xác

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

## 📚 Tài liệu tham khảo

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [dbt Documentation](https://docs.getdbt.com/)
- [Great Expectations Documentation](https://docs.greatexpectations.io/)
- [Grafana Documentation](https://grafana.com/docs/)

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

### Production Deployment

- Thay đổi passwords trong `.env`
- Cấu hình external databases
- Setup backup và monitoring
- Implement CI/CD pipeline

## 🚀 Roadmap

- [ ] Thêm CI/CD với GitHub Actions
- [ ] Implement streaming với Kafka
- [ ] Thêm ML models với MLflow
- [ ] Dashboard tự động với Streamlit
- [ ] Data lineage với Apache Atlas
- [ ] Security scanning với Snyk

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Tạo Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact

- **Author**: Your Name
- **Email**: your.email@example.com
- **Project Link**: [https://github.com/your-username/olist-data-pipeline](https://github.com/your-username/olist-data-pipeline)

## 🙏 Acknowledgments

- [Olist Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) on Kaggle
- Apache Software Foundation for amazing open-source tools
- dbt Labs for modern data transformation approach
- Docker community for containerization best practices

## 📄 License

MIT License - xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

**Happy Data Engineering!** 🎉
