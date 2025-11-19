# HSBC Fraud Detection System - Technical Design Document

## 1. System Architecture

### 1.1 Overview
Hệ thống fraud detection real-time sử dụng Kappa Architecture để xử lý streaming data và phát hiện giao dịch gian lận với độ chính xác cao.

### 1.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Data Sources                                 │
│  ┌────────────┐    ┌────────────┐    ┌─────────────┐               │
│  │fraudTrain  │    │fraudTest   │    │df_test_hdfs │               │
│  │(1.3M rows) │    │(0.5M rows) │    │(100K rows)  │               │
│  └────────────┘    └────────────┘    └─────────────┘               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Kafka Message Broker                            │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Topic: transactions_hsbc                                   │    │
│  │  Partitions: 3                                              │    │
│  │  Replication: 1                                             │    │
│  │  Format: JSON                                               │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Spark Streaming Pipeline                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. Read from Kafka                                          │   │
│  │  2. Feature Engineering (21 features)                        │   │
│  │  3. Load XGBoost Model (AUC: 0.9964)                        │   │
│  │  4. Predict Fraud Probability                                │   │
│  │  5. Filter Fraud Transactions (threshold > 0.5)             │   │
│  │  6. Write to Multiple Sinks                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
┌──────────────────────┐      ┌──────────────────────┐
│   Cassandra DB       │      │   MinIO (S3)         │
│   (Real-time Store)  │      │   (Data Lake)        │
│                      │      │                      │
│  - fraud_alerts      │      │  - Raw data          │
│  - Quick queries     │      │  - Archival          │
│  - Low latency       │      │  - Analytics         │
└──────────────────────┘      └──────────────────────┘
         │
         ▼
┌──────────────────────┐
│  Streamlit Dashboard │
│                      │
│  - Real-time viz     │
│  - Fraud metrics     │
│  - Alert monitoring  │
└──────────────────────┘
```

## 2. Component Design

### 2.1 Data Producer

**File**: `producer/producer.py`

**Responsibilities**:
- Read data từ CSV files
- Parse và validate transaction data
- Produce messages to Kafka topic
- Control message rate (15 tx/sec)

**Configuration**:
```python
KAFKA_BOOTSTRAP_SERVERS = 'kafka:29092'
TOPIC_NAME = 'transactions_hsbc'
TRANSACTION_RATE = 15  # tx/sec
BATCH_SIZE = 100
DATA_PATH = '/data/raw/df_test_hdfs.csv'
```

**Message Format**:
```json
{
  "transaction_id": "abc123",
  "transaction_time": "2025-01-15 14:30:00",
  "amount": 150.50,
  "merchant": "Amazon",
  "category": "shopping_net",
  "cc_num": "1234567890123456",
  "first": "John",
  "last": "Doe",
  "gender": "M",
  "state": "CA",
  "city": "Los Angeles",
  "zip": "90001",
  "lat": 34.0522,
  "long": -118.2437,
  "city_pop": 3979576,
  "job": "Engineer",
  "dob": "1990-01-15",
  "unix_time": 1705330200,
  "merch_lat": 34.0522,
  "merch_long": -118.2437,
  "is_fraud": 0
}
```

### 2.2 Feature Engineering

**File**: `streaming-pipeline/feature_engineering.py`

**Class**: `FeatureEngineer`

**21 Features**:
1. **amount** (renamed from amt) - Transaction amount
2. **age** - Customer age calculated from DOB
3. **city_pop** - City population
4. **hour_of_day** - Hour extracted from transaction time
5. **is_weekend** - 1 if weekend, 0 otherwise
6. **amount_log** - Log transformation of amount
7. **is_high_value** - 1 if amount > $500
8. **is_extreme_value** - 1 if amount > $1000
9. **distance_customer_merchant** - Haversine distance in km
10. **is_out_of_state** - 1 if customer and merchant in different states
11. **amt_to_pop_ratio** - Amount normalized by city population
12. **gender_encoded** - 0 for F, 1 for M
13-21. **cat_*** - One-hot encoded categories (9 categories)
    - cat_grocery_pos
    - cat_shopping_net
    - cat_misc_net
    - cat_gas_transport
    - cat_shopping_pos
    - cat_food_dining
    - cat_personal_care
    - cat_health_fitness
    - cat_entertainment

**Key Methods**:
```python
def engineer_features(self, df: DataFrame) -> DataFrame:
    """Apply all 21 feature transformations"""
    
