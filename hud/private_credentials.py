"""Store Draeven API credentials in Windows Credential Manager."""
from __future__ import annotations
import ctypes
import json
from ctypes import wintypes
import sys

CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ERROR_NOT_FOUND = 1168
OPENAI_TARGET = "Draeven/OpenAI/API-Key"
WRIGHT_TARGET = "Draeven/Wright/Tool-Token"
TWILIO_TARGET = "Draeven/Twilio/Connection"
SHOPIFY_TARGET = "Draeven/Shopify/Connection"
ETSY_TARGET = "Draeven/Etsy/Connection"
ETSY_OAUTH_TARGET = "Draeven/Etsy/OAuth"

# Try to load Windows credential manager API
_win_available = False
_api = None
_write = None
_read = None
_free = None

if sys.platform == 'win32':
    try:
        class CREDENTIALW(ctypes.Structure):
            _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
                ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
                ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
                ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR),
                ("UserName", wintypes.LPWSTR)]

        PCREDENTIALW = ctypes.POINTER(CREDENTIALW)
        _api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
        _write = _api.CredWriteW
        _write.argtypes = (ctypes.POINTER(CREDENTIALW), wintypes.DWORD)
        _write.restype = wintypes.BOOL
        _read = _api.CredReadW
        _read.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(PCREDENTIALW))
        _read.restype = wintypes.BOOL
        _free = _api.CredFree
        _free.argtypes = (ctypes.c_void_p,)
        _win_available = True
    except Exception as e:
        # Windows Credential Manager not available; will use fallback
        pass

def _valid(value: str) -> str:
    key = value.strip()
    if not key.startswith("sk-") or len(key) < 20 or any(ch.isspace() for ch in key):
        raise ValueError("Enter a valid OpenAI secret API key.")
    if len(key.encode("utf-16-le")) > 5120:
        raise ValueError("The API key is too long.")
    return key

def _save(target: str, value: str, comment: str) -> None:
    if not _win_available:
        raise OSError("Windows credential storage is unavailable on this system.")
    blob = value.encode("utf-16-le")
    buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    credential = CREDENTIALW(Type=CRED_TYPE_GENERIC, TargetName=target,
        Comment=comment, CredentialBlobSize=len(blob),
        CredentialBlob=ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)),
        Persist=CRED_PERSIST_LOCAL_MACHINE, UserName="Draeven")
    if not _write(ctypes.byref(credential), 0):
        raise ctypes.WinError(ctypes.get_last_error())

def _load(target: str) -> str | None:
    if not _win_available:
        return None
    credential = PCREDENTIALW()
    if not _read(target, CRED_TYPE_GENERIC, 0, ctypes.byref(credential)):
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return None
        raise ctypes.WinError(error)
    try:
        item = credential.contents
        return ctypes.string_at(item.CredentialBlob, item.CredentialBlobSize).decode("utf-16-le")
    finally:
        _free(credential)

def _save_bundle(target: str, values: dict[str, str], required: tuple[str, ...], comment: str) -> None:
    clean = {key: str(value).strip() for key, value in values.items()}
    if any(not clean.get(key) for key in required):
        raise ValueError("Complete every required field.")
    encoded = json.dumps(clean, separators=(",", ":"))
    if len(encoded.encode("utf-16-le")) > 5120:
        raise ValueError("The connection details are too long.")
    _save(target, encoded, comment)

def _load_bundle(target: str) -> dict[str, str]:
    raw = _load(target)
    if not raw:
        return {}
    value = json.loads(raw)
    return value if isinstance(value, dict) else {}

def save_openai_key(value: str) -> None:
    _save(OPENAI_TARGET, _valid(value), "Draeven private OpenAI API key")

def save_wright_token(value: str) -> None:
    _save(WRIGHT_TARGET, value, "Draeven private Wright tool token")

def openai_key_is_configured() -> bool:
    if not _win_available:
        return False
    credential = PCREDENTIALW()
    if not _read(OPENAI_TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(credential)):
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return False
        raise ctypes.WinError(error)
    _free(credential)
    return True

def load_openai_key() -> str | None:
    """Return the secret to trusted local provider code only."""
    return _load(OPENAI_TARGET)

def wright_token_is_configured() -> bool:
    if not _win_available:
        return False
    credential = PCREDENTIALW()
    if not _read(WRIGHT_TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(credential)):
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return False
        raise ctypes.WinError(error)
    _free(credential)
    return True

def load_wright_token() -> str | None:
    """Return the Wright tool token to trusted local integration code only."""
    return _load(WRIGHT_TARGET)

def save_twilio_connection(values: dict[str, str]) -> None:
    _save_bundle(TWILIO_TARGET, values,
        ("account_sid", "auth_token", "from_number"), "Draeven private Twilio connection")

def load_twilio_connection() -> dict[str, str]:
    return _load_bundle(TWILIO_TARGET)

def save_shopify_connection(values: dict[str, str]) -> None:
    _save_bundle(SHOPIFY_TARGET, values,
        ("store", "client_id", "client_secret"), "Draeven private Shopify connection")

def load_shopify_connection() -> dict[str, str]:
    return _load_bundle(SHOPIFY_TARGET)

def save_etsy_connection(values: dict[str, str]) -> None:
    _save_bundle(ETSY_TARGET, values,
        ("keystring", "shared_secret", "shop_id"), "Draeven private Etsy connection")

def load_etsy_connection() -> dict[str, str]:
    return _load_bundle(ETSY_TARGET)

def save_etsy_oauth(values: dict[str, str]) -> None:
    _save_bundle(ETSY_OAUTH_TARGET, values,
        ("access_token", "refresh_token", "expires_at", "scope"),
        "Draeven private Etsy OAuth tokens")

def load_etsy_oauth() -> dict[str, str]:
    return _load_bundle(ETSY_OAUTH_TARGET)
