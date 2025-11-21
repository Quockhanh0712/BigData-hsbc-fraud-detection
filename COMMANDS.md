# 📋 HSBC Fraud Detection - Command Cheat Sheet

Quick reference cho các lệnh thường dùng.

---

## 🚀 KHỞI ĐỘNG HỆ THỐNG

### Cách 1: Sử dụng Makefile (Đơn giản nhất)
```powershell
make start      # Khởi động tất cả services
make setup      # Setup database
make train      # Train model
make stream     # Start streaming
```

### Cách 2: Sử dụng Automation Script
```powershell
.\scripts\automation.ps1 start
.\scripts\automation.ps1 setup
.\scripts\automation.ps1 train
.\scripts\automation.ps1 stream
```

### Cách 3: Docker Compose Manual
```powershell
docker compose up -d
docker exec -it cassandra cqlsh -e "CREATE KEYSPACE..."
docker exec spark-master /opt/spark/bin/spark-submit...
```

---

## 🔍 KIỂM TRA TRẠNG THÁI

### Xem tất cả containers
```powershell
docker compose ps
# hoặc
make status
# hoặc
.\scripts\automation.ps1 status
```

### Health check toàn hệ thống
```powershell
make health
# hoặc
.\scripts\automation.ps1 health
```

### Kiểm tra resource usage
```powershell
docker stats
```

---

## 📊 XEM LOGS

### Logs của tất cả services
```powershell
docker compose logs -f
# hoặc
make logs
```

### Logs của service cụ thể
```powershell
# Producer (xem transactions đang gửi)
docker logs -f producer --tail 100

# Spark Master (xem batch processing)
docker logs -f spark-master --tail 200

# API (xem requests)
docker logs -f api --tail 50

# Dashboard
docker logs -f dashboard --tail 30

# Hoặc dùng Makefile
make logs-service SERVICE=producer
```

### Search trong logs
```powershell
# Tìm fraud detections
docker logs spark-master 2>&1 | Select-String "fraud"

# Tìm errors
docker logs api 2>&1 | Select-String "ERROR"

# Tìm batch processing
docker logs spark-master 2>&1 | Select-String "Batch"
```

---

## 💾 CASSANDRA COMMANDS

### Kết nối CQL Shell
```powershell
docker exec -it cassandra cqlsh
```

### Queries thường dùng
```powershell
# Đếm tổng fraud alerts
docker exec -it cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Xem 10 alerts gần nhất
docker exec -it cassandra cqlsh -e "SELECT transaction_id, amount, category, merchant, detected_at FROM hsbc.fraud_alerts LIMIT 10;"

# Query theo category
docker exec -it cassandra cqlsh -e "SELECT * FROM hsbc.fraud_alerts WHERE category='grocery_pos' LIMIT 5 ALLOW FILTERING;"

# Hoặc dùng Makefile
make cassandra-query
```

### Xóa dữ liệu
```powershell
# Truncate table
docker exec -it cassandra cqlsh -e "TRUNCATE hsbc.fraud_alerts;"

# Drop và recreate table
docker exec -it cassandra cqlsh -e "DROP TABLE IF EXISTS hsbc.fraud_alerts;"
make setup  # Tạo lại table
```

---

## 📨 KAFKA COMMANDS

### List topics
```powershell
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Describe topic
```powershell
docker exec kafka kafka-topics --describe --topic transactions_hsbc --bootstrap-server localhost:9092
```

### Consume messages (xem transactions)
```powershell
# Xem 10 messages đầu tiên
docker exec kafka kafka-console-consumer \
  --topic transactions_hsbc \
  --from-beginning \
  --bootstrap-server localhost:9092 \
  --max-messages 10

# Consume real-time
docker exec kafka kafka-console-consumer \
  --topic transactions_hsbc \
  --bootstrap-server localhost:9092
```

### Consumer groups
```powershell
# List groups
docker exec kafka kafka-consumer-groups --list --bootstrap-server localhost:9092

# Describe group
docker exec kafka kafka-consumer-groups --describe \
  --group spark-kafka-streaming \
  --bootstrap-server localhost:9092
```

---

## ⚡ SPARK COMMANDS

### Spark UI URLs
```powershell
# Spark Master UI
start http://localhost:8080
# hoặc
make spark-ui

