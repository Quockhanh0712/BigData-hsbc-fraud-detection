# HSBC Fraud Detection - Automation Scripts
# Sử dụng: .\scripts\automation.ps1 <command>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'health', 'setup', 'train', 'stream', 'logs', 'clean', 'help')]
    [string]$Command = 'help'
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                                                       ║" -ForegroundColor Cyan
    Write-Host "║     🏦  HSBC FRAUD DETECTION SYSTEM                   ║" -ForegroundColor Cyan
    Write-Host "║         Real-time ML-based Fraud Detection            ║" -ForegroundColor Cyan
    Write-Host "║                                                       ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

# Commands
function Start-System {
    Write-Info "🚀 Starting HSBC Fraud Detection System..."
    
    # Check if already running
    $running = docker compose ps --services --filter "status=running" 2>$null
    if ($running) {
        Write-Warning "⚠️  Some services are already running:"
        docker compose ps
        $response = Read-Host "Do you want to restart? (y/N)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            Write-Info "Aborted."
            return
        }
        docker compose down
    }
    
    Write-Info "📦 Starting all services..."
    docker compose up -d
    
    Write-Info "⏳ Waiting for services to initialize (120 seconds)..."
    Start-Sleep -Seconds 120
    
    Write-Success "✅ All services started!"
    docker compose ps
    
    Write-Info "`n📊 Access Points:"
    Write-Host "  • Dashboard:      http://localhost:8501" -ForegroundColor Yellow
    Write-Host "  • API:            http://localhost:8000" -ForegroundColor Yellow
    Write-Host "  • API Docs:       http://localhost:8000/docs" -ForegroundColor Yellow
    Write-Host "  • Spark Master:   http://localhost:8080" -ForegroundColor Yellow
    Write-Host "  • MinIO Console:  http://localhost:9001 (admin/password123)" -ForegroundColor Yellow
}

function Stop-System {
    Write-Info "🛑 Stopping HSBC Fraud Detection System..."
    
    $response = Read-Host "Keep data? (Y/n)"
    if ($response -eq 'n' -or $response -eq 'N') {
        Write-Warning "⚠️  This will DELETE all data (Cassandra, MinIO, Kafka)!"
        $confirm = Read-Host "Are you sure? Type 'yes' to confirm"
        if ($confirm -eq 'yes') {
            docker compose down -v
            Write-Success "✅ System stopped and all data deleted."
        } else {
            Write-Info "Aborted."
        }
    } else {
        docker compose stop
        Write-Success "✅ System stopped. Data preserved."
    }
}

function Restart-System {
    Write-Info "🔄 Restarting HSBC Fraud Detection System..."
    
    docker compose restart
    
    Write-Info "⏳ Waiting for services to restart (60 seconds)..."
    Start-Sleep -Seconds 60
    
    Write-Success "✅ System restarted!"
    docker compose ps
}

function Show-Status {
    Write-Info "📊 System Status:"
    Write-Host ""
    docker compose ps
    
    Write-Host "`n📈 Resource Usage:" -ForegroundColor Cyan
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

function Show-Health {
    Write-Info "🔍 Health Check - HSBC Fraud Detection System"
    Write-Host ""
    
    # 1. Containers
    Write-Info "✅ Container Status:"
    docker compose ps
    Write-Host ""
    
    # 2. Kafka Topics
    Write-Info "✅ Kafka Topics:"
    try {
        docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 2>$null
    } catch {
        Write-Error "❌ Kafka not responding"
    }
    Write-Host ""
    
    # 3. Cassandra
    Write-Info "✅ Cassandra Fraud Count:"
    try {
        docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" 2>$null
    } catch {
        Write-Error "❌ Cassandra not responding or table not created"
    }
    Write-Host ""
    
    # 4. API
    Write-Info "✅ API Health:"
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/" -TimeoutSec 5
        $response | ConvertTo-Json
    } catch {
        Write-Error "❌ API not responding"
    }
    Write-Host ""
    
    # 5. MinIO
    Write-Info "✅ MinIO Buckets:"
    try {
        docker exec minio mc ls myminio/ 2>$null
    } catch {
        Write-Error "❌ MinIO not responding"
    }
    Write-Host ""
    
    Write-Success "✅ Health Check Complete!"
}

function Setup-Database {
    Write-Info "🗄️  Setting up Cassandra Database..."
    
    Write-Info "Creating keyspace 'hsbc'..."
    docker exec -it cassandra cqlsh -e "CREATE KEYSPACE IF NOT EXISTS hsbc WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"
    
    Write-Info "Creating table 'fraud_alerts'..."
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
    
    Write-Success "✅ Database setup complete!"
    
    # Verify
    Write-Info "Verifying table..."
    docker exec -it cassandra cqlsh -e "DESCRIBE hsbc.fraud_alerts;"
}

