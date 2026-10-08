# Head Room Integration into JARVIS

## Architecture
Head Room is a system tray application that displays real-time Claude Code and GitHub Copilot quota usage, integrated with JARVIS metrics dashboard.

## Integration Points

### 1. Installation
Head Room runs as a standalone Tauri 2 desktop application:
- Windows: Native Windows tray app
- macOS: Menu bar app
- Linux: System tray integration

### 2. Setup
```bash
cd modules/headroom
npm install
npm run tauri:build  # Build native binaries for current platform
```

### 3. Configuration
Create `~/.headroom/config.json`:
```json
{
  "jarvis_api": "http://127.0.0.1:4783/api/health",
  "update_interval": 30000,
  "show_notifications": true,
  "quota_alert_threshold": 80,
  "services": {
    "claude-code": true,
    "github-copilot": true,
    "jarvis": true
  }
}
```

### 4. JARVIS API Integration
Head Room polls JARVIS health endpoint:
```
GET http://127.0.0.1:4783/api/health
Response includes:
- usage.claude_code_tokens
- usage.github_tokens
- services[].ready
- quota_breakdown by provider
```

### 5. Dashboard Integration
Head Room feeds metrics to JARVIS dashboard:
- Real-time quota burndown charts
- Service health indicators
- Token usage trends
- Provider load distribution

### 6. Notifications
Alerts when:
- Quota approaches 80% of monthly limit
- Any service becomes unavailable
- Token burn rate exceeds threshold
- Provider switches due to exhaustion

### 7. Startup
```bash
# Build and run
cd modules/headroom
npm run tauri:build

# Launch (runs in system tray automatically)
./src-tauri/target/release/headroom
```

## Token Transparency
Head Room displays:
- Current month usage per provider
- Remaining tokens (estimated)
- Burn rate (tokens/day)
- Days until exhaustion per provider
- Free tier vs. paid tier breakdown

## Cross-Platform Support
- **Windows**: Native Win32, tray icon shows usage
- **macOS**: Menu bar app, click for details
- **Linux**: System tray (GNOME/KDE compatible)

## Metrics Exposed to JARVIS
```javascript
{
  "timestamp": "2026-10-05T20:26:00Z",
  "services": {
    "claude_code": {
      "used": 2500000,
      "limit": 10000000,
      "percentage": 25,
      "burn_rate": 50000,  // tokens/day
      "days_remaining": 150
    },
    "github_copilot": {
      "used": 1200000,
      "limit": 5000000,
      "percentage": 24,
      "burn_rate": 20000,
      "days_remaining": 190
    },
    "omniroute": {
      "free_tier_used": 500000,
      "free_tier_available": 1620000000,
      "percentage": 0.03,
      "provider_distribution": {...}
    }
  }
}
```

## Performance
- Minimal CPU usage (<1%)
- Memory footprint: ~40MB
- Update interval: configurable (default 30s)
- No system impact when minimized

## Privacy
- All data stays local
- No telemetry sent to external services
- Config stored in user's home directory
- Can be completely air-gapped