# Spark Application UI (khi job đang chạy)
start http://localhost:4040
```

### Submit Streaming Job
```powershell
# Cách 1: Makefile
make stream

# Cách 2: Automation script
.\scripts\automation.ps1 stream

# Cách 3: Manual
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  /opt/spark-apps/unified_streaming.py
```

### Stop Streaming Job
```powershell
docker exec spark-master pkill -f unified_streaming.py
```

### Restart Spark Cluster
```powershell
docker compose restart spark-master spark-worker
Start-Sleep -Seconds 30
```

---

## 🤖 MODEL TRAINING

### Train XGBoost Model
```powershell
# Cách 1: Makefile
make train

# Cách 2: Automation script
.\scripts\automation.ps1 train

# Cách 3: Manual
# Install XGBoost first
docker exec spark-master bash -c "pip3 install xgboost scikit-learn pyarrow"

# Copy files
docker cp streaming-pipeline/model_retraining_xgb.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/

# Train (local mode recommended for training)
docker exec spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining_xgb.py"
```

### Verify Model
```powershell
# Check XGBoost model exists
docker exec spark-master ls -lh /opt/data/models/fraud_xgb_21features

# View metadata
docker exec spark-master cat /opt/data/models/fraud_xgb_21features/metadata/part-00000

# Check XGBoost version
docker exec spark-master python3 -c "import xgboost; print('XGBoost version:', xgboost.__version__)"
```

---

## 🌐 API COMMANDS

### Health Check
```powershell
curl http://localhost:8000/
```

### Get Fraud Alerts
```powershell
# Get 10 latest alerts
curl http://localhost:8000/fraud/alerts?limit=10

# Filter by category
curl "http://localhost:8000/fraud/alerts?category=grocery_pos&limit=20"

# Filter by state
curl "http://localhost:8000/fraud/alerts?state=CA&limit=15"

