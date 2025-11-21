# 📋 HSBC FRAUD DETECTION - CHECKLIST VẬN HÀNH

## ✅ KHỞI ĐỘNG HỆ THỐNG (Lần đầu hoặc sau khi tắt)

### Bước 1: Khởi động Infrastructure
```powershell
cd A:\hsbc-fraud-detection-new

# Start tất cả services
docker compose up -d
```

**Đợi 30 giây** để các services khởi động hoàn tất.

---

### Bước 2: Kiểm tra Services
```powershell
# Xem tất cả containers đang chạy
docker ps

# Kết quả mong đợi: 9 containers
# - zookeeper
# - kafka
# - minio
# - cassandra
# - spark-master
# - spark-worker
# - producer
# - api
# - dashboard
```

---

### Bước 3: Kiểm tra Cassandra & Data
```powershell
# Xem số lượng fraud alerts
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Xem 5 alerts mới nhất
docker exec cassandra cqlsh -e "SELECT * FROM hsbc.fraud_alerts LIMIT 5;"
```

---

### Bước 4: Kiểm tra Model và Dependencies
```powershell
# Check XGBoost model
docker exec spark-master ls -lh /opt/data/models/fraud_xgb_21features/

# Check XGBoost installed
docker exec spark-master python3 -c "import xgboost; print('XGBoost version:', xgboost.__version__)"

# Nếu không có XGBoost, install:
docker exec spark-master bash -c "pip3 install xgboost scikit-learn pyarrow"

# Nếu KHÔNG có model → Chạy Bước 5 (Training)
# Nếu CÓ model → Bỏ qua Bước 5, chuyển sang Bước 6
```

---

### Bước 5: Training XGBoost Model (Nếu chưa có model)
```powershell
# Copy files mới nhất vào spark-master
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/model_retraining_xgb.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/

# Train XGBoost model (mất ~6-10 phút, 1.3M rows)
docker exec spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining_xgb.py"

# Verify model đã được tạo
docker exec spark-master ls -lh /opt/data/models/fraud_xgb_21features/
```

**Kết quả mong đợi:**
```
✅ Model trained successfully
✅ AUC-ROC: 0.9964
✅ XGBoost model saved to /opt/data/models/fraud_xgb_21features
```

---

### Bước 6: Start Streaming Pipeline
```powershell
# Kill streaming cũ nếu có
docker exec spark-master pkill -f unified_streaming

# Start streaming mới
docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 2g --conf spark.sql.shuffle.partitions=20 --conf spark.streaming.kafka.consumer.poll.ms=256 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 /opt/spark-apps/unified_streaming.py"

# Đợi 10 giây
Start-Sleep -Seconds 10

# Verify streaming đang chạy
docker exec spark-master ps aux | Select-String "unified_streaming"
```

---

### Bước 7: Kiểm tra Producer
```powershell
# Check producer logs
docker logs producer --tail 20

# Kết quả mong đợi:
# Rate: 15 tx/sec
# 📊 Sent: XXX | Fraud: XX (XX.XX%) | Rate: XX.X tx/sec
```

**Nếu producer chưa chạy hoặc bị lỗi:**
```powershell
docker compose restart producer
```

---

### Bước 8: Verify End-to-End
```powershell
# 1. Check Cassandra có nhận fraud alerts
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# 2. Test API
curl http://localhost:8000/
curl http://localhost:8000/fraud/stats

# 3. Check API logs
docker logs api --tail 10

# 4. Check Dashboard logs
docker logs dashboard --tail 10
```

---

### Bước 9: Mở Dashboard
```
🌐 API:        http://localhost:8000
📊 Dashboard:  http://localhost:8501
🎯 Spark UI:   http://localhost:8080
```

**Trong Dashboard:**
- Chọn Limit = **5000** hoặc **10000** để xem nhiều alerts
- Bật **Auto-refresh (5s)** để xem real-time

---

## 🔄 RETRAIN MODEL (Khi cần update model)

### Chuẩn bị
```powershell
# Stop streaming hiện tại
docker exec spark-master pkill -f unified_streaming

# Xóa model cũ
docker exec spark-master rm -rf /opt/data/models/fraud_xgb_21features
```

### Train lại
```powershell
# Copy files mới (nếu có thay đổi)
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/model_retraining_xgb.py spark-master:/opt/spark-apps/

# Install/update XGBoost if needed
docker exec spark-master bash -c "pip3 install xgboost scikit-learn pyarrow"

# Train XGBoost
docker exec spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining_xgb.py"

# Đợi ~6-10 phút để training hoàn tất
```

### Restart Streaming
```powershell
# Copy streaming file mới
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/

# Start streaming với model mới
docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 2g --conf spark.sql.shuffle.partitions=20 --conf spark.streaming.kafka.consumer.poll.ms=256 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 /opt/spark-apps/unified_streaming.py"
```

---

## 📊 MONITORING

### Xem Logs Real-time
```powershell
# Streaming logs
docker logs -f spark-master --tail 50

# Producer logs
docker logs -f producer --tail 30

# API logs
docker logs -f api --tail 20

# Dashboard logs
docker logs -f dashboard --tail 20
```

