"""Local Draeven adapter for the canonical, draft-only JARVIS Front Door."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, unquote
import html, json, re, secrets, socket, threading, time, urllib.request
import eleven_voice
import service_connections
from draeven_core import DraevenCore
from private_credentials import (openai_key_is_configured, save_openai_key,
    save_wright_token, wright_token_is_configured, save_twilio_connection,
    save_shopify_connection, save_etsy_connection)

ROOT = Path(__file__).resolve().parent
FRONTDOOR = 'http://127.0.0.1:4719'
LAYA = 'http://127.0.0.1:8090'
WRIGHT = 'http://127.0.0.1:8091'
NGROK = 'http://127.0.0.1:4040'
CLIENT = urllib.request.build_opener(urllib.request.ProxyHandler({}))
CHAT_LOCK = threading.Lock()
HOSTS = {'127.0.0.1:4783', 'localhost:4783'}
ORIGINS = {'http://' + host for host in HOSTS}
WRIGHT_TOOL_MARKER = ROOT / 'wright_elevenlabs_tools_verified.json'
ETSY_OAUTH_FLOW = {}
ETSY_OAUTH_LOCK = threading.Lock()
CORE = DraevenCore(Path.home() / '.config' / 'draeven' / 'conversation.json')

def upstream(path, body=None, timeout=5):
    data = None if body is None else json.dumps(body).encode('utf-8')
    req = urllib.request.Request(FRONTDOOR + path, data, {'Content-Type':'application/json'})
    with CLIENT.open(req, timeout=timeout) as response:
        return json.load(response)

def local_health(base, path='/health'):
    try:
        with CLIENT.open(base + path, timeout=2) as response:
            return json.load(response)
    except Exception:
        return {}

def wright_tools_verified(ngrok):
    try:
        marker = json.loads(WRIGHT_TOOL_MARKER.read_text(encoding='utf-8'))
        public_urls = {item.get('public_url') for item in ngrok.get('tunnels', [])}
        return marker.get('tool_count') == 9 and marker.get('public_url') in public_urls
    except (OSError, ValueError, TypeError):
        return False

class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    def server_bind(self):
        # Enable socket reuse to allow immediate restart after shutdown
        # This prevents "Address already in use" errors on Windows and Unix
        if hasattr(socket, 'SO_REUSEADDR'):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()
    def local_request(self):
        return (self.headers.get('Host') in HOSTS
                and self.headers.get('Origin') in (None, *ORIGINS)
                and self.headers.get('Sec-Fetch-Site') != 'cross-site')
    def send_json(self, status, payload):
        data = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if self.command != 'HEAD':
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
    def send_html(self, status, html):
        data = html.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path == "/api/connections/etsy/callback":
            query = parse_qs(urlsplit(self.path).query)
            state = query.get('state', [''])[0]
            error = query.get('error_description', query.get('error', ['']))[0]
            with ETSY_OAUTH_LOCK:
                flow = ETSY_OAUTH_FLOW.pop(state, None)
            try:
                if error:
                    raise service_connections.ConnectionError(error)
                if not flow or int(flow.get('created_at', '0')) < int(time.time()) - 600:
                    raise service_connections.ConnectionError('This Etsy authorization request expired. Start it again from Draeven.')
                service_connections.finish_etsy_oauth(query.get('code', [''])[0], flow)
                return self.send_html(200, '<!doctype html><meta charset="utf-8"><title>Etsy connected</title><style>body{font:18px system-ui;background:#0d1112;color:#f2dfb4;padding:4rem;max-width:42rem;margin:auto}h1{color:#e1a85d}</style><h1>Etsy is connected to Draeven.</h1><p>You may close this tab and return to Draeven.</p>')
            except service_connections.ConnectionError as exc:
                return self.send_html(400, '<!doctype html><meta charset="utf-8"><title>Etsy connection failed</title><style>body{font:18px system-ui;background:#0d1112;color:#f2dfb4;padding:4rem;max-width:42rem;margin:auto}h1{color:#e1a85d}</style><h1>Etsy connection failed.</h1><p>'+html.escape(str(exc))+'</p><p>Return to Draeven and try again.</p>')
        if self.path == "/api/connections/openai":
            if not self.local_request():
                self.send_json(403, {"error": "Local requests only."})
                return
            try:
                self.send_json(200, {"configured": openai_key_is_configured()})
            except OSError:
                self.send_json(500, {"configured": False, "error": "Windows credential storage is unavailable."})
            return
        if self.path == "/api/connections/wright":
            if not self.local_request():
                return self.send_json(403, {"error":"Local requests only."})
            return self.send_json(200, {"configured":wright_token_is_configured()})
        if self.path == "/api/connections/services":
            if not self.local_request():
                return self.send_json(403, {"error":"Local requests only."})
            return self.send_json(200, service_connections.status())
        if self.path == "/api/core/status":
            if not self.local_request():
                return self.send_json(403, {"error":"Local requests only."})
            return self.send_json(200, CORE.status())
        if not self.local_request():
            return self.send_json(403, {'error':'Local access only.'})
        if path == '/api/voice/voices':
            try:return self.send_json(200,eleven_voice.voices())
            except eleven_voice.VoiceError as error:return self.send_json(503,{'error':str(error)})
        if path == '/api/health':
            try:
                # The HUD is always healthy as long as this endpoint is responding
                # Try to reach backend services, but don't fail if they're unavailable
                health = {}
                try:
                    health = upstream('/health')
                    if health.get('ok') is not True:
                        health = {}
                except Exception:
                    # Backend is unreachable; that's OK, report it in services status
                    pass

                laya = local_health(LAYA)
                wright = local_health(WRIGHT)
                ngrok = local_health(NGROK, '/api/tunnels')

                return self.send_json(200, {'app':'draeven-hud', 'ok':True,
                    'backend':'JARVIS Front Door', 'mode':'approval-gated',
                    'model_verified':False, 'notes_indexed':health.get('notes_indexed'),
                    'providers':health.get('providers', {}), 'usage':health.get('usage', {}),
                    'services':{
                        'frontdoor': {'ready': bool(health)},
                        'core': {'ready': True, 'routing': 'tool-first'},
                        'laya': {'ready': laya.get('ok') is True and laya.get('model_loaded') is True},
                        'wright': {'ready': wright.get('ok') is True,
                            'webhook_verification': wright.get('webhook_verification') is True,
                            'twilio_configured': wright.get('twilio_configured') is True,
                            'public_tunnel': bool(ngrok.get('tunnels')),
                            'elevenlabs_tools': wright_tools_verified(ngrok)},
                        'voice': {'ready': bool(eleven_voice.get_key())},
                        'vault': {'ready': health.get('notes_indexed', 0) > 0},
                    }})
            except Exception:
                # Only return 503 if there's an unexpected error; HUD running = healthy
                return self.send_json(200, {'app':'draeven-hud', 'ok':True,
                    'backend':'JARVIS Front Door', 'mode':'approval-gated',
                    'model_verified':False, 'error':'Backend services unavailable'})
        allowed = path in {'/', '/index.html', '/styles.css', '/snapshot.js', '/js/main.js', '/js/voice.js'}
        if path.startswith('/assets/'):
            asset = (ROOT / path.lstrip('/')).resolve()
            allowed = asset.is_relative_to(ROOT / 'assets') and asset.suffix.lower() in {'.png','.jpg','.jpeg','.webp','.svg','.ico'}
        if not allowed:
            return self.send_error(404)
        if self.command == 'HEAD':
            super().do_HEAD()
        else:
            super().do_GET()
    def do_HEAD(self):
        self.do_GET()
    def do_POST(self):
        if self.path == "/api/connections/etsy/authorize":
            if not self.local_request():
                return self.send_json(403, {"error":"Local requests only."})
            try:
                url, flow = service_connections.begin_etsy_oauth()
                with ETSY_OAUTH_LOCK:
                    ETSY_OAUTH_FLOW.clear()
                    ETSY_OAUTH_FLOW[flow['state']] = flow
                return self.send_json(200, {"url":url})
            except service_connections.ConnectionError as exc:
                return self.send_json(400, {"error":str(exc)})
        if self.path == "/api/connections/openai":
            if not self.local_request():
                self.send_json(403, {"error": "Local requests only."})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 8192:
                    raise ValueError("Invalid request size.")
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError("Invalid request.")
                save_openai_key(str(body.get("api_key", "")))
                self.send_json(200, {"configured": True, "status": "saved"})
            except ValueError as exc:
                self.send_json(400, {"configured": False, "error": str(exc)})
            except OSError:
                self.send_json(500, {"configured": False, "error": "Windows could not save the credential."})
            return
        if self.path == "/api/connections/wright":
            if not self.local_request():
                return self.send_json(403, {"error":"Local requests only."})
            token = secrets.token_urlsafe(32)
            try:
                save_wright_token(token)
                return self.send_json(200, {"configured":True, "token":token,
                    "header":"X-Draeven-Tool-Token"})
            except OSError:
                return self.send_json(500, {"configured":False,"error":"Windows could not save the Wright token."})
        if self.path == "/api/connections/service":
            if not self.local_request():
                return self.send_json(403, {"error":"Local requests only."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > 16384:
                    raise ValueError("Invalid request size.")
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict):
                    raise ValueError("Invalid request.")
                service = body.get("service")
                values = body.get("values")
                if not isinstance(values, dict):
                    raise ValueError("Connection fields are missing.")
                if service == "twilio":
                    result = service_connections.validate_twilio(values)
                    if not result.get("phone_route"):
                        result = service_connections.repair_twilio_route(values)
                    save_twilio_connection(values)
                elif service == "shopify":
                    result = service_connections.validate_shopify(values)
                    save_shopify_connection(values)
                elif service == "etsy":
                    result = service_connections.validate_etsy(values)
                    save_etsy_connection(values)
                else:
                    raise ValueError("Unknown service.")
                return self.send_json(200, result)
            except (ValueError, service_connections.ConnectionError) as exc:
                return self.send_json(400, {"configured":False, "verified":False, "error":str(exc)})
            except OSError:
                return self.send_json(500, {"configured":False, "verified":False,
                    "error":"Windows could not save the connection."})
        if not self.local_request():
            return self.send_json(403, {'error':'Local access only.'})
        if self.path not in ('/api/chat','/api/confirm','/api/voice/speak'):
            return self.send_json(404, {'error':'Not found.'})
        if self.headers.get_content_type() != 'application/json':
            return self.send_json(415, {'error':'Send application/json.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                return self.send_json(413, {'error':'Message is too large or empty.'})
            data = json.loads(self.rfile.read(length))
            if self.path == '/api/voice/speak':
                if not isinstance(data,dict):return self.send_json(400,{'error':'Invalid voice request.'})
                try:
                    audio=eleven_voice.synthesize(data.get('text'),data.get('voice_id'))
                    self.send_response(200)
                    self.send_header('Content-Type','audio/mpeg')
                    self.send_header('Content-Length',str(len(audio)))
                    self.end_headers()
                    try:self.wfile.write(audio)
                    except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
                    return
                except eleven_voice.VoiceError as error:return self.send_json(503,{'error':str(error)})
            if self.path == '/api/confirm':
                confirm_id = data.get('confirm_id') if isinstance(data,dict) else None
                if not isinstance(confirm_id,str) or not confirm_id:
                    return self.send_json(400,{'error':'Missing approval identifier.'})
                core_reply = CORE.confirm(confirm_id)
                if core_reply:
                    return self.send_json(200, {'reply':core_reply.answer, 'provider':core_reply.route,
                        'receipt':core_reply.receipt, 'mode':core_reply.mode})
                result = upstream('/confirm', {'id':confirm_id}, timeout=720)
                answer = result.get('answer')
                if not isinstance(answer,str) or not answer.strip():
                    raise ValueError('Missing approval response')
                return self.send_json(200, {'reply':answer, 'provider':result.get('route','JARVIS'),
                    'receipt':result.get('receipt'), 'mode':'approval-gated'})
            message = data.get('message') if isinstance(data, dict) else None
            if not isinstance(message, str) or not message.strip() or len(message) > 16000:
                return self.send_json(400, {'error':'Enter a message of 1-16000 characters.'})
        except (ValueError, UnicodeDecodeError):
            return self.send_json(400, {'error':'Invalid JSON request.'})
        if not CHAT_LOCK.acquire(blocking=False):
            return self.send_json(409, {'error':'JARVIS is still answering. Please wait.'})
        try:
            # Draeven Core routes verified tools before using one model route.
            agent = data.get('agent') if isinstance(data,dict) else None
            if agent is not None and agent not in {'lucien','garrick','vaelis','azrath'}:
                return self.send_json(400, {'error':'Unknown council agent.'})
            reply = CORE.respond(message.strip(), agent, upstream)
            payload = {'reply':reply.answer, 'provider':reply.route, 'mode':reply.mode}
            if reply.receipt:payload['receipt']=reply.receipt
            if reply.confirm_id:
                payload['confirm_id']=reply.confirm_id;payload['approval_required']=True
            return self.send_json(200,payload)
        except (TimeoutError, socket.timeout):
            self.send_json(504, {'error':'JARVIS timed out. It may still be finishing; check before retrying.'})
        except Exception:
            self.send_json(502, {'error':'JARVIS could not return an answer. Open Draeven again and check Connections.'})
        finally:
            CHAT_LOCK.release()
    def list_directory(self, path):
        self.send_error(403, 'Directory listing disabled')

if __name__ == '__main__':
    print('Draeven: http://127.0.0.1:4783 | JARVIS Front Door: 4719', flush=True)
    Server(('127.0.0.1', 4783), Handler).serve_forever()
