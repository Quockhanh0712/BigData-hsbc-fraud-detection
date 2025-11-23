# 🏗️ HSBC Fraud Detection System - Architecture

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HSBC FRAUD DETECTION SYSTEM                      │
│                  Real-time ML-based Fraud Detection                 │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────┐      ┌────────────────┐      ┌──────────┐
│   CSV Data   │ ───▶ │ Producer │ ───▶ │ Kafka (Topic)  │ ───▶ │  Spark   │
│ fraudTrain   │      │  Python  │      │ transactions   │      │ Streaming│
└──────────────┘      └──────────┘      └────────────────┘      └─────┬────┘
                                                                       │
                                                    ┌──────────────────┴─────────────┐
                                                    │                                │
                                                    ▼                                ▼
                                            ┌──────────────┐                 ┌──────────────┐
                                            │   MinIO S3   │                 │  ML Model    │
                                            │   Archive    │                 │   XGBoost    │
                                            └──────────────┘                 └──────┬───────┘
                                                                                    │
                                                                                    ▼
                                                                            ┌──────────────┐
                                                                            │  Cassandra   │
                                                                            │fraud_alerts │
                                                                            └──────┬───────┘
                                                                                   │
                                    ┌──────────────────────────────────────────────┘
                                    │
                                    ▼
                            ┌──────────────┐
                            │   FastAPI    │
                            │  REST API    │
                            └──────┬───────┘
                                   │
                                   ▼
                            ┌──────────────┐
                            │  Streamlit   │
                            │  Dashboard   │
                            └──────────────┘
```

---

## 🎯 Data Flow Pipeline

### Phase 1: Data Ingestion
```
CSV File → Producer → Kafka Topic
```

**Components**:
- **Source**: `data/raw/fraudTrain.csv` (1.3M transactions)
- **Producer**: Python script generates transactions at configurable rate (2/sec)
- **Kafka Topic**: `transactions_hsbc` (3 partitions)

**Data Format**:
```json
{
  "trans_num": "abc123",
  "trans_date_trans_time": "2020-01-01 00:00:00",
  "cc_num": "1234567890123456",
  "merchant": "fraud_Merchant",
  "category": "grocery_pos",
  "amt": 123.45,
  "first": "John",
  "last": "Doe",
  "gender": "M",
  "street": "123 Main St",
  "city": "Springfield",
  "state": "IL",
  "zip": "62701",
  "lat": 39.78,
  "long": -89.65,
  "city_pop": 116250,
  "job": "Engineer",
  "dob": "1980-01-01",
  "trans_num": "abc123",
  "unix_time": 1577836800,
  "merch_lat": 39.78,
  "merch_long": -89.65,
  "is_fraud": 0
}
```

---

### Phase 2: Stream Processing
```
Kafka → Spark Structured Streaming → Feature Engineering → ML Prediction
```

**Components**:
- **Spark Cluster**: 
  - Master (coordinator)
  - Worker (executor with 12 cores, 1GB RAM)
- **Batch Interval**: 2 seconds (inference), 10 seconds (archive)

**Processing Steps**:
1. Read from Kafka (micro-batches)
2. Parse JSON to DataFrame
3. Feature engineering (7 core features)
4. ML model prediction
5. Filter fraud predictions (probability > threshold)
6. Write to Cassandra & MinIO

**Feature Engineering**:
```
Raw Features:
- amount
- category
- hour_of_day
- state
- merchant
- ...

Engineered Features:
1. amount_log = log(amount + 1)
2. is_high_value = amount > 100
3. is_extreme_value = amount > 500
4. category_risk_score = risk mapping
5. risk_amount_interaction = category_risk * amount
6. hour_of_day = extract hour from timestamp
7. is_night = hour between 22:00 - 06:00
```

---

### Phase 3: Model Prediction
```
Features → XGBoost Model → Fraud Probability
```

**Model Architecture**:
- **Algorithm**: XGBoost Classifier (Gradient Boosting)
- **Trees**: 100 estimators
- **Max Depth**: 6
- **Learning Rate**: 0.3
- **Subsample**: 0.8
- **Features**: 21 engineered features (numeric, demographic, temporal, geographic, category)
- **Output**: Fraud probability (0.0 - 1.0)
- **Threshold**: Configurable (default: model prediction = 1.0)

**Training**:
- **Dataset**: fraudTrain.csv (1,296,675 rows - 100% data)
- **Split**: 80% train, 20% test
- **Evaluation**: AUC-ROC 0.9964, Recall ~99%, Precision ~54.6%
- **Location**: `/opt/data/models/fraud_xgb_21features`

---

### Phase 4: Storage
```
Predictions → Cassandra (Fraud Alerts) + MinIO (Archive)
```

**Cassandra Schema**:
```sql
CREATE TABLE hsbc.fraud_alerts (
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
);
```

**MinIO Structure**:
```
hsbc-data/
├── stream-archive/
│   └── year=2020/month=01/day=01/
│       └── part-00000-xxxxx.parquet
└── models/
    └── fraud_xgb_21features/
        ├── metadata/
        ├── stages/
        └── data/
