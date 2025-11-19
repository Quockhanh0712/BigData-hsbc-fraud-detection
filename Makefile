# ╔═══════════════════════════════════════════════════════╗
# ║     HSBC Fraud Detection System - Makefile           ║
# ╚═══════════════════════════════════════════════════════╝

.PHONY: help start stop restart status health setup train stream logs clean build

# Default target
.DEFAULT_GOAL := help

## help: Show this help message
help:
	@echo ""
	@echo "╔═══════════════════════════════════════════════════════╗"
	@echo "║     🏦  HSBC FRAUD DETECTION SYSTEM                   ║"
	@echo "╚═══════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "  make start       - Start all services"
	@echo "  make stop        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make status      - Show system status"
	@echo "  make health      - Run health check"
	@echo "  make setup       - Setup Cassandra database"
	@echo "  make train       - Train ML model"
	@echo "  make stream      - Start fraud detection streaming"
	@echo "  make logs        - View logs (all or specific service)"
	@echo "  make clean       - Clean system (remove all data)"
	@echo "  make build       - Build Docker images"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make start"
	@echo "  2. make setup"
	@echo "  3. make train"
	@echo "  4. make stream"
	@echo "  5. Open http://localhost:8501"
	@echo ""

## start: Start all services
start:
	@echo "🚀 Starting HSBC Fraud Detection System..."
	docker compose up -d
	@echo "⏳ Waiting for services to initialize (60 seconds)..."
	@timeout /t 60 /nobreak > NUL
	@echo "✅ All services started!"
	@docker compose ps
	@echo ""
	@echo "📊 Access Points:"
	@echo "  • Dashboard:      http://localhost:8501"
	@echo "  • API:            http://localhost:8000"
	@echo "  • API Docs:       http://localhost:8000/docs"
	@echo "  • Spark Master:   http://localhost:8080"
	@echo "  • MinIO Console:  http://localhost:9001"
	@echo ""

## stop: Stop all services (keep data)
stop:
	@echo "🛑 Stopping all services..."
	docker compose stop
	@echo "✅ All services stopped. Data preserved."

## restart: Restart all services
restart:
	@echo "🔄 Restarting all services..."
	docker compose restart
	@echo "⏳ Waiting for services to restart (30 seconds)..."
	@timeout /t 30 /nobreak > NUL
	@echo "✅ All services restarted!"
	@docker compose ps

## status: Show system status
status:
	@echo "📊 System Status:"
	@docker compose ps
	@echo ""
	@echo "📈 Resource Usage:"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

## health: Run health check
health:
	@echo "🔍 Health Check - HSBC Fraud Detection System"
	@echo ""
	@echo "✅ Container Status:"
	@docker compose ps
	@echo ""
	@echo "✅ Kafka Topics:"
	@docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 2>NUL || echo "❌ Kafka not responding"
	@echo ""
	@echo "✅ Cassandra Fraud Count:"
	@docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" 2>NUL || echo "❌ Cassandra not ready or table not created"
	@echo ""
	@echo "✅ API Health:"
	@curl -s http://localhost:8000/ || echo "❌ API not responding"
	@echo ""

## setup: Setup Cassandra database
setup:
	@echo "🗄️  Setting up Cassandra Database..."
	@echo "Creating keyspace 'hsbc'..."
	@docker exec -it cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS hsbc WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"
	@echo "Creating table 'fraud_alerts'..."
	@docker exec -it cassandra cqlsh -e "CREATE TABLE IF NOT EXISTS hsbc.fraud_alerts (transaction_id text PRIMARY KEY, transaction_time timestamp, amount double, merchant text, category text, cc_num text, first text, last text, gender text, job text, state text, city text, zip text, is_fraud double, detected_at timestamp);"
	@echo "✅ Database setup complete!"

## train: Train ML model
train:
	@echo "🤖 Training Fraud Detection Model..."
	@echo "Copying training scripts to Spark Master..."
	@docker cp streaming-pipeline/model_retraining.py spark-master:/opt/spark-apps/
	@docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
	@echo "Starting training job (5-10 minutes)..."
	@echo "💡 Monitor progress: docker logs -f spark-master"
	docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --deploy-mode client /opt/spark-apps/model_retraining.py
	@echo "✅ Model training complete!"

## stream: Start fraud detection streaming
stream:
	@echo "⚡ Starting Fraud Detection Streaming..."
	@echo "Copying streaming pipeline to Spark Master..."
	@docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
	@docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
	@echo "Starting streaming job..."
	@echo "💡 Press Ctrl+C to stop"
	docker exec spark-master /opt/spark/bin/spark-submit --master spark://spark-master:7077 --deploy-mode client --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 /opt/spark-apps/unified_streaming.py

## logs: View logs (interactive)
logs:
	@docker compose logs -f

## logs-service: View logs for specific service (usage: make logs-service SERVICE=api)
logs-service:
	@docker logs -f $(SERVICE) --tail 100

## clean: Complete cleanup (removes all data)
clean:
	@echo "⚠️  WARNING: This will DELETE all data!"
	@echo "Press Ctrl+C to cancel, or"
	@pause
	@echo "Stopping and removing all containers, networks, and volumes..."
	docker compose down -v
	@echo "✅ System cleaned!"

## build: Build Docker images
build:
	@echo "🔨 Building Docker images..."
	docker compose build
	@echo "✅ Build complete!"

## down: Remove containers (keep volumes)
down:
	@echo "Removing all containers..."
	docker compose down
	@echo "✅ Containers removed. Volumes preserved."

## up: Alias for start
up: start

## ps: Show running containers
ps:
	@docker compose ps

## api-test: Test API endpoints
api-test:
	@echo "Testing API endpoints..."
	@echo "Health check:"
	@curl -s http://localhost:8000/ | jq
	@echo ""
	@echo "Fraud count:"
	@curl -s http://localhost:8000/fraud/count | jq
	@echo ""
	@echo "Latest 5 alerts:"
	@curl -s "http://localhost:8000/fraud/alerts?limit=5" | jq

## cassandra-query: Query Cassandra fraud alerts
cassandra-query:
	@echo "Querying Cassandra fraud_alerts table..."
	@docker exec -it cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"
	@docker exec -it cassandra cqlsh -e "SELECT transaction_id, amount, category, merchant, detected_at FROM hsbc.fraud_alerts LIMIT 10;"

## spark-ui: Open Spark Master UI
spark-ui:
	@echo "Opening Spark Master UI: http://localhost:8080"
	@start http://localhost:8080

## dashboard: Open Dashboard
dashboard:
	@echo "Opening Dashboard: http://localhost:8501"
	@start http://localhost:8501

## api-docs: Open API Documentation
api-docs:
	@echo "Opening API Docs: http://localhost:8000/docs"
	@start http://localhost:8000/docs
