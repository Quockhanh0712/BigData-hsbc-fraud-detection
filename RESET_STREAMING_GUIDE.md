# 🔄 Hướng Dẫn Reset và Chạy Lại Streaming từ Đầu

## 📋 Tóm tắt

Để reset và chạy lại streaming pipeline từ đầu (đọc lại tất cả messages từ Kafka), bạn cần:
1. Xóa dữ liệu trong Cassandra
2. Cấu hình Kafka offset về "earliest"
3. Restart streaming pipeline

## 🚀 Các bước thực hiện

### **Bước 1: Stop các services (giữ infrastructure)**

```powershell
# Stop producer và streaming (giữ Kafka, Cassandra, Spark infrastructure)
docker compose stop producer
docker exec spark-master pkill -f "unified_streaming.py"
```

### **Bước 2: Xóa dữ liệu Cassandra**

```powershell
# Truncate bảng fraud_alerts để xóa tất cả data
docker exec cassandra cqlsh -e "TRUNCATE hsbc.fraud_alerts;"

# Verify đã xóa
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"
# Output: count = 0 ✅
```

### **Bước 3: Reset Kafka Topic (Optional)**

**Option A: Xóa và tạo lại topic (recommended cho reset hoàn toàn)**

```powershell
# Delete topic
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic transactions

# Recreate topic
docker exec kafka kafka-topics --create --topic transactions --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

**Option B: Giữ nguyên topic** (streaming sẽ đọc lại từ offset earliest)

Nếu giữ nguyên topic, messages cũ vẫn còn trong Kafka retention period (default 7 days).

### **Bước 4: Cấu hình Streaming đọc từ đầu**

File: `streaming-pipeline/unified_streaming.py`

```python
# BEFORE (chỉ đọc message mới):
.option("startingOffsets", "latest")

# AFTER (đọc tất cả messages từ đầu):
.option("startingOffsets", "earliest")
```

**Lưu ý quan trọng:**
- `"latest"`: Chỉ đọc messages MỚI sau khi streaming start
- `"earliest"`: Đọc TẤT CẢ messages từ đầu topic (hoặc từ retention period)

### **Bước 5: Install dependencies (nếu chưa có)**

```powershell
# Spark-master container cần các packages này
docker exec spark-master pip3 install numpy pandas xgboost scikit-learn pyarrow
```

### **Bước 6: Copy code mới vào container**

```powershell
# Copy updated streaming script
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
```

### **Bước 7: Restart Producer**

```powershell
# Restart producer để gửi lại data từ đầu
docker compose restart producer

# Check producer logs
docker logs producer --tail 5
```

### **Bước 8: Start Streaming Pipeline**

```powershell
docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 ; /opt/spark/bin/spark-submit --master local[4] --driver-memory 2g --conf spark.sql.shuffle.partitions=20 --conf spark.streaming.kafka.consumer.poll.ms=256 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 /opt/spark-apps/unified_streaming.py"
```

### **Bước 9: Verify Streaming hoạt động**

```powershell
# Wait 20-30 seconds
Start-Sleep -Seconds 25

# Check fraud alerts count (should be > 0 and increasing)
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Check producer progress
docker logs producer --tail 3

# Check streaming process
docker exec spark-master ps aux | Select-String "spark-submit"
```

### **Bước 10: Start Dashboard (Optional)**

```powershell
docker compose up -d api dashboard

# Access dashboard
# http://localhost:8501
```

---

## 🔧 Script Tự Động Reset

Tạo file `reset_streaming.ps1`:

```powershell
# reset_streaming.ps1
Write-Host "🔄 Resetting Streaming Pipeline..." -ForegroundColor Cyan

# 1. Stop services
Write-Host "1️⃣ Stopping producer and streaming..." -ForegroundColor Yellow
docker compose stop producer
docker exec spark-master pkill -f "unified_streaming.py" 2>$null

# 2. Truncate Cassandra
Write-Host "2️⃣ Truncating Cassandra fraud_alerts table..." -ForegroundColor Yellow
docker exec cassandra cqlsh -e "TRUNCATE hsbc.fraud_alerts;"

# 3. Verify
$count = docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" | Select-String "\d+" | ForEach-Object { $_.Matches.Value }
Write-Host "   Cassandra count: $count (should be 0)" -ForegroundColor Green

# 4. Delete and recreate Kafka topic
Write-Host "3️⃣ Resetting Kafka topic..." -ForegroundColor Yellow
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic transactions 2>$null
Start-Sleep -Seconds 2
docker exec kafka kafka-topics --create --topic transactions --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# 5. Copy updated streaming code
Write-Host "4️⃣ Copying updated streaming code..." -ForegroundColor Yellow
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/

# 6. Restart producer
Write-Host "5️⃣ Restarting producer..." -ForegroundColor Yellow
docker compose restart producer
Start-Sleep -Seconds 5

# 7. Start streaming
Write-Host "6️⃣ Starting streaming pipeline..." -ForegroundColor Yellow
docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 ; /opt/spark/bin/spark-submit --master local[4] --driver-memory 2g --conf spark.sql.shuffle.partitions=20 --conf spark.streaming.kafka.consumer.poll.ms=256 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 /opt/spark-apps/unified_streaming.py"

# 8. Wait and verify
Write-Host "7️⃣ Waiting for streaming to process..." -ForegroundColor Yellow
Start-Sleep -Seconds 25

