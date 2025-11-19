# 🚀 DEPLOYMENT GUIDE - Decision Tree 21 Features

## 📋 Tổng quan thay đổi

### ✅ Đã cập nhật (completed):
1. **Feature Engineering** → 21 features (từ 7 features cũ)
   - Numeric: amount, amount_log, is_high_value, is_extreme_value
   - Demographic: age, gender_encoded
   - Temporal: hour_of_day, is_weekend
   - Geographic: distance_customer_merchant, is_out_of_state, amt_to_pop_ratio
   - Category one-hot: 13 binary flags

2. **Model Training** → DecisionTree (từ RandomForest)
   - Sample: 50% dataset (từ 20%)
   - Max depth: 10 (từ 8)
   - Model path: `/opt/data/models/fraud_dt_21features`

3. **Producer** → Throughput tăng
   - Data file: `df_sampled.csv` (từ `fraudTrain.csv`)
   - Rate: 15 tx/s (từ 2 tx/s)

4. **Streaming** → Spark configs tuned
   - Shuffle partitions: 20 (từ 10)
   - Kafka poll ms: 256 (từ 512)
   - Model path: `/opt/data/models/fraud_dt_21features`

---

## 🔄 BƯỚC 1: Copy files mới vào containers

### 1.1 Copy files vào spark-master
```powershell
# Copy feature engineering
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/feature_engineering.py

# Copy model retraining script
docker cp streaming-pipeline/model_retraining.py spark-master:/opt/spark-apps/model_retraining.py

# Copy unified streaming
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/unified_streaming.py

# Verify files
docker exec spark-master ls -lh /opt/spark-apps/
```

### 1.2 Copy producer files
```powershell
# Stop producer trước
docker compose stop producer

# Copy config
docker cp producer/config.py producer:/app/config.py

# Copy producer script
docker cp producer/producer.py producer:/app/producer.py

# Verify
docker exec producer ls -lh /app/
```

---

## 🎯 BƯỚC 2: Train DecisionTree Model

### 2.1 Xóa model cũ (nếu có)
```powershell
docker exec spark-master rm -rf /opt/data/models/fraud_dt_21features
```

### 2.2 Chạy training (50% sample, ~650k rows)
```powershell
docker exec -it spark-master spark-submit `
  --master local[*,2] `
  --driver-memory 4g `
  --executor-memory 4g `
  --conf spark.sql.shuffle.partitions=20 `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 `
  /opt/spark-apps/model_retraining.py
```

**Thời gian dự kiến**: 5-10 phút

### 2.3 Verify model đã được tạo
```powershell
# Check model directory
docker exec spark-master ls -lh /opt/data/models/fraud_dt_21features/

# Check metadata
docker exec spark-master cat /opt/data/models/fraud_dt_21features/metadata/part-00000
```

**Kết quả mong đợi**:
```
✅ AUC-ROC: 0.8xxx
✅ DecisionTree model saved to /opt/data/models/fraud_dt_21features
```

---

## 🌊 BƯỚC 3: Start Streaming Pipeline

### 3.1 Stop streaming cũ (nếu đang chạy)
```powershell
# Kiểm tra Spark jobs
docker exec spark-master ps aux | grep spark-submit

# Kill process nếu cần (thay PID)
docker exec spark-master kill -9 <PID>
```

### 3.2 Start unified streaming với model mới
```powershell
docker exec -d spark-master spark-submit `
  --master local[*,2] `
  --driver-memory 2g `
  --executor-memory 2g `
  --conf spark.sql.shuffle.partitions=20 `
  --conf spark.streaming.kafka.consumer.poll.ms=256 `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 `
  /opt/spark-apps/unified_streaming.py
