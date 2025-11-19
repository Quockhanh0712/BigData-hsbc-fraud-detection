# 📊 Monitoring Real-Time Fraud Detection

## 🎯 Các Cách Xem Logs Real-Time

### **Option 1: Monitor Script (RECOMMENDED)** ✅

Script này query Cassandra mỗi 3 giây và hiển thị fraud alerts mới:

```powershell
.\monitor_fraud_realtime.ps1
```

**Output:**
```
🚨 REAL-TIME FRAUD DETECTION MONITOR
================================================================================
[18:30:15] 🚨 NEW FRAUD DETECTED! +3 alerts (Total: 442)

────────────────────────────────────────────────────────────────────────────
🔴 FRAUD ALERT:
   TX ID:      a3f8d2e1...
   Time:       2025-11-20 18:30:10
   Amount:     $1,234.56
   Merchant:   Amazon Web Services
   Category:   shopping_net
   Customer:   John Doe
   Location:   San Francisco, CA
────────────────────────────────────────────────────────────────────────────
```

### **Option 2: Cassandra Count Loop**

Xem số lượng fraud alerts tăng theo thời gian:

```powershell
while ($true) {
    $count = docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Fraud Alerts: $count" -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}
```

**Output:**
```
[18:30:00] Fraud Alerts: 439
[18:30:05] Fraud Alerts: 442  ← +3 new
[18:30:10] Fraud Alerts: 445  ← +3 new
[18:30:15] Fraud Alerts: 447  ← +2 new
```

### **Option 3: Producer Logs**

Xem producer đang gửi bao nhiêu transactions (bao gồm cả fraud thực tế):

```powershell
docker logs producer -f
```

**Output:**
```
2025-11-19 18:30:15 - INFO - 📊 Sent: 4,500 | Fraud: 466 (10.36%) | Errors: 0 | Rate: 12.4 tx/sec
2025-11-19 18:30:23 - INFO - 📊 Sent: 4,600 | Fraud: 483 (10.50%) | Errors: 0 | Rate: 12.4 tx/sec
```

### **Option 4: Spark Worker Logs**

Xem detailed streaming processing logs:

```powershell
docker logs spark-worker -f 2>&1 | Select-String "FRAUD|Batch|ERROR"
```

### **Option 5: Latest Fraud Alerts từ Cassandra**

Xem 10 fraud alerts mới nhất:

```powershell
docker exec cassandra cqlsh -e "SELECT transaction_id, transaction_time, amount, merchant, first, last FROM hsbc.fraud_alerts LIMIT 10;"
```

**Output:**
```
 transaction_id                   | transaction_time            | amount  | merchant              | first | last
----------------------------------+-----------------------------+---------+-----------------------+-------+----------
 a3f8d2e1fc80670714c6a2b6888d0d60 | 2025-11-20 18:30:10.000000  | 1234.56 | Amazon Web Services   | John  | Doe
 b4e9c3f2ed91781825d7b3c7999e1e71 | 2025-11-20 18:30:12.000000  | 567.89  | Walmart              | Jane  | Smith
```

---

## 📈 Monitoring Dashboard

### **Streamlit Dashboard (Best for visualization)**

```powershell
# Start dashboard
docker compose up -d api dashboard

# Open browser
Start-Process "http://localhost:8501"
```

**Features:**
- 📊 Real-time charts (fraud by category, state)
- 📋 Fraud alerts table with filters
- 💰 Total amount, average amount metrics
- 🔄 Auto-refresh every 5 seconds

---

## 🎯 Understanding the Metrics

### **Producer Metrics**

```
📊 Sent: 4,500 | Fraud: 466 (10.36%) | Errors: 0 | Rate: 12.4 tx/sec
```

- **Sent**: Total transactions sent to Kafka
- **Fraud**: Actual fraud count from is_fraud label in data (ground truth)
- **%**: Percentage of actual fraud in sent data
- **Rate**: Transactions per second

### **Cassandra Count**

```
count
-------
  466
```

- **count**: Number of fraud alerts DETECTED by XGBoost model
- This is DIFFERENT from actual fraud count in producer
- If count > actual fraud → Model has false positives
- If count < actual fraud → Model missed some fraud

### **Detection Metrics**

```
Producer Actual Fraud:  466 transactions (10.36%)
Cassandra Detected:     442 transactions
```

**Calculations:**
- **True Positives (TP)**: ≈ 442 (detected correctly)
- **False Negatives (FN)**: 466 - 442 = 24 (missed)
- **Recall**: 442/466 = 94.8% (good!)
- **False Positives (FP)**: Detected - TP ≈ unknown without full analysis

---

## 🔍 Detailed Fraud Investigation

### **Query specific fraud transaction:**

```powershell
$txId = "a3f8d2e1fc80670714c6a2b6888d0d60"
docker exec cassandra cqlsh -e "SELECT * FROM hsbc.fraud_alerts WHERE transaction_id='$txId';"
```

### **Query by amount range:**

```sql
-- Fraud > $1000
SELECT transaction_id, amount, merchant, first, last 
FROM hsbc.fraud_alerts 
WHERE amount > 1000.0 
ALLOW FILTERING;
```

### **Export to CSV:**

```powershell
docker exec cassandra cqlsh -e "COPY hsbc.fraud_alerts TO '/tmp/fraud_alerts.csv' WITH HEADER=TRUE;"
docker cp cassandra:/tmp/fraud_alerts.csv ./fraud_alerts.csv
```

---

## 📊 Real-Time Metrics Script

Save as `metrics_live.ps1`:

