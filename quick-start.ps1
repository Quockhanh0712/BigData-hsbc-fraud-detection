# HSBC Fraud Detection - Quick Start Script
# Chạy file này: .\quick-start.ps1

param(
    [string]$Action = "start"
)

$ErrorActionPreference = "Continue"

function Show-Banner {
    Write-Host "`n" -NoNewline
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "   🚨 HSBC FRAUD DETECTION SYSTEM" -ForegroundColor Yellow
    Write-Host "   DecisionTree | 21 Features | Real-time Streaming" -ForegroundColor White
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

function Start-System {
    Show-Banner
    Write-Host "🚀 KHỞI ĐỘNG HỆ THỐNG...`n" -ForegroundColor Green
    
    # Bước 1: Start Docker Compose
    Write-Host "[1/9] Starting Docker Compose..." -ForegroundColor Cyan
    docker compose up -d
    Write-Host "✓ Docker Compose started`n" -ForegroundColor Green
    
    # Đợi services khởi động
    Write-Host "[2/9] Waiting for services to start (30s)..." -ForegroundColor Cyan
    Start-Sleep -Seconds 30
    Write-Host "✓ Services ready`n" -ForegroundColor Green
    
    # Bước 3: Check containers
    Write-Host "[3/9] Checking containers..." -ForegroundColor Cyan
    docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String "api|dashboard|producer|spark|cassandra|kafka|minio|zookeeper"
    Write-Host ""
    
    # Bước 4: Check model
    Write-Host "[4/9] Checking model..." -ForegroundColor Cyan
    $modelExists = docker exec spark-master test -d /opt/data/models/fraud_dt_21features 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Model exists: /opt/data/models/fraud_dt_21features`n" -ForegroundColor Green
        $trainModel = $false
    } else {
        Write-Host "⚠ Model NOT found. Will train new model...`n" -ForegroundColor Yellow
        $trainModel = $true
    }
    
    # Bước 5: Train model nếu cần
    if ($trainModel) {
        Write-Host "[5/9] Training DecisionTree model (this will take ~2 minutes)..." -ForegroundColor Cyan
        
        # Copy files
        docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
        docker cp streaming-pipeline/model_retraining.py spark-master:/opt/spark-apps/
        docker cp streaming-pipeline/unified_streaming.py spark-master:/opt/spark-apps/
        
        # Train
        docker exec spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining.py"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Model trained successfully`n" -ForegroundColor Green
        } else {
            Write-Host "✗ Model training failed`n" -ForegroundColor Red
            return
        }
    } else {
        Write-Host "[5/9] Skipping training (model exists)`n" -ForegroundColor Cyan
    }
    
    # Bước 6: Start streaming
    Write-Host "[6/9] Starting streaming pipeline..." -ForegroundColor Cyan
    docker exec spark-master pkill -f unified_streaming 2>$null
    docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 2g --conf spark.sql.shuffle.partitions=20 --conf spark.streaming.kafka.consumer.poll.ms=256 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 /opt/spark-apps/unified_streaming.py"
    Start-Sleep -Seconds 5
    Write-Host "✓ Streaming started`n" -ForegroundColor Green
    
    # Bước 7: Check producer
    Write-Host "[7/9] Checking producer..." -ForegroundColor Cyan
    docker logs producer --tail 3
    Write-Host ""
    
    # Bước 8: Verify Cassandra
    Write-Host "[8/9] Checking Cassandra alerts..." -ForegroundColor Cyan
    docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" 2>$null
    Write-Host ""
    
    # Bước 9: Show URLs
    Write-Host "[9/9] System ready!`n" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "✅ HỆ THỐNG ĐÃ KHỞI ĐỘNG THÀNH CÔNG!" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🌐 URLs:" -ForegroundColor Yellow
    Write-Host "   API:        http://localhost:8000" -ForegroundColor White
    Write-Host "   Dashboard:  http://localhost:8501" -ForegroundColor White
    Write-Host "   Spark UI:   http://localhost:8080" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Monitoring:" -ForegroundColor Yellow
    Write-Host "   docker logs -f producer --tail 30" -ForegroundColor Gray
    Write-Host "   docker logs -f spark-master --tail 50" -ForegroundColor Gray
    Write-Host ""
}

function Stop-System {
    Show-Banner
    Write-Host "🛑 STOPPING SYSTEM...`n" -ForegroundColor Red
    
    Write-Host "Stopping streaming..." -ForegroundColor Cyan
    docker exec spark-master pkill -f unified_streaming 2>$null
    
    Write-Host "Stopping containers..." -ForegroundColor Cyan
    docker compose stop
    
    Write-Host "`n✓ System stopped`n" -ForegroundColor Green
}

function Restart-System {
    Show-Banner
    Write-Host "🔄 RESTARTING SYSTEM...`n" -ForegroundColor Yellow
    
    Stop-System
    Start-Sleep -Seconds 5
    Start-System
}