```

### 3.3 Monitor streaming logs
```powershell
# Real-time logs
docker logs -f spark-master --tail 50
```

**Xem log mong đợi**:
```
INFO - Loading model from /opt/data/models/fraud_dt_21features
INFO - ✅ Model loaded successfully
INFO - ✅ Subscribed to topic: transactions_hsbc
INFO - ✅ ALL STREAMS STARTED SUCCESSFULLY
INFO - 📦 Batch 0: X transactions
INFO - 🚨 Batch 0: Detected Y fraud alerts → Cassandra
```

---

## 📊 BƯỚC 4: Start Producer với throughput cao

### 4.1 Verify df_sampled.csv mounted
```powershell
docker exec producer ls -lh /data/raw/df_sampled.csv
```

### 4.2 Start producer (15 tx/s)
```powershell
docker compose up -d producer
```

### 4.3 Monitor producer
```powershell
docker logs -f producer --tail 30
```

**Log mong đợi**:
```
INFO - Dataset: /data/raw/df_sampled.csv
INFO - ✅ Loaded: XXX,XXX transactions
INFO - Topic: transactions_hsbc
INFO - Rate: 15 tx/sec
INFO - 📊 Sent: 100 | Fraud: X (X.XX%) | Rate: 15.1 tx/sec
```

---

## ✅ BƯỚC 5: Verify End-to-End

### 5.1 Check Cassandra alerts
```powershell
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"
docker exec cassandra cqlsh -e "SELECT * FROM hsbc.fraud_alerts LIMIT 5;"
```

### 5.2 Check API
```powershell
# Health check
curl http://localhost:8000/

# Latest alerts
curl http://localhost:8000/fraud/alerts?limit=10

# Stats
curl http://localhost:8000/fraud/stats
```

### 5.3 Open Dashboard
```
http://localhost:8501
```

---

## 📈 Performance Expectations

| Metric | Old | New | Improvement |
|--------|-----|-----|-------------|
| **Features** | 7 | 21 | +200% |
| **Model Type** | RandomForest | DecisionTree | Faster inference |
| **Training Sample** | 20% | 50% | +150% data |
| **Producer Rate** | 2 tx/s | 15 tx/s | **+650%** |
| **Shuffle Partitions** | 10 | 20 | Better parallelism |
| **Kafka Poll** | 512ms | 256ms | Lower latency |

---

## 🐛 Troubleshooting

### Producer không đọc được df_sampled.csv
```powershell
# Check file exists
docker exec producer ls -lh /data/raw/

# Nếu không có, copy từ host
docker cp ./data/raw/df_sampled.csv producer:/data/raw/df_sampled.csv
```

### Model không load được
```powershell
# Check model path
docker exec spark-master ls -lh /opt/data/models/

# Re-run training nếu cần
# (xem BƯỚC 2)
```

### Streaming lag (batches falling behind)
```powershell
# Tăng resources
# Edit docker-compose.yml:
# spark-worker:
#   deploy:
#     resources:
#       limits:
#         cpus: '2.0'
#         memory: 4G

docker compose up -d --force-recreate spark-worker
```

### Out of memory khi training
```powershell
# Tăng driver memory
spark-submit --driver-memory 6g --executor-memory 6g ...
```

---

## 🎯 Quick Commands Reference

### Full Restart
```powershell
# Stop all
docker compose down

# Start infrastructure
docker compose up -d zookeeper kafka minio cassandra spark-master spark-worker api dashboard

# Wait 30s, then deploy (BƯỚC 1-4)
```

### Monitor System
```powershell
# All containers
docker ps

# Resources
docker stats

# Logs
docker logs -f spark-master
docker logs -f producer
docker logs -f api
```

---

## ✅ Success Criteria

1. ✅ Model trained: AUC > 0.80
2. ✅ Streaming running: No errors in logs
3. ✅ Producer rate: ~15 tx/sec
4. ✅ Cassandra: Fraud alerts increasing
5. ✅ API: Returns fresh data
6. ✅ Dashboard: Real-time metrics updating

---

**Ready to deploy! Execute BƯỚC 1 → BƯỚC 5 in sequence.**