```powershell
while ($true) {
    Clear-Host
    Write-Host "`n📊 FRAUD DETECTION SYSTEM METRICS" -ForegroundColor Cyan
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')`n" -ForegroundColor Gray
    
    # Producer stats
    $producerLog = docker logs producer --tail 1 2>$null
    if ($producerLog -match "Sent: ([\d,]+).*Fraud: (\d+).*Rate: ([\d.]+)") {
        Write-Host "📤 PRODUCER:" -ForegroundColor Yellow
        Write-Host "   Transactions Sent:  $($Matches[1])" -ForegroundColor White
        Write-Host "   Actual Fraud:       $($Matches[2])" -ForegroundColor Red
        Write-Host "   Rate:               $($Matches[3]) tx/sec" -ForegroundColor Green
    }
    
    Write-Host ""
    
    # Cassandra stats
    $count = docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" 2>$null | Select-String "\d+" | ForEach-Object { $_.Matches[0].Value }
    Write-Host "🗄️  CASSANDRA:" -ForegroundColor Cyan
    Write-Host "   Fraud Detected:     $count" -ForegroundColor White
    
    Write-Host ""
    
    # Detection rate
    if ($Matches[2] -and $count) {
        $actualFraud = [int]$Matches[2]
        $detected = [int]$count
        $recall = [math]::Round(($detected / $actualFraud) * 100, 2)
        
        Write-Host "🎯 DETECTION METRICS:" -ForegroundColor Magenta
        Write-Host "   Recall:             $recall%" -ForegroundColor White
        
        if ($recall -ge 95) {
            Write-Host "   Status:             ✅ Excellent" -ForegroundColor Green
        }
        elseif ($recall -ge 85) {
            Write-Host "   Status:             ⚠️  Good" -ForegroundColor Yellow
        }
        else {
            Write-Host "   Status:             ❌ Needs Improvement" -ForegroundColor Red
        }
    }
    
    Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
    
    Start-Sleep -Seconds 5
}
```

**Run with:**
```powershell
.\metrics_live.ps1
```

---

## 🚀 Quick Commands Reference

```powershell
# Check all services status
docker compose ps

# Producer logs (live)
docker logs producer -f

# Fraud count
docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;"

# Latest 5 frauds
docker exec cassandra cqlsh -e "SELECT transaction_id, amount, merchant FROM hsbc.fraud_alerts LIMIT 5;"

# Streaming process check
docker exec spark-master ps aux | Select-String "spark"

# Dashboard
Start-Process "http://localhost:8501"

# Spark UI
Start-Process "http://localhost:8080"

# MinIO Console
Start-Process "http://localhost:9001"
```

---

## 🎨 Advanced Visualization

### **PowerShell Progress Bar**

```powershell
$target = 10000  # Target transactions
while ($true) {
    $log = docker logs producer --tail 1 2>$null
    if ($log -match "Sent: ([\d,]+)") {
        $sent = [int]$Matches[1].Replace(',', '')
        $percent = [math]::Min(100, [int](($sent / $target) * 100))
        
        Write-Progress -Activity "Fraud Detection System" `
                       -Status "$sent / $target transactions processed" `
                       -PercentComplete $percent
    }
    Start-Sleep -Seconds 2
}
```

### **ASCII Chart (Fraud Rate Over Time)**

```powershell
$history = @()
$maxHistory = 20

while ($true) {
    $log = docker logs producer --tail 1 2>$null
    if ($log -match "Sent: ([\d,]+).*Fraud: (\d+)") {
        $sent = [int]$Matches[1].Replace(',', '')
        $fraud = [int]$Matches[2]
        $rate = [math]::Round(($fraud / $sent) * 100, 2)
        
        $history += $rate
        if ($history.Count -gt $maxHistory) {
            $history = $history[-$maxHistory..-1]
        }
        
        Clear-Host
        Write-Host "`n📈 FRAUD RATE OVER TIME" -ForegroundColor Cyan
        Write-Host "=" * 60 -ForegroundColor Cyan
        
        foreach ($r in $history) {
            $bars = [int]($r * 3)  # Scale for display
            $bar = "█" * $bars
            Write-Host ("{0,5:N2}% | {1}" -f $r, $bar) -ForegroundColor Yellow
        }
        
        Write-Host "=" * 60 -ForegroundColor Cyan
    }
    Start-Sleep -Seconds 5
}
```

---

## ✅ Best Practices

1. **Use monitor_fraud_realtime.ps1** for continuous monitoring
2. **Check dashboard** for visual analytics
3. **Monitor producer logs** to ensure data is flowing
4. **Query Cassandra** for detailed fraud investigation
5. **Export CSV** periodically for offline analysis

---

## 🔧 Troubleshooting

### **No new fraud alerts appearing**

**Check:**
```powershell
# 1. Producer running?
docker logs producer --tail 5

# 2. Streaming running?
docker exec spark-master ps aux | Select-String "spark-submit"

# 3. Kafka has messages?
docker exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --all-groups
```

### **Monitoring script shows errors**

**Fix:**
```powershell
# Ensure Cassandra is ready
docker exec cassandra cqlsh -e "DESCRIBE KEYSPACE hsbc;"

# Restart Cassandra if needed
docker compose restart cassandra
Start-Sleep -Seconds 30
```

---

**Last Updated**: 2025-11-20  
**Scripts Included**:
- `monitor_fraud_realtime.ps1` - Real-time fraud monitor (RECOMMENDED)
- `metrics_live.ps1` - Live system metrics
- `tail_fraud_logs.ps1` - Tail streaming logs
- `monitor_fraud_live.ps1` - Advanced log monitoring

**Status**: ✅ Production Ready
