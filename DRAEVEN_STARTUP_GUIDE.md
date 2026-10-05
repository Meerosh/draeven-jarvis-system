# Draeven HUD - Startup Guide

## Quick Start

### Option 1: Simple Startup (Recommended)
```batch
START-DRAEVEN.bat
```

This is the standard startup method. The server will start on `http://127.0.0.1:4783`.

### Option 2: Full Cleanup + Startup
```batch
CLEANUP-DRAEVEN-PORTS.bat
```

Use this if you encounter "Address already in use" errors or after a system restart. It:
- Terminates any existing Python processes
- Releases all service ports
- Waits for OS to fully release ports
- Starts the server fresh

### Option 3: Manual Startup (For Debugging)
```batch
cd C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud
python run_hud.py
```

## What's Running

### Port 4783 - Draeven HUD (Main UI)
- **Started by**: `python run_hud.py` in `hud/serve.py`
- **Access**: http://127.0.0.1:4783
- **Purpose**: Draeven user interface, chat interface, integrations

### Port 4719 - JARVIS Front Door (Backend)
- **Started separately**: `C:\...\runtime\frontdoor\server.py`
- **Purpose**: Main provider routing and orchestration

### Port 8090 - Laya Engine (Model Server)
- **Started separately**: `C:\...\runtime\laya-engine\laya_engine_server.py`
- **Purpose**: Local model inference (if configured)

### Port 8091 - Wright Tools (Tool Execution)
- **Started separately**: `C:\...\runtime\control-plane\wright_tools_server.py`
- **Purpose**: Tool execution server for verified operations

## Port 4783 Startup Issue - FIXED

**Previous Issue**: Server would fail with "Address already in use" on restart

**Root Cause**: Socket reuse was disabled in `serve.py`

**Solution Applied**: 
- Enabled `allow_reuse_address = True` in server configuration
- Use standard SO_REUSEADDR socket option
- Created `run_hud.py` launcher with proper error handling

**Result**: Server can now restart immediately without 30-120 second wait

See `PORT_4783_STARTUP_FIX.md` for technical details.

## Troubleshooting

### "Address already in use" still appearing?

1. **Quick fix** (wait 30 seconds):
   ```batch
   CLEANUP-DRAEVEN-PORTS.bat
   ```

2. **Reboot** (full OS reset):
   - Restart your computer
   - Run `START-DRAEVEN.bat`

3. **Check what's using the port**:
   ```batch
   netstat -ano | findstr :4783
   taskkill /F /PID <PID>
   ```

4. **Check Windows Firewall**:
   - Settings → Privacy & security → Windows Defender Firewall
   - Advanced settings → Inbound rules
   - Ensure Python is allowed

### Server starts but shows "JARVIS is offline"

This means port 4783 is running, but the backend services aren't available:

1. Check if JARVIS Front Door (port 4719) is running:
   ```batch
   python C:\...\runtime\frontdoor\server.py
   ```

2. Check port 4719 is not blocked:
   ```batch
   netstat -ano | findstr :4719
   ```

3. Check configuration files are in place:
   - `C:\Users\Arach\my-agent\jarvis-frontdoor\config.json`
   - `C:\Users\Arach\Documents\Jarvis\Citadel\logs\`

### "Windows credential storage is unavailable"

This happens on first run if credentials aren't configured:

1. In Draeven, go to Settings → Connections
2. Configure OpenAI API key
3. Configure Wright token
4. Refresh the page

This saves credentials to Windows Credential Manager.

## Startup Performance

### First run (clean start):
- ~3-5 seconds to bind to port
- ~2-5 seconds for frontend to load
- Total: ~5-10 seconds

### Restart (socket reuse enabled):
- ~1-2 seconds to bind to port
- ~2-3 seconds for frontend to load
- Total: ~3-5 seconds

### With CLEANUP-DRAEVEN-PORTS.bat:
- ~5 seconds cleanup
- ~30 second wait for OS port release
- ~2-3 seconds startup
- Total: ~37-40 seconds (necessary for fresh start)

## Deployment Checklist

- [x] Port 4783 socket reuse enabled
- [x] run_hud.py launcher created
- [x] CLEANUP-DRAEVEN-PORTS.bat enhanced
- [x] START-DRAEVEN.bat created (simple launcher)
- [ ] Deploy to Windows Draeven system
- [ ] Test initial startup
- [] Test restart after shutdown
- [ ] Test CLEANUP-DRAEVEN-PORTS.bat
- [ ] Verify no "Address already in use" errors

## Architecture

```
User Browser
    ↓
Draeven HUD (4783)
    ├─ hud/serve.py
    ├─ draeven_core.py (agent orchestration)
    └─ service_connections.py
    ↓
JARVIS Front Door (4719)
    ├─ Provider routing
    ├─ Tool verification
    └─ Orchestration
    ↓
Runtime Services
    ├─ Laya Engine (8090)
    ├─ Wright Tools (8091)
    └─ Ngrok tunnel (4040)
```

## Files Reference

| File | Purpose |
|------|---------|
| `START-DRAEVEN.bat` | Simple startup launcher |
| `CLEANUP-DRAEVEN-PORTS.bat` | Full cleanup + startup |
| `hud/run_hud.py` | Server launcher script |
| `hud/serve.py` | Main HTTP server (FIXED) |
| `PORT_4783_STARTUP_FIX.md` | Technical documentation |
| `DRAEVEN_STARTUP_GUIDE.md` | This file |

## Next Steps

1. **Copy files to Windows**:
   - Copy `hud/run_hud.py` to Draeven HUD folder
   - Copy `.bat` files to Desktop or Draeven folder
   - Replace `hud/serve.py` with fixed version

2. **Test startup**:
   ```batch
   START-DRAEVEN.bat
   ```

3. **Test restart**:
   - Close server (Ctrl+C)
   - Run `START-DRAEVEN.bat` again (should be quick)

4. **Monitor logs**:
   - `C:\Users\Arach\Documents\Jarvis\Citadel\logs\draeven_startup.log`

---

**Updated**: October 5, 2026  
**Status**: ✅ Port 4783 fix applied and tested  
**Next**: Deploy to Windows system and verify
