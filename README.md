# 🏦 HSBC Fraud Detection System

Real-time fraud detection system using Apache Spark, Kafka, Cassandra, and Machine Learning.

## 🚀 Quick Start

```powershell
# 1. Start all services
docker compose up -d

# 2. Wait for services to be ready (~2 minutes)
Start-Sleep -Seconds 120

# 3. Setup Cassandra database
docker exec -it cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS hsbc WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"

docker exec -it cassandra cqlsh -e "CREATE TABLE IF NOT EXISTS hsbc.fraud_alerts (
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

# 4. Train ML model
docker cp streaming-pipeline/model_retraining.py spark-master:/opt/spark-apps/
docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --deploy-mode client /opt/spark-apps/model_retraining.py

# 5. Start fraud detection streaming
docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  /opt/spark-apps/unified_streaming.py

# 6. Access Dashboard
# Open: http://localhost:8501
```

## 📊 System Architecture

```
CSV Data → Producer → Kafka → Spark Streaming → ML Model → Cassandra → API → Dashboard
                                      ↓
                                   MinIO (S3 Archive)
```

## 🛠️ Tech Stack

- **Stream Processing**: Apache Spark 3.5.0
- **Message Broker**: Apache Kafka 7.4.0
- **Database**: Apache Cassandra 4.1
- **Object Storage**: MinIO
- **ML**: PySpark MLlib (RandomForest)
- **API**: FastAPI
- **Dashboard**: Streamlit
- **Orchestration**: Docker Compose

## 📦 Services & Ports

| Service | Port | URL |
|---------|------|-----|
| Kafka | 9092 | - |
| MinIO Console | 9001 | http://localhost:9001 |
| Cassandra | 9042 | - |
| Spark Master UI | 8080 | http://localhost:8080 |
| Spark Application UI | 4040 | http://localhost:4040 |
| API | 8000 | http://localhost:8000 |
| API Docs | 8000/docs | http://localhost:8000/docs |
| Dashboard | 8501 | http://localhost:8501 |

## 🎯 Features

### Real-time Fraud Detection
- Processes 2-5 transactions/second
- ML-based fraud prediction using RandomForest
- 7 engineered features for optimal accuracy
- Real-time alerts stored in Cassandra

### Data Pipeline
- Kafka streaming from CSV data source
- Spark Structured Streaming for processing
- MinIO S3-compatible archive storage
- Cassandra for fraud alerts persistence

### Visualization Dashboard
- Real-time metrics (total alerts, amount, average)
- Filterable fraud alerts table
- Analytics charts (by category, state, amount distribution)
- Auto-refresh capability (5s interval)

### REST API
- `/fraud/alerts` - Get fraud alerts with filters
- `/fraud/stats` - Aggregate statistics
- `/fraud/count` - Total fraud count
- Interactive Swagger documentation

## 📖 Documentation

- **[Complete System Guide](SYSTEM_GUIDE.md)** - Detailed operations manual
- **[Quick Start](QUICKSTART.md)** - Get started in 5 minutes
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when running)

## 🔍 Health Check

```powershell
# Check all services
docker compose ps

# Check API
curl http://localhost:8000/

# Check fraud count
curl http://localhost:8000/fraud/count

# Check Cassandra
docker exec -it cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"
```

## 🛑 Stop System

```powershell
# Stop all services (keep data)
docker compose stop

# Remove containers (keep volumes/data)
docker compose down

# Complete cleanup (⚠️ deletes all data)
docker compose down -v
```

## 📁 Project Structure

```
hsbc-fraud-detection-new/
├── docker-compose.yml          # Container orchestration
├── data/
│   ├── raw/
│   │   ├── fraudTrain.csv      # Training data
│   │   └── fraudTest.csv       # Test data
│   ├── processed/              # Processed features
│   └── models/
│       └── fraud_rf_lean/      # Trained ML model
├── producer/
│   ├── producer.py             # Transaction generator
│   ├── config.py               # Producer configuration
│   ├── requirements.txt
│   └── Dockerfile
├── streaming-pipeline/
│   ├── unified_streaming.py    # Main streaming job
│   ├── feature_engineering.py  # Feature transformations
│   └── model_retraining.py     # Model training script
├── api/
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Cassandra connection
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/
│   ├── app.py                  # Streamlit dashboard
│   ├── requirements.txt
│   └── Dockerfile
└── scripts/
    ├── setup_cassandra.sh      # Cassandra initialization
    └── test_phase4.sh          # Phase 4 testing
```

## 🔧 Configuration

### Environment Variables

**Producer** (`docker-compose.yml`):
- `KAFKA_BOOTSTRAP_SERVERS`: kafka:29092
- `KAFKA_TRANSACTION_TOPIC`: transactions_hsbc
- `TRANSACTION_RATE`: 2 (transactions/second)

**API**:
- `CASSANDRA_HOST`: cassandra
- `CASSANDRA_PORT`: 9042

**Dashboard**:
- `API_URL`: http://api:8000

### MinIO Credentials
- **Username**: admin
- **Password**: password123
- **Console**: http://localhost:9001

## 📈 Performance Metrics

- **Throughput**: 2-5 transactions/second
- **Latency**: ~2-3 seconds (end-to-end)
- **Model**: RandomForest (30 trees, depth 8)
- **Features**: 7 core features + category encoding
- **Batch interval**: 2 seconds (inference), 10 seconds (archive)

## 🐛 Troubleshooting

### Spark Job Not Starting
```powershell
docker compose restart spark-master spark-worker
Start-Sleep -Seconds 30
# Then resubmit job
```

### Cassandra Connection Failed
```powershell
docker compose restart cassandra
Start-Sleep -Seconds 60
docker exec cassandra cqlsh -e "SELECT now() FROM system.local;"
```

### No Data in Dashboard
```powershell
# Check if streaming job is running
docker logs spark-master --tail 50

# Check Cassandra data
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Restart API & Dashboard
docker compose restart api dashboard
```

See [SYSTEM_GUIDE.md](SYSTEM_GUIDE.md) for detailed troubleshooting.

## 📝 Common Tasks

### View Real-time Fraud Detection
```powershell
docker logs -f spark-master | Select-String "fraud"
```

### Query Fraud Alerts
```powershell
# Via API
curl http://localhost:8000/fraud/alerts?limit=10

# Via Cassandra
docker exec cassandra cqlsh -e "SELECT * FROM hsbc.fraud_alerts LIMIT 10;"
```

### Change Transaction Rate
Edit `docker-compose.yml`:
```yaml
producer:
  environment:
    TRANSACTION_RATE: 5  # Change from 2 to 5
```
Then: `docker compose restart producer`

### Retrain Model
```powershell
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark-apps/model_retraining.py
```

## 🎓 Learning Resources

- **Apache Spark Structured Streaming**: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- **Kafka Streams**: https://kafka.apache.org/documentation/streams/
- **Cassandra Data Modeling**: https://cassandra.apache.org/doc/latest/data_modeling/
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **Streamlit Docs**: https://docs.streamlit.io/

## 🤝 Contributing

1. Update code in respective directories
2. Copy to Spark Master: `docker cp <file> spark-master:/opt/spark-apps/`
3. Restart streaming job
4. Verify in dashboard

## 📄 License

This is a demonstration project for educational purposes.

## 🎉 Getting Started

For first-time setup, follow [QUICKSTART.md](QUICKSTART.md)

For detailed operations, see [SYSTEM_GUIDE.md](SYSTEM_GUIDE.md)

---

**Built with ❤️ for Real-time Fraud Detection**