function Show-Status {
    Show-Banner
    Write-Host "📊 SYSTEM STATUS`n" -ForegroundColor Cyan
    
    Write-Host "Containers:" -ForegroundColor Yellow
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "api|dashboard|producer|spark|cassandra|kafka"
    Write-Host ""
    
    Write-Host "Fraud Alerts Count:" -ForegroundColor Yellow
    docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" 2>$null
    Write-Host ""
    
    Write-Host "Producer Status:" -ForegroundColor Yellow
    docker logs producer --tail 3
    Write-Host ""
    
    Write-Host "Streaming Process:" -ForegroundColor Yellow
    docker exec spark-master ps aux | Select-String "unified_streaming" | Select-Object -First 1
    Write-Host ""
}

function Retrain-Model {
    Show-Banner
    Write-Host "🔄 RETRAINING MODEL...`n" -ForegroundColor Yellow
    
    Write-Host "Stopping streaming..." -ForegroundColor Cyan
    docker exec spark-master pkill -f unified_streaming 2>$null
    
    Write-Host "Removing old model..." -ForegroundColor Cyan
    docker exec spark-master rm -rf /opt/data/models/fraud_dt_21features
    
    Write-Host "Copying files..." -ForegroundColor Cyan
    docker cp streaming-pipeline/feature_engineering.py spark-master:/opt/spark-apps/
    docker cp streaming-pipeline/model_retraining.py spark-master:/opt/spark-apps/
    
    Write-Host "Training new model (this will take ~2 minutes)..." -ForegroundColor Cyan
    docker exec spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 4g --conf spark.sql.shuffle.partitions=20 /opt/spark-apps/model_retraining.py"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✓ Model trained successfully`n" -ForegroundColor Green
        
        Write-Host "Starting streaming with new model..." -ForegroundColor Cyan
        docker exec -d spark-master bash -c "cd /opt/spark-apps && export PYSPARK_PYTHON=/usr/bin/python3 && /opt/spark/bin/spark-submit --master local[4] --driver-memory 2g --conf spark.sql.shuffle.partitions=20 --conf spark.streaming.kafka.consumer.poll.ms=256 --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.datastax.spark:spark-cassandra-connector_2.12:3.4.0 /opt/spark-apps/unified_streaming.py"
        
        Write-Host "✓ Streaming restarted with new model`n" -ForegroundColor Green
    } else {
        Write-Host "✗ Model training failed`n" -ForegroundColor Red
    }
}

function Show-Logs {
    param([string]$Service = "all")
    
    Show-Banner
    
    if ($Service -eq "all" -or $Service -eq "producer") {
        Write-Host "📊 PRODUCER LOGS:" -ForegroundColor Yellow
        docker logs producer --tail 20
        Write-Host ""
    }
    
    if ($Service -eq "all" -or $Service -eq "spark") {
        Write-Host "🔥 SPARK STREAMING LOGS:" -ForegroundColor Yellow
        docker logs spark-master --tail 30 | Select-String "Batch|fraud|Model|ERROR"
        Write-Host ""
    }
    
    if ($Service -eq "all" -or $Service -eq "api") {
        Write-Host "🌐 API LOGS:" -ForegroundColor Yellow
        docker logs api --tail 15
        Write-Host ""
    }
    
    if ($Service -eq "all" -or $Service -eq "dashboard") {
        Write-Host "📊 DASHBOARD LOGS:" -ForegroundColor Yellow
        docker logs dashboard --tail 15
        Write-Host ""
    }
}

function Show-Help {
    Show-Banner
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\quick-start.ps1 [action]`n" -ForegroundColor White
    
    Write-Host "ACTIONS:" -ForegroundColor Yellow
    Write-Host "  start       - Start the entire system (default)" -ForegroundColor White
    Write-Host "  stop        - Stop all containers" -ForegroundColor White
    Write-Host "  restart     - Restart the system" -ForegroundColor White
    Write-Host "  status      - Show system status" -ForegroundColor White
    Write-Host "  retrain     - Retrain the model" -ForegroundColor White
    Write-Host "  logs        - Show all logs" -ForegroundColor White
    Write-Host "  logs-producer   - Show producer logs only" -ForegroundColor White
    Write-Host "  logs-spark      - Show spark logs only" -ForegroundColor White
    Write-Host "  logs-api        - Show API logs only" -ForegroundColor White
    Write-Host "  help        - Show this help" -ForegroundColor White
    Write-Host ""
    
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  .\quick-start.ps1" -ForegroundColor Gray
    Write-Host "  .\quick-start.ps1 start" -ForegroundColor Gray
    Write-Host "  .\quick-start.ps1 status" -ForegroundColor Gray
    Write-Host "  .\quick-start.ps1 retrain" -ForegroundColor Gray
    Write-Host "  .\quick-start.ps1 logs-producer" -ForegroundColor Gray
    Write-Host ""
}

# Main
switch ($Action.ToLower()) {
    "start" { Start-System }
    "stop" { Stop-System }
    "restart" { Restart-System }
    "status" { Show-Status }
    "retrain" { Retrain-Model }
    "logs" { Show-Logs -Service "all" }
    "logs-producer" { Show-Logs -Service "producer" }
    "logs-spark" { Show-Logs -Service "spark" }
    "logs-api" { Show-Logs -Service "api" }
    "logs-dashboard" { Show-Logs -Service "dashboard" }
    "help" { Show-Help }
    default { 
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Write-Host "Run '.\quick-start.ps1 help' for usage" -ForegroundColor Yellow
    }
}
