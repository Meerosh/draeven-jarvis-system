#!/usr/bin/env python3
"""
Draeven HUD Server with CORS and local proxy to Jarvis backend.
Serves the HUD on http://127.0.0.1:4783/
Proxies /api/chat requests to http://localhost:8000/api/chat
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
import os
import sys

class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler with CORS and proxy support for localhost only."""

    def end_headers(self):
        # Allow CORS for localhost only (secure)
        self.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:4783')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '3600')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        """Handle POST requests. Proxy /api/chat to backend."""
        if self.path == '/api/chat':
            self._proxy_to_backend()
        else:
            self.send_error(404)

    def _proxy_to_backend(self):
        """Proxy the request to the Jarvis backend."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        try:
            # Forward to local Jarvis backend
            req = urllib.request.Request(
                'http://localhost:8000/api/chat',
                data=body,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(response_data.encode('utf-8'))
        except urllib.error.HTTPError as e:
            # Backend returned an error
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                'reply': f'Backend error: {e.reason}',
                'provider': 'error',
                'session_id': 'error'
            })
            self.wfile.write(error_response.encode('utf-8'))
        except urllib.error.URLError as e:
            # Connection error
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                'reply': f'Cannot reach Jarvis backend at localhost:8000. Is it running? Error: {str(e.reason)}',
                'provider': 'error',
                'session_id': 'error'
            })
            self.wfile.write(error_response.encode('utf-8'))
        except Exception as e:
            # Unexpected error
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({
                'reply': f'Proxy error: {str(e)}',
                'provider': 'error',
                'session_id': 'error'
            })
            self.wfile.write(error_response.encode('utf-8'))

    def log_message(self, format, *args):
        """Custom logging."""
        print(f'[{self.client_address[0]}] {format % args}')


def run_server(host='127.0.0.1', port=4783):
    """Start the Draeven HUD server."""
    os.chdir(Path(__file__).parent)
    server_address = (host, port)
    httpd = HTTPServer(server_address, CORSHTTPRequestHandler)

    print(f'\n╔═══════════════════════════════════════════════════════╗')
    print(f'║ Draeven HUD Server                                    ║')
    print(f'║ URL:     http://{host}:{port}/                ║')
    print(f'║ Backend: http://localhost:8000/api/chat               ║')
    print(f'║ CORS:    Localhost only (secure)                      ║')
    print(f'║ Press Ctrl+C to stop                                  ║')
    print(f'╚═══════════════════════════════════════════════════════╝\n')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n\nShutting down...')
        httpd.shutdown()
        print('Done.')


if __name__ == '__main__':
    run_server()
