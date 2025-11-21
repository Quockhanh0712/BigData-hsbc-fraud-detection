# 📊 TÀI LIỆU LUỒNG DỮ LIỆU HỆ THỐNG HSBC FRAUD DETECTION

## 📋 MỤC LỤC
1. [Tổng Quan Luồng Dữ Liệu](#1-tổng-quan-luồng-dữ-liệu)
2. [Chi Tiết Từng Giai Đoạn](#2-chi-tiết-từng-giai-đoạn)
3. [Dữ Liệu Training](#3-dữ-liệu-training)
4. [Dữ Liệu Streaming](#4-dữ-liệu-streaming)
5. [Schema Chi Tiết](#5-schema-chi-tiết)

---

## 1. TỔNG QUAN LUỒNG DỮ LIỆU

### 1.1 Kiến Trúc Kappa - Luồng Duy Nhất

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HSBC FRAUD DETECTION SYSTEM                      │
│                         Data Flow Architecture                           │
└─────────────────────────────────────────────────────────────────────────┘

GIAI ĐOẠN 1: DATA SOURCE (Nguồn Dữ Liệu)
═══════════════════════════════════════════
📁 /data/raw/
   ├── fraudTrain.csv      1,296,675 dòng (Training - 100%)
   ├── fraudTest.csv         555,719 dòng (Testing)
   └── df_test_hdfs.csv      ~10% fraud rate (Production replay)

Thông tin dataset:
• Tổng cột: 23 columns
• Fraud rate: 0.58% (fraudTrain), ~10% (df_test_hdfs)
• Format: CSV → JSON → Kafka Messages
• Size: ~500MB raw data

                              ↓

GIAI ĐOẠN 2: PRODUCER (Phát Sinh Giao Dịch)
═══════════════════════════════════════════
🔄 Producer Container (producer.py)

Nhiệm vụ:
1. Đọc CSV file (df_test_hdfs.csv)
2. Chuyển đổi pandas DataFrame → JSON
3. Shuffle data (random replay)
4. Gửi lên Kafka với rate control

Xử lý:
┌─────────────────────────────────────┐
│ 1. Load CSV                         │
│    • Read with pandas               │
│    • Parse datetime fields          │
│    • Handle data types (cc_num→str) │
│    • Shuffle for randomness         │
├─────────────────────────────────────┤
│ 2. Convert Row → JSON               │
│    • 23 fields mapping              │
│    • Type conversion (int64→int)    │
│    • ISO timestamp format           │
│    • Preserve leading zeros (zip)   │
├─────────────────────────────────────┤
│ 3. Send to Kafka                    │
│    • Topic: transactions_hsbc       │
│    • Key: transaction_id            │
│    • Rate: 2-12 tx/sec (config)     │
│    • Compression: gzip              │
└─────────────────────────────────────┘

Output: JSON Messages → Kafka Topic
Rate: ~12.5 transactions/second (configurable)

                              ↓

GIAI ĐOẠN 3: KAFKA (Message Queue)
═══════════════════════════════════
📨 Kafka Cluster

Topic Configuration:
• Topic: transactions_hsbc
• Partitions: 3
• Replication: 1
• Retention: 7 days

Message Format:
{
  "transaction_id": "abc123...",
  "transaction_time": "2024-01-15T10:30:45",
  "amount": 89.50,
  "merchant": "Target",
  "category": "grocery_pos",
  ... (23 fields total)
}

Storage: In-memory + disk (temporary)
Purpose: Decoupling Producer ↔ Consumer

                              ↓

GIAI ĐOẠN 4: SPARK STREAMING (Xử Lý Real-time)
═══════════════════════════════════════════════
⚡ Spark Streaming Pipeline (unified_streaming.py)

┌──────────────────────────────────────────────────────────┐
│              SPARK STREAMING PROCESSING                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Step 1: READ FROM KAFKA                                │
│  ────────────────────────                               │
│  • Subscribe topic: transactions_hsbc                   │
│  • Offset: earliest (đọc từ đầu)                        │
│  • Batch: 1000 messages/trigger                         │
│  • Interval: 2 seconds                                  │
│                                                          │
│  Step 2: PARSE JSON                                     │
│  ───────────────────                                    │
│  • from_json() với schema 23 cột                        │
│  • Validate data types                                  │
│  • Add kafka_timestamp                                  │
│                                                          │
│  Step 3: FEATURE ENGINEERING (21 features)              │
│  ──────────────────────────────────────                 │
│  🔧 Feature Engineer (feature_engineering.py)           │
│                                                          │
│  A. NUMERIC FEATURES (4)                                │
│     • amount            : Original transaction amount   │
│     • amount_log        : log1p(amount)                 │
│     • is_high_value     : 1 if amount > $100           │
│     • is_extreme_value  : 1 if amount > $500           │
│                                                          │
│  B. DEMOGRAPHIC FEATURES (2)                            │
│     • age               : Calculated from dob           │
│     • gender_encoded    : M=1, F=0, Other=-1           │
│                                                          │
│  C. TEMPORAL FEATURES (2)                               │
│     • hour_of_day       : 0-23 extracted from time     │
│     • is_weekend        : 1 if Sat/Sun                 │
│                                                          │
│  D. GEOGRAPHIC FEATURES (2)                             │
│     • distance_customer_merchant : Haversine distance  │
│     • is_out_of_state   : 1 if cross-state            │
│                                                          │
│  E. CATEGORY ONE-HOT (13)                               │
│     • cat_grocery_pos, cat_shopping_net,               │
│       cat_misc_net, cat_gas_transport,                 │
│       cat_shopping_pos, cat_food_dining,               │
│       cat_personal_care, cat_health_fitness,           │
│       cat_entertainment, cat_utilities,                │
│       cat_travel, cat_electronics, cat_others          │
│                                                          │
│  F. ADDITIONAL FEATURES (2)                             │
│     • amt_to_pop_ratio  : amount / city_pop            │
│     • city_pop          : Customer city population     │
│                                                          │
│  Total: 21 engineered features                          │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Step 4: DUAL STREAM (Kappa Architecture)               │
│  ─────────────────────────────────────────              │
│                                                          │
│  ┌─────────────────────┐   ┌─────────────────────┐    │
│  │  STREAM A: ARCHIVE  │   │ STREAM B: INFERENCE │    │
│  └─────────────────────┘   └─────────────────────┘    │
│           │                          │                  │
│           ↓                          ↓                  │
│    [MinIO Storage]          [ML Model Prediction]      │
│                                                          │
└──────────────────────────────────────────────────────────┘

                    ↓                        ↓
              
    ┌─────────────────────┐        ┌─────────────────────┐
    │   STREAM A DETAIL   │        │   STREAM B DETAIL   │
    └─────────────────────┘        └─────────────────────┘

STREAM A: ARCHIVE (Data Lake)
═════════════════════════════
📦 MinIO (S3-compatible Storage)

Purpose: Lưu trữ lịch sử để retrain model

Process:
1. Lấy transactions + features
2. Partition by date
3. Write as Parquet format
4. Checkpoint for fault tolerance

Storage Path:
s3a://hsbc-data/
  ├── stream-archive/
  │   └── transactions/
  │       ├── date=2024-01-15/
  │       │   ├── part-00000.parquet
  │       │   └── part-00001.parquet
  │       └── date=2024-01-16/
  └── checkpoints/
      └── archive/

Configuration:
• Trigger: Every 10 seconds
• Format: Parquet (compressed)
• Partitioning: By date column
• Mode: Append

Data Retention: Permanent (for retraining)


STREAM B: INFERENCE (Real-time Detection)
═════════════════════════════════════════
🤖 ML Model Prediction

Purpose: Phát hiện gian lận real-time

Process:
┌────────────────────────────────────┐
│ 1. Load Model                      │
│    Path: /opt/data/models/         │
│          fraud_xgb_21features      │
│    Type: XGBoost Pipeline          │
│    Features: 21 inputs             │
├────────────────────────────────────┤
│ 2. Batch Processing                │
│    • Trigger: Every 2 seconds      │
│    • Process micro-batch           │
│    • Apply model.transform()       │
├────────────────────────────────────┤
│ 3. Prediction                      │
│    Model Output:                   │
│    • prediction: 0 (normal)        │
│                  1 (FRAUD)         │
│    • probability: [p0, p1]         │
├────────────────────────────────────┤
│ 4. Filter Fraud Alerts             │
│    • Keep only prediction = 1      │
│    • Add detected_at timestamp     │
│    • Prepare for Cassandra         │
└────────────────────────────────────┘

Logging: Chi tiết mỗi fraud transaction
• Transaction ID, Time, Amount
• Merchant, Category
• Customer name, Location
• Card number (masked)

                    ↓

GIAI ĐOẠN 5: CASSANDRA (Fraud Alerts Storage)
═════════════════════════════════════════════
🗄️ Cassandra Database

Keyspace: hsbc
Table: fraud_alerts

**QUAN TRỌNG**: Chỉ lưu FRAUD DETECTED (prediction=1)
                KHÔNG lưu tất cả transactions

Insert Process:
1. Receive fraud alerts from Spark
2. Write to Cassandra (append mode)
3. Primary key: transaction_id
4. Add detected_at timestamp

Storage Schema:
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

Query Pattern: 
• Real-time dashboard queries
• API endpoints
• Fraud analysis

Data Volume: ~0.6-10% of input (chỉ fraud)

                    ↓

GIAI ĐOẠN 6: API & DASHBOARD (Visualization)
════════════════════════════════════════════
🌐 FastAPI + 📊 Streamlit

API (FastAPI):
┌─────────────────────────────────┐
│ Endpoints:                      │
│ • GET /fraud/alerts             │
│ • GET /fraud/stats              │
│ • GET /fraud/recent             │
├─────────────────────────────────┤
│ Cassandra Connection:           │
│ • Host: cassandra:9042          │
│ • Keyspace: hsbc                │
│ • Query: SELECT * FROM alerts   │
└─────────────────────────────────┘

Dashboard (Streamlit):
┌─────────────────────────────────┐
│ Real-time Charts:               │
│ • Fraud count over time         │
│ • Amount distribution           │
│ • Category breakdown            │
│ • Geographic heatmap            │
├─────────────────────────────────┤
│ Data Source: API REST calls     │
│ Refresh: Every 3 seconds        │
│ Port: http://localhost:8501     │
└─────────────────────────────────┘
```

---

## 2. CHI TIẾT TỪNG GIAI ĐOẠN

### GIAI ĐOẠN 2.1: PRODUCER - Đọc và Chuyển Đổi Dữ Liệu

#### A. Load CSV File

```python
# File: producer/producer.py

def load_data(self):
    """
    Đọc CSV với pandas
    Input: /data/raw/df_test_hdfs.csv
    Output: pandas DataFrame
    """
    
    # 1. Define data types để tránh overflow
    dtype_spec = {
        'cc_num': str,        # Card number as string (16 digits)
        'zip': str,           # ZIP code with leading zeros
        'is_fraud': int,      # Target: 0 or 1
        'city_pop': int       # City population
    }
    
    # 2. Read CSV
    self.df = pd.read_csv(
        '/data/raw/df_test_hdfs.csv',
        dtype=dtype_spec,
        parse_dates=['trans_date_trans_time']  # Parse datetime
    )
    
    # 3. Data preprocessing
    self.df['hour_of_day'] = self.df['trans_date_trans_time'].dt.hour
    
    # 4. Shuffle for random replay
    self.df = self.df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Statistics
    total = len(self.df)                    # ~100K rows
    fraud_count = self.df['is_fraud'].sum() # ~10K fraud
    fraud_rate = fraud_count / total        # ~10%
```

**Dữ liệu đầu vào (CSV row example):**
```csv
trans_num,trans_date_trans_time,cc_num,merchant,category,amt,first,last,gender,street,city,state,zip,lat,long,city_pop,job,dob,trans_num,unix_time,merch_lat,merch_long,is_fraud
abc123,2024-01-15 10:30:45,4532123456789012,Target,grocery_pos,89.50,John,Smith,M,123 Main St,Springfield,IL,62701,39.7817,-89.6501,116250,Engineer,1985-03-15,123456789,1705315845,39.7850,-89.6450,0
```

**Dữ liệu đầu ra (JSON object):**
```json
{
  "transaction_id": "abc123",
  "transaction_time": "2024-01-15T10:30:45",
  "amount": 89.50,
  "unix_time": 1705315845,
  "hour_of_day": 10,
  "cc_num": "4532123456789012",
  "first": "John",
  "last": "Smith",
  "gender": "M",
  "dob": "1985-03-15",
  "job": "Engineer",
  "street": "123 Main St",
  "city": "Springfield",
  "state": "IL",
  "zip": "62701",
  "lat": 39.7817,
  "long": -89.6501,
  "city_pop": 116250,
  "merchant": "Target",
  "category": "grocery_pos",
  "merch_lat": 39.7850,
  "merch_long": -89.6450,
  "is_fraud": 0
}
```

#### B. Send to Kafka

```python
def send_transaction(self, transaction):
    """
    Gửi JSON lên Kafka
    """
    self.producer.send(
        topic='transactions_hsbc',
        value=transaction,                          # JSON object
        key=transaction['transaction_id'].encode() # Partition key
    )
```

**Kafka Message Structure:**
```
Key: "abc123" (transaction_id)
Value: {JSON object 23 fields}
Topic: transactions_hsbc
Partition: Auto (based on key hash)
Timestamp: Kafka ingestion time
```

**Rate Control:**
- Config: `TRANSACTION_RATE = 12` (transactions/second)
- Sleep: `time.sleep(1 / 12)` = 0.083 seconds between sends
- Daily volume: 12 * 60 * 60 * 24 = 1,036,800 transactions/day

---

### GIAI ĐOẠN 4.1: SPARK STREAMING - Feature Engineering Chi Tiết

#### Input: Raw Transaction (23 fields)

```python
# Original columns từ Kafka
raw_transaction = {
    "transaction_id": "abc123",
    "transaction_time": "2024-01-15T10:30:45",
    "amount": 89.50,
    "unix_time": 1705315845,
    "hour_of_day": 10,
    "cc_num": "4532123456789012",
    "first": "John",
    "last": "Smith",
    "gender": "M",
    "dob": "1985-03-15",
    "job": "Engineer",
    "street": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip": "62701",
    "lat": 39.7817,
    "long": -89.6501,
    "city_pop": 116250,
    "merchant": "Target",
    "category": "grocery_pos",
    "merch_lat": 39.7850,
    "merch_long": -89.6450,
    "is_fraud": 0
}
```

#### Feature Engineering Process (feature_engineering.py)

```python
class FeatureEngineer:
    def engineer_features(self, df):
        """
        Transform 23 raw columns → 44 columns (23 original + 21 features)
        """
        
        # ═══════════════════════════════════════════════════
        # 1. NUMERIC FEATURES (4 features)
        # ═══════════════════════════════════════════════════
        
        # F1: amount_log - Log transformation for skewed distribution
        df = df.withColumn('amount_log', log1p(col('amount')))
        # Example: amount=89.50 → amount_log=4.50
        
        # F2: is_high_value - Flag for high-value transactions
        df = df.withColumn('is_high_value', 
                          when(col('amount') > 100, 1).otherwise(0))
        # Example: 89.50 < 100 → is_high_value=0
        
        # F3: is_extreme_value - Flag for very high amounts
        df = df.withColumn('is_extreme_value', 
                          when(col('amount') > 500, 1).otherwise(0))
        # Example: 89.50 < 500 → is_extreme_value=0
        
        # ═══════════════════════════════════════════════════
        # 2. DEMOGRAPHIC FEATURES (2 features)
        # ═══════════════════════════════════════════════════
        
        # F4: age - Calculate from date of birth
        df = df.withColumn('age', 
            floor(months_between(current_date(), to_date(col('dob'))) / 12))
        # Example: dob="1985-03-15" → age=39 (in 2024)
        
        # F5: gender_encoded - Numerical encoding
        df = df.withColumn('gender_encoded',
            when(lower(col('gender')) == 'm', 1)
            .when(lower(col('gender')) == 'f', 0)
            .otherwise(-1))
        # Example: gender="M" → gender_encoded=1
        
        # ═══════════════════════════════════════════════════
        # 3. TEMPORAL FEATURES (2 features)
        # ═══════════════════════════════════════════════════
        
        # F6: hour_of_day - Already provided, validate
        df = df.withColumn('hour_of_day', hour(col('transaction_time')))
        # Example: "10:30:45" → hour_of_day=10
        
        # F7: is_weekend - Weekend indicator
        df = df.withColumn('is_weekend', 
            when(dayofweek(col('transaction_time')).isin([1, 7]), 1)
            .otherwise(0))
        # Example: Monday → is_weekend=0
        
        # ═══════════════════════════════════════════════════
        # 4. GEOGRAPHIC FEATURES (2 features)
        # ═══════════════════════════════════════════════════
        
        # F8: distance_customer_merchant - Haversine formula
        df = df.withColumn('distance_customer_merchant',
            2 * 6371 * asin(sqrt(
                pow(sin(radians(col('merch_lat') - col('lat')) / 2), 2) +
                cos(radians(col('lat'))) * 
                cos(radians(col('merch_lat'))) * 
                pow(sin(radians(col('merch_long') - col('long')) / 2), 2)
            )))
        # Example: Customer(39.7817,-89.6501) → Merchant(39.7850,-89.6450)
        #          distance_customer_merchant = 0.58 km
        
        # F9: is_out_of_state - Cross-state transaction
        df = df.withColumn('is_out_of_state', lit(0))
        # Currently disabled (merchant_state not available)
        
        # ═══════════════════════════════════════════════════
        # 5. CATEGORY ONE-HOT ENCODING (13 features)
        # ═══════════════════════════════════════════════════
        
        categories = [
            'grocery_pos',      # F10
            'shopping_net',     # F11
            'misc_net',         # F12
            'gas_transport',    # F13
            'shopping_pos',     # F14
            'food_dining',      # F15
            'personal_care',    # F16
            'health_fitness',   # F17
            'entertainment',    # F18
            'utilities',        # F19
            'travel',           # F20
            'electronics',      # F21
            'others'            # F22
        ]
        
        for cat in categories:
            df = df.withColumn(f'cat_{cat}',
                when(lower(col('category')) == cat, 1).otherwise(0))
        
        # Example: category="grocery_pos"
        #   → cat_grocery_pos=1, all other cat_*=0
        
        # ═══════════════════════════════════════════════════
        # 6. ADDITIONAL CRAFTED FEATURE (1 feature)
        # ═══════════════════════════════════════════════════
        
        # F23: amt_to_pop_ratio - Amount relative to city size
        df = df.withColumn('amt_to_pop_ratio',
            when((col('city_pop') > 0), 
                 col('amount') / col('city_pop'))
            .otherwise(0.0))
        # Example: amount=89.50, city_pop=116,250
        #          amt_to_pop_ratio = 0.00077
        
        return df
```

#### Output: Engineered Features (44 columns total)

```python
engineered_transaction = {
    # ──────────────────────────────────────────
    # ORIGINAL 23 FIELDS (kept)
    # ──────────────────────────────────────────
    "transaction_id": "abc123",
    "transaction_time": "2024-01-15T10:30:45",
    "amount": 89.50,
    "unix_time": 1705315845,
    "hour_of_day": 10,
    "cc_num": "4532123456789012",
    "first": "John",
    "last": "Smith",
    "gender": "M",
    "dob": "1985-03-15",
    "job": "Engineer",
    "street": "123 Main St",
    "city": "Springfield",
    "state": "IL",
    "zip": "62701",
    "lat": 39.7817,
    "long": -89.6501,
    "city_pop": 116250,
    "merchant": "Target",
    "category": "grocery_pos",
    "merch_lat": 39.7850,
    "merch_long": -89.6450,
    "is_fraud": 0,
    
    # ──────────────────────────────────────────
    # ENGINEERED 21 FEATURES (new)
    # ──────────────────────────────────────────
    
    # Numeric (4)
    "amount_log": 4.50,
    "is_high_value": 0,
    "is_extreme_value": 0,
    "amt_to_pop_ratio": 0.00077,
    
    # Demographic (2)
    "age": 39,
    "gender_encoded": 1,
    
    # Temporal (2)
    "is_weekend": 0,
    
    # Geographic (2)
    "distance_customer_merchant": 0.58,
    "is_out_of_state": 0,
    
    # Category one-hot (13)
    "cat_grocery_pos": 1,
    "cat_shopping_net": 0,
    "cat_misc_net": 0,
    "cat_gas_transport": 0,
    "cat_shopping_pos": 0,
    "cat_food_dining": 0,
    "cat_personal_care": 0,
    "cat_health_fitness": 0,
    "cat_entertainment": 0,
    "cat_utilities": 0,
    "cat_travel": 0,
    "cat_electronics": 0,
    "cat_others": 0
}
```

**Total Columns**: 23 original + 21 engineered = 44 columns

---

### GIAI ĐOẠN 4.2: MODEL INFERENCE - Dự Đoán Gian Lận

#### A. Load Model

```python
# Model: /opt/data/models/fraud_xgb_21features

model = PipelineModel.load('/opt/data/models/fraud_xgb_21features')

# Model Pipeline:
# 1. StringIndexer: is_fraud → label
# 2. VectorAssembler: 21 features → features vector
# 3. XGBoost Classifier: features → prediction, probability
```

#### B. Feature Vector Preparation

```python
# Select 21 features for model input
feature_cols = [
    'amount', 'age', 'city_pop', 'hour_of_day', 'is_weekend',
    'amount_log', 'is_high_value', 'is_extreme_value',
    'distance_customer_merchant', 'is_out_of_state',
    'amt_to_pop_ratio', 'gender_encoded',
    'cat_grocery_pos', 'cat_shopping_net', 'cat_misc_net',
    'cat_gas_transport', 'cat_shopping_pos', 'cat_food_dining',
    'cat_personal_care', 'cat_health_fitness', 'cat_entertainment'
]

# VectorAssembler combines into single vector
features = [89.50, 39, 116250, 10, 0, 4.50, 0, 0, 0.58, 0, 
            0.00077, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0]

# Dense vector format: [21 values]
```

#### C. XGBoost Prediction

```python
# Model.transform() applies prediction
predictions = model.transform(batch_df)

# Output columns:
# - prediction: 0 (normal) or 1 (fraud)
# - probability: [p_normal, p_fraud]
```

**Example Prediction Output:**
```python
{
    # Original + Features (44 cols)
    "transaction_id": "abc123",
    "amount": 89.50,
    ... (all previous fields),
    
    # Model Output (3 new cols)
    "features": DenseVector([89.50, 39, 116250, ...]),
    "probability": [0.92, 0.08],  # [normal, fraud]
    "prediction": 0.0              # 0=normal, 1=fraud
}
```

#### D. Filter Fraud Alerts

```python
# Keep only FRAUD predictions
fraud_alerts = predictions.filter(col("prediction") == 1)

# Select columns for Cassandra
fraud_alerts = fraud_alerts.select(
    col("transaction_id"),
    col("transaction_time"),
    col("amount"),
    col("merchant"),
    col("category"),
    col("cc_num"),
    col("first"),
    col("last"),
    col("gender"),
    col("job"),
    col("state"),
    col("city"),
    col("zip"),
    col("prediction").alias("is_fraud"),  # Rename: 1
    current_timestamp().alias("detected_at")
)
```

**Example Fraud Alert:**
```python
{
    "transaction_id": "xyz789",
    "transaction_time": "2024-01-15T23:45:30",
    "amount": 987.50,
    "merchant": "Online Store XYZ",
    "category": "shopping_net",
    "cc_num": "4532987654321098",
    "first": "Jane",
    "last": "Doe",
    "gender": "F",
    "job": "Manager",
    "state": "CA",
    "city": "Los Angeles",
    "zip": "90001",
    "is_fraud": 1.0,
    "detected_at": "2024-01-15T23:45:32"
}
```

---

### GIAI ĐOẠN 5.1: CASSANDRA - Chi Tiết Lưu Trữ

#### Table Schema

```cql
CREATE TABLE hsbc.fraud_alerts (
    -- Primary Key
    transaction_id text PRIMARY KEY,
    
    -- Transaction Info
    transaction_time timestamp,
    amount double,
    merchant text,
    category text,
    
    -- Customer Info
    cc_num text,
    first text,
    last text,
    gender text,
    job text,
    
    -- Location
    state text,
    city text,
    zip text,
    
    -- Detection Info
    is_fraud double,      -- Always 1.0 (fraud detected)
    detected_at timestamp -- When system detected
);
```

#### Insert Process

```python
# Spark writes directly to Cassandra
fraud_alerts.write \
    .format("org.apache.spark.sql.cassandra") \
    .mode("append") \
    .options(table="fraud_alerts", keyspace="hsbc") \
    .save()
```

**Data Flow:**
```
Spark DataFrame (fraud_alerts)
         ↓
Cassandra Connector
         ↓
hsbc.fraud_alerts table
         ↓
INSERT INTO hsbc.fraud_alerts 
VALUES ('xyz789', '2024-01-15 23:45:30', 987.50, ...)
```

#### Storage Characteristics

**Quan trọng - Hiểu đúng về Cassandra:**

```
Producer gửi:     100,000 transactions
                      ↓
Spark xử lý:      100,000 transactions
                      ↓
Model dự đoán:     10,000 fraud (10%)
                      ↓
Cassandra lưu:     10,000 fraud ONLY ✓

KHÔNG LƯU 90,000 normal transactions!
```

**Tỷ lệ:**
- Input: 100% transactions
- Cassandra: ~0.6-10% (chỉ fraud detected)
- Compression ratio: 10-167x reduction

---

## 3. DỮ LIỆU TRAINING

### 3.1 Dataset Training (fraudTrain.csv)

**File:** `/data/raw/fraudTrain.csv`

**Thông số:**
```
Rows:        1,296,675 transactions
Fraud:       7,506 (0.58%)
Normal:      1,289,169 (99.42%)
Columns:     23
Size:        ~300 MB
Format:      CSV with header
```

**Schema (23 columns):**
```python
fraudTrain.csv columns:
[
    'trans_num',              # Transaction ID
    'trans_date_trans_time',  # DateTime: YYYY-MM-DD HH:MM:SS
    'cc_num',                 # Credit card number (16 digits)
    'merchant',               # Merchant name
    'category',               # Transaction category
    'amt',                    # Amount ($)
    'first',                  # First name
    'last',                   # Last name
    'gender',                 # M/F
    'street',                 # Street address
    'city',                   # City
    'state',                  # State (2-letter code)
    'zip',                    # ZIP code (5 digits)
    'lat',                    # Customer latitude
    'long',                   # Customer longitude
    'city_pop',               # City population
    'job',                    # Job title
    'dob',                    # Date of birth
    'trans_num',              # (duplicate)
    'unix_time',              # Unix timestamp
    'merch_lat',              # Merchant latitude
    'merch_long',             # Merchant longitude
    'is_fraud'                # Target: 0 or 1
]
```

### 3.2 Training Process (model_retraining_xgb.py)

```
┌────────────────────────────────────────────────────────────┐
│              MODEL TRAINING WORKFLOW                       │
└────────────────────────────────────────────────────────────┘

Step 1: LOAD DATA
─────────────────
Input:  /opt/data/raw/fraudTrain.csv
Method: spark.read.csv()
Result: 1,296,675 rows × 23 columns

Step 2: FEATURE ENGINEERING
────────────────────────────
Apply: feature_engineering.engineer_features()
Input:  23 raw columns
Output: 44 columns (23 + 21 features)

Step 3: FEATURE SELECTION
──────────────────────────
Select 21 features for model:
• amount, age, city_pop, hour_of_day, is_weekend
• amount_log, is_high_value, is_extreme_value
• distance_customer_merchant, is_out_of_state
• amt_to_pop_ratio, gender_encoded
• cat_grocery_pos, cat_shopping_net, cat_misc_net
• cat_gas_transport, cat_shopping_pos, cat_food_dining
• cat_personal_care, cat_health_fitness, cat_entertainment

Step 4: PREPARE LABEL
──────────────────────
StringIndexer: is_fraud (0/1) → label (0.0/1.0)

Step 5: VECTOR ASSEMBLY
────────────────────────
VectorAssembler: 21 features → Dense vector [21 values]

Step 6: TRAIN/TEST SPLIT
─────────────────────────
Training set: 80% = 1,037,340 rows
Test set:     20% =   259,335 rows

Step 7: XGBOOST TRAINING
─────────────────────────
Algorithm: XGBoost Classifier
Hyperparameters:
  • max_depth: 6
  • learning_rate: 0.3
  • n_estimators: 100 trees
  • subsample: 0.8
  • colsample_bytree: 0.8
  • eval_metric: AUC

Training time: ~6-10 minutes
Iterations: 100 boosting rounds

Step 8: EVALUATION
──────────────────
Metric: AUC-ROC
Test set predictions:
  • True Positives
  • False Positives
  • True Negatives
  • False Negatives

Result: AUC-ROC = 0.9964 (99.64%)

Step 9: SAVE MODEL
──────────────────
Path: /opt/data/models/fraud_xgb_21features/
Format: PipelineModel (Spark ML)
Components:
  ├── metadata/
  ├── stages/
  │   ├── 0_StringIndexer/
  │   ├── 1_VectorAssembler/
  │   └── 2_XGBoostClassifier/
  └── _SUCCESS
```

### 3.3 Model Performance

**Confusion Matrix (Example):**
```
                 Predicted
                Fraud   Normal
Actual Fraud    [ TP ]  [ FN ]
       Normal   [ FP ]  [ TN ]

TP (True Positive):  ~7,400 (correctly detected fraud)
FN (False Negative): ~100   (missed fraud)
FP (False Positive): ~1,000 (false alarms)
TN (True Negative):  ~250,835 (correctly normal)

Precision: TP / (TP + FP) = 7,400 / 8,400 = 88%
Recall:    TP / (TP + FN) = 7,400 / 7,500 = 99%
F1-Score:  2 * (P * R) / (P + R) = 93%
AUC-ROC:   0.9964 (excellent)
```

---

## 4. DỮ LIỆU STREAMING

### 4.1 Production Dataset (df_test_hdfs.csv)

**File:** `/data/raw/df_test_hdfs.csv`

**Characteristics:**
```
Purpose:     Production replay for testing
Rows:        ~100,000 transactions
Fraud rate:  ~10% (higher than training for demo)
Format:      Same 23 columns as fraudTrain
Usage:       Producer reads and streams to Kafka
```

**Why different fraud rate?**
- Training: 0.58% (realistic fraud rate)
- Testing: 10% (easier to demo and monitor)

### 4.2 Streaming Data Volume

**Daily Throughput (với rate=12 tx/sec):**
```
Transactions per second:  12
Transactions per minute:  720
Transactions per hour:    43,200
Transactions per day:     1,036,800

Fraud detected (10%):     103,680 per day
Cassandra inserts:        103,680 per day
MinIO archive:            1,036,800 per day (all)
```

**Data Size Estimation:**
```
JSON message size:        ~1 KB per transaction
Kafka throughput:         12 KB/sec = 720 KB/min
Daily Kafka volume:       ~1 GB/day

Parquet (MinIO):          Compressed ~300 MB/day
Cassandra (fraud only):   ~100 MB/day
```

### 4.3 Data Retention

```
┌─────────────────┬──────────────┬─────────────────────┐
│ Component       │ Retention    │ Purpose             │
├─────────────────┼──────────────┼─────────────────────┤
│ Kafka           │ 7 days       │ Message queue       │
│ MinIO Archive   │ Permanent    │ Model retraining    │
│ Cassandra       │ Permanent    │ Fraud analysis      │
│ Dashboard       │ Real-time    │ Visualization       │
└─────────────────┴──────────────┴─────────────────────┘
```

---

## 5. SCHEMA CHI TIẾT

### 5.1 Complete Data Schema

```python
COMPLETE_SCHEMA = {
    # ═══════════════════════════════════════
    # SECTION 1: IDENTIFIERS (2 fields)
    # ═══════════════════════════════════════
    "transaction_id": {
        "type": "string",
        "format": "UUID or alphanumeric",
        "example": "abc123def456",
        "nullable": False,
        "source": "trans_num column"
    },
    
    # ═══════════════════════════════════════
    # SECTION 2: TRANSACTION DETAILS (5 fields)
    # ═══════════════════════════════════════
    "transaction_time": {
        "type": "timestamp",
        "format": "ISO 8601 (YYYY-MM-DDTHH:MM:SS)",
        "example": "2024-01-15T10:30:45",
        "nullable": False,
        "source": "trans_date_trans_time"
    },
    "amount": {
        "type": "double",
        "range": "[0.01, 10000.00]",
        "unit": "USD",
        "example": 89.50,
        "nullable": False,
        "source": "amt column"
    },
    "unix_time": {
        "type": "long",
        "format": "Unix epoch seconds",
        "example": 1705315845,
        "nullable": False,
        "source": "unix_time column"
    },
    "hour_of_day": {
        "type": "integer",
        "range": "[0, 23]",
        "example": 10,
        "nullable": False,
        "source": "Extracted from transaction_time"
    },
    
    # ═══════════════════════════════════════
    # SECTION 3: CARD & CUSTOMER (6 fields)
    # ═══════════════════════════════════════
    "cc_num": {
        "type": "string",
        "format": "16-digit credit card number",
        "example": "4532123456789012",
        "nullable": False,
        "masked": "****9012 (in display)",
        "source": "cc_num column"
    },
    "first": {
        "type": "string",
        "example": "John",
        "nullable": True,
        "source": "first column"
    },
    "last": {
        "type": "string",
        "example": "Smith",
        "nullable": True,
        "source": "last column"
    },
    "gender": {
        "type": "string",
        "values": ["M", "F"],
        "example": "M",
        "nullable": True,
        "source": "gender column"
    },
    "dob": {
        "type": "string",
        "format": "YYYY-MM-DD",
        "example": "1985-03-15",
        "nullable": True,
        "source": "dob column"
    },
    "job": {
        "type": "string",
        "example": "Engineer",
        "nullable": True,
        "source": "job column"
    },
    
    # ═══════════════════════════════════════
    # SECTION 4: CUSTOMER LOCATION (7 fields)
    # ═══════════════════════════════════════
    "street": {
        "type": "string",
        "example": "123 Main St",
        "nullable": True,
        "source": "street column"
    },
    "city": {
        "type": "string",
        "example": "Springfield",
        "nullable": True,
        "source": "city column"
    },
    "state": {
        "type": "string",
        "format": "2-letter code",
        "example": "IL",
        "nullable": True,
        "source": "state column"
    },
    "zip": {
        "type": "string",
        "format": "5-digit ZIP code",
        "example": "62701",
        "nullable": True,
        "note": "Leading zeros preserved",
        "source": "zip column"
    },
    "lat": {
        "type": "double",
        "range": "[-90, 90]",
        "example": 39.7817,
        "unit": "degrees",
        "nullable": True,
        "source": "lat column"
    },
    "long": {
        "type": "double",
        "range": "[-180, 180]",
        "example": -89.6501,
        "unit": "degrees",
        "nullable": True,
        "source": "long column"
    },
    "city_pop": {
        "type": "integer",
        "example": 116250,
        "nullable": True,
        "source": "city_pop column"
    },
    
    # ═══════════════════════════════════════
    # SECTION 5: MERCHANT (4 fields)
    # ═══════════════════════════════════════
    "merchant": {
        "type": "string",
        "example": "Target",
        "nullable": False,
        "source": "merchant column"
    },
    "category": {
        "type": "string",
        "values": [
            "grocery_pos", "shopping_net", "misc_net",
            "gas_transport", "shopping_pos", "food_dining",
            "personal_care", "health_fitness", "entertainment",
            "utilities", "travel", "electronics", "others"
        ],
        "example": "grocery_pos",
        "nullable": False,
        "source": "category column"
    },
    "merch_lat": {
        "type": "double",
        "range": "[-90, 90]",
        "example": 39.7850,
        "nullable": True,
        "source": "merch_lat column"
    },
    "merch_long": {
        "type": "double",
        "range": "[-180, 180]",
        "example": -89.6450,
        "nullable": True,
        "source": "merch_long column"
    },
    
    # ═══════════════════════════════════════
    # SECTION 6: TARGET (1 field)
    # ═══════════════════════════════════════
    "is_fraud": {
        "type": "integer",
        "values": [0, 1],
        "example": 0,
        "nullable": True,
        "note": "Ground truth label",
        "source": "is_fraud column"
    },
    
    # ═══════════════════════════════════════
    # SECTION 7: ENGINEERED FEATURES (21 fields)
    # ═══════════════════════════════════════
    
    # Numeric Features (4)
    "amount_log": {
        "type": "double",
        "formula": "log1p(amount)",
        "example": 4.50,
        "purpose": "Handle skewed distribution"
    },
    "is_high_value": {
        "type": "integer",
        "values": [0, 1],
        "formula": "amount > 100",
        "example": 0,
        "purpose": "Flag high-value transactions"
    },
    "is_extreme_value": {
        "type": "integer",
        "values": [0, 1],
        "formula": "amount > 500",
        "example": 0,
        "purpose": "Flag very high amounts"
    },
    "amt_to_pop_ratio": {
        "type": "double",
        "formula": "amount / city_pop",
        "example": 0.00077,
        "purpose": "Amount relative to city size"
    },
    
    # Demographic Features (2)
    "age": {
        "type": "integer",
        "formula": "floor(months_between(current_date, dob) / 12)",
        "example": 39,
        "purpose": "Customer age"
    },
    "gender_encoded": {
        "type": "integer",
        "values": [-1, 0, 1],
        "mapping": {"M": 1, "F": 0, "Other": -1},
        "example": 1,
        "purpose": "Numerical gender encoding"
    },
    
    # Temporal Features (2)
    "is_weekend": {
        "type": "integer",
        "values": [0, 1],
        "formula": "dayofweek in [1, 7]",
        "example": 0,
        "purpose": "Weekend indicator"
    },
    
    # Geographic Features (2)
    "distance_customer_merchant": {
        "type": "double",
        "unit": "kilometers",
        "formula": "haversine(customer_lat/long, merchant_lat/long)",
        "example": 0.58,
        "purpose": "Distance between customer and merchant"
    },
    "is_out_of_state": {
        "type": "integer",
        "values": [0, 1],
        "example": 0,
        "note": "Currently disabled",
        "purpose": "Cross-state transaction flag"
    },
    
    # Category One-Hot (13 features)
    "cat_grocery_pos": {"type": "integer", "values": [0, 1]},
    "cat_shopping_net": {"type": "integer", "values": [0, 1]},
    "cat_misc_net": {"type": "integer", "values": [0, 1]},
    "cat_gas_transport": {"type": "integer", "values": [0, 1]},
    "cat_shopping_pos": {"type": "integer", "values": [0, 1]},
    "cat_food_dining": {"type": "integer", "values": [0, 1]},
    "cat_personal_care": {"type": "integer", "values": [0, 1]},
    "cat_health_fitness": {"type": "integer", "values": [0, 1]},
    "cat_entertainment": {"type": "integer", "values": [0, 1]},
    "cat_utilities": {"type": "integer", "values": [0, 1]},
    "cat_travel": {"type": "integer", "values": [0, 1]},
    "cat_electronics": {"type": "integer", "values": [0, 1]},
    "cat_others": {"type": "integer", "values": [0, 1]}
}

# Total: 23 original + 21 engineered = 44 columns
```

### 5.2 Data Type Mapping

```
CSV (pandas)  →  Kafka (JSON)  →  Spark  →  Cassandra
─────────────────────────────────────────────────────
str           →  string        →  string →  text
datetime64    →  string (ISO)  →  timestamp → timestamp
int64         →  number        →  long   →  bigint
float64       →  number        →  double →  double
object        →  string        →  string →  text
```

---

## 📊 TÓM TẮT LUỒNG DỮ LIỆU

```
┌────────────────────────────────────────────────────────────┐
│                    DATA FLOW SUMMARY                       │
└────────────────────────────────────────────────────────────┘

1. SOURCE: CSV (1.3M rows, 23 cols, 0.58% fraud)
              ↓
2. PRODUCER: Read → JSON → Kafka (12 tx/sec)
              ↓
3. KAFKA: Queue (transactions_hsbc topic)
              ↓
4. SPARK STREAMING:
   - Parse JSON (23 cols)
   - Feature Engineering (+21 features → 44 cols total)
   - Split into 2 streams:
     
     Branch A: ARCHIVE          Branch B: INFERENCE
     → MinIO (all data)         → XGBoost Model
       Parquet format             → Predict (21 features)
       Partitioned by date        → Filter (prediction=1)
       For retraining             → Cassandra (fraud only)
              ↓                            ↓
5. STORAGE:                      6. ALERTS:
   MinIO: 100% data                Cassandra: ~0.6-10% fraud
   Permanent                        Permanent
              ↓                            ↓
7. CONSUMPTION:                  8. VISUALIZATION:
   Batch retraining                FastAPI → Streamlit
   Analytics                       Real-time dashboard
   Audit trail                     Alerts monitoring

KEY METRICS:
────────────
• Throughput: 12 transactions/second
• Latency: <2 seconds (ingestion → detection)
• Fraud rate: 0.58% (training), ~10% (production demo)
• Features: 21 engineered features
• Model: XGBoost (100 trees, AUC=0.9964)
• Storage: 100% MinIO, ~10% Cassandra
• Retention: Kafka 7d, MinIO/Cassandra permanent
```

---

## 📝 LƯU Ý QUAN TRỌNG

### ✅ Các Điểm Cần Nhớ

1. **Cassandra chỉ lưu FRAUD detected**, không phải tất cả transactions
2. **Feature engineering** tạo 21 features từ 23 columns gốc
3. **Model sử dụng 21 features**, không phải tất cả 44 columns
4. **Kappa architecture**: Một luồng streaming duy nhất, phân nhánh sau khi feature engineering
5. **Rate control** ở Producer: 12 tx/sec (có thể config)
6. **Kafka offset**: earliest (đọc từ đầu) hoặc latest (chỉ đọc mới)

### 🎯 Performance Targets

- **Latency**: <2 giây từ Producer → Cassandra
- **Throughput**: 12 tx/sec sustained
- **Model AUC**: >0.99
- **Fraud detection rate**: ~99% recall
- **False positive rate**: <1%

---

**Tài liệu này mô tả chi tiết 100% luồng dữ liệu trong hệ thống HSBC Fraud Detection của bạn.**
