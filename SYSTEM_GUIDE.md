# 🚀 HƯỚNG DẪN VẬN HÀNH HỆ THỐNG HSBC FRAUD DETECTION

## 📋 Mục Lục
1. [Tổng Quan Hệ Thống](#tổng-quan-hệ-thống)
2. [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
3. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
4. [Khởi Động Hệ Thống](#khởi-động-hệ-thống)
5. [Vận Hành Từng Thành Phần](#vận-hành-từng-thành-phần)
6. [Giám Sát & Kiểm Tra](#giám-sát--kiểm-tra)
7. [Tắt Hệ Thống](#tắt-hệ-thống)
8. [Xử Lý Sự Cố](#xử-lý-sự-cố)

---

## 1️⃣ Tổng Quan Hệ Thống

### Mô tả
Hệ thống phát hiện giao dịch gian lận real-time cho HSBC sử dụng:
- **Apache Kafka**: Message streaming
- **Apache Spark**: Stream processing & ML
- **Cassandra**: NoSQL database
- **MinIO**: Object storage (S3-compatible)
- **FastAPI**: REST API backend
- **Streamlit**: Real-time dashboard

### Luồng Dữ Liệu
```
CSV Data → Producer → Kafka → Spark Streaming → ML Model → Cassandra → API → Dashboard
                                      ↓
                                   MinIO (Archive)
```

---

## 2️⃣ Yêu Cầu Hệ Thống

### Phần Mềm
- **Docker Desktop**: v20.10+
- **Docker Compose**: v2.0+
- **RAM**: Tối thiểu 8GB (khuyến nghị 16GB)
- **Disk**: Tối thiểu 20GB trống

### Kiểm Tra Yêu Cầu
```powershell
# Kiểm tra Docker
docker --version

# Kiểm tra Docker Compose
docker compose version

# Kiểm tra Docker đang chạy
docker ps
```

---

## 3️⃣ Kiến Trúc Hệ Thống

### Danh Sách Services

| Service | Container | Port | Mục đích |
|---------|-----------|------|----------|
| Zookeeper | zookeeper | 2181 | Kafka coordination |
| Kafka | kafka | 9092, 29092 | Message broker |
| MinIO | minio | 9000, 9001 | Object storage |
| Cassandra | cassandra | 9042 | Fraud alerts storage |
| Spark Master | spark-master | 8080, 7077, 4040 | Spark cluster manager |
| Spark Worker | spark-worker | 8081 | Spark executor |
| Producer | producer | - | Generate transactions |
| API | api | 8000 | REST API backend |
| Dashboard | dashboard | 8501 | Web UI |

### Network
- **Bridge Network**: `hsbc-network` - Kết nối tất cả containers

### Volumes
- `zookeeper-data`: Zookeeper persistent data
- `kafka-data`: Kafka logs & topics
- `minio-data`: S3 objects (models, archives)
- `cassandra-data`: Cassandra database

---

## 4️⃣ Khởi Động Hệ Thống

### 🟢 OPTION 1: Khởi Động Toàn Bộ (Recommended)

```powershell
# Di chuyển vào thư mục project
cd A:\hsbc-fraud-detection-new

# Khởi động tất cả services
docker compose up -d

# Kiểm tra trạng thái
docker compose ps
```

**Thời gian khởi động**: ~2-3 phút

### 🟡 OPTION 2: Khởi Động Từng Giai Đoạn

#### Bước 1: Infrastructure Layer (Zookeeper, Kafka, MinIO, Cassandra)
```powershell
docker compose up -d zookeeper kafka minio cassandra

# Đợi services khởi động hoàn tất (30-60 giây)
Start-Sleep -Seconds 60

# Kiểm tra health
docker ps --filter "name=zookeeper|kafka|minio|cassandra"
```

#### Bước 2: Processing Layer (Spark Cluster)
```powershell
docker compose up -d spark-master spark-worker

# Đợi Spark cluster khởi động (20-30 giây)
Start-Sleep -Seconds 30

# Kiểm tra Spark UI: http://localhost:8080
```

#### Bước 3: Data Source (Producer)
```powershell
docker compose up -d producer

# Kiểm tra producer logs
docker logs -f producer
```

#### Bước 4: Application Layer (API, Dashboard)
```powershell
docker compose up -d api dashboard

# Kiểm tra API health
curl http://localhost:8000/

# Mở Dashboard: http://localhost:8501
```

### ✅ Xác Nhận Khởi Động Thành Công

```powershell
# Xem tất cả containers đang chạy
docker compose ps

# Expected output: 9 containers with status "Up"
```

---

## 5️⃣ Vận Hành Từng Thành Phần

### 📦 5.1 MinIO (Object Storage)

#### Khởi Động
```powershell
docker compose up -d minio
```

#### Truy Cập
- **Console**: http://localhost:9001
- **Username**: `admin`
- **Password**: `password123`

#### Kiểm Tra Buckets
```powershell
# List buckets
docker exec minio mc ls myminio/

# Xem nội dung bucket
docker exec minio mc ls -r myminio/hsbc-data/

# Xem models đã lưu
docker exec minio mc ls myminio/hsbc-data/models/
```

#### Tạo Bucket (nếu chưa có)
```powershell
docker exec minio mc mb myminio/hsbc-data
```

#### Logs
```powershell
docker logs -f minio
```

#### Tắt
```powershell
docker compose stop minio
```

---

### 🗄️ 5.2 Cassandra (Database)

#### Khởi Động
```powershell
docker compose up -d cassandra

# Đợi Cassandra hoàn toàn ready (~60 giây)
Start-Sleep -Seconds 60
```

#### Kiểm Tra Health
```powershell
docker exec -it cassandra cqlsh -e "SELECT now() FROM system.local;"
```

#### Tạo Keyspace & Table
```powershell
# Tạo keyspace
docker exec -it cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS hsbc WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"

# Tạo bảng fraud_alerts
docker exec -it cassandra cqlsh -e "CREATE TABLE IF NOT EXISTS hsbc.fraud_alerts (
    transaction_id text PRIMARY KEY,
    transaction_time timestamp,
    amount double,
    merchant text,
    category text,
    cc_num text,
    first text,
    last text,
    gender text,
    job text,
    state text,
    city text,
    zip text,
    is_fraud double,
    detected_at timestamp
);"
```

#### Truy Vấn Dữ Liệu
```powershell
# Đếm tổng số fraud alerts
docker exec -it cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Xem 10 fraud alerts gần nhất
docker exec -it cassandra cqlsh -e "SELECT transaction_id, amount, category, merchant, detected_at FROM hsbc.fraud_alerts LIMIT 10;"

# Query theo category
docker exec -it cassandra cqlsh -e "SELECT * FROM hsbc.fraud_alerts WHERE category='grocery_pos' LIMIT 5 ALLOW FILTERING;"
```

#### Xóa Dữ Liệu (nếu cần reset)
```powershell
# Truncate table
docker exec -it cassandra cqlsh -e "TRUNCATE hsbc.fraud_alerts;"

# Drop table
docker exec -it cassandra cqlsh -e "DROP TABLE IF EXISTS hsbc.fraud_alerts;"
```

#### CQL Shell Interactive
```powershell
# Vào CQL shell
docker exec -it cassandra cqlsh

# Trong CQL shell:
USE hsbc;
DESCRIBE TABLES;
SELECT * FROM fraud_alerts LIMIT 5;
EXIT;
```

#### Logs
```powershell
docker logs -f cassandra
```

#### Tắt
```powershell
docker compose stop cassandra
```

---

### 📨 5.3 Kafka (Message Broker)

#### Khởi Động
```powershell
# Khởi động Zookeeper trước
docker compose up -d zookeeper
Start-Sleep -Seconds 10

# Khởi động Kafka
docker compose up -d kafka
Start-Sleep -Seconds 20
```

#### Kiểm Tra Topics
```powershell
# List tất cả topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Xem chi tiết topic
docker exec kafka kafka-topics --describe --topic transactions_hsbc --bootstrap-server localhost:9092
```

#### Tạo Topic Thủ Công (nếu cần)
```powershell
docker exec kafka kafka-topics --create \
  --topic transactions_hsbc \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

#### Consume Messages (để test)
```powershell
# Xem messages từ đầu topic
docker exec kafka kafka-console-consumer \
  --topic transactions_hsbc \
  --from-beginning \
  --bootstrap-server localhost:9092 \
  --max-messages 10
```

#### Produce Test Message
```powershell
# Gửi test message
docker exec -it kafka kafka-console-producer \
  --topic transactions_hsbc \
  --bootstrap-server localhost:9092

# Nhập JSON và Enter, Ctrl+C để thoát
```

#### Monitor Consumer Groups
```powershell
# List consumer groups
docker exec kafka kafka-consumer-groups --list --bootstrap-server localhost:9092

# Xem chi tiết group
docker exec kafka kafka-consumer-groups --describe \
  --group spark-kafka-streaming \
  --bootstrap-server localhost:9092
```

#### Logs
```powershell
docker logs -f kafka
```

#### Tắt
```powershell
docker compose stop kafka zookeeper
```

---

### ⚡ 5.4 Spark Cluster (Processing)

#### Khởi Động Cluster
```powershell
# Khởi động Master
docker compose up -d spark-master
Start-Sleep -Seconds 15

# Khởi động Worker
docker compose up -d spark-worker
Start-Sleep -Seconds 10
```

#### Kiểm Tra Cluster
```powershell
# Spark Master UI: http://localhost:8080
# Workers tab should show 1 worker với 12 cores, 1024.0 MB RAM

# Kiểm tra từ command line
docker exec spark-master curl -s http://localhost:8080 | Select-String "Workers"
```

#### Restart Cluster (khi cần)
```powershell
# Stop all Spark processes
docker exec spark-master /opt/spark/sbin/stop-all.sh

# Restart containers
docker compose restart spark-master spark-worker

# Đợi cluster ready
Start-Sleep -Seconds 20
```

#### Copy Code vào Spark Master
```powershell
# Copy streaming pipeline
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/

# Copy feature engineering
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/

# Copy XGBoost model retraining
docker cp streaming-pipeline/model_retraining_xgb.py spark-master:/opt/spark-apps/
```

#### Submit Streaming Job
```powershell
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  /opt/spark-apps/unified_streaming.py
```

**Output mong đợi**:
```
INFO:__main__:✅ Spark session created: 3.5.0
INFO:__main__:Loading XGBoost model from /opt/data/models/fraud_xgb_21features
INFO:__main__:✅ Model loaded successfully
INFO:__main__:✅ Subscribed to topic: transactions_hsbc
INFO:__main__:✅ Archive stream started → s3a://hsbc-data/stream-archive/
INFO:__main__:✅ Inference stream started
INFO:__main__:✅ ALL STREAMS STARTED SUCCESSFULLY
INFO:__main__:📦 Batch 1: 100 transactions
INFO:__main__:🚨 Batch 1: Detected 2 fraud alerts → Cassandra
INFO:__main__:🚨 FRAUD DETECTED: Transaction abc123, Amount: $285.54
```

#### Dừng Streaming Job
```powershell
# Kill process
docker exec spark-master pkill -f unified_streaming.py

# Hoặc Ctrl+C nếu chạy foreground
```

#### Spark UI
- **Master UI**: http://localhost:8080 - Cluster status, workers
- **Application UI**: http://localhost:4040 - Job progress, stages, executors

#### Logs
```powershell
# Spark Master logs
docker logs -f spark-master

# Spark Worker logs
docker logs -f spark-worker

# Application logs (khi job đang chạy)
docker exec spark-master cat /opt/spark/work/*/stdout
```

#### Tắt
```powershell
docker compose stop spark-master spark-worker
```

---

### 🔄 5.5 Producer (Transaction Generator)

#### Khởi Động
```powershell
docker compose up -d producer
```

#### Cấu Hình
File: `producer/config.py`
```python
KAFKA_BOOTSTRAP_SERVERS = 'kafka:29092'
KAFKA_TRANSACTION_TOPIC = 'transactions_hsbc'
TRANSACTION_RATE = 2  # transactions/second
CSV_FILE = '/data/raw/fraudTrain.csv'
```

#### Thay Đổi Transaction Rate
```powershell
# Edit docker-compose.yml
# environment:
#   TRANSACTION_RATE: 5  # tăng lên 5 tx/s

docker compose restart producer
```

#### Kiểm Tra Hoạt Động
```powershell
# Xem logs real-time
docker logs -f producer

# Expected output:
# 📤 Sent transaction: {'trans_num': 'abc123', 'amount': 45.67, ...}
# 📤 Sent 100 transactions (rate: 2.0/s)
```

#### Stop/Start
```powershell
# Tạm dừng gửi transactions
docker compose stop producer

# Tiếp tục
docker compose start producer
```

#### Logs
```powershell
docker logs -f producer --tail 50
```

#### Tắt
```powershell
docker compose stop producer
```

---

### 🔧 5.6 Model Training (One-time/Periodic)

#### Chuẩn Bị
```powershell
# Copy training script vào Spark Master
docker cp streaming-pipeline/model_retraining.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
```

#### Chạy XGBoost Training
```powershell
docker exec spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining_xgb.py"
```

#### Training Process
```
1. Load data: fraudTrain.csv (100% - 1,296,675 rows)
2. Feature engineering: 21 features (numeric, demographic, temporal, geographic, category)
3. Train XGBoost: 100 trees, depth 6, learning_rate 0.3
4. Evaluate: AUC-ROC 0.9964, Recall ~99%, Precision ~54.6%
5. Save model: /opt/data/models/fraud_xgb_21features
```

**Thời gian**: ~6-10 phút (1.3M rows)

#### Kiểm Tra Model Đã Lưu
```powershell
# Kiểm tra XGBoost model
docker exec spark-master ls -lh /opt/data/models/fraud_xgb_21features

# Xem metadata
docker exec spark-master cat /opt/data/models/fraud_xgb_21features/metadata/part-00000

# Check XGBoost version
docker exec spark-master python3 -c "import xgboost; print('XGBoost:', xgboost.__version__)"
```

#### Model Location
- **Container path**: `/opt/data/models/fraud_xgb_21features`
- **Host path**: `./data/models/fraud_xgb_21features`

---

### 🌐 5.7 API Backend (FastAPI)

#### Khởi Động
```powershell
docker compose up -d api
```

#### Kiểm Tra Health
```powershell
# Health check
curl http://localhost:8000/

# Expected: {"service":"HSBC Fraud Detection API","status":"running","version":"1.0.0"}
```

#### API Endpoints

##### 1. Health Check
```powershell
curl http://localhost:8000/
```

##### 2. Get Fraud Alerts (with filters)
```powershell
# Get 10 latest alerts
curl http://localhost:8000/fraud/alerts?limit=10

# Filter by category
curl http://localhost:8000/fraud/alerts?category=grocery_pos&limit=20

# Filter by state
curl http://localhost:8000/fraud/alerts?state=CA&limit=15

# PowerShell với formatted output
(curl http://localhost:8000/fraud/alerts?limit=5).Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
```

##### 3. Get Statistics
```powershell
curl http://localhost:8000/fraud/stats

# PowerShell formatted
(curl http://localhost:8000/fraud/stats).Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
```

##### 4. Get Total Count
```powershell
curl http://localhost:8000/fraud/count
```

#### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

#### Logs
```powershell
# Real-time logs
docker logs -f api

# Last 50 lines
docker logs api --tail 50
```

#### Restart (sau khi thay đổi code)
```powershell
# Rebuild image
docker compose build api

# Restart container
docker compose restart api
```

#### Tắt
```powershell
docker compose stop api
```

---

### 📊 5.8 Dashboard (Streamlit)

#### Khởi Động
```powershell
docker compose up -d dashboard
```

#### Truy Cập
- **URL**: http://localhost:8501
- **Auto-open browser**: Dashboard tự động mở khi container start

#### Features
1. **Overview Metrics**
   - Total fraud alerts
   - Total amount ($)
   - Average amount ($)

2. **Fraud Alerts Table**
   - Sortable columns
   - Filters: Limit (10/25/50/100), Category
   - Real-time data

3. **Analytics Charts**
   - Bar chart: Fraud by category
   - Bar chart: Top 10 states
   - Histogram: Amount distribution

4. **Auto-Refresh**
   - Checkbox để enable
   - Refresh interval: 5 seconds

#### Sử Dụng Dashboard

```
1. Mở http://localhost:8501
2. Quan sát Overview metrics ở top
3. Scroll xuống xem Fraud Alerts table
4. Sử dụng filters:
   - "Number of alerts to display": chọn 10/25/50/100
   - "Filter by category": chọn category cụ thể
5. Xem Analytics charts bên dưới
6. Check "Auto-refresh (5s)" để cập nhật real-time
```

#### Thay Đổi Cấu Hình
File: `dashboard/app.py`

```python
# API URL
API_URL = os.getenv('API_URL', 'http://api:8000')

# Refresh interval (seconds)
time.sleep(5)  # thay đổi số giây ở đây
```

#### Rebuild Dashboard (sau khi thay đổi)
```powershell
docker compose build dashboard
docker compose restart dashboard
```

#### Logs
```powershell
docker logs -f dashboard
```

#### Tắt
```powershell
docker compose stop dashboard
```

---

## 6️⃣ Giám Sát & Kiểm Tra

### 🔍 6.1 Container Health

#### Xem Tất Cả Containers
```powershell
docker compose ps
```

#### Kiểm Tra Resource Usage
```powershell
docker stats

# Specific containers
docker stats kafka spark-master spark-worker cassandra
```

#### Container Status
```powershell
# Check if running
docker ps --filter "name=api"

# Check exit code
docker compose ps api
```

---

### 📈 6.2 Logs Monitoring

#### Real-time Logs (All Services)
```powershell
docker compose logs -f
```

#### Specific Service Logs
```powershell
# Producer (xem transactions đang gửi)
docker logs -f producer --tail 100

# Spark Master (xem job progress)
docker logs -f spark-master --tail 200

# API (xem API requests)
docker logs -f api --tail 50

# Dashboard (xem Streamlit activity)
docker logs -f dashboard --tail 30
```

#### Search Logs
```powershell
# Tìm errors
docker logs api 2>&1 | Select-String "ERROR"

# Tìm fraud detections
docker logs spark-master 2>&1 | Select-String "fraud alerts"

# Tìm batch processing
docker logs spark-master 2>&1 | Select-String "Batch"
```

---

### 🎯 6.3 Data Flow Verification

#### 1. Kafka Messages
```powershell
# Xem messages trong topic
docker exec kafka kafka-console-consumer \
  --topic transactions_hsbc \
  --from-beginning \
  --bootstrap-server localhost:9092 \
  --max-messages 5
```

#### 2. Spark Processing
```powershell
# Xem Spark UI
# http://localhost:4040 (khi streaming job đang chạy)

# Check batch processing trong logs
docker logs spark-master --tail 50 | Select-String "Batch"
```

#### 3. Cassandra Data
```powershell
# Đếm fraud alerts
docker exec -it cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Xem latest alerts
docker exec -it cassandra cqlsh -e "SELECT transaction_id, amount, category, detected_at FROM hsbc.fraud_alerts LIMIT 10;"
```

#### 4. MinIO Archives
```powershell
# List archived files
docker exec minio mc ls -r myminio/hsbc-data/stream-archive/

# Xem số lượng files
docker exec minio mc du myminio/hsbc-data/stream-archive/
```

#### 5. API Response
```powershell
# Test API endpoints
curl http://localhost:8000/fraud/count
curl http://localhost:8000/fraud/stats
```

#### 6. Dashboard Visibility
- Mở http://localhost:8501
- Kiểm tra metrics đang update
- Verify charts hiển thị data

---

### 🚨 6.4 Health Checks

#### Automated Health Check Script
```powershell
# Tạo file health_check.ps1
@"
Write-Host "🔍 HSBC Fraud Detection - Health Check" -ForegroundColor Cyan

# 1. Containers
Write-Host "`n✅ Container Status:" -ForegroundColor Green
docker compose ps

# 2. Kafka
Write-Host "`n✅ Kafka Topics:" -ForegroundColor Green
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# 3. Cassandra
Write-Host "`n✅ Cassandra Fraud Count:" -ForegroundColor Green
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# 4. API
Write-Host "`n✅ API Health:" -ForegroundColor Green
curl http://localhost:8000/ | ConvertFrom-Json

# 5. MinIO
Write-Host "`n✅ MinIO Buckets:" -ForegroundColor Green
docker exec minio mc ls myminio/

Write-Host "`n✅ Health Check Complete!" -ForegroundColor Cyan
"@ | Out-File health_check.ps1

# Chạy health check
.\health_check.ps1
```

---

## 7️⃣ Tắt Hệ Thống

### 🛑 7.1 Stop All Services (Giữ Data)

```powershell
# Dừng tất cả containers (data vẫn được giữ trong volumes)
docker compose stop

# Hoặc dừng từng service cụ thể
docker compose stop producer
docker compose stop spark-master spark-worker
docker compose stop api dashboard
```

### 🗑️ 7.2 Down All Services (Xóa Containers, Giữ Volumes)

```powershell
# Xóa containers nhưng GIỮ volumes (data)
docker compose down

# Kiểm tra volumes vẫn còn
docker volume ls | Select-String "hsbc"
```

### 💥 7.3 Complete Cleanup (Xóa Tất Cả, Kể Cả Data)

```powershell
# ⚠️ CẢNH BÁO: Lệnh này sẽ XÓA TOÀN BỘ DỮ LIỆU

# Down và xóa volumes
docker compose down -v

# Xóa images (optional)
docker compose down -v --rmi all

# Xóa orphan containers
docker compose down -v --remove-orphans
```

### 📦 7.4 Backup Data Trước Khi Tắt

#### Backup Cassandra
```powershell
# Export fraud_alerts table
docker exec cassandra cqlsh -e "COPY hsbc.fraud_alerts TO '/tmp/fraud_alerts_backup.csv' WITH HEADER=TRUE;"

# Copy ra host
docker cp cassandra:/tmp/fraud_alerts_backup.csv ./backups/fraud_alerts_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv
```

#### Backup MinIO
```powershell
# Sync bucket to local
docker exec minio mc mirror myminio/hsbc-data ./backups/minio-backup/
```

#### Backup XGBoost Model
```powershell
# Copy XGBoost model directory
docker cp spark-master:/opt/data/models/fraud_xgb_21features ./backups/model_$(Get-Date -Format 'yyyyMMdd_HHmmss')
```

---

## 8️⃣ Xử Lý Sự Cố

### ❌ 8.1 Container Không Khởi Động

#### Triệu chứng
```powershell
docker compose ps
# Output: Container status = "Exited (1)"
```

#### Giải pháp
```powershell
# 1. Xem logs để tìm lỗi
docker logs <container_name>

# 2. Kiểm tra port conflicts
netstat -ano | Select-String "8080|9092|9042|8000|8501"

# 3. Restart container
docker compose restart <service_name>

# 4. Rebuild nếu cần
docker compose build <service_name>
docker compose up -d <service_name>
```

---

### ⚠️ 8.2 Spark Job Không Chạy

#### Triệu chứng
```
Initial job has not accepted any resources
```

#### Giải pháp
```powershell
# 1. Restart Spark cluster
docker compose restart spark-master spark-worker

# 2. Đợi cluster ready
Start-Sleep -Seconds 30

# 3. Kiểm tra Spark Master UI
# http://localhost:8080 - phải thấy 1 worker

# 4. Submit lại job
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  /opt/spark-apps/unified_streaming.py
```

---

### 🔌 8.3 Kafka Connection Issues

#### Triệu chứng
```
Connection refused: kafka:29092
```

#### Giải pháp
```powershell
# 1. Kiểm tra Kafka đang chạy
docker ps --filter "name=kafka"

# 2. Kiểm tra Zookeeper
docker ps --filter "name=zookeeper"

# 3. Restart Kafka stack
docker compose restart zookeeper kafka

# 4. Đợi Kafka ready (~30s)
Start-Sleep -Seconds 30

# 5. Test connection
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

---

### 🗄️ 8.4 Cassandra Not Ready

#### Triệu chứng
```
NoHostAvailable: ('Unable to connect to any servers')
```

#### Giải pháp
```powershell
# 1. Kiểm tra Cassandra health
docker exec cassandra cqlsh -e "SELECT now() FROM system.local;"

# 2. Nếu fail, restart Cassandra
docker compose restart cassandra

# 3. Đợi ready (~60s)
Start-Sleep -Seconds 60

# 4. Test lại
docker exec -it cassandra cqlsh -e "DESCRIBE KEYSPACES;"

# 5. Recreate table nếu cần
docker exec -it cassandra cqlsh -e "CREATE TABLE IF NOT EXISTS hsbc.fraud_alerts (
    transaction_id text PRIMARY KEY,
    transaction_time timestamp,
    amount double,
    merchant text,
    category text,
    cc_num text,
    first text,
    last text,
    gender text,
    job text,
    state text,
    city text,
    zip text,
    is_fraud double,
    detected_at timestamp
);"
```

---

### 💾 8.5 Model Not Found

#### Triệu chứng
```
Model not found at /opt/data/models/fraud_rf_lean
```

#### Giải pháp
```powershell
# 1. Kiểm tra model có tồn tại không
docker exec spark-master ls -lh /opt/data/models/fraud_rf_lean

# 2. Nếu không có, chạy lại training
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  /opt/spark-apps/model_retraining.py

# 3. Đợi training hoàn tất (~5-10 phút)

# 4. Verify model đã được tạo
docker exec spark-master ls -lh /opt/data/models/fraud_rf_lean
```

---

### 🌐 8.6 API/Dashboard Connection Issues

#### Triệu chứng
Dashboard không hiển thị data hoặc API trả về errors

#### Giải pháp
```powershell
# 1. Kiểm tra API đang chạy
curl http://localhost:8000/

# 2. Test API endpoints
curl http://localhost:8000/fraud/count
curl http://localhost:8000/fraud/alerts?limit=5

# 3. Kiểm tra Cassandra connection từ API
docker logs api --tail 50

# 4. Restart API
docker compose restart api

# 5. Restart Dashboard
docker compose restart dashboard

# 6. Clear browser cache và refresh http://localhost:8501
```

---

### 🔄 8.7 Complete System Reset

Khi mọi thứ fail, reset toàn bộ hệ thống:

```powershell
# 1. Stop tất cả
docker compose down

# 2. Xóa volumes (⚠️ mất data)
docker compose down -v

# 3. Clean Docker system
docker system prune -a --volumes -f

# 4. Rebuild từ đầu
docker compose build --no-cache

# 5. Start lại
docker compose up -d

# 6. Đợi tất cả services ready (~3 phút)
Start-Sleep -Seconds 180

# 7. Setup Cassandra
docker exec -it cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS hsbc WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"
docker exec -it cassandra cqlsh -e "CREATE TABLE IF NOT EXISTS hsbc.fraud_alerts (
    transaction_id text PRIMARY KEY,
    transaction_time timestamp,
    amount double,
    merchant text,
    category text,
    cc_num text,
    first text,
    last text,
    gender text,
    job text,
    state text,
    city text,
    zip text,
    is_fraud double,
    detected_at timestamp
);"

# 8. Train model
docker cp streaming-pipeline/model_retraining.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  /opt/spark-apps/model_retraining.py

# 9. Start streaming
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  /opt/spark-apps/unified_streaming.py

# 10. Verify dashboard: http://localhost:8501
```

---

## 📝 Quick Reference Commands

### Start System
```powershell
docker compose up -d
```

### Stop System
```powershell
docker compose stop
```

### View Logs
```powershell
docker compose logs -f [service_name]
```

### Health Check
```powershell
docker compose ps
curl http://localhost:8000/
```

### Access UIs
- Spark Master: http://localhost:8080
- MinIO Console: http://localhost:9001
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

### Clean Restart
```powershell
docker compose down
docker compose up -d
```

---

## 🎓 Luồng Làm Việc Tiêu Biểu

### Scenario 1: Khởi Động Hệ Thống Mới (Lần Đầu)

```powershell
# 1. Clone/setup project
cd A:\hsbc-fraud-detection-new

# 2. Start infrastructure
docker compose up -d

# 3. Đợi services ready
Start-Sleep -Seconds 120

# 4. Setup Cassandra
docker exec -it cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS hsbc WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"
docker exec -it cassandra cqlsh -e "CREATE TABLE IF NOT EXISTS hsbc.fraud_alerts (...);"

# 5. Train model
docker cp streaming-pipeline/model_retraining.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/model_retraining.py

# 6. Start streaming
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --packages [...] /opt/spark-apps/unified_streaming.py

# 7. Access dashboard
# http://localhost:8501
```

---

### Scenario 2: Restart Hệ Thống Đã Setup

```powershell
# 1. Start all services
docker compose up -d

# 2. Đợi ready
Start-Sleep -Seconds 60

# 3. Start streaming (model đã có)
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --packages [...] /opt/spark-apps/unified_streaming.py

# 4. Monitor
docker logs -f spark-master
```

---

### Scenario 3: Update Code & Redeploy

```powershell
# 1. Stop streaming job
docker exec spark-master pkill -f unified_streaming.py

# 2. Update code files (edit locally)

# 3. Copy updated files
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/

# 4. Restart streaming
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --packages [...] /opt/spark-apps/unified_streaming.py

# 5. Verify logs
docker logs -f spark-master
```

---

### Scenario 4: Retrain Model với Data Mới

```powershell
# 1. Upload new training data
# Copy CSV vào ./data/raw/fraudTrain.csv

# 2. Stop streaming job
docker exec spark-master pkill -f unified_streaming.py

# 3. Run training
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 /opt/spark-apps/model_retraining.py

# 4. Restart streaming với model mới
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --packages [...] /opt/spark-apps/unified_streaming.py

# 5. Monitor accuracy
docker logs -f spark-master | Select-String "fraud"
```

---

## 📞 Support & Resources

### Logs Location
- **Container logs**: `docker logs <container_name>`
- **Spark logs**: `docker exec spark-master ls /opt/spark/work/`
- **Application logs**: Real-time via `docker logs -f`

### Configuration Files
- **Docker Compose**: `docker-compose.yml`
- **Producer**: `producer/config.py`
- **API**: `api/main.py`, `api/database.py`
- **Dashboard**: `dashboard/app.py`
- **Streaming**: `streaming-pipeline/unified_streaming.py`

### Useful Links
- Docker Documentation: https://docs.docker.com/
- Apache Spark: https://spark.apache.org/docs/3.5.0/
- FastAPI: https://fastapi.tiangolo.com/
- Streamlit: https://docs.streamlit.io/

---

**🎉 Hệ thống HSBC Fraud Detection đã sẵn sàng!**

Mọi thắc mắc hoặc issues, vui lòng kiểm tra section "Xử Lý Sự Cố" hoặc xem logs chi tiết.
