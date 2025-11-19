# Simple Fraud Detection Log Viewer
# Shows continuous stream of fraud detections

Write-Host "`n🚨 REAL-TIME FRAUD DETECTION LOGS" -ForegroundColor Red
Write-Host "=" * 80 -ForegroundColor Yellow
Write-Host "Monitoring streaming pipeline..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray

# Tail the log file continuously
docker exec spark-master bash -c "tail -f /tmp/streaming.log | grep --line-buffered -E 'FRAUD|fraud|Batch|Amount|Merchant|Customer|Location|Writing|saved|ERROR'"
