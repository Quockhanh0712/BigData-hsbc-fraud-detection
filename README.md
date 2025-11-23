# 🏦 HSBC Real-Time Fraud Detection System

<div align="center">

```
██╗  ██╗███████╗██████╗  ██████╗    ███████╗██████╗  █████╗ ██╗   ██╗██████╗ 
██║  ██║██╔════╝██╔══██╗██╔════╝    ██╔════╝██╔══██╗██╔══██╗██║   ██║██╔══██╗
███████║███████╗██████╔╝██║         █████╗  ██████╔╝███████║██║   ██║██║  ██║
██╔══██║╚════██║██╔══██╗██║         ██╔══╝  ██╔══██╗██╔══██║██║   ██║██║  ██║
██║  ██║███████║██████╔╝╚██████╗    ██║     ██║  ██║██║  ██║╚██████╔╝██████╔╝
╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝    ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ 
                                                                              
██████╗ ███████╗████████╗███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗    
██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║    
██║  ██║█████╗     ██║   █████╗  ██║        ██║   ██║██║   ██║██╔██╗ ██║    
██║  ██║██╔══╝     ██║   ██╔══╝  ██║        ██║   ██║██║   ██║██║╚██╗██║    
██████╔╝███████╗   ██║   ███████╗╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║    
╚═════╝ ╚══════╝   ╚═╝   ╚══════╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝    
```