def calculate_distance(self, lat1, lon1, lat2, lon2) -> float:
    """Haversine distance calculation"""
    
def one_hot_encode_category(self, df: DataFrame) -> DataFrame:
    """One-hot encode transaction categories"""
```

### 2.3 Machine Learning Models

#### 2.3.1 XGBoost Model (Production)

**File**: `streaming-pipeline/model_retraining_xgb.py`

**Configuration**:
```python
xgb = SparkXGBClassifier(
    # objective auto-set for binary classification
    max_depth=6,
    learning_rate=0.3,
    n_estimators=100,
    subsample=0.8,
    colsample_bytree=0.8,
    gamma=0,
    min_child_weight=1,
    reg_alpha=0,
    reg_lambda=1,
    scale_pos_weight=1,
    eval_metric='auc',
    seed=42,
    featuresCol='features',
    labelCol='label',
    predictionCol='prediction',
    probabilityCol='probability'
)
```

**Performance**:
- AUC-ROC: 0.9964
- Training Time: ~6 minutes
- Training Data: 1,296,675 transactions
- Test Split: 80/20

**Model Pipeline**:
1. StringIndexer (label encoding)
2. VectorAssembler (feature vectorization)
3. SparkXGBClassifier (gradient boosting)

#### 2.3.2 DecisionTree Model (Baseline)

**File**: `streaming-pipeline/model_retraining.py`

**Configuration**:
```python
dt = DecisionTreeClassifier(
    featuresCol='features',
    labelCol='label',
    predictionCol='prediction',
    probabilityCol='probability',
    maxDepth=30,
    minInstancesPerNode=10,
    impurity='gini',
    seed=42
)
```

**Performance**:
- AUC-ROC: 0.8221
- Training Time: ~2 minutes

#### 2.3.3 RandomForest Model (Alternative)

**File**: `streaming-pipeline/model_retraining_rf.py`

**Configuration**:
```python
rf = RandomForestClassifier(
    featuresCol='features',
    labelCol='label',
    predictionCol='prediction',
    probabilityCol='probability',
    numTrees=200,
    maxDepth=30,
    featureSubsetStrategy='sqrt',
    seed=41
)
```

**Status**: Ready but not trained yet

### 2.4 Streaming Pipeline

**File**: `streaming-pipeline/unified_streaming.py`

**Class**: `UnifiedStreamingPipeline`

**Workflow**:
```python
1. Read from Kafka
   ├── readStream()
   ├── format('kafka')
   └── load()

2. Parse JSON & Schema Validation
   ├── from_json()
   └── select()

3. Feature Engineering
   ├── FeatureEngineer.engineer_features()
   └── 21 features generated

4. Model Inference
   ├── Load XGBoost model
   ├── transform()
   └── probability > 0.5 → fraud

5. Write to Sinks
   ├── Cassandra (fraud_alerts)
   │   └── foreachBatch()
   └── MinIO/S3 (archive)
       └── parquet format
```

**Streaming Configuration**:
```python
spark.conf.set("spark.sql.shuffle.partitions", "20")
spark.conf.set("spark.streaming.kafka.consumer.poll.ms", "256")
spark.conf.set("spark.streaming.backpressure.enabled", "true")
```

### 2.5 Data Storage

#### 2.5.1 Cassandra

**Keyspace**: `hsbc`

**Table**: `fraud_alerts`
```cql
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

**Purpose**:
- Store real-time fraud alerts
- Low-latency queries (<10ms)
- Point lookups by transaction_id

#### 2.5.2 MinIO (S3-compatible)

**Buckets**:
- `fraud-data-lake`: Raw and processed data archive
- `fraud-models`: Trained model artifacts

**Storage Format**: Parquet (columnar, compressed)

**Purpose**:
- Long-term data archival
- Batch analytics
- Model versioning

### 2.6 Dashboard

**File**: `dashboard/app.py`

**Technology**: Streamlit

**Features**:
- Real-time fraud alerts monitoring
- Transaction volume trends
- Fraud detection rate
- Geographic distribution
- Merchant analysis
- Alert severity levels

**Refresh Rate**: 5 seconds

## 3. Data Flow

### 3.1 Real-time Flow

