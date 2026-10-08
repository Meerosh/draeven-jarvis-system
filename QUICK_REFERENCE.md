# JARVIS Front Door v2 - Quick Reference Guide

## Deployment Checklist

### 1. Pre-Deployment (Do Once)
- [ ] Python 3.11+ installed on Windows
- [ ] Git installed and configured
- [ ] Repository cloned to `C:\Users\Arach\Documents\Jarvis\Citadel\desktop\draeven-jarvis-system`

### 2. Initial Deployment
```powershell
# Run the deployment script
C:\Users\Arach\my-agent\jarvis-frontdoor\DEPLOY_JARVIS_FrontDoor.bat

# Or manual deployment:
cd C:\Users\Arach\Documents\Jarvis\Citadel\desktop\draeven-jarvis-system
git pull origin main
cd runtime\frontdoor
python server.py
```

### 3. Verification
Open in browser or PowerShell:
```powershell
# Health check
Invoke-RestMethod -Uri "http://127.0.0.1:4719/health" | ConvertTo-Json

# Expected response:
{
  "ok": true,
  "pending_count": 0,
  "history_count": 0-20,
  "usage": {
    "cloud_calls_today": N,
    "cloud_calls_remaining": 40-N
  }
}
```

## Monitoring Commands

### Real-Time Health Monitoring
```powershell
# Run every 5 seconds (continuously)
& "C:\Users\Arach\my-agent\jarvis-frontdoor\Monitor-JARVISHealth.ps1"

# Check every 10 seconds
& "C:\Users\Arach\my-agent\jarvis-frontdoor\Monitor-JARVISHealth.ps1" -IntervalSeconds 10
```

### Log Analysis
```powershell
# Analyze today's logs (all issues)
& "C:\Users\Arach\my-agent\jarvis-frontdoor\Analyze-JARVISLogs.ps1" -ShowAll

# Show only errors
& "C:\Users\Arach\my-agent\jarvis-frontdoor\Analyze-JARVISLogs.ps1" -ShowErrors

# Show performance issues
& "C:\Users\Arach\my-agent\jarvis-frontdoor\Analyze-JARVISLogs.ps1" -ShowPerformance

# Analyze specific date
& "C:\Users\Arach\my-agent\jarvis-frontdoor\Analyze-JARVISLogs.ps1" -DateFilter "2026-10-05" -ShowAll
```

## Key Metrics to Monitor

### Healthy State
- ✅ pending_count: 0-5 (most of the time)
- ✅ history_count: 0-20
- ✅ cloud_calls_remaining: >10
- ✅ No ERROR lines in logs

### Warning State (Investigate)
- ⚠️ pending_count: 10-50 (pending confirmations backing up)
- ⚠️ history_count: >20 (data loss on oldest turn)
- ⚠️ cloud_calls_remaining: 5-10 (running low for the day)
- ⚠️ WARNING lines in logs (transient issues)

### Critical State (Act Now)
- 🔴 pending_count: >100 (stuck confirmations)
- 🔴 cloud_calls_remaining: <5 (about to hit daily limit)
- 🔴 ERROR lines in logs (serious issues)
- 🔴 Server unresponsive (check if running)

## Common Tasks

### Stop the Server
```powershell
# If running in console:
# Press Ctrl+C in the terminal

# Or from PowerShell:
Get-Process python | Where-Object {$_.Path -like "*jarvis-frontdoor*"} | Stop-Process
```

### Check if Server is Running
```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 4719
# Should show: TcpTestSucceeded: True

# Or check process:
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*server.py*"}
```

### View Real-Time Logs
```powershell
# Watch logs as they're written
Get-Content "C:\Users\Arach\my-agent\jarvis-frontdoor\logs\frontdoor-$(Get-Date -Format 'yyyy-MM-dd').log" -Tail 20 -Wait

# Search for specific pattern
Select-String "ERROR\|WARNING\|Provider" "C:\Users\Arach\my-agent\jarvis-frontdoor\logs\*.log"
```

### Restart Server
```powershell
# Stop all Python JARVIS processes
Get-Process python | Where-Object {$_.CommandLine -like "*jarvis*"} | Stop-Process -Force

# Wait a moment
Start-Sleep -Seconds 2

# Restart
C:\Users\Arach\my-agent\jarvis-frontdoor\DEPLOY_JARVIS_FrontDoor.bat
```

## Troubleshooting

### Issue: Server won't start
**Check:**
- Python installed: `python --version`
- Port 4719 available: `netstat -ano | findstr :4719`
- Syntax errors: See console output
- Logs directory writable: `dir C:\Users\Arach\my-agent\jarvis-frontdoor\logs`

### Issue: Health check fails
**Try:**
```powershell
# Verify server is running
Get-Process python

# Check if listening on port 4719
Test-NetConnection -ComputerName 127.0.0.1 -Port 4719

# Check logs for startup errors
Get-Content "C:\Users\Arach\my-agent\jarvis-frontdoor\logs\*.log" | Select-String ERROR
```

### Issue: High pending_count
**Cause:** Confirmations waiting for approval  
**Fix:**
- Check HUD for pending confirmations
- Approve or reject pending actions
- Monitor in real-time: `Monitor-JARVISHealth.ps1`

### Issue: Slow requests
**Cause:** Provider latency or network issues  
**Check:**
- Cloud call limits: `Invoke-RestMethod -Uri "http://127.0.0.1:4719/health"`
- Provider availability: Check Ollama, Laya running
- Network latency: Test provider endpoints
- Logs for warnings: `Analyze-JARVISLogs.ps1 -ShowPerformance`

## Environment Variables (Optional)

Set these before starting server for custom configuration:

```powershell
# PowerShell - temporary (session only)
$env:JARVIS_FRONTDOOR_PORT = "4719"
$env:JARVIS_VAULT = "C:\Users\Arach\Documents\Jarvis"
$env:JARVIS_PENDING_TTL = "1800"

# Or set permanently (System Properties)
setx JARVIS_FRONTDOOR_PORT "4719"
setx JARVIS_VAULT "C:\Users\Arach\Documents\Jarvis"
setx JARVIS_PENDING_TTL "1800"
```

## Useful Endpoints

```powershell
# Health status
curl http://127.0.0.1:4719/health | jq

# Conversation history
curl http://127.0.0.1:4719/history | jq

# Server info
$health = Invoke-RestMethod -Uri "http://127.0.0.1:4719/health"
$health | Format-Table
```

## Log Locations

- **Main logs:** `C:\Users\Arach\my-agent\jarvis-frontdoor\logs\frontdoor-YYYY-MM-DD.log`
- **Vault logs:** `C:\Users\Arach\Documents\Jarvis\00 - Inbox\JARVIS Log\YYYY-MM-DD.md`
- **Status file:** `C:\Users\Arach\my-agent\jarvis-frontdoor\status.txt`

## Performance Baselines

These are normal ranges for your system:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Request latency | <5s | 5-10s | >10s |
| Pending count | 0-5 | 10-50 | >100 |
| Cloud calls/day | <30 | 30-38 | >40 |
| Memory usage | <200MB | 200-500MB | >500MB |
| Errors/hour | 0-1 | 2-5 | >5 |

---

**Version:** 2.0 (2026-10-05)  
**Last Updated:** 2026-10-05  
**Next Review:** After first week of production deployment