# PowerShell formatted output
(curl http://localhost:8000/fraud/alerts?limit=5).Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
```

### Get Statistics
```powershell
curl http://localhost:8000/fraud/stats

# PowerShell formatted
(curl http://localhost:8000/fraud/stats).Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
```

### Get Total Count
```powershell
curl http://localhost:8000/fraud/count
```

### API Docs
```powershell
start http://localhost:8000/docs
# hoặc
make api-docs
```

### Test All Endpoints
```powershell
make api-test
```

---

## 📊 DASHBOARD

### Mở Dashboard
```powershell
start http://localhost:8501
# hoặc
make dashboard
```

### Restart Dashboard
```powershell
docker compose restart dashboard
```

---

## 💾 MINIO COMMANDS

### MinIO Console
```powershell
start http://localhost:9001
# Login: admin / password123
```

### List Buckets
```powershell
docker exec minio mc ls myminio/
```

### List Files
```powershell
# List all files in bucket
docker exec minio mc ls -r myminio/hsbc-data/

# List archived streams
docker exec minio mc ls -r myminio/hsbc-data/stream-archive/

# List models
docker exec minio mc ls myminio/hsbc-data/models/
```

### Disk Usage
```powershell
docker exec minio mc du myminio/hsbc-data/
```

---

## 🔄 UPDATE CODE

### Update Streaming Pipeline
```powershell
# 1. Edit file locally
# 2. Stop streaming job
docker exec spark-master pkill -f unified_streaming.py

# 3. Copy updated file
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/

# 4. Restart streaming
make stream
```

### Update API
```powershell
# 1. Edit api/main.py or api/database.py locally
# 2. Rebuild and restart
docker compose build api
docker compose restart api

# 3. Test
curl http://localhost:8000/
```

### Update Dashboard
```powershell
# 1. Edit dashboard/app.py locally
# 2. Rebuild and restart
docker compose build dashboard
docker compose restart dashboard

# 3. Refresh browser
start http://localhost:8501
```

---

## 🔧 PRODUCER CONTROL

### Start/Stop Producer
```powershell
# Stop (ngừng gửi transactions)
docker compose stop producer

# Start (tiếp tục gửi)
docker compose start producer

# Restart
docker compose restart producer
```

### Change Transaction Rate
```powershell
# Edit docker-compose.yml:
# producer:
#   environment:
#     TRANSACTION_RATE: 5  # Thay đổi từ 2 → 5

# Restart producer
docker compose restart producer
```

### View Producer Logs
```powershell
docker logs -f producer --tail 100
```

---

## 🛑 STOP/RESTART SYSTEM

### Stop All (giữ data)
```powershell
docker compose stop
# hoặc
make stop
# hoặc
.\scripts\automation.ps1 stop
```

### Restart All
```powershell
docker compose restart
# hoặc
make restart
# hoặc
.\scripts\automation.ps1 restart
```

### Down (xóa containers, giữ volumes)
```powershell
docker compose down
# hoặc
make down
```

### Complete Cleanup (XÓA TẤT CẢ)
```powershell
docker compose down -v
# hoặc
make clean
# hoặc
.\scripts\automation.ps1 clean
```

---

## 🔍 TROUBLESHOOTING QUICK FIXES

### Container không start
```powershell
docker logs <container_name>
docker compose restart <service_name>
```

### Spark job không chạy
```powershell
docker compose restart spark-master spark-worker
Start-Sleep -Seconds 30
# Submit lại job
```

### Kafka connection failed
```powershell
docker compose restart zookeeper kafka
Start-Sleep -Seconds 30
```

### Cassandra not ready
```powershell
docker compose restart cassandra
Start-Sleep -Seconds 60
docker exec cassandra cqlsh -e "SELECT now() FROM system.local;"
```

### API/Dashboard không có data
```powershell
# Check streaming job
docker logs spark-master --tail 50

# Check Cassandra data
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Restart API & Dashboard
docker compose restart api dashboard
```

### Port conflicts
```powershell
# Tìm process đang dùng port
netstat -ano | Select-String "8000"

# Kill process hoặc change port trong docker-compose.yml
```

### Complete Reset
```powershell
# 1. Clean everything
docker compose down -v
docker system prune -a --volumes -f

# 2. Rebuild
docker compose build --no-cache

# 3. Start
make start
make setup
make train
make stream
```

---

## 📖 HELPFUL ALIASES (Add to PowerShell Profile)

Thêm vào `$PROFILE`:

```powershell
# HSBC Fraud Detection Aliases
function hsbc-start { Set-Location A:\hsbc-fraud-detection-new; make start }
function hsbc-stop { Set-Location A:\hsbc-fraud-detection-new; make stop }
function hsbc-status { Set-Location A:\hsbc-fraud-detection-new; make status }
function hsbc-logs { Set-Location A:\hsbc-fraud-detection-new; make logs }
function hsbc-health { Set-Location A:\hsbc-fraud-detection-new; make health }
function hsbc-dashboard { start http://localhost:8501 }
function hsbc-api { start http://localhost:8000/docs }
function hsbc-spark { start http://localhost:8080 }
```

Reload profile:
```powershell
. $PROFILE
```

Sử dụng:
```powershell
hsbc-start
hsbc-status
hsbc-dashboard
```

---

## 🎯 COMMON WORKFLOWS

### Daily Startup
```powershell
make start
Start-Sleep -Seconds 60
make stream
make dashboard
```

### Check System Health
```powershell
make health
make api-test
make cassandra-query
```

### Monitor Real-time
```powershell
# Terminal 1: Streaming logs
docker logs -f spark-master | Select-String "Batch|fraud"

# Terminal 2: API requests
docker logs -f api

# Browser: Dashboard
start http://localhost:8501
```

### Update & Redeploy
```powershell
# 1. Update code
# 2. Stop streaming
docker exec spark-master pkill -f unified_streaming.py

# 3. Copy files
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/

# 4. Restart
make stream
```

### Backup Data
```powershell
# Cassandra
docker exec cassandra cqlsh -e "COPY hsbc.fraud_alerts TO '/tmp/backup.csv' WITH HEADER=TRUE;"
docker cp cassandra:/tmp/backup.csv ./backups/

# XGBoost Model
docker cp spark-master:/opt/data/models/fraud_xgb_21features ./backups/model_backup/
```

---

**💡 Tip**: Bookmark file này để reference nhanh các lệnh thường dùng!

**📚 Xem thêm**:
- [Complete System Guide](SYSTEM_GUIDE.md) - Hướng dẫn chi tiết
- [Quick Start](QUICKSTART.md) - Khởi động nhanh 5 phút
- [README](README.md) - Tổng quan hệ thống
