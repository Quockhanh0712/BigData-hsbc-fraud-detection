# 📚 HSBC Fraud Detection - Documentation Index

Welcome to the complete documentation for the HSBC Fraud Detection System!

---

## 🚀 Getting Started

### For First-Time Users
1. **[QUICKSTART.md](QUICKSTART.md)** - Get the system running in 5 minutes
   - Prerequisites check
   - 5-step setup process
   - Verification steps
   - Common troubleshooting

### For Understanding the System
2. **[README.md](README.md)** - Project overview
   - What is this system?
   - Features & capabilities
   - Tech stack summary
   - Quick reference

---

## 📖 Core Documentation

### Operations & Usage
3. **[SYSTEM_GUIDE.md](SYSTEM_GUIDE.md)** - Complete operations manual (MUST READ)
   - Detailed component documentation
   - Start/stop procedures for each service
   - Configuration options
   - Advanced troubleshooting
   - Maintenance procedures
   - **Length**: ~500 lines, comprehensive guide

4. **[COMMANDS.md](COMMANDS.md)** - Command cheat sheet
   - Quick reference for all commands
   - Common workflows
   - Troubleshooting quick fixes
   - PowerShell aliases
   - **Use this**: When you need to find a command fast

### Architecture & Design
5. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
   - Data flow diagrams
   - Component interactions
   - Technology stack details
   - Design decisions explained
   - Performance characteristics
   - **Read this**: To understand how everything works

---

## 🛠️ Automation Tools

### PowerShell Automation
6. **[scripts/automation.ps1](scripts/automation.ps1)** - Automation script
   ```powershell
   .\scripts\automation.ps1 <command>
   
   Commands:
   - start    : Start all services
   - stop     : Stop all services
   - restart  : Restart all services
   - status   : Show system status
   - health   : Run health check
   - setup    : Setup Cassandra database
   - train    : Train ML model
   - stream   : Start streaming job
   - logs     : View logs
   - clean    : Clean system
   ```

### Makefile Commands
7. **[Makefile](Makefile)** - Make commands
   ```bash
   make start       # Start all services
   make stop        # Stop all services
   make status      # Show status
   make health      # Health check
   make setup       # Setup database
   make train       # Train model
   make stream      # Start streaming
   make logs        # View logs
   make clean       # Clean system
   
   # Quick start
   make start && make setup && make train && make stream
   ```

---

## 📊 How to Use This Documentation

### Scenario-Based Guide

#### "I'm new and want to get started quickly"
1. Read **[README.md](README.md)** - 5 minutes overview
2. Follow **[QUICKSTART.md](QUICKSTART.md)** - 5 minutes setup
3. Bookmark **[COMMANDS.md](COMMANDS.md)** - For future reference

#### "I want to understand how it works"
1. Read **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design
2. Read **[SYSTEM_GUIDE.md](SYSTEM_GUIDE.md)** Section 1-3 - Core concepts
3. Explore code in `streaming-pipeline/`, `api/`, `dashboard/`

#### "I need to operate/maintain the system"
1. Keep **[SYSTEM_GUIDE.md](SYSTEM_GUIDE.md)** open - Complete reference
2. Keep **[COMMANDS.md](COMMANDS.md)** handy - Quick commands
3. Use automation: `.\scripts\automation.ps1` or `make`

#### "I'm troubleshooting an issue"
1. Check **[SYSTEM_GUIDE.md](SYSTEM_GUIDE.md)** Section 8 - Troubleshooting
2. Check **[COMMANDS.md](COMMANDS.md)** - Quick fixes
3. Check **[QUICKSTART.md](QUICKSTART.md)** - Verification steps

#### "I want to modify/extend the system"
1. Read **[ARCHITECTURE.md](ARCHITECTURE.md)** - Design decisions
2. Read **[SYSTEM_GUIDE.md](SYSTEM_GUIDE.md)** Section 5 - Component details
3. Check **[COMMANDS.md](COMMANDS.md)** - Update code workflow

---

## 📁 File Structure Reference

