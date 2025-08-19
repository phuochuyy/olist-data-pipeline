# 🚀 Olist Data Engineering Pipeline

Data pipeline tự động để xử lý và phân tích dữ liệu e-commerce từ Brazil (Olist dataset).

## ✨ Tính năng chính

- 🔄 **Tự động hóa hoàn toàn**: Chỉ cần 1 lệnh để khởi chạy
- 📊 **Xử lý 1.5M+ records**: 9 bảng dữ liệu thật từ Olist
- 🧪 **Kiểm tra chất lượng**: 15 tests tự động
- 📈 **Dashboard sẵn có**: Phân tích khách hàng và doanh thu
- 🐳 **Docker**: Không cần cài đặt phức tạp

## 🛠️ Công nghệ sử dụng

- **Apache Airflow**: Điều phối pipeline tự động
- **Apache Spark**: Xử lý dữ liệu lớn  
- **PostgreSQL**: Database lưu trữ
- **dbt**: Transform dữ liệu
- **Grafana**: Dashboard và giám sát
- **Docker**: Container hóa tất cả

## � Cài đặt nhanh

```bash
# 1. Clone project
git clone https://github.com/phuochuyy/olist-data-pipeline.git
cd olist-data-pipeline

# 2. Khởi chạy (1 lệnh duy nhất)
make setup && make up
```

**Chờ 2-3 phút để tất cả services khởi động xong.**

## 🎯 Sử dụng

### Truy cập các giao diện

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Airflow (Workflow) | localhost:8080 | admin | admin |
| Grafana (Dashboard) | localhost:3000 | admin | admin |
| Jupyter (Analysis) | localhost:8888 | - | - |

### Chạy Pipeline

1. Mở **Airflow**: http://localhost:8080
2. Đăng nhập: `admin` / `admin`  
3. Tìm DAG: `olist_pipeline_dag`
4. Bật DAG và click **Trigger**
5. Chờ 5-10 phút để hoàn thành

### Xem kết quả

- **Grafana**: Xem dashboard phân tích khách hàng
- **Jupyter**: Khám phá dữ liệu chi tiết

## ⚙️ Các lệnh hữu ích

```bash
# Khởi động
make up

# Dừng lại  
make down

# Xem logs
make logs

# Chạy dbt
make dbt-run

# Test dữ liệu
make dbt-test

# Dọn dẹp
make clean
```

## � Dữ liệu được xử lý

Pipeline tự động xử lý **9 bảng dữ liệu** từ Olist:

- 👥 Khách hàng (100k records)
- 📦 Đơn hàng (100k records) 
- 🛍️ Sản phẩm (73k records)
- 💳 Thanh toán (103k records)
- ⭐ Đánh giá (100k records)
- 🏪 Người bán (3k records)
- 📍 Địa lý (1M records)

**Tổng cộng: 1.5M+ records được xử lý tự động**

## 📈 Kết quả phân tích

Sau khi pipeline chạy xong, bạn sẽ có:

✅ **Dashboard Grafana** với:
- Phân tích khách hàng (VIP, Premium, Regular)  
- Xu hướng doanh thu theo thời gian
- Top sản phẩm bán chạy
- Phân bố địa lý

✅ **Database PostgreSQL** với dữ liệu clean:
- Schema `staging`: Dữ liệu đã làm sạch
- Schema `marts`: Dữ liệu đã tổng hợp sẵn sàng phân tích

✅ **15 Data Quality Tests** đều PASS

---

⭐ **Nếu project hữu ích, hãy cho 1 star nhé!**

## 📄 License

MIT License - xem file [LICENSE](LICENSE) để biết thêm chi tiết.



