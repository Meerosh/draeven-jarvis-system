# JARVIS Front Door v2 - Log Analysis Script
# Analyzes logs for errors, warnings, performance issues

param(
    [string]$LogDir = "C:\Users\Arach\my-agent\jarvis-frontdoor\logs",
    [string]$DateFilter = (Get-Date -Format "yyyy-MM-dd"),
    [switch]$ShowErrors,
    [switch]$ShowWarnings,
    [switch]$ShowPerformance,
    [switch]$ShowAll
)

if (-not (Test-Path $LogDir)) {
    Write-Host "Log directory not found: $LogDir" -ForegroundColor Red
    exit 1
}

$logFile = Join-Path $LogDir "frontdoor-$DateFilter.log"

if (-not (Test-Path $logFile)) {
    Write-Host "No logs found for $DateFilter" -ForegroundColor Yellow
    Write-Host "Available logs:"
    Get-ChildItem $LogDir -Filter "*.log" | ForEach-Object { Write-Host "  - $($_.Name)" }
    exit 1
}

Write-Host "Analyzing logs from: $logFile" -ForegroundColor Cyan
Write-Host ""

$logContent = Get-Content $logFile
$lines = @($logContent | Select-String "")

# Parse and categorize logs
$errors = @()
$warnings = @()
$infos = @()
$debugs = @()

foreach ($line in $lines) {
    if ($line -match "ERROR") {
        $errors += $line
    }
    elseif ($line -match "WARNING") {
        $warnings += $line
    }
    elseif ($line -match "INFO") {
        $infos += $line
    }
    elseif ($line -match "DEBUG") {
        $debugs += $line
    }
}

# Summary statistics
Write-Host "📊 Log Summary:" -ForegroundColor Cyan
Write-Host "  Total lines: $($lines.Count)"
Write-Host "  INFO: $($infos.Count)" -ForegroundColor Green
Write-Host "  DEBUG: $($debugs.Count)" -ForegroundColor Gray
Write-Host "  WARNING: $($warnings.Count)" -ForegroundColor Yellow
Write-Host "  ERROR: $($errors.Count)" -ForegroundColor Red
Write-Host ""

# Show errors if requested or found
if ($errors.Count -gt 0 -and ($ShowErrors -or $ShowAll)) {
    Write-Host "🔴 ERRORS:" -ForegroundColor Red
    $errors | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Red
    }
    Write-Host ""
}

# Show warnings if requested
if ($warnings.Count -gt 0 -and ($ShowWarnings -or $ShowAll)) {
    Write-Host "⚠️  WARNINGS:" -ForegroundColor Yellow
    $warnings | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Performance analysis - find slow requests
if ($ShowPerformance -or $ShowAll) {
    Write-Host "⏱️  Performance Analysis:" -ForegroundColor Cyan

    $requestTimings = @()
    foreach ($line in $infos) {
        if ($line -match "Total=(\d+)ms") {
            $timing = [int]$matches[1]
            if ($timing -gt 1000) {  # Over 1 second
                $requestTimings += @{
                    Line = $line
                    Timing = $timing
                }
            }
        }
    }

    if ($requestTimings.Count -gt 0) {
        Write-Host "  Slow requests (>1000ms):" -ForegroundColor Yellow
        $requestTimings | Sort-Object -Property Timing -Descending | ForEach-Object {
            Write-Host "    $($_.Timing)ms - $($_.Line)" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  ✅ No slow requests detected" -ForegroundColor Green
    }

    # Circuit breaker events
    $circuitEvents = @($logContent | Select-String -Pattern "circuit|breaker|failed|retry")
    if ($circuitEvents.Count -gt 0) {
        Write-Host ""
        Write-Host "  Circuit Breaker Activity:" -ForegroundColor Cyan
        $circuitEvents | ForEach-Object {
            Write-Host "    $_" -ForegroundColor Gray
        }
    }

    Write-Host ""
}

# Most recent activity
Write-Host "📋 Recent Activity (last 10 entries):" -ForegroundColor Cyan
$lines[-10..-1] | ForEach-Object {
    $lineStr = $_
    if ($lineStr -match "ERROR") {
        Write-Host $lineStr -ForegroundColor Red
    }
    elseif ($lineStr -match "WARNING") {
        Write-Host $lineStr -ForegroundColor Yellow
    }
    else {
        Write-Host $lineStr -ForegroundColor Gray
    }
}

# Recommendations
Write-Host ""
Write-Host "💡 Recommendations:" -ForegroundColor Cyan
if ($errors.Count -gt 0) {
    Write-Host "  ⚠️  Review errors above and check provider availability" -ForegroundColor Red
}
if ($warnings.Count -gt 5) {
    Write-Host "  ⚠️  High warning count - monitor closely" -ForegroundColor Yellow
}
if ($requestTimings.Count -gt 0) {
    Write-Host "  ⚠️  Slow requests detected - check provider latency" -ForegroundColor Yellow
}
if ($errors.Count -eq 0 -and $warnings.Count -lt 3) {
    Write-Host "  ✅ System operating normally" -ForegroundColor Green
}
