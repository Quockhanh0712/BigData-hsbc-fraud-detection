# Quick Start Guide - HSBC Fraud Detection System

## 🚀 5-Minute Quick Start

### Prerequisites
- Docker Desktop installed and running
- At least 8GB RAM available
- 20GB disk space

### Step 1: Start Infrastructure (2 minutes)

```powershell
# Start core services
docker compose up -d zookeeper kafka cassandra minio spark-master spark-worker

# Wait for services to initialize
Start-Sleep -Seconds 60
```

### Step 2: Setup Kafka & Cassandra (1 minute)

```powershell
# Create Kafka topic
docker exec kafka kafka-topics --create --topic transactions_hsbc --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

# Setup Cassandra
docker exec cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS hsbc WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"

docker exec cassandra cqlsh -e "CREATE TABLE IF NOT EXISTS hsbc.fraud_alerts (transaction_id text PRIMARY KEY, transaction_time timestamp, amount double, merchant text, category text, cc_num text, first text, last text, gender text, job text, state text, city text, zip text, is_fraud double, detected_at timestamp);"
```

### Step 3: Train Model & Start Streaming (2 minutes)

```powershell
# Install dependencies
docker exec spark-master bash -c "pip3 install xgboost scikit-learn pyarrow"

# Copy scripts
docker cp streaming-pipeline/model_retraining_xgb.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/config.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/

# Train XGBoost model (takes ~6 minutes - run in background)
docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining_xgb.py"
```

### Step 4: Monitor Training Progress

```powershell
# Watch training logs
docker logs spark-master --tail 50 -f

# Wait until you see: "✅ AUC-ROC: 0.9964"
# Press Ctrl+C to exit log view
```

### Step 5: Start Producer & Dashboard

```powershell
# Start streaming pipeline
docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 2g --conf spark.sql.shuffle.partitions=20 --conf spark.streaming.kafka.consumer.poll.ms=256 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 /opt/spark-apps/unified_streaming.py"

# Start producer
docker compose up -d --build producer

# Start API and dashboard
docker compose up -d api dashboard
```

### Step 7: Monitor Real-Time Fraud Detection

**Option 1: Live Fraud Alerts Monitor (RECOMMENDED)**
```powershell
# Watch fraud alerts in real-time
.\watch_fraud.ps1
```
This displays:
- New fraud alerts as they're detected
- Transaction ID, amount, merchant
- Customer name and location
- Running total count

**Option 2: Streaming Logs**
```powershell
# View detailed streaming logs
.\tail_fraud_logs.ps1

# Or use Docker logs
docker logs spark-master --tail 50 -f | Select-String "FRAUD|Amount|Merchant|Customer"
```

**Option 3: Cassandra Count**
```powershell
# Check fraud count every 5 seconds
while ($true) { docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"; Start-Sleep 5 }
```

### Step 6: Verify & Access

```powershell
# Check producer is sending transactions
docker logs producer --tail 10

# Check fraud alerts being detected
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Open dashboard
Start-Process "http://localhost:8501"

# Open Spark UI
Start-Process "http://localhost:8080"
```

## ✅ Success Indicators

After 2-3 minutes, you should see:
- Producer logs: `📊 Sent: 500 | Fraud: 50 (10.00%)`
- Cassandra: `count: 38` (fraud alerts detected)
- Dashboard: Real-time charts updating
- Spark UI: 1 active streaming application

## 🛑 Stop Everything

```powershell
docker compose down
```

## 📊 One-Command Full Setup

```powershell
# Copy and run this entire block
docker compose up -d zookeeper kafka cassandra minio spark-master spark-worker; `
Start-Sleep -Seconds 60; `
docker exec kafka kafka-topics --create --topic transactions_hsbc --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1; `
docker exec cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS hsbc WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"; `
docker exec cassandra cqlsh -e "CREATE TABLE IF NOT EXISTS hsbc.fraud_alerts (transaction_id text PRIMARY KEY, transaction_time timestamp, amount double, merchant text, category text, cc_num text, first text, last text, gender text, job text, state text, city text, zip text, is_fraud double, detected_at timestamp);"; `
docker exec spark-master bash -c "pip3 install xgboost scikit-learn pyarrow"; `
docker cp streaming-pipeline/model_retraining_xgb.py spark-master:/opt/spark-apps/; `
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/; `
docker cp streaming-pipeline/config.py spark-master:/opt/spark-apps/; `
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/; `
Write-Host "`n🎯 Starting model training (6 minutes)...`n" -ForegroundColor Yellow; `
docker exec spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining_xgb.py"; `
Write-Host "`n✅ Model trained! Starting services...`n" -ForegroundColor Green; `
docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 2g --conf spark.sql.shuffle.partitions=20 --conf spark.streaming.kafka.consumer.poll.ms=256 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 /opt/spark-apps/unified_streaming.py"; `
docker compose up -d --build producer dashboard; `
Write-Host "`n🚀 System is ready!`n" -ForegroundColor Green; `
Write-Host "Dashboard: http://localhost:8501" -ForegroundColor Cyan; `
Write-Host "Spark UI: http://localhost:8080" -ForegroundColor Cyan
```