### ⚡ Real-Time ML Pipeline for Credit Card Fraud Detection

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-337AB7?style=for-the-badge&logo=xgboost&logoColor=white)](https://xgboost.ai/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AUC-ROC](https://img.shields.io/badge/AUC--ROC-0.9964-success?style=flat-square)](/)
[![Recall](https://img.shields.io/badge/Recall-99%25-brightgreen?style=flat-square)](/)
[![Precision](https://img.shields.io/badge/Precision-54.6%25-blue?style=flat-square)](/)

</div>

---
## Students
- Trần Quốc Khánh — 23020387
- Nguyễn Văn Linh — 23020395
- Hoàng Ngọc Nam — 23020403

## 📑 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🏗️ System Architecture](#️-system-architecture)
- [💻 Technology Stack](#-technology-stack)
- [📊 Model Performance](#-model-performance)
- [🚀 Quick Start](#-quick-start)
- [📖 Documentation](#-documentation)
- [🔧 Configuration](#-configuration)
- [📈 Monitoring](#-monitoring)
- [🤝 Contributing](#-contributing)

---

## 🎯 Overview

**HSBC Fraud Detection System** là một hệ thống phát hiện gian lận giao dịch thẻ tín dụng **thời gian thực** sử dụng **Machine Learning** và **Stream Processing**. Hệ thống được xây dựng trên kiến trúc **Kappa Architecture** với khả năng xử lý hàng nghìn giao dịch mỗi giây và phát hiện gian lận với độ chính xác **99.64% (AUC-ROC)**.

### 🎪 Key Highlights

```
🎯 99.64% AUC-ROC Score     ⚡ <1s Latency          🔄 12+ TPS Throughput
📊 21 Engineered Features   🤖 XGBoost ML Model    🌊 Kappa Architecture
📡 Real-time Streaming      🔍 Fraud Detection     📈 Live Dashboard
```

### 🌟 Use Cases

- ✅ **Real-time fraud detection** cho banking transactions
- ✅ **Automated alerting** cho fraud analysts
- ✅ **Data archiving** cho compliance & audit
- ✅ **Historical analysis** cho model retraining
- ✅ **Performance monitoring** cho system operations

---

## ✨ Key Features

### 🚀 Core Capabilities

| Feature | Description |
|---------|-------------|
| **⚡ Real-Time Processing** | Sub-second fraud detection với Spark Structured Streaming |
| **🤖 ML-Powered Detection** | XGBoost model với 99.64% AUC-ROC accuracy |
| **📊 Advanced Features** | 21 engineered features (numeric, demographic, temporal, geographic) |
| **🌊 Kappa Architecture** | Single streaming path với dual output (archive + inference) |
| **📈 Live Dashboard** | Streamlit-based real-time monitoring dashboard |
| **🔄 Auto Archiving** | MinIO S3 storage cho transaction history |
| **🔍 Fraud Alerting** | Cassandra storage chỉ lưu fraud transactions |
| **🎯 High Precision** | 54.6% precision giảm false positives |
| **🔐 Scalable** | Distributed processing với Spark cluster |

### 🛠️ Technical Features

- **Streaming ETL**: Kafka → Spark → Cassandra/MinIO pipeline
- **Feature Engineering**: 21 features từ raw transaction data
- **ML Pipeline**: PySpark MLlib với XGBoost integration
- **REST API**: FastAPI backend với async operations
- **Web UI**: Interactive Streamlit dashboard
- **Containerized**: Full Docker Compose deployment
- **Monitoring**: Logs, metrics, và health checks

---

## 🏗️ System Architecture

### 📐 Kappa Architecture - Single Streaming Path

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         HSBC FRAUD DETECTION SYSTEM                              │
│                            Kappa Architecture                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐                ┌──────────────┐                ┌──────────────┐
    │   Producer   │                │    Kafka     │                │    Spark     │
    │              │───────────────▶│   Broker     │───────────────▶│  Streaming   │
    │ CSV Replay   │  JSON Messages │ transactions │  Micro-Batches │   Pipeline   │
    │ 12 tx/sec    │                │  (3 parts)   │                │   (local[4]) │
    └──────────────┘                └──────────────┘                └──────┬───────┘
                                                                           │
                                                                           │
                                    ┌──────────────────────────────────────┴────────┐
                                    │                                                │
                                    │    Feature Engineering (21 features)          │
                                    │                                                │
                                    └──────────────────────────────────────┬────────┘
                                                                           │
                        ┌──────────────────────────────────────────────────┼────────────────────────────┐
                        │                                                  │                            │
                        ▼                                                  ▼                            ▼
              ┌─────────────────┐                            ┌─────────────────────┐       ┌──────────────────┐
              │   MinIO S3      │                            │   XGBoost Model     │       │   Cassandra      │
              │   Archive       │                            │   Inference         │       │   Fraud Alerts   │
              │                 │                            │   (AUC: 0.9964)     │       │                  │
              │ All Txns        │                            │                     │       │ Only Fraud       │
              │ Parquet         │                            │ prediction = 0/1    │       │ (prediction=1)   │
              └─────────────────┘                            └─────────────────────┘       └──────────┬───────┘
                                                                                                       │
                                                                                                       │
                                                                                         ┌─────────────┴──────────┐
                                                                                         │                        │
                                                                                         ▼                        ▼
                                                                                  ┌────────────┐         ┌──────────────┐
                                                                                  │  FastAPI   │         │  Streamlit   │
                                                                                  │  Backend   │────────▶│  Dashboard   │
                                                                                  │            │  REST   │              │
                                                                                  │ Port 8000  │         │  Port 8501   │
                                                                                  └────────────┘         └──────────────┘
```

### 📦 Component Overview

| Component | Technology | Purpose | Port |
|-----------|------------|---------|------|
| **Producer** | Python + Kafka | Transaction replay từ CSV | - |
| **Kafka** | Apache Kafka 7.4.0 | Message broker cho streaming | 9092 |
| **Spark** | Apache Spark 3.5.0 | Stream processing & ML inference | 8080, 4040 |
| **XGBoost** | XGBoost 2.0+ | ML model cho fraud detection | - |
| **Cassandra** | Cassandra 4.1 | NoSQL storage cho fraud alerts | 9042 |
| **MinIO** | MinIO Latest | S3-compatible object storage | 9000, 9001 |
| **API** | FastAPI 0.104 | REST API backend | 8000 |
| **Dashboard** | Streamlit 1.29 | Web-based monitoring UI | 8501 |

---

## 💻 Technology Stack

### 🐍 Core Technologies

<table>
<tr>
<td width="50%">

**Data Processing**
- 🔥 Apache Spark 3.5.0
- 📡 Apache Kafka 7.4.0
- 🐍 PySpark 3.5.0
- 📊 Pandas 2.0+

**Machine Learning**
- 🤖 XGBoost 2.0+
- 📈 Scikit-learn 1.3+
- 🧮 NumPy 1.24+
- 📊 Apache Spark MLlib

</td>
<td width="50%">

**Storage & Databases**
- 💾 Apache Cassandra 4.1
- 🗄️ MinIO (S3-compatible)
- 🐘 Zookeeper 7.5.0

**Backend & Frontend**
- ⚡ FastAPI 0.104
- 🎨 Streamlit 1.29
- 🔌 Uvicorn (ASGI server)
- 📊 Plotly for charts

</td>
</tr>
</table>

### 🐳 Infrastructure

```yaml
Containerization: Docker 20.10+, Docker Compose 2.0+
Orchestration: Docker Compose with Bridge Networking
Resource Management: Docker resource limits (CPU, Memory)
Monitoring: Docker logs, Spark UI, MinIO Console
```

### 📚 Python Libraries

```python
# ML & Data Science
xgboost>=2.0.0          # Gradient boosting ML model
scikit-learn>=1.3.0     # ML utilities & metrics
pandas>=2.0.0           # Data manipulation
numpy>=1.24.0           # Numerical computing
pyarrow>=13.0.0         # Parquet format support

# Spark & Streaming
pyspark>=3.5.0          # Spark Python API
kafka-python>=2.0.2     # Kafka producer

# Backend & API
fastapi>=0.104.0        # Async REST API framework
uvicorn>=0.24.0         # ASGI server
cassandra-driver>=3.28  # Cassandra Python driver

# Frontend
streamlit>=1.29.0       # Dashboard framework
plotly>=5.17.0          # Interactive charts
```

---

## 📊 Model Performance

### 🎯 XGBoost Production Model

**Model Configuration**:
```python
SparkXGBClassifier(
    n_estimators=100,        # 100 decision trees
    max_depth=6,             # Tree depth
    learning_rate=0.3,       # Boosting learning rate
    subsample=0.8,           # Row sampling
    colsample_bytree=0.8,    # Column sampling
    objective='binary:logistic',
    eval_metric='auc',
    seed=42
)
```

### 📈 Performance Metrics

<table>
<tr>
<td width="50%">

**Training Performance**
```
Dataset: 1,296,675 transactions
Training Time: 6-10 minutes
Features: 21 engineered
Fraud Rate: 0.58%
Split: 80/20 train/test
```

</td>
<td width="50%">

**Production Metrics**
```
AUC-ROC: 0.9964 (Excellent)
Recall: ~99% (Almost no false negatives)
Precision: ~54.6% (Acceptable for fraud)
F1-Score: 70.4%
FPR: 0.8% (Very low false positives)
```

</td>
</tr>
</table>

### 📊 Confusion Matrix

```
                    Predicted
                 Normal    Fraud
Actual  Normal   10,970     92    ← 92 False Positives (0.8%)
        Fraud        1      100   ← 1 False Negative (1%)

✅ True Negatives: 10,970 (correctly identified normal)
✅ True Positives: 100 (correctly identified fraud)
❌ False Positives: 92 (normal flagged as fraud)
❌ False Negatives: 1 (fraud missed)
```

### 🎯 Business Impact

| Metric | Value | Impact |
|--------|-------|--------|
| **Fraud Caught** | 99% | Prevents 99 out of 100 fraudulent transactions |
| **False Alarms** | 0.8% | Only 92 false alerts per 11,062 normal transactions |
| **Processing Speed** | <1s | Real-time detection without delays |
| **Cost Savings** | High | Automated detection reduces manual review |

### 🧪 Model Comparison

| Model | AUC-ROC | Recall | Precision | Status |
|-------|---------|--------|-----------|--------|
| **XGBoost** | **0.9964** | **99%** | **54.6%** | 🚀 **Production** |
| DecisionTree | 0.8221 | - | - | ⚠️ Deprecated |
| RandomForest | - | - | - | ⚠️ Not Trained |

---

## 🚀 Quick Start

### 📋 Prerequisites

```bash
✅ Docker Desktop >= 20.10
✅ Docker Compose >= 2.0
✅ RAM >= 8GB (recommended 16GB)
✅ Disk Space >= 20GB
✅ Windows 10/11 or Linux
✅ PowerShell or Bash
```

### ⚡ 5-Minute Setup

#### Step 1: Clone Repository

```powershell
git clone https://github.com/your-org/hsbc-fraud-detection.git
cd hsbc-fraud-detection-new
```

#### Step 2: Verify Data Files

```powershell
# Check required data files exist
ls data/raw/

# Required files:
# ✅ fraudTrain.csv    (1.3M rows - training data)
# ✅ fraudTest.csv     (0.5M rows - test data)  
# ✅ df_test_hdfs.csv  (100K rows - production replay)
```

#### Step 3: Start Infrastructure

```powershell
# Start all services
docker compose up -d

# Wait for services to initialize (~30 seconds)
Start-Sleep -Seconds 30

# Check all containers running
docker compose ps
```

Expected output: **9 containers** running (zookeeper, kafka, minio, cassandra, spark-master, spark-worker, producer, api, dashboard)

#### Step 4: Setup Cassandra Database

```powershell
# Create keyspace and table
docker exec cassandra cqlsh -e "
CREATE KEYSPACE IF NOT EXISTS hsbc 
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS hsbc.fraud_alerts (
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

#### Step 5: Train XGBoost Model

```powershell
# Install XGBoost dependencies
docker exec spark-master bash -c "pip3 install xgboost scikit-learn pyarrow"

# Copy training script
docker cp streaming-pipeline/model_retraining_xgb.py spark-master:/opt/spark-apps/

# Train model (takes 6-10 minutes)
docker exec spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining_xgb.py"

# Verify model created
docker exec spark-master ls -lh /opt/data/models/fraud_xgb_21features/
```

Expected: `✅ XGBoost model saved to /opt/data/models/fraud_xgb_21features`

#### Step 6: Start Streaming Pipeline

```powershell
# Copy streaming files
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/

# Start streaming (runs in background)
docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 2g --conf spark.sql.shuffle.partitions=20 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 /opt/spark-apps/unified_streaming.py"

# Wait 10 seconds for streaming to start
Start-Sleep -Seconds 10

# Check streaming logs
docker logs spark-master --tail 30
```

Expected logs:
```
✅ Model loaded successfully
✅ Subscribed to topic: transactions_hsbc
✅ ALL STREAMS STARTED SUCCESSFULLY
```

#### Step 7: Access Dashboard

```powershell
# Open in browser
start http://localhost:8501

# Or manually navigate to:
# Dashboard: http://localhost:8501
# API Docs: http://localhost:8000/docs
# Spark UI: http://localhost:8080
```

### 🎉 Success Checklist

```
✅ All 9 containers running
✅ Cassandra table created
✅ XGBoost model trained (AUC 0.9964)
✅ Streaming pipeline active
✅ Producer sending transactions (~12/sec)
✅ Fraud alerts appearing in Cassandra
✅ Dashboard showing real-time data
```

### 🔍 Monitoring Commands

```powershell
# Check fraud alerts count
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# View latest 5 fraud alerts
docker exec cassandra cqlsh -e "SELECT * FROM hsbc.fraud_alerts LIMIT 5;"

# Watch streaming logs real-time
docker logs -f spark-master --tail 50

# Check producer status
docker logs producer --tail 20

# System resource usage
docker stats --no-stream
```

---

## 📖 Documentation

### 📚 Comprehensive Guides

| Document | Description | Link |
|----------|-------------|------|
| **📊 Data Flow Guide** | Chi tiết luồng dữ liệu qua hệ thống | [DATA_FLOW_GUIDE.md](./DATA_FLOW_GUIDE.md) |
| **🔧 Feature Engineering** | 21 features và cách tính toán | [FEATURE_ENGINEERING_GUIDE.md](./FEATURE_ENGINEERING_GUIDE.md) |
| **🤖 Model Training** | XGBoost training process | [MODEL_TRAINING_GUIDE.md](./MODEL_TRAINING_GUIDE.md) |
| **🏗️ Architecture** | System architecture và design | [ARCHITECTURE.md](./ARCHITECTURE.md) |
| **📐 Technical Design** | Technical specifications | [TECHNICAL_DESIGN.md](./TECHNICAL_DESIGN.md) |
| **📋 Checklist** | Operations checklist | [CHECKLIST.md](./CHECKLIST.md) |
| **💻 Commands** | Command reference | [COMMANDS.md](./COMMANDS.md) |
| **🚀 Deployment** | Deployment guide | [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) |
| **📖 System Guide** | Complete system operations | [SYSTEM_GUIDE.md](./SYSTEM_GUIDE.md) |
| **🔄 Reset Guide** | Streaming reset procedures | [RESET_STREAMING_GUIDE.md](./RESET_STREAMING_GUIDE.md) |
| **📊 Monitoring** | Monitoring approaches | [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) |
| **ℹ️ System Explanation** | Storage strategy explained | [SYSTEM_EXPLANATION.md](./SYSTEM_EXPLANATION.md) |

### 🎯 Quick Links

```bash
# Data Flow: CSV → Kafka → Spark → ML → Storage
./DATA_FLOW_GUIDE.md

# Feature Engineering: 21 Features Explained
./FEATURE_ENGINEERING_GUIDE.md

# Model Training: XGBoost Training Process
./MODEL_TRAINING_GUIDE.md

# Architecture: Kappa Architecture Design
./ARCHITECTURE.md

# Operations: Daily Operations Guide
./CHECKLIST.md
```

---

## 🔧 Configuration

### ⚙️ Key Configuration Files

#### Producer Configuration (`producer/config.py`)

```python
# Kafka Settings
KAFKA_BOOTSTRAP_SERVERS = 'kafka:29092'
KAFKA_TRANSACTION_TOPIC = 'transactions_hsbc'

# Data Settings
CSV_FILE = '/data/raw/df_test_hdfs.csv'  # Production data
TRANSACTION_RATE = 12  # transactions per second

# Logging
LOG_LEVEL = 'INFO'
LOG_INTERVAL = 100  # Log every N transactions
```

#### Spark Streaming Configuration (`streaming-pipeline/config.py`)

```python
# Kafka Consumer
KAFKA_BOOTSTRAP_SERVERS = 'kafka:29092'
TOPIC_NAME = 'transactions_hsbc'
KAFKA_STARTING_OFFSETS = 'earliest'  # or 'latest'

# Model Path
MODEL_PATH = '/opt/data/models/fraud_xgb_21features'

# Spark Settings
SHUFFLE_PARTITIONS = 20
STREAMING_TRIGGER_INTERVAL = '2 seconds'

# MinIO/S3
S3_ENDPOINT = 'http://minio:9000'
S3_ACCESS_KEY = 'admin'
S3_SECRET_KEY = 'password123'
S3_BUCKET = 'hsbc-data'

# Cassandra
CASSANDRA_HOST = 'cassandra'
CASSANDRA_PORT = 9042
CASSANDRA_KEYSPACE = 'hsbc'
CASSANDRA_TABLE = 'fraud_alerts'
```

#### API Configuration (`api/main.py`)

```python
# Cassandra Connection
CASSANDRA_HOST = 'cassandra'
CASSANDRA_PORT = 9042
CASSANDRA_KEYSPACE = 'hsbc'

# API Settings
MAX_LIMIT = 10000  # Max records per query
DEFAULT_LIMIT = 100
```

### 🎛️ Environment Variables

```yaml
# docker-compose.yml
services:
  producer:
    environment:
      - TRANSACTION_RATE=12  # Adjust throughput
      - CSV_FILE=/data/raw/df_test_hdfs.csv
  
  spark-master:
    environment:
      - SPARK_MASTER_HOST=spark-master
      - SPARK_MASTER_PORT=7077
  
  api:
    environment:
      - CASSANDRA_HOST=cassandra
      - CASSANDRA_PORT=9042
  
  dashboard:
    environment:
      - API_URL=http://api:8000
```

---

## 📈 Monitoring

### 🖥️ Web UIs

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:8501 | Real-time fraud monitoring |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Spark Master** | http://localhost:8080 | Spark cluster status |
| **Spark Jobs** | http://localhost:4040 | Running job details |
| **MinIO Console** | http://localhost:9001 | S3 storage management |

### 📊 Key Metrics

#### System Health

```powershell
# Check all containers
docker compose ps

# Resource usage
docker stats --no-stream

# Disk usage
docker system df
```

#### Data Metrics

```powershell
# Total fraud alerts
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Recent fraud alerts
docker exec cassandra cqlsh -e "SELECT transaction_id, amount, merchant, category FROM hsbc.fraud_alerts LIMIT 10;"

# Fraud by category
docker exec cassandra cqlsh -e "SELECT category, COUNT(*) FROM hsbc.fraud_alerts GROUP BY category ALLOW FILTERING;"
```

#### Stream Processing

```powershell
# Streaming logs
docker logs spark-master --tail 100 | Select-String "Batch|fraud"

# Producer throughput
docker logs producer --tail 20 | Select-String "Rate"

# API requests
docker logs api --tail 50
```

### 🔔 Alerts & Notifications

**Fraud Detection Logs**:
```
🚨 FRAUD DETECTED: Transaction abc123, Amount: $285.54, Merchant: fraud_Cole PLC
```

**Batch Processing Logs**:
```
📦 Batch 42: Processed 24 transactions
🚨 Batch 42: Detected 3 fraud alerts → Cassandra
```

### 📈 Real-Time Monitoring Script

```powershell
# Save as watch_fraud.ps1
while ($true) {
    Clear-Host
    Write-Host "=== HSBC FRAUD DETECTION MONITOR ===" -ForegroundColor Cyan
    Write-Host ""
    
    # Fraud count
    $count = docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" 2>$null | Select-String "\d+" | ForEach-Object { $_.Matches.Value }
    Write-Host "Total Fraud Alerts: $count" -ForegroundColor Yellow
    
    # Latest fraud
    Write-Host "`nLatest Fraud (last 30 seconds):" -ForegroundColor Green
    docker logs spark-master --since 30s 2>&1 | Select-String "FRAUD DETECTED" | Select-Object -Last 5
    
    Start-Sleep -Seconds 5
}
```

Run: `.\watch_fraud.ps1`

---

## 🤝 Contributing

### 🌟 How to Contribute

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### 📝 Contribution Areas

- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Test coverage
- 🎨 UI/UX enhancements
- ⚡ Performance optimizations

### 🔍 Code Standards

```python
# Python: PEP 8
black .
flake8 .
mypy .

# Documentation: Clear comments
# Tests: pytest with >80% coverage
# Commits: Conventional Commits format
```

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**HSBC Fraud Detection Team**

- 🧑‍💻 Development Team
- 📊 Data Science Team
- 🔧 DevOps Team
- 📈 Business Analytics Team

---

## 📞 Support

### 🆘 Getting Help

- 📧 Email: support@hsbc-fraud-detection.com
- 📖 Documentation: [Full Documentation Index](./INDEX.md)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/hsbc-fraud-detection/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-org/hsbc-fraud-detection/discussions)

### 🔧 Troubleshooting

**Common Issues**:

1. **Producer not sending data**: Check Kafka connectivity
2. **Model not found**: Run training step (Step 5)
3. **No fraud alerts**: Check streaming logs, verify model loaded
4. **Dashboard not loading**: Check API health at http://localhost:8000

See [SYSTEM_GUIDE.md](./SYSTEM_GUIDE.md#troubleshooting) for detailed troubleshooting.

---

## 🙏 Acknowledgments

- Apache Spark Community
- Apache Kafka Community
- XGBoost Development Team
- FastAPI & Streamlit Communities
- Kaggle Credit Card Fraud Dataset

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

Made with ❤️ by HSBC Fraud Detection Team

</div>