```

---

### Phase 5: API Layer
```
Cassandra → FastAPI → REST Endpoints
```

**API Endpoints**:
```
GET  /                      Health check
GET  /fraud/alerts          List fraud alerts (with filters)
  ?limit=10                   Max results
  &category=grocery_pos       Filter by category
  &state=CA                   Filter by state
GET  /fraud/stats            Aggregate statistics
GET  /fraud/count            Total fraud count
```

**Response Format**:
```json
// GET /fraud/alerts?limit=2
[
  {
    "transaction_id": "abc123",
    "transaction_time": "2020-01-01T10:30:00",
    "amount": 285.54,
    "merchant": "fraud_Cole PLC",
    "category": "grocery_pos",
    "cc_num": "1234567890123456",
    "first": "John",
    "last": "Doe",
    "state": "CA",
    "city": "Los Angeles",
    "is_fraud": 1.0,
    "detected_at": "2025-11-16T10:30:15"
  },
  ...
]

// GET /fraud/stats
{
  "total_alerts": 42,
  "total_amount": 11076.21,
  "avg_amount": 263.72,
  "by_category": {
    "grocery_pos": 24,
    "gas_transport": 13,
    "shopping_net": 2,
    ...
  },
  "by_state": {
    "CA": 5,
    "NY": 3,
    ...
  }
}
```

---

### Phase 6: Visualization
```
API → Streamlit Dashboard → Web Browser
```

**Dashboard Components**:

1. **Overview Metrics** (3 columns)
   - Total fraud alerts
   - Total amount ($)
   - Average amount ($)

2. **Fraud Alerts Table**
   - Sortable columns
   - Filters: Limit, Category
   - Real-time data

3. **Analytics Charts**
   - Bar Chart: Fraud by category
   - Bar Chart: Top 10 states
   - Histogram: Amount distribution

4. **Auto-Refresh**
   - Checkbox to enable
   - 5-second interval

---

## 🛠️ Technology Stack

### Infrastructure Layer
```
┌─────────────────────────────────────┐
│         Docker Compose              │
│  Container Orchestration & Networking│
└─────────────────────────────────────┘
```

**Components**:
- Docker Compose 3.8
- Bridge Network: `hsbc-network`
- Volumes: zookeeper-data, kafka-data, minio-data, cassandra-data

---

### Messaging Layer
```
┌──────────────┐     ┌─────────────┐
│  Zookeeper   │────▶│   Kafka     │
│   (Coord)    │     │  (Broker)   │
└──────────────┘     └─────────────┘
```

**Specs**:
- **Zookeeper**: Confluent 7.5.0
  - Port: 2181
  - Role: Kafka coordination
  
- **Kafka**: Confluent 7.4.0
  - Ports: 9092 (external), 29092 (internal)
  - Topic: `transactions_hsbc` (3 partitions, RF=1)

---

### Processing Layer
```
┌──────────────────────────────────────┐
│        Apache Spark 3.5.0            │
│                                      │
│  ┌─────────────┐   ┌──────────────┐ │
│  │   Master    │──▶│   Worker     │ │
│  │  (Manager)  │   │ (Executor)   │ │
│  └─────────────┘   └──────────────┘ │
└──────────────────────────────────────┘
```

**Specs**:
- **Spark Master**:
  - Ports: 8080 (UI), 7077 (cluster), 4040 (app UI)
  - Role: Cluster manager
  
- **Spark Worker**:
  - Port: 8081 (UI)
  - Resources: 12 cores, 1GB RAM
  - Role: Task execution

**Libraries**:
- spark-sql-kafka-0-10 (Kafka integration)
- spark-cassandra-connector (Cassandra write)
- hadoop-aws (S3/MinIO support)

---

### Storage Layer
```
┌─────────────┐  ┌─────────────┐
│  Cassandra  │  │   MinIO     │
│  (NoSQL DB) │  │ (S3 Store)  │
└─────────────┘  └─────────────┘
```

**Cassandra**:
- Version: 4.1
- Port: 9042
- Keyspace: `hsbc` (SimpleStrategy, RF=1)
- Table: `fraud_alerts`
- Use case: Real-time fraud alerts storage

**MinIO**:
- Version: Latest
- Ports: 9000 (API), 9001 (Console)
- Credentials: admin/password123
- Bucket: `hsbc-data`
- Use case: Transaction archive, model storage

---

### ML Layer
```
┌─────────────────────────────────────┐
│     PySpark MLlib (Spark ML)        │
│                                     │
│  ┌────────────────────────────────┐ │
│  │   XGBoost Classifier           │ │
│  │   - 100 estimators             │ │
│  │   - Max depth: 6               │ │
│  │   - Learning rate: 0.3         │ │
│  │   - Features: 21               │ │
│  │   - AUC-ROC: 0.9964            │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Pipeline**:
1. StringIndexer (label encoding)
2. VectorAssembler (21 feature vector)
3. SparkXGBClassifier (gradient boosting prediction)