```
1. Transaction occurs → Producer reads from CSV
2. Producer sends to Kafka topic (transactions_hsbc)
3. Spark Streaming consumes from Kafka
4. Feature Engineering transforms raw data
5. XGBoost model predicts fraud probability
6. If prob > 0.5:
   ├── Write to Cassandra (fraud_alerts)
   └── Trigger alert
7. All transactions archived to MinIO
8. Dashboard queries Cassandra for display
```

### 3.2 Model Training Flow

```
1. Load fraudTrain.csv (1.3M rows)
2. Apply same feature engineering (21 features)
3. Split 80/20 train/test
4. Train XGBoost model:
   ├── 100 estimators
   ├── max_depth=6
   └── learning_rate=0.3
5. Evaluate on test set (AUC-ROC)
6. Save model to /opt/data/models/fraud_xgb_21features
7. Model loaded by streaming pipeline
```

## 4. Performance Characteristics

### 4.1 Throughput
- **Producer**: 15 transactions/second
- **Streaming**: Can handle 1000+ tx/sec
- **Cassandra Write**: <10ms latency
- **End-to-end latency**: <1 second

### 4.2 Scalability
- **Kafka Partitions**: 3 (can increase)
- **Spark Executors**: 4 cores
- **Cassandra Nodes**: 1 (can cluster)
- **Horizontal scaling**: Add more Spark workers

### 4.3 Resource Usage
- **Spark Master**: 4GB RAM, 4 cores
- **Spark Worker**: 2GB RAM, 2 cores
- **Cassandra**: 2GB RAM
- **Kafka**: 1GB RAM
- **Total**: ~10GB RAM minimum

## 5. Error Handling

### 5.1 Producer Errors
- Connection retry: 3 attempts
- Backoff: Exponential (1s, 2s, 4s)
- Logging: All errors logged with transaction_id

### 5.2 Streaming Errors
- Checkpoint: Every 10 seconds
- Failed batches: Retry once
- Model errors: Skip transaction, log error
- Write failures: Dead letter queue (MinIO)

### 5.3 Model Fallback
If XGBoost model fails to load:
1. Log error
2. Continue in archive-only mode
3. No fraud detection
4. Alert operations team

## 6. Monitoring & Alerting

### 6.1 Metrics
- Transactions processed/second
- Fraud detection rate
- False positive rate
- Model inference latency
- Kafka consumer lag
- Cassandra write latency

### 6.2 Logs
- Producer: `/logs/producer.log`
- Streaming: Spark UI + container logs
- Model: Training metrics logged

### 6.3 Health Checks
- Kafka: Topic availability
- Cassandra: Connection test
- Spark: Active streaming query
- MinIO: Bucket accessibility

## 7. Security

### 7.1 Data Protection
- Credit card numbers: Masked in logs
- PII: Encrypted at rest (MinIO)
- Access control: MinIO IAM policies

### 7.2 Network Security
- Internal Docker network
- No external ports except UI
- TLS for production (not in dev)

## 8. Deployment

### 8.1 Environment
- **Development**: Docker Compose
- **Production**: Kubernetes (future)

### 8.2 CI/CD Pipeline
```
1. Code commit → GitHub
2. Unit tests → pytest
3. Integration tests → Docker Compose
4. Model validation → AUC threshold check
5. Docker build → Container registry
6. Deploy → Rolling update
```

## 9. Future Enhancements

### 9.1 Short-term
- [ ] Add more ML models (Neural Networks)
- [ ] Implement A/B testing framework
- [ ] Add feature importance tracking
- [ ] Improve dashboard with more metrics

### 9.2 Long-term
- [ ] Real-time model retraining
- [ ] Federated learning across branches
- [ ] Advanced anomaly detection
- [ ] Integration with fraud investigation system
- [ ] Mobile app for alerts

## 10. References

### 10.1 Technologies
- Apache Spark: https://spark.apache.org/
- Apache Kafka: https://kafka.apache.org/
- Cassandra: https://cassandra.apache.org/
- XGBoost: https://xgboost.readthedocs.io/
- MinIO: https://min.io/

### 10.2 Documentation
- Spark Streaming Guide: https://spark.apache.org/docs/latest/streaming-programming-guide.html
- XGBoost with Spark: https://xgboost.readthedocs.io/en/stable/jvm/xgboost4j_spark_tutorial.html
- Cassandra CQL: https://cassandra.apache.org/doc/latest/cql/

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-19  
**Author**: HSBC Fraud Detection Team
