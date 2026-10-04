"""ElevenLabs adapter. Credentials stay encrypted on this Windows account."""
from pathlib import Path
import ctypes, os, json, re, urllib.request, urllib.error, threading
from ctypes import wintypes
KEY_FILE=Path.home()/'.config'/'draeven'/'elevenlabs.key'
LOCK=threading.Lock()
CLIENT=urllib.request.build_opener(urllib.request.ProxyHandler({}))
class VoiceError(Exception):pass
class Blob(ctypes.Structure):
    _fields_=[('size',wintypes.DWORD),('data',ctypes.POINTER(ctypes.c_ubyte))]
def protect(data, decrypt=False):
    buf=ctypes.create_string_buffer(data);source=Blob(len(data),ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte)));out=Blob()
    function=ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    function.argtypes=[ctypes.POINTER(Blob),ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(Blob)]
    function.restype=wintypes.BOOL
    if not function(ctypes.byref(source),None,None,None,None,1,ctypes.byref(out)):
        raise VoiceError('Windows could not access the saved credential.')
    try:return ctypes.string_at(out.data,out.size)
    finally:
        ctypes.windll.kernel32.LocalFree.argtypes=[ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree(ctypes.cast(out.data,ctypes.c_void_p))
def get_key():
    key=os.environ.get('ELEVENLABS_API_KEY','').strip()
    if key:return key
    try:return protect(KEY_FILE.read_bytes(),True).decode('utf-8')
    except FileNotFoundError:return ''
    except Exception:raise VoiceError('Saved ElevenLabs key could not be opened. Run Connect ElevenLabs again.')
def save_key(key):
    KEY_FILE.parent.mkdir(parents=True,exist_ok=True)
    encrypted=protect(key.encode('utf-8'))
    temporary=KEY_FILE.with_suffix('.tmp');temporary.write_bytes(encrypted);temporary.replace(KEY_FILE)
def call(path,payload=None,key=None):
    key=key or get_key()
    if not key:raise VoiceError('Run Connect ElevenLabs on your desktop to add your API key privately.')
    body=None if payload is None else json.dumps(payload).encode('utf-8')
    req=urllib.request.Request('https://api.elevenlabs.io'+path,body,{'xi-api-key':key,'Content-Type':'application/json'})
    try:
        with CLIENT.open(req,timeout=60) as response:
            return response.read(),response.headers.get_content_type()
    except urllib.error.HTTPError as e:
        errors={401:'ElevenLabs rejected the API key.',403:'The API key lacks permission for this operation.',429:'ElevenLabs quota or request limit reached.'}
        raise VoiceError(errors.get(e.code,f'ElevenLabs request failed (HTTP {e.code}). No automatic retry was sent.')) from None
    except Exception:raise VoiceError('Could not reach ElevenLabs. Please try again later.') from None
def voices(key=None):
    raw,_=call('/v2/voices?page_size=100',key=key)
    try:
        data=json.loads(raw)
        result=[{'id':v['voice_id'],'name':v['name'],'labels':v.get('labels') or {},'description':v.get('description') or ''} for v in data.get('voices',[])]
        def score(v):
            labels=v['labels'];description=(v['name']+' '+v['description']+' '+str(labels)).lower()
            return (20 if labels.get('gender')=='male' else 0)+sum(4 for w in ('deep','calm','warm','baritone','resonant') if w in description)
        result.sort(key=score,reverse=True)
        return {'voices':result,'has_more':bool(data.get('has_more'))}
    except Exception:raise VoiceError('ElevenLabs returned an unexpected voice list.') from None
def synthesize(text,voice_id):
    if not isinstance(text,str) or not 1<=len(text.strip())<=5000:raise VoiceError('Speech text must be between 1 and 5000 characters.')
    if not isinstance(voice_id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',voice_id):raise VoiceError('Choose an ElevenLabs voice first.')
    if not LOCK.acquire(False):raise VoiceError('A voice request is already running. Please wait.')
    try:
        audio,kind=call('/v1/text-to-speech/'+voice_id+'?output_format=mp3_44100_128',{'text':text.strip(),'model_id':'eleven_multilingual_v2','voice_settings':{'stability':0.6,'similarity_boost':0.75}})
        if kind not in ('audio/mpeg','audio/mp3') or not audio:raise VoiceError('ElevenLabs did not return MP3 audio.')
        return audio
    finally:LOCK.release()
