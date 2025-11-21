# 🚀 DEPLOYMENT GUIDE - XGBoost Production Model

## 📋 Tổng quan hệ thống hiện tại

### ✅ Production Configuration:
1. **Feature Engineering** → 21 engineered features
   - Numeric: amount, amount_log, is_high_value, is_extreme_value
   - Demographic: age, gender_encoded
   - Temporal: hour_of_day, is_weekend
   - Geographic: distance_customer_merchant, is_out_of_state, amt_to_pop_ratio
   - Category one-hot: 13 binary flags (cat_grocery_pos, cat_shopping_net, etc.)

2. **Model Training** → XGBoost Classifier
   - **Algorithm**: Gradient Boosting (XGBoost)
   - **Dataset**: 100% fraudTrain.csv (1,296,675 rows)
   - **Trees**: 100 estimators
   - **Max Depth**: 6
   - **Learning Rate**: 0.3
   - **Performance**: AUC-ROC 0.9964, Recall ~99%, Precision ~54.6%
   - **Model Path**: `/opt/data/models/fraud_xgb_21features`

3. **Producer** → High throughput
   - Data file: `df_test_hdfs.csv` or `df_sampled.csv`
   - Rate: 12 tx/s (configurable)

4. **Streaming** → Optimized Spark
   - Shuffle partitions: 20
   - Driver memory: 2GB (streaming), 4GB (training)
   - Model path: `/opt/data/models/fraud_xgb_21features`

---

## 🔄 BƯỚC 1: Copy files mới vào containers

### 1.1 Copy files vào spark-master
```powershell
# Copy feature engineering
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/feature_engineering.py

# Copy XGBoost model retraining script
docker cp streaming-pipeline/model_retraining_xgb.py spark-master:/opt/spark-apps/model_retraining_xgb.py

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

## 🎯 BƯỚC 2: Train XGBoost Model

### 2.1 Install dependencies (nếu chưa có)
```powershell
docker exec spark-master bash -c "pip3 install xgboost scikit-learn pyarrow"
```

### 2.2 Xóa model cũ (nếu có)
```powershell
docker exec spark-master rm -rf /opt/data/models/fraud_xgb_21features
```

### 2.3 Chạy XGBoost training (100% data, 1.3M rows)
```powershell
docker exec spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining_xgb.py"
```

**Thời gian dự kiến**: 6-10 phút

### 2.4 Verify model đã được tạo
```powershell
# Check model directory
docker exec spark-master ls -lh /opt/data/models/fraud_xgb_21features/

# Check metadata
docker exec spark-master cat /opt/data/models/fraud_xgb_21features/metadata/part-00000
```

**Kết quả mong đợi**:
```
✅ AUC-ROC: 0.9964
✅ Recall: ~99%
✅ Precision: ~54.6%
✅ XGBoost model saved to /opt/data/models/fraud_xgb_21features
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
INFO - Loading XGBoost model from /opt/data/models/fraud_xgb_21features
INFO - ✅ Model loaded successfully
INFO - ✅ Subscribed to topic: transactions_hsbc
INFO - ✅ ALL STREAMS STARTED SUCCESSFULLY
INFO - 📦 Batch 0: X transactions
INFO - 🚨 Batch 0: Detected Y fraud alerts → Cassandra
INFO - 🚨 FRAUD DETECTED: Transaction abc123, Amount: $285.54
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

| Metric | Value | Notes |
|--------|-------|-------|
| **Features** | 21 | Numeric + Demographic + Temporal + Geographic + Category |
| **Model Type** | XGBoost | Gradient Boosting (100 trees, depth=6) |
| **Training Data** | 100% | 1,296,675 transactions from fraudTrain.csv |
| **AUC-ROC** | 0.9964 | Excellent discrimination |
| **Recall** | ~99% | Almost no false negatives |
| **Precision** | ~54.6% | Some false positives (acceptable for fraud detection) |
| **Producer Rate** | 12 tx/s | Configurable in producer/config.py |
| **Inference Latency** | ~2-3 sec | End-to-end from Kafka to Cassandra |
| **Training Time** | 6-10 min | Full 1.3M dataset on local[4] |

---

## 🐛 Troubleshooting

### Producer không đọc được df_test_hdfs.csv
```powershell
# Check file exists
docker exec producer ls -lh /data/raw/

# Nếu không có, copy từ host
docker cp ./data/raw/df_test_hdfs.csv producer:/data/raw/df_test_hdfs.csv
```

### XGBoost Model không load được
```powershell
# Check model path
docker exec spark-master ls -lh /opt/data/models/fraud_xgb_21features/

# Check if XGBoost installed
docker exec spark-master python3 -c "import xgboost; print(xgboost.__version__)"

# Re-install if needed
docker exec spark-master pip3 install xgboost scikit-learn pyarrow

# Re-run training if needed (see BƯỚC 2)
```

### ModuleNotFoundError: No module named 'xgboost'
```powershell
# Install XGBoost in spark-master container
docker exec spark-master bash -c "pip3 install numpy xgboost scikit-learn pyarrow"
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

1. ✅ XGBoost Model trained: AUC-ROC = 0.9964
2. ✅ Model path exists: `/opt/data/models/fraud_xgb_21features`
3. ✅ Streaming running: No errors, logs show "Model loaded successfully"
4. ✅ Producer rate: ~12 tx/sec (consistent throughput)
5. ✅ Cassandra: Fraud alerts increasing (only prediction=1 stored)
6. ✅ API: Returns fresh data with correct schema
7. ✅ Dashboard: Real-time metrics updating every 5 seconds
8. ✅ Logs show fraud detection: "🚨 FRAUD DETECTED" messages

---

**Ready to deploy! Execute BƯỚC 1 → BƯỚC 5 in sequence.**
