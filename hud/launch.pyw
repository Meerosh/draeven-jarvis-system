"""Start the canonical JARVIS Front Door and Draeven, then open the HUD."""
from pathlib import Path
import ctypes, json, socket, subprocess, sys, time, urllib.request, urllib.error, webbrowser

ROOT = Path(__file__).resolve().parent
FRONTDOOR = ROOT.parent / 'runtime' / 'frontdoor' / 'server.py'
LAYA = Path.home() / 'my-agent' / 'laya-engine' / 'laya_engine_server.py'
WRIGHT = Path.home() / 'my-agent' / 'jarvis-control-plane' / 'wright_tools_server.py'
CLIENT = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def health(port, path):
    try:
        with CLIENT.open(f'http://127.0.0.1:{port}{path}',timeout=10) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            return json.load(error)
        except Exception:
            return {}
    except Exception:
        return {}

def listening(port):
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=1):
            return True
    except OSError:
        return False

def start(script, log_name):
    if not script.is_file():
        raise RuntimeError(f'Missing service file: {script}')
    with (ROOT / log_name).open('a',encoding='utf-8') as log:
        return subprocess.Popen([sys.executable,'-u',str(script)],cwd=script.parent,
            stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))

def ensure(port,path,script,log_name,valid):
    if valid(health(port,path)):
        return
    if listening(port):
        # The service may still be loading its model (it binds the port first), so wait for it.
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            if valid(health(port,path)):
                return
            time.sleep(.5)
        raise RuntimeError(f'Port {port} is occupied but the expected service is not ready after 90 seconds. Check {log_name}; no process was stopped.')
    process=start(script,log_name)
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        if valid(health(port,path)):
            return
        if process.poll() is not None:
            break
        time.sleep(.5)
    raise RuntimeError(f'Service on port {port} did not become ready. See {ROOT / log_name}.')

def main():
    ensure(8090,'/health',LAYA,'laya-start.log',lambda h:h.get('ok') is True and h.get('model_loaded') is True)
    ensure(8091,'/health',WRIGHT,'wright-start.log',lambda h:h.get('ok') is True and h.get('service')=='wright-tools')
    ensure(4719,'/health',FRONTDOOR,'jarvis-start.log',lambda h:h.get('ok') is True and 'notes_indexed' in h)
    ensure(4783,'/api/health',ROOT/'serve.py','preview-server.log',lambda h:h.get('app')=='draeven-hud')
    webbrowser.open('http://127.0.0.1:4783/')

if __name__=='__main__':
    try:
        main()
    except Exception as error:
        ctypes.windll.user32.MessageBoxW(0,str(error),'Draeven could not start',0x10)
