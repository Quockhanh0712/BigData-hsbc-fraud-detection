# Simple Fraud Detection Monitor
Write-Host "`nFRAUD DETECTION LIVE MONITOR" -ForegroundColor Red
Write-Host ("=" * 80) -ForegroundColor Yellow
Write-Host "Monitoring Cassandra fraud alerts... Press Ctrl+C to stop`n" -ForegroundColor Cyan

$previousCount = 0

while ($true) {
    try {
        $countResult = docker exec cassandra cqlsh -e "SELECT COUNT(*) FROM hsbc.fraud_alerts;" 2>$null
        $match = $countResult | Select-String "\d+" | Select-Object -First 1
        if ($match) {
            $currentCount = [int]$match.Matches[0].Value
        } else {
            $currentCount = 0
        }
        
        if ($currentCount -gt $previousCount) {
            $newAlerts = $currentCount - $previousCount
            
            Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] " -NoNewline -ForegroundColor Gray
            Write-Host "NEW FRAUD DETECTED! " -NoNewline -ForegroundColor Red
            Write-Host "+$newAlerts alerts " -NoNewline -ForegroundColor Yellow
            Write-Host "(Total: $currentCount)" -ForegroundColor White
            
            # Get latest alerts
            $query = "SELECT transaction_id, amount, merchant, first, last, city FROM hsbc.fraud_alerts LIMIT $currentCount;"
            $results = docker exec cassandra cqlsh -e $query 2>$null
            
            if ($results) {
                $lines = $results -split "`n" | Where-Object { $_ -match "^\s*\w{32}" }
                $latest = $lines | Select-Object -Last $newAlerts
                
                Write-Host ("`n" + ("-" * 80)) -ForegroundColor DarkGray
                
                foreach ($line in $latest) {
                    $parts = $line -split '\|'
                    if ($parts.Count -ge 6) {
                        $txId = $parts[0].Trim().Substring(0, 16) + "..."
                        $amount = $parts[1].Trim()
                        $merchant = $parts[2].Trim()
                        $first = $parts[3].Trim()
                        $last = $parts[4].Trim()
                        $city = $parts[5].Trim()
                        
                        Write-Host "FRAUD ALERT:" -ForegroundColor Red
                        Write-Host "  TX: $txId | Amount: `$$amount | $merchant" -ForegroundColor White
                        Write-Host "  Customer: $first $last | Location: $city" -ForegroundColor Cyan
                        Write-Host ""
                    }
                }
                
                Write-Host ("-" * 80) -ForegroundColor DarkGray
            }
            
            $previousCount = $currentCount
        }
        elseif ($currentCount -eq $previousCount -and $previousCount -gt 0) {
            Write-Host "." -NoNewline -ForegroundColor DarkGray
        }
        
        Start-Sleep -Seconds 3
    }
    catch {
        Write-Host "`nError: $_" -ForegroundColor Red
        Start-Sleep -Seconds 5
    }
}