---

### Application Layer
```
┌─────────────┐     ┌──────────────┐
│   FastAPI   │────▶│  Streamlit   │
│  (Backend)  │     │  (Frontend)  │
└─────────────┘     └──────────────┘
```

**FastAPI**:
- Version: 0.104.1
- Port: 8000
- Framework: Python async
- Database: Cassandra (cassandra-driver)

**Streamlit**:
- Version: 1.29.0
- Port: 8501
- Charts: Plotly
- Data: Pandas

---

## 🔒 Security & Configuration

### Network Security
- All services in isolated bridge network
- External ports: 8000, 8501, 8080, 9001, 9042, 9092
- Internal communication: service names (DNS)

### Environment Variables
```yaml
Producer:
  - KAFKA_BOOTSTRAP_SERVERS: kafka:29092
  - KAFKA_TRANSACTION_TOPIC: transactions_hsbc
  - TRANSACTION_RATE: 2

API:
  - CASSANDRA_HOST: cassandra
  - CASSANDRA_PORT: 9042

Dashboard:
  - API_URL: http://api:8000

Spark:
  - SPARK_MASTER_HOST: spark-master
  - SPARK_MASTER_PORT: 7077
```

### Data Persistence
```
Volumes (persistent):
  - zookeeper-data    → /var/lib/zookeeper/data
  - kafka-data        → /var/lib/kafka/data
  - minio-data        → /data
  - cassandra-data    → /var/lib/cassandra

Bind Mounts (development):
  - ./data            → /opt/data (Spark)
  - ./streaming-pipeline → /opt/spark-apps
  - ./api             → /app
  - ./dashboard       → /app
```

---

## 📊 Performance Characteristics

### Throughput
- **Producer**: 2 transactions/second (configurable)
- **Spark**: Can handle up to 100+ tx/sec
- **API**: Async, handles concurrent requests
- **Dashboard**: Auto-refresh every 5 seconds

### Latency
- **End-to-end**: ~2-3 seconds
  - Producer → Kafka: <100ms
  - Kafka → Spark: ~2 sec (batch interval)
  - Spark → Cassandra: <500ms
  - API query: <100ms
  - Dashboard refresh: <200ms

### Resource Usage (Typical)
```
Container        CPU      Memory
─────────────────────────────────
kafka            5-10%    512MB
cassandra        10-15%   768MB
spark-master     5-10%    512MB
spark-worker     20-30%   1GB
minio            2-5%     256MB
producer         1-2%     128MB
api              1-2%     128MB
dashboard        2-5%     256MB
```

### Scalability
- **Horizontal**: Add more Spark workers
- **Vertical**: Increase worker cores/memory
- **Kafka partitions**: Increase for parallelism
- **Cassandra RF**: Increase for reliability

---

## 🔄 Failure Handling

### Kafka Resilience
- Topic replication: RF=1 (single node)
- Producer: Retries on failure
- Consumer: Checkpointing (Spark)

### Spark Resilience
- Master failure: Worker reconnect on restart
- Worker failure: Tasks redistributed
- Checkpoint: Kafka offsets tracked

### Cassandra Resilience
- Write consistency: ONE (single node)
- Health check: CQL ping every 30s
- Retry logic: Spark connector retries

### API Resilience
- Startup wait: Cassandra health check
- Connection pool: Reuse connections
- Graceful shutdown: Close connections

---

## 📈 Monitoring & Observability

### Logs
```
Component       Log Location
─────────────────────────────────────
Producer        docker logs producer
Kafka           docker logs kafka
Spark Master    docker logs spark-master
Spark Worker    docker logs spark-worker
Cassandra       docker logs cassandra
MinIO           docker logs minio
API             docker logs api
Dashboard       docker logs dashboard
```

### Metrics Endpoints
```
Service          Metrics URL
──────────────────────────────────────
Spark Master     http://localhost:8080
Spark App        http://localhost:4040
MinIO            http://localhost:9001
API Docs         http://localhost:8000/docs
Dashboard        http://localhost:8501
```

---

## 📚 References

- **Apache Spark**: https://spark.apache.org/docs/3.5.0/
- **Kafka**: https://kafka.apache.org/documentation/
- **Cassandra**: https://cassandra.apache.org/doc/latest/
- **MinIO**: https://min.io/docs/minio/linux/index.html
- **FastAPI**: https://fastapi.tiangolo.com/
- **Streamlit**: https://docs.streamlit.io/

---