function Train-Model {
    Write-Info "🤖 Training Fraud Detection Model..."
    
    Write-Info "Copying training scripts to Spark Master..."
    docker cp streaming-pipeline/model_retraining.py spark-master:/opt/spark-apps/
    docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
    
    Write-Info "Starting training job (this may take 5-10 minutes)..."
    Write-Host "💡 Tip: Monitor progress in another terminal with: docker logs -f spark-master" -ForegroundColor Yellow
    Write-Host ""
    
    docker exec spark-master /opt/spark/bin/spark-submit `
        --master spark://spark-master:7077 `
        --deploy-mode client `
        /opt/spark-apps/model_retraining.py
    
    Write-Success "✅ Model training complete!"
    
    Write-Info "Verifying model..."
    docker exec spark-master ls -lh /opt/data/models/fraud_rf_lean
}

function Start-Streaming {
    Write-Info "⚡ Starting Fraud Detection Streaming..."
    
    Write-Info "Copying streaming pipeline to Spark Master..."
    docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
    docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
    
    Write-Info "Starting streaming job..."
    Write-Host "💡 This will run in foreground. Press Ctrl+C to stop." -ForegroundColor Yellow
    Write-Host "💡 Or run in background with: docker exec -d spark-master ..." -ForegroundColor Yellow
    Write-Host ""
    
    docker exec spark-master /opt/spark/bin/spark-submit `
        --master spark://spark-master:7077 `
        --deploy-mode client `
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 `
        /opt/spark-apps/unified_streaming.py
}

function Show-Logs {
    Write-Info "📋 Available services:"
    $services = docker compose ps --services
    $services | ForEach-Object { Write-Host "  • $_" -ForegroundColor Yellow }
    Write-Host ""
    
    $service = Read-Host "Enter service name (or 'all' for all services)"
    
    if ($service -eq 'all') {
        docker compose logs -f
    } else {
        $tail = Read-Host "Number of lines to show (default: 100)"
        if ([string]::IsNullOrWhiteSpace($tail)) { $tail = 100 }
        
        $follow = Read-Host "Follow logs? (Y/n)"
        if ($follow -eq 'n' -or $follow -eq 'N') {
            docker logs $service --tail $tail
        } else {
            docker logs -f $service --tail $tail
        }
    }
}

function Clean-System {
    Write-Warning "⚠️  CLEAN SYSTEM - This will:"
    Write-Host "  1. Stop all containers"
    Write-Host "  2. Remove all containers"
    Write-Host "  3. Remove all volumes (DELETE ALL DATA)"
    Write-Host "  4. Remove all images (optional)"
    Write-Host ""
    
    $confirm = Read-Host "Are you sure? Type 'yes' to confirm"
    if ($confirm -ne 'yes') {
        Write-Info "Aborted."
        return
    }
    
    Write-Info "Stopping all containers..."
    docker compose down
    
    Write-Info "Removing volumes..."
    docker compose down -v
    
    $removeImages = Read-Host "Remove Docker images too? (y/N)"
    if ($removeImages -eq 'y' -or $removeImages -eq 'Y') {
        Write-Info "Removing images..."
        docker compose down -v --rmi all
    }
    
    Write-Info "Cleaning Docker system..."
    docker system prune -f
    
    Write-Success "✅ System cleaned!"
}

function Show-Help {
    Show-Banner
    
    Write-Host "Usage: .\scripts\automation.ps1 <command>" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available Commands:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  start       " -ForegroundColor Green -NoNewline
    Write-Host "  Start all services"
    Write-Host "  stop        " -ForegroundColor Green -NoNewline
    Write-Host "  Stop all services (with option to keep/delete data)"
    Write-Host "  restart     " -ForegroundColor Green -NoNewline
    Write-Host "  Restart all services"
    Write-Host "  status      " -ForegroundColor Green -NoNewline
    Write-Host "  Show system status and resource usage"
    Write-Host "  health      " -ForegroundColor Green -NoNewline
    Write-Host "  Run health check on all components"
    Write-Host "  setup       " -ForegroundColor Green -NoNewline
    Write-Host "  Setup Cassandra database (keyspace + table)"
    Write-Host "  train       " -ForegroundColor Green -NoNewline
    Write-Host "  Train fraud detection ML model"
    Write-Host "  stream      " -ForegroundColor Green -NoNewline
    Write-Host "  Start fraud detection streaming job"
    Write-Host "  logs        " -ForegroundColor Green -NoNewline
    Write-Host "  View service logs"
    Write-Host "  clean       " -ForegroundColor Green -NoNewline
    Write-Host "  Complete system cleanup (removes all data)"
    Write-Host "  help        " -ForegroundColor Green -NoNewline
    Write-Host "  Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\scripts\automation.ps1 start" -ForegroundColor Yellow
    Write-Host "  .\scripts\automation.ps1 health" -ForegroundColor Yellow
    Write-Host "  .\scripts\automation.ps1 logs" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Quick Setup (First Time):" -ForegroundColor Cyan
    Write-Host "  1. .\scripts\automation.ps1 start" -ForegroundColor Yellow
    Write-Host "  2. .\scripts\automation.ps1 setup" -ForegroundColor Yellow
    Write-Host "  3. .\scripts\automation.ps1 train" -ForegroundColor Yellow
    Write-Host "  4. .\scripts\automation.ps1 stream" -ForegroundColor Yellow
    Write-Host "  5. Open http://localhost:8501" -ForegroundColor Yellow
    Write-Host ""
}

# Main
Show-Banner

switch ($Command) {
    'start'   { Start-System }
    'stop'    { Stop-System }
    'restart' { Restart-System }
    'status'  { Show-Status }
    'health'  { Show-Health }
    'setup'   { Setup-Database }
    'train'   { Train-Model }
    'stream'  { Start-Streaming }
    'logs'    { Show-Logs }
    'clean'   { Clean-System }
    'help'    { Show-Help }
    default   { Show-Help }
}

Write-Host ""
