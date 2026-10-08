# JARVIS Front Door v2 - Health Monitoring Script
# Run this to continuously monitor system health and pending requests

param(
    [int]$IntervalSeconds = 5,
    [string]$FrontDoorUrl = "http://127.0.0.1:4719"
)

function Get-HealthStatus {
    try {
        $response = Invoke-RestMethod -Uri "$FrontDoorUrl/health" -Method Get -ErrorAction Stop
        return $response
    }
    catch {
        return $null
    }
}

function Format-HealthReport {
    param($health)

    if ($null -eq $health) {
        Write-Host "❌ OFFLINE: Cannot reach Front Door at $FrontDoorUrl" -ForegroundColor Red
        return $false
    }

    $timestamp = Get-Date -Format "HH:mm:ss"

    # Extract key metrics
    $ok = $health.ok
    $pendingCount = $health.pending_count ?? 0
    $historyCount = $health.history_count ?? 0
    $cloudCallsToday = $health.usage.cloud_calls_today ?? 0
    $dailyLimit = $health.usage.daily_cloud_call_limit ?? 40
    $remaining = $health.usage.cloud_calls_remaining ?? 0
    $notesIndexed = $health.notes_indexed ?? 0

    # Display status
    $statusColor = if ($ok) { "Green" } else { "Red" }
    $statusText = if ($ok) { "✅ ONLINE" } else { "❌ OFFLINE" }

    Write-Host "`n[$timestamp] $statusText" -ForegroundColor $statusColor

    if ($ok) {
        # Color code based on thresholds
        $pendingColor = if ($pendingCount -gt 50) { "Yellow" } else { if ($pendingCount -gt 100) { "Red" } else { "Green" } }
        $cloudColor = if ($remaining -lt 10) { "Red" } else { if ($remaining -lt 20) { "Yellow" } else { "Green" } }

        Write-Host "  📊 Metrics:" -ForegroundColor Cyan
        Write-Host "    Pending Requests: " -NoNewline
        Write-Host "$pendingCount" -ForegroundColor $pendingColor -NoNewline
        Write-Host " (should be near 0)"

        Write-Host "    Conversation History: " -NoNewline
        Write-Host "$historyCount" -ForegroundColor Green -NoNewline
        Write-Host " / 20 turns"

        Write-Host "    Cloud Calls Today: " -NoNewline
        Write-Host "$cloudCallsToday" -ForegroundColor $cloudColor -NoNewline
        Write-Host " / $dailyLimit (remaining: $remaining)"

        Write-Host "    Vault Indexed: " -NoNewline
        Write-Host "$notesIndexed" -ForegroundColor Green -NoNewline
        Write-Host " markdown files"

        # Check provider status
        $providers = $health.providers | Get-Member -MemberType NoteProperty
        Write-Host "  🔌 Providers:"
        foreach ($provider in $providers) {
            $name = $provider.Name
            $status = $health.providers.$name
            $enabled = if ($status.enabled) { "✅" } else { "❌" }
            $reason = $status.reason ?? "Ready"
            Write-Host "    $enabled $name - $reason" -ForegroundColor $(if ($status.enabled) { "Green" } else { "Red" })
        }
    }

    return $ok
}

# Main monitoring loop
Write-Host "================================" -ForegroundColor Cyan
Write-Host "JARVIS Front Door Health Monitor" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Checking every $IntervalSeconds seconds..."
Write-Host "Press Ctrl+C to stop"

$consecutiveFailures = 0
$offlineTime = $null

while ($true) {
    $health = Get-HealthStatus
    $isHealthy = Format-HealthReport -health $health

    if ($isHealthy) {
        $consecutiveFailures = 0
        if ($null -ne $offlineTime) {
            $recoveredAfter = (Get-Date) - $offlineTime
            Write-Host "✅ Recovered after $(([int]$recoveredAfter.TotalSeconds))s downtime" -ForegroundColor Yellow
            $offlineTime = $null
        }
    }
    else {
        $consecutiveFailures++
        if ($null -eq $offlineTime) {
            $offlineTime = Get-Date
        }
        if ($consecutiveFailures -eq 1) {
            Write-Host "⚠️  Server unresponsive (check if running)" -ForegroundColor Yellow
        }
    }

    # Alert thresholds
    if ($isHealthy) {
        if ($pendingCount -gt 100) {
            Write-Host "⚠️  ALERT: High pending count ($pendingCount) - may indicate stuck confirmations" -ForegroundColor Red
        }
        if ($remaining -lt 5) {
            Write-Host "⚠️  ALERT: Only $remaining cloud calls remaining for today" -ForegroundColor Red
        }
    }

    Start-Sleep -Seconds $IntervalSeconds
}