### Kiểm tra Performance
```powershell
# Producer throughput
docker logs producer --tail 5

# Fraud detection count
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# System resources
docker stats --no-stream
```

---

## 🛑 STOP HỆ THỐNG

### Stop toàn bộ
```powershell
# Stop tất cả containers
docker compose down

# Hoặc stop nhưng giữ data
docker compose stop
```

### Stop từng service
```powershell
# Stop streaming
docker exec spark-master pkill -f unified_streaming

# Stop producer
docker compose stop producer

# Stop API/Dashboard
docker compose stop api dashboard
```

---

## 🔧 TROUBLESHOOTING

### Producer không gửi data
```powershell
# Restart producer
docker compose restart producer

# Check Kafka
docker logs kafka --tail 20
```

### Streaming không detect fraud
```powershell
# Check XGBoost model path
docker exec spark-master ls -lh /opt/data/models/fraud_xgb_21features/

# Check XGBoost installed
docker exec spark-master python3 -c "import xgboost"

# Install if missing
docker exec spark-master bash -c "pip3 install xgboost scikit-learn pyarrow"

# Restart streaming
docker exec spark-master pkill -f unified_streaming
# Rồi start lại (Bước 6)
```

### API không trả về data
```powershell
# Check Cassandra
docker exec cassandra cqlsh -e "SELECT * FROM hsbc.fraud_alerts LIMIT 5;"

# Restart API
docker compose restart api

# Check API logs
docker logs api --tail 20
```

### Dashboard chỉ hiện 1000 alerts
```powershell
# Copy file đã fix
docker cp api/main.py api:/app/main.py
docker cp dashboard/app.py dashboard:/app/app.py

# Restart
docker compose restart api dashboard

# Trong dashboard, chọn Limit = 5000 hoặc 10000
```

### Out of Memory
```powershell
# Tăng memory cho Spark (edit docker-compose.yml)
# spark-worker:
#   deploy:
#     resources:
#       limits:
#         memory: 4G

docker compose up -d --force-recreate spark-worker
```

---

## 📈 THÔNG SỐ HỆ THỐNG

### Model Specifications
- **Type**: XGBoost Classifier (Gradient Boosting)
- **Features**: 21 engineered features (numeric, demographic, temporal, geographic, category one-hot)
- **Training Data**: 1,296,675 rows (100% of fraudTrain.csv)
- **Performance**: AUC-ROC 0.9964, Recall ~99%, Precision ~54.6%
- **Hyperparameters**: 100 trees, max_depth=6, learning_rate=0.3, subsample=0.8
- **Model Path**: `/opt/data/models/fraud_xgb_21features`

### Performance Settings
- **Producer Rate**: 12 tx/s (configurable via TRANSACTION_RATE env)
- **Spark Shuffle Partitions**: 20
- **Driver Memory**: 2GB (streaming), 4GB (training)
- **Kafka Consumer Poll**: 256ms
- **Streaming Trigger**: 2 seconds
- **API Limit**: 10,000 records max
- **Dashboard Limit**: 100, 500, 1000, 5000, 10000 options

### Data Paths
- **Training Data**: `./data/raw/fraudTrain.csv` (1.3M rows)
- **Production Data**: `./data/raw/df_test_hdfs.csv` or `df_sampled.csv`
- **Container Data**: `/data/raw/`
- **Model**: `/opt/data/models/fraud_xgb_21features`
- **Cassandra Keyspace**: `hsbc.fraud_alerts`

---

## ✅ QUICK STATUS CHECK

Chạy lệnh này để kiểm tra nhanh:
```powershell
Write-Host "`n=== HSBC FRAUD DETECTION STATUS ===" -ForegroundColor Cyan
Write-Host "`n📦 Containers:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "api|dashboard|producer|spark|cassandra|kafka"

Write-Host "`n🚨 Fraud Alerts:" -ForegroundColor Yellow
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

Write-Host "`n📊 Producer:" -ForegroundColor Yellow
docker logs producer --tail 3

Write-Host "`n🎯 URLs:" -ForegroundColor Green
Write-Host "API:       http://localhost:8000"
Write-Host "Dashboard: http://localhost:8501"
Write-Host "Spark UI:  http://localhost:8080"
```

---

## 📝 GHI CHÚ

1. **Lần đầu chạy**: Thực hiện đầy đủ từ Bước 1 → 9
2. **Chạy lại sau khi tắt**: Bước 1 → Bước 4 (check model) → Bước 6 → 9
3. **Retrain model**: Follow section "RETRAIN MODEL"
4. **Nếu có lỗi**: Xem section "TROUBLESHOOTING"

**Thời gian khởi động:**
- Infrastructure: ~30 giây
- Training XGBoost model: ~6-10 phút (1.3M rows)
- Streaming startup: ~10 giây
- **Tổng**: ~7-11 phút (lần đầu training model)

**Lưu ý:**
- Model đã train sẽ được lưu persistent trong `./data/models/`
- Cassandra data được lưu trong Docker volume
- Không cần retrain nếu model đã tồn tại
