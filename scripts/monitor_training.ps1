# Monitor Training Progress
Write-Host "🔍 Monitoring DecisionTree Training..." -ForegroundColor Cyan
Write-Host ""

$count = 0
while ($count -lt 60) {  # Monitor for up to 5 minutes
    Start-Sleep -Seconds 5
    $count++
    
    # Check if model directory exists
    $modelCheck = docker exec spark-master ls -d /opt/data/models/fraud_dt_21features 2>$null
    
    if ($modelCheck) {
        Write-Host "✅ MODEL TRAINING COMPLETED!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Model location: /opt/data/models/fraud_dt_21features" -ForegroundColor Yellow
        
        # Show model contents
        Write-Host ""
        Write-Host "Model files:" -ForegroundColor Cyan
        docker exec spark-master ls -lh /opt/data/models/fraud_dt_21features/
        
        # Show metadata
        Write-Host ""
        Write-Host "Model metadata:" -ForegroundColor Cyan
        docker exec spark-master cat /opt/data/models/fraud_dt_21features/metadata/part-00000 2>$null
        
        break
    }
    
    # Show progress indicator
    Write-Host "[$count/60] Training in progress..." -NoNewline
    Write-Host "`r" -NoNewline
}

if (-not $modelCheck) {
    Write-Host ""
    Write-Host "⏱️ Training still running. Check logs:" -ForegroundColor Yellow
    Write-Host "docker logs spark-master --tail 50" -ForegroundColor Gray
}
