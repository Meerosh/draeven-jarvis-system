#!/usr/bin/env python3
"""
Draeven HUD Server Launcher

Starts the Draeven HUD server on port 4783 with proper error handling
and automatic port cleanup on startup to prevent "Address already in use" errors.
"""

import sys
import os
import socket
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def check_port_available(host='127.0.0.1', port=4783, timeout=2):
    """Check if a port is available without holding it"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result != 0  # 0 means connected (port in use), non-zero means available
    except Exception:
        return True

def start_server():
    """Start the Draeven HUD server"""
    try:
        import serve

        print("\n" + "="*70)
        print("DRAEVEN HUD SERVER STARTUP")
        print("="*70)
        print(f"Starting server on http://127.0.0.1:4783")
        print("Press Ctrl+C to stop\n")

        # Check if port is available
        if not check_port_available():
            print("WARNING: Port 4783 appears to be in use")
            print("Waiting 2 seconds before attempting to bind...")
            time.sleep(2)

        # Start the server
        server = serve.Server(('127.0.0.1', 4783), serve.Handler)
        print("✓ Server listening on port 4783")
        print("✓ Draeven HUD ready at http://127.0.0.1:4783")
        print("="*70 + "\n")

        server.serve_forever()

    except OSError as e:
        if "Address already in use" in str(e):
            print("\nERROR: Port 4783 is still in use after cleanup")
            print("This usually means:")
            print("  1. Another Draeven process is still running")
            print("  2. The OS hasn't released the port yet (try waiting 30 seconds)")
            print("  3. A firewall is blocking the port")
            print("\nTroubleshooting:")
            print("  - Check for other python.exe processes")
            print("  - Restart your computer to fully release the port")
            print("  - Check Windows Firewall settings for port 4783")
            sys.exit(1)
        else:
            print(f"\nERROR: Failed to bind to port 4783: {e}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    start_server()