```
hsbc-fraud-detection-new/
│
├── 📚 DOCUMENTATION
│   ├── README.md              ⭐ Start here - Project overview
│   ├── QUICKSTART.md          🚀 5-minute setup guide
│   ├── SYSTEM_GUIDE.md        📖 Complete operations manual
│   ├── COMMANDS.md            📋 Command cheat sheet
│   ├── ARCHITECTURE.md        🏗️ System architecture
│   └── INDEX.md               📚 This file
│
├── 🔧 AUTOMATION & MONITORING
│   ├── Makefile               🛠️ Make commands
│   ├── quick-start.ps1        🚀 Quick start automation
│   ├── check_system.ps1       ✅ System health check
│   ├── watch_fraud.ps1        👁️ Real-time fraud monitor
│   ├── tail_fraud_logs.ps1    📜 Streaming logs viewer
│   └── scripts/
│       └── automation.ps1     🤖 PowerShell automation
│
├── 📦 APPLICATION CODE
│   ├── producer/              📤 Transaction generator
│   │   ├── producer.py
│   │   ├── config.py
│   │   └── Dockerfile
│   │
│   ├── streaming-pipeline/    ⚡ Spark streaming & ML
│   │   ├── unified_streaming.py
│   │   ├── feature_engineering.py
│   │   └── model_retraining.py
│   │
│   ├── api/                   🌐 FastAPI backend
│   │   ├── main.py
│   │   ├── database.py
│   │   └── Dockerfile
│   │
│   └── dashboard/             📊 Streamlit frontend
│       ├── app.py
│       └── Dockerfile
│
├── 💾 DATA
│   ├── data/raw/              📁 Source data
│   │   ├── fraudTrain.csv
│   │   └── fraudTest.csv
│   │
│   ├── data/processed/        🔄 Processed data
│   └── data/models/           🤖 Trained models
│       └── fraud_rf_lean/
│
└── 🐳 INFRASTRUCTURE
    └── docker-compose.yml     🏗️ Container orchestration
```

---

## 🎯 Quick Actions

### I want to...

#### Start the system
```powershell
# Option 1: Makefile
make start

# Option 2: Automation script
.\scripts\automation.ps1 start

# Option 3: Docker Compose
docker compose up -d
```
📖 **See**: [QUICKSTART.md](QUICKSTART.md) Step 2

---

#### Check if everything is working
```powershell
make health
```
📖 **See**: [QUICKSTART.md](QUICKSTART.md) - "Verify Everything is Working"

---

#### View real-time fraud detection
```powershell
# Live fraud alerts monitor (RECOMMENDED)
.\watch_fraud.ps1

# Streaming logs with details
.\tail_fraud_logs.ps1

# Browser dashboard
start http://localhost:8501
```
📖 **See**: [QUICKSTART.md](QUICKSTART.md) Step 7 - Monitor Real-Time Fraud Detection

---

#### Query fraud alerts
```powershell
# Via API
curl http://localhost:8000/fraud/alerts?limit=10

# Via Cassandra
docker exec cassandra cqlsh -e "SELECT * FROM hsbc.fraud_alerts LIMIT 10;"
```
📖 **See**: [COMMANDS.md](COMMANDS.md) - API Commands

---

#### Change transaction rate
Edit `docker-compose.yml`:
```yaml
producer:
  environment:
    TRANSACTION_RATE: 5  # Change from 2 to 5
```
Then: `docker compose restart producer`

📖 **See**: [SYSTEM_GUIDE.md](SYSTEM_GUIDE.md) Section 5.5 - Producer

---

#### Retrain the model
```powershell
make train
```
📖 **See**: [SYSTEM_GUIDE.md](SYSTEM_GUIDE.md) Section 5.6 - Model Training

---

#### Stop the system
```powershell
# Keep data
make stop

# Delete everything
make clean
```
📖 **See**: [SYSTEM_GUIDE.md](SYSTEM_GUIDE.md) Section 7 - Tắt Hệ Thống

---

#### Troubleshoot issues
1. Check logs: `make logs`
2. Check health: `make health`
3. Restart: `make restart`

📖 **See**: [SYSTEM_GUIDE.md](SYSTEM_GUIDE.md) Section 8 - Xử Lý Sự Cố

---

## 🔗 External Resources

