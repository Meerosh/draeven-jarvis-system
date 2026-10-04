"""JARVIS Laya engine: thin local HTTP wrapper around the REAL laya.Router.
Replaces the keyword mock in Documents\\Jarvis\\laya_server.py (left untouched until this passes).

  GET  /health    -> {"ok": true, "model_loaded": bool}
  POST /predict   -> body {"state": str, "questions": [...], "model": optional str}
                     returns laya's own result dict (answers with choice/confidence/score)
  GET  /selftest  -> runs a built-in triage question set on a sample O&L support message

Port 8090 (the mock uses 8080). Local only: binds 127.0.0.1.
"""
import json, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import socket as _socket

class XServer(ThreadingHTTPServer):
    """Refuses to share its port (Windows would otherwise let a 2nd copy bind too)."""
    allow_reuse_address = False
    def server_bind(self):
        if hasattr(_socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(_socket.SOL_SOCKET, _socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

PORT = int(os.environ.get("LAYA_PORT", "8090"))
_router, _lock = None, threading.Lock()

def router():
    global _router
    with _lock:
        if _router is None:
            import laya
            _router = laya.Router(preload=False)  # loads only the model a request needs (English), ~1/3 the memory
        return _router

def jsonable(o):
    try:
        return float(o)
    except Exception:
        return str(o)

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, default=jsonable).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True, "engine": "laya (real)", "model_loaded": _router is not None})
        if self.path == "/selftest":
            try:
                import laya
                qs = laya.triage_questions()
                st = "Etsy buyer: planner hyperlinks don't work in Goodnotes on my iPad."
                return self._send(200, {"state": st, "result": router().predict(st, qs)})
            except Exception as e:
                return self._send(500, {"error": repr(e)})
        self._send(404, {"error": "unknown path"})

    def do_POST(self):
        if self.path != "/predict":
            return self._send(404, {"error": "unknown path"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            kw = {"model": req["model"]} if req.get("model") else {}
            self._send(200, router().predict(req["state"], req["questions"], **kw))
        except KeyError as e:
            self._send(400, {"error": f"missing field {e}"})
        except Exception as e:
            self._send(500, {"error": repr(e)})

    def log_message(self, fmt, *args):
        sys.stderr.write("[laya-engine] " + fmt % args + "\n")

def _status(msg):
    import datetime
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "laya_engine_status.txt"), "w", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")

if __name__ == "__main__":
    try:
        srv = XServer(("127.0.0.1", PORT), H)
    except OSError:
        _status(f"ALREADY RUNNING (port {PORT} in use) - nothing to do")
        sys.exit(0)
    _status("LOADING model...")
    print("Loading real Laya model (first run downloads it)...")
    router()
    _status(f"READY on http://127.0.0.1:{PORT}")
    print(f"JARVIS Laya engine ready on http://127.0.0.1:{PORT}")
    srv.serve_forever()