$newCount = docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" | Select-String "\d+" | ForEach-Object { $_.Matches.Value }
Write-Host "   New fraud alerts: $newCount" -ForegroundColor Green

Write-Host "✅ Reset complete! Streaming is processing from beginning." -ForegroundColor Green
Write-Host ""
Write-Host "📊 Monitor progress:" -ForegroundColor Cyan
Write-Host "   Producer:  docker logs producer --tail 5" -ForegroundColor White
Write-Host "   Cassandra: docker exec cassandra cqlsh -e 'SELECT COUNT(*) FROM hsbc.fraud_alerts;'" -ForegroundColor White
```

**Chạy script:**

```powershell
.\reset_streaming.ps1
```

---

## 🎯 Kết quả Mong Đợi

### **Sau khi reset thành công:**

```
Producer:
- Sent: 3,900 transactions
- Fraud: 405 actual fraud (10.38%)

Cassandra:
- Fraud alerts: 439 (CHỈ fraud detected)

Detection:
- Model đang xử lý từ earliest offset
- Alerts tăng dần theo producer progress
```

### **Timeline:**

| Thời gian | Producer Sent | Actual Fraud | Cassandra Alerts |
|-----------|---------------|--------------|------------------|
| 0s        | 0             | 0            | 0 (truncated)    |
| 30s       | 500           | 50           | 52-55            |
| 60s       | 1,000         | 100          | 105-110          |
| 5 min     | 3,900         | 405          | 430-450          |
| 10 min    | 7,800         | 810          | 850-900          |

---

## ⚠️ Troubleshooting

### **Problem 1: Cassandra count vẫn là 0**

**Nguyên nhân:**
- Streaming process chưa start hoặc bị lỗi
- Producer chưa gửi data
- Kafka topic trống

**Giải pháp:**

```powershell
# Check streaming process
docker exec spark-master ps aux | Select-String "spark-submit"

# Check producer
docker logs producer --tail 5

# Check Kafka messages
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic transactions --time -1
```

### **Problem 2: ModuleNotFoundError: No module named 'numpy'**

**Nguyên nhân:**
- Spark-master container thiếu Python dependencies

**Giải pháp:**

```powershell
docker exec spark-master pip3 install numpy pandas xgboost scikit-learn pyarrow
```

### **Problem 3: Streaming đọc từ "latest" thay vì "earliest"**

**Nguyên nhân:**
- File `unified_streaming.py` vẫn có `startingOffsets="latest"`

**Giải pháp:**

```python
# Edit streaming-pipeline/unified_streaming.py line 128
.option("startingOffsets", "earliest")  # ← Change from "latest"

# Copy to container
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/

# Restart streaming
docker exec spark-master pkill -f "unified_streaming.py"
# Then start again
```

### **Problem 4: Fraud alerts không tăng**

**Check points:**

```powershell
# 1. Streaming process running?
docker exec spark-master ps aux | Select-String "spark"

# 2. Producer sending?
docker logs producer --tail 5

# 3. Kafka has messages?
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell --broker-list localhost:9092 --topic transactions --time -1

# 4. Model loaded?
docker logs spark-master 2>&1 | Select-String "XGBoost|Model"
```

---

## 📚 Giải thích Kỹ thuật

### **Kafka Offset Management**

```
startingOffsets="earliest":
┌─────────────────────────────────┐
│ Kafka Topic: transactions       │
│                                 │
│ [Offset 0] ─────────────────→   │ ← Đọc từ đây
│ [Offset 1]                      │
│ [Offset 2]                      │
│ ...                             │
│ [Offset 3,900] (latest)         │
└─────────────────────────────────┘

startingOffsets="latest":
┌─────────────────────────────────┐
│ Kafka Topic: transactions       │
│                                 │
│ [Offset 0]                      │
│ [Offset 1]                      │
│ [Offset 2]                      │
│ ...                             │
│ [Offset 3,900] ─────────────→   │ ← Đọc từ đây (bỏ qua cũ)
└─────────────────────────────────┘
```

### **Data Flow**

```
Producer (df_test_hdfs.csv)
    ↓
    📤 Send to Kafka
    ↓
Kafka Topic (transactions)
    ↓ startingOffsets="earliest" ← Đọc từ đầu
    ↓
Spark Streaming
    ├─ Feature Engineering
    ├─ XGBoost Prediction
    └─ Filter (prediction=1)
         ↓
    Cassandra (fraud_alerts) ← CHỈ fraud detected
```

---

## ✅ Best Practices

1. **Backup trước khi reset:**
   ```powershell
   # Backup Cassandra data
   docker exec cassandra cqlsh -e "COPY hsbc.fraud_alerts TO '/tmp/fraud_alerts_backup.csv' WITH HEADER=TRUE;"
   ```

2. **Monitor trong quá trình reset:**
   ```powershell
   # Terminal 1: Producer logs
   docker logs producer -f

   # Terminal 2: Cassandra count
   while ($true) { docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"; Start-Sleep 10 }
   ```

3. **Verify model loaded:**
   ```powershell
   # Check streaming logs for model loading
   docker logs spark-master 2>&1 | Select-String "Loading.*model|XGBoost"
   ```

4. **Use "earliest" cho development, "latest" cho production:**
   - Development: Test với full dataset → `"earliest"`
   - Production: Real-time processing → `"latest"`

---

**Last Updated**: 2025-11-20  
**Tested**: ✅ Working  
**Status**: Production Ready
