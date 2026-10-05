# Port 4783 Startup Issue - Root Cause and Fix

## Problem Summary

Draeven HUD fails to start with error:
```
OSError: [WinError 10048] Only one usage of each socket address (protocol/IP port combination) per socket is normally permitted
```

This occurs when trying to restart the service, even after all processes are killed.

## Root Cause Analysis

The issue was in `hud/serve.py` lines 48-53:

```python
class Server(ThreadingHTTPServer):
    allow_reuse_address = False  # ❌ PROBLEM: Prevents socket reuse
    def server_bind(self):
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)  # ❌ Even more restrictive
        super().server_bind()
```

**Why this is a problem:**

1. **TCP TIME_WAIT State**: When a server closes a connection, the OS enters TIME_WAIT state (typically 30-120 seconds) before fully releasing the socket
2. **`allow_reuse_address = False`**: This prevents the Python server from binding to a port that's in TIME_WAIT state
3. **`SO_EXCLUSIVEADDRUSE`**: This Windows-specific socket option is even MORE restrictive than SO_REUSEADDR, preventing any reuse
4. **Result**: After a restart or crash, the server cannot bind to port 4783 until the OS timeout expires

## The Fix

### Change 1: Fix serve.py (Permanent Solution)

```python
class Server(ThreadingHTTPServer):
    allow_reuse_address = True  # ✅ Allow socket reuse after TIME_WAIT
    def server_bind(self):
        if hasattr(socket, 'SO_REUSEADDR'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # ✅ Allows TIME_WAIT reuse
        super().server_bind()
```

**Why this works:**
- `allow_reuse_address = True` enables SO_REUSEADDR on all platforms
- SO_REUSEADDR tells the OS "it's safe to bind to this port even if it's in TIME_WAIT state"
- This is the standard Python HTTPServer configuration and is used by Flask, Django, etc.

### Change 2: Create run_hud.py (Proper Launcher)

New file: `hud/run_hud.py`

This launcher:
- Starts the server with proper error handling
- Provides clear feedback if port is still in use
- Includes timeout logic and port availability checks
- Gives helpful troubleshooting information

### Change 3: Improve CLEANUP-DRAEVEN-PORTS.bat (Windows Startup)

Enhanced batch script that:
- Terminates existing processes first
- Releases all service ports (4783, 4719, 4091, 8090, 8091)
- Waits 30 seconds for OS to fully release the port
- Provides detailed logging
- Includes helpful error messages

## Testing the Fix

### On Windows:

1. **First startup** (no processes running):
   ```batch
   python hud/run_hud.py
   ```
   Should start immediately and bind to port 4783

2. **Restart test** (immediate restart):
   ```batch
   # Terminal 1:
   python hud/run_hud.py
   
   # After server starts, press Ctrl+C
   
   # Immediately run again (within 1 second):
   python hud/run_hud.py
   ```
   Should succeed on restart (with new SO_REUSEADDR setting)

3. **Full cleanup test**:
   ```batch
   CLEANUP-DRAEVEN-PORTS.bat
   ```
   Should cleanly kill processes, wait, and start fresh

## How It Works: Socket Reuse

```
Old behavior (allow_reuse_address = False):
  - Server binds to :4783
  - Server crashes/stops
  - Socket enters TIME_WAIT (30-120 sec)
  - Restart attempt fails: "Address already in use"
  - Must wait 30-120 seconds

New behavior (allow_reuse_address = True):
  - Server binds to :4783
  - Server crashes/stops
  - Socket enters TIME_WAIT (OS still sees it as "in use")
  - Restart attempt succeeds: OS allows SO_REUSEADDR binding
  - Immediate restart possible
```

## Platform Compatibility

- **Windows**: SO_REUSEADDR works correctly (unlike the old SO_EXCLUSIVEADDRUSE conflict)
- **Linux/Mac**: SO_REUSEADDR is standard and required for server restart
- **Both**: This is how standard web servers (Flask, Django, httpd) handle port binding

## Verification

After applying fix, verify with:

```python
# test_port_reuse.py
import socket
import sys

def can_bind(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('127.0.0.1', port))
            return True
    except:
        return False

print(f"Port 4783 available: {can_bind(4783)}")
```

## If Issue Persists

If restarting still fails:

1. **System is still holding the port** (OS-level TIME_WAIT):
   - Wait 60 seconds (full timeout)
   - Or restart your computer

2. **Another service is using port 4783**:
   ```batch
   netstat -ano | findstr :4783
   taskkill /F /PID <PID>
   ```

3. **Firewall blocking**:
   - Windows Firewall → Allow app through firewall
   - Ensure Python is allowed on private networks

4. **Invalid socket state** (should not happen with fix):
   ```batch
   # Full reset
   CLEANUP-DRAEVEN-PORTS.bat
   timeout /t 60  # Wait full 60 seconds
   CLEANUP-DRAEVEN-PORTS.bat  # Try again
   ```

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Socket reuse | ❌ Blocked | ✅ Enabled |
| Restart wait time | 30-120 seconds | Immediate |
| First run | ✓ Works | ✓ Works |
| Restart after crash | ✗ Fails | ✓ Works |
| Configuration | Non-standard | Standard (Flask/Django) |

## Files Changed

- ✅ `hud/serve.py` - Fixed socket reuse settings
- ✅ `hud/run_hud.py` - Created proper launcher
- ✅ `CLEANUP-DRAEVEN-PORTS.bat` - Enhanced with logging and retry logic

---

**Date Fixed**: October 5, 2026  
**Root Cause**: `allow_reuse_address = False` preventing TIME_WAIT reuse  
**Solution**: Use standard `allow_reuse_address = True` with SO_REUSEADDR  
**Impact**: Draeven can now restart immediately without 30-120 second wait