### Official Documentation
- **Apache Spark**: https://spark.apache.org/docs/3.5.0/
- **Apache Kafka**: https://kafka.apache.org/documentation/
- **Apache Cassandra**: https://cassandra.apache.org/doc/latest/
- **MinIO**: https://min.io/docs/minio/linux/index.html
- **FastAPI**: https://fastapi.tiangolo.com/
- **Streamlit**: https://docs.streamlit.io/
- **Docker**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/

### Tutorials & Guides
- **Spark Structured Streaming**: https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- **Kafka Streams**: https://kafka.apache.org/documentation/streams/
- **Cassandra Data Modeling**: https://cassandra.apache.org/doc/latest/data_modeling/
- **PySpark MLlib**: https://spark.apache.org/docs/latest/ml-guide.html

---

## 📞 Support & Contribution

### Getting Help
1. Check **[SYSTEM_GUIDE.md](SYSTEM_GUIDE.md)** Section 8 - Troubleshooting
2. Check **[QUICKSTART.md](QUICKSTART.md)** - Verification steps
3. Review logs: `make logs`
4. Run health check: `make health`

### Reporting Issues
When reporting issues, include:
- What you were trying to do
- What happened vs. what you expected
- Relevant logs (`docker logs <service>`)
- System status (`docker compose ps`)
- Environment (OS, Docker version)

### Contributing
1. Fork the repository
2. Make changes in a feature branch
3. Test thoroughly
4. Submit pull request with documentation updates

---

## 📊 Documentation Statistics

| Document | Purpose | Length | Read Time |
|----------|---------|--------|-----------|
| README.md | Overview | ~200 lines | 3 min |
| QUICKSTART.md | Fast setup | ~400 lines | 5 min |
| SYSTEM_GUIDE.md | Complete guide | ~500 lines | 30 min |
| COMMANDS.md | Command reference | ~600 lines | 10 min |
| ARCHITECTURE.md | System design | ~500 lines | 20 min |
| INDEX.md | This file | ~300 lines | 5 min |

**Total**: ~2,500 lines of comprehensive documentation

---

## 🎓 Learning Path

### Beginner (Day 1)
1. ✅ Read **README.md** (3 min)
2. ✅ Follow **QUICKSTART.md** (5 min)
3. ✅ Access dashboard: http://localhost:8501
4. ✅ Explore API docs: http://localhost:8000/docs
5. ✅ Bookmark **COMMANDS.md**

**Outcome**: System running, understand basics

### Intermediate (Day 2-3)
1. ✅ Read **ARCHITECTURE.md** (20 min)
2. ✅ Read **SYSTEM_GUIDE.md** Sections 1-5 (30 min)
3. ✅ Explore Spark UI: http://localhost:8080
4. ✅ Query Cassandra directly
5. ✅ Try different API endpoints

**Outcome**: Understand architecture, can operate system

### Advanced (Week 1)
1. ✅ Read **SYSTEM_GUIDE.md** Sections 6-8 (20 min)
2. ✅ Modify feature engineering code
3. ✅ Retrain model with different parameters
4. ✅ Customize dashboard
5. ✅ Add new API endpoints

**Outcome**: Can maintain, troubleshoot, extend system

---

## ✨ Document Updates

### Version History
- **v1.0.0** (2025-11-16): Initial documentation release
  - Complete system guide
  - Quick start guide
  - Architecture documentation
  - Command reference
  - Automation scripts

### Future Additions (Planned)
- [ ] Video tutorials
- [ ] FAQ section
- [ ] Performance tuning guide
- [ ] Production deployment guide
- [ ] API client examples (Python, JavaScript)
- [ ] Monitoring & alerting setup

---

## 🎯 Document Quality Checklist

All documentation includes:
- ✅ Clear objectives
- ✅ Step-by-step instructions
- ✅ Code examples with comments
- ✅ Expected outputs
- ✅ Troubleshooting tips
- ✅ Cross-references to related docs
- ✅ Visual aids (ASCII diagrams)
- ✅ Quick reference sections

---

## 📝 Feedback

Documentation feedback welcome! Please include:
- Which document you're referring to
- What was unclear/missing
- Suggestions for improvement

---

**Happy Fraud Detecting! 🎉**

Built with ❤️ for Real-time Fraud Detection

---

**Last Updated**: November 16, 2025  
**Documentation Version**: 1.0.0  
**System Version**: 1.0.0
