"""Wright Connector tool webhook server (Phase 3 vertical slice).

Exposes the nine Build Brief tools as plain HTTP POST endpoints for an
ElevenLabs Conversational AI agent's "server tools" to call mid-conversation.
Same minimal stdlib-server pattern as laya-engine/laya_engine_server.py --
no new framework dependency.

  GET  /health          -> {"ok": true}
  POST /tools/<name>     -> one of the nine Build Brief tools; body is the
                             tool's JSON arguments (always includes call_id)

Local only by default (binds 127.0.0.1); exposed to ElevenLabs via an ngrok
tunnel pointed at this port (see WRIGHT_TOOLS_README.md).

Webhook authenticity: if ELEVENLABS_WEBHOOK_SECRET is set, every request's
raw body is checked against the X-ElevenLabs-Signature header (HMAC-SHA256)
before processing. NOT YET VERIFIED against ElevenLabs' actual current
header/algorithm -- confirm this against the live dashboard before relying
on it (see the design doc's "still open" list). If the secret isn't set,
requests are processed without verification and a warning is logged --
fine for local testing, not for anything public-facing.
"""
import hashlib
import hmac
import json
import os
import sys
import ctypes
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dotenv import load_dotenv

import wright_control_plane as wcp

load_dotenv(Path(__file__).parent / ".env")

PORT = int(os.environ.get("WRIGHT_TOOLS_PORT", "8091"))
RAW_EVENTS = Path(__file__).parent / "raw_webhook_events"

TOOLS = {
    "load_industry_profile": lambda a: wcp.tool_load_industry_profile(a["call_id"], a["industry"]),
    "get_business_information": lambda a: wcp.tool_get_business_information(a["call_id"], a["question"]),
    "capture_lead": lambda a: wcp.tool_capture_lead(a["call_id"], a.get("fields", {})),
    "check_demo_availability": lambda a: wcp.tool_check_demo_availability(a["call_id"], a["preferred_time"]),
    "request_demo_appointment": lambda a: wcp.tool_request_demo_appointment(a["call_id"], a["confirmed_time"]),
    "send_demo_customer_sms": lambda a: wcp.tool_send_demo_customer_sms(a["call_id"]),
    "send_demo_owner_alert": lambda a: wcp.tool_send_demo_owner_alert(a["call_id"], a.get("reason", "")),
    "escalate_to_demo_human": lambda a: wcp.tool_escalate_to_demo_human(a["call_id"], a.get("reason", "")),
    "record_demo_receipt": lambda a: wcp.tool_record_demo_receipt(a["call_id"]),
}

class _Credential(ctypes.Structure):
    _fields_ = [("Flags",wintypes.DWORD),("Type",wintypes.DWORD),("TargetName",wintypes.LPWSTR),
        ("Comment",wintypes.LPWSTR),("LastWritten",wintypes.FILETIME),("CredentialBlobSize",wintypes.DWORD),
        ("CredentialBlob",ctypes.POINTER(ctypes.c_ubyte)),("Persist",wintypes.DWORD),
        ("AttributeCount",wintypes.DWORD),("Attributes",ctypes.c_void_p),("TargetAlias",wintypes.LPWSTR),
        ("UserName",wintypes.LPWSTR)]

def protected_tool_token() -> str:
    pointer=ctypes.POINTER(_Credential)()
    api=ctypes.WinDLL("Advapi32.dll",use_last_error=True)
    read=api.CredReadW
    read.argtypes=(wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p)
    read.restype=wintypes.BOOL
    free=api.CredFree
    free.argtypes=(ctypes.c_void_p,)
    if not read("Draeven/Wright/Tool-Token",1,0,ctypes.byref(pointer)):
        return ""
    try:
        item=pointer.contents
        return ctypes.string_at(item.CredentialBlob,item.CredentialBlobSize).decode("utf-16-le")
    finally:
        free(pointer)

def tool_request_authorized(header) -> bool:
    expected=protected_tool_token()
    return bool(expected and header and hmac.compare_digest(expected,header))


def verify_signature(raw_body: bytes, signature_header) -> bool:
    secret = os.environ.get("ELEVENLABS_WEBHOOK_SECRET")
    if not secret:
        return False
    if not signature_header:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def store_raw_event(tool_name: str, raw_body: bytes) -> None:
    RAW_EVENTS.mkdir(parents=True, exist_ok=True)
    stamp = wcp.now().replace(":", "-")
    (RAW_EVENTS / f"{stamp}_{tool_name}.json").write_bytes(raw_body)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True, "service": "wright-tools",
                "webhook_verification": bool(protected_tool_token()),
                "twilio_configured": all(wcp.twilio_credentials().get(name) for name in
                    ("account_sid", "auth_token", "from_number"))})
        self._send(404, {"error": "unknown path"})

    def do_POST(self):
        if not self.path.startswith("/tools/"):
            return self._send(404, {"error": "unknown path"})
        tool_name = self.path[len("/tools/"):]
        handler = TOOLS.get(tool_name)
        if handler is None:
            return self._send(404, {"error": f"unknown tool '{tool_name}'"})

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length else b"{}"

        if not protected_tool_token():
            return self._send(503, {"error": "tool authentication is unavailable; configure the protected Wright token"})
        if not tool_request_authorized(self.headers.get("X-Draeven-Tool-Token")):
            return self._send(401, {"error": "invalid tool token"})

        store_raw_event(tool_name, raw_body)

        try:
            args = json.loads(raw_body or b"{}")
            if "call_id" not in args:
                return self._send(400, {"error": "missing field 'call_id'"})
            result = handler(args)
            self._send(200, result)
        except KeyError as exc:
            self._send(400, {"error": f"missing field {exc}"})
        except wcp.ControlPlaneError as exc:
            self._send(409, {"status": "failed", "reason": str(exc)})
        except Exception as exc:  # keep the call alive with a truthful failure, never a silent 500
            self._send(500, {"status": "failed", "reason": repr(exc)})

    def log_message(self, fmt, *args):
        sys.stderr.write("[wright-tools] " + fmt % args + "\n")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Wright Connector tool server ready on http://127.0.0.1:{PORT}")
    print("Tunnel this port with ngrok before configuring the ElevenLabs agent's tool webhooks.")
    server.serve_forever()
