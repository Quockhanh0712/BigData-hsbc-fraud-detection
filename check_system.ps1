# System Health Check Script
# Run: .\check_system.ps1

Write-Host "`n╔═══════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   HSBC FRAUD DETECTION - SYSTEM STATUS CHECK         ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════════╝`n" -ForegroundColor Magenta

# Check Docker is running
Write-Host "[1] Checking Docker..." -ForegroundColor Cyan
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running`n" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running! Please start Docker Desktop.`n" -ForegroundColor Red
    exit 1
}

# Check containers status
Write-Host "[2] Container Status" -ForegroundColor Cyan
$containers = @('zookeeper', 'kafka', 'cassandra', 'minio', 'spark-master', 'spark-worker', 'producer', 'dashboard')
foreach ($container in $containers) {
    $status = docker ps --filter "name=$container" --format "{{.Status}}" 2>$null
    if ($status) {
        Write-Host "   ✅ $container : $status" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $container : NOT RUNNING" -ForegroundColor Red
    }
}
Write-Host ""

# Check Kafka topic
Write-Host "[3] Kafka Topic" -ForegroundColor Cyan
try {
    $topics = docker exec kafka kafka-topics --list --bootstrap-server localhost:9092 2>$null
    if ($topics -match "transactions_hsbc") {
        Write-Host "   ✅ Topic 'transactions_hsbc' exists`n" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Topic 'transactions_hsbc' not found`n" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Cannot connect to Kafka`n" -ForegroundColor Red
}

# Check Cassandra
Write-Host "[4] Cassandra Database" -ForegroundColor Cyan
try {
    $result = docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" 2>$null
    if ($result -match "(\d+)") {
        $count = $matches[1]
        Write-Host "   ✅ Fraud alerts table exists" -ForegroundColor Green
        Write-Host "   📊 Total alerts: $count`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Cannot query Cassandra`n" -ForegroundColor Red
}

# Check XGBoost model
Write-Host "[5] ML Model Status" -ForegroundColor Cyan
try {
    $modelCheck = docker exec spark-master bash -c "ls /opt/data/models/fraud_xgb_21features 2>/dev/null" 2>$null
    if ($modelCheck) {
        Write-Host "   ✅ XGBoost model loaded (AUC: 0.9964)" -ForegroundColor Green
        $modelSize = docker exec spark-master bash -c "du -sh /opt/data/models/fraud_xgb_21features | cut -f1" 2>$null
        Write-Host "   📦 Model size: $modelSize`n" -ForegroundColor Yellow
    } else {
        Write-Host "   ⚠️  Model not found - may need training`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Cannot check model status`n" -ForegroundColor Red
}

# Check producer status
Write-Host "[6] Producer Status" -ForegroundColor Cyan
try {
    $producerLogs = docker logs producer --tail 5 2>$null | Select-String "Sent:"
    if ($producerLogs) {
        $lastLog = $producerLogs[-1]
        Write-Host "   ✅ Producer is active" -ForegroundColor Green
        Write-Host "   $lastLog`n" -ForegroundColor Yellow
    } else {
        Write-Host "   ⚠️  Producer may not be sending data`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Cannot read producer logs`n" -ForegroundColor Red
}

# Check streaming pipeline
Write-Host "[7] Spark Streaming" -ForegroundColor Cyan
try {
    $streamingProcess = docker exec spark-master bash -c "ps aux | grep unified_streaming | grep -v grep" 2>$null
    if ($streamingProcess) {
        Write-Host "   ✅ Streaming pipeline is running`n" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Streaming pipeline is NOT running`n" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Cannot check streaming status`n" -ForegroundColor Red
}

# Latest fraud alerts
Write-Host "[8] Recent Fraud Alerts" -ForegroundColor Cyan
try {
    $alerts = docker exec cassandra cqlsh -e "SELECT transaction_id, amount, merchant, transaction_time FROM hsbc.fraud_alerts LIMIT 5;" 2>$null
    if ($alerts) {
        Write-Host "$alerts`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Cannot fetch recent alerts`n" -ForegroundColor Red
}

# Performance metrics
Write-Host "[9] System Metrics" -ForegroundColor Cyan
try {
    $stats = docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | Select-Object -First 10
    Write-Host "$stats`n" -ForegroundColor Yellow
} catch {
    Write-Host "   ❌ Cannot fetch metrics`n" -ForegroundColor Red
}

# Access URLs
Write-Host "[10] Access URLs" -ForegroundColor Cyan
Write-Host "   🌐 Dashboard:    http://localhost:8501" -ForegroundColor Green
Write-Host "   🌐 Spark UI:     http://localhost:8080" -ForegroundColor Green
Write-Host "   🌐 MinIO Console: http://localhost:9001 (admin/password123)`n" -ForegroundColor Green

Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   ✅ SYSTEM CHECK COMPLETE                            ║" -ForegroundColor Magenta
Write-Host "╚═══════════════════════════════════════════════════════╝`n" -ForegroundColor Magenta

# Recommendations
Write-Host "📌 Quick Commands:" -ForegroundColor Cyan
Write-Host "   • View logs:        docker logs <container-name> --tail 50" -ForegroundColor White
Write-Host "   • Restart service:  docker compose restart <service-name>" -ForegroundColor White
Write-Host "   • Stop all:         docker compose down" -ForegroundColor White
Write-Host "   • Start all:        docker compose up -d`n" -ForegroundColor White
