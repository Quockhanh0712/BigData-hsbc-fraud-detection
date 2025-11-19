# HSBC Fraud Detection - Welcome Script
# Display system banner and status

# Display banner
Get-Content "$PSScriptRoot\..\BANNER.txt"

Write-Host ""
Write-Host "🔍 System Health Check..." -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "Docker Status: " -NoNewline
try {
    $dockerVersion = docker --version
    Write-Host "✅ $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found or not running" -ForegroundColor Red
    exit 1
}

Write-Host "Docker Compose: " -NoNewline
try {
    $composeVersion = docker compose version
    Write-Host "✅ $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check if services are running
Write-Host "📊 Running Services:" -ForegroundColor Cyan
$runningServices = docker compose ps --services --filter "status=running" 2>$null
if ($runningServices) {
    $count = ($runningServices | Measure-Object).Count
    Write-Host "✅ $count services running" -ForegroundColor Green
    $runningServices | ForEach-Object { Write-Host "  • $_" -ForegroundColor Yellow }
} else {
    Write-Host "⚠️  No services running. Start with: make start" -ForegroundColor Yellow
}

Write-Host ""

# Quick actions
Write-Host "🎯 Quick Actions:" -ForegroundColor Cyan
Write-Host "  make start      - Start all services" -ForegroundColor White
Write-Host "  make status     - Check system status" -ForegroundColor White
Write-Host "  make health     - Run health check" -ForegroundColor White
Write-Host "  make dashboard  - Open dashboard" -ForegroundColor White
Write-Host "  make help       - Show all commands" -ForegroundColor White

Write-Host ""
Write-Host "📚 Documentation: See INDEX.md for complete guide" -ForegroundColor Cyan
Write-Host ""
