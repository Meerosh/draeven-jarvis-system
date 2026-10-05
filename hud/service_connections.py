"""Read-only validation for Draeven's private external-service connections."""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

import certifi

from private_credentials import (
    load_etsy_connection, load_etsy_oauth, load_shopify_connection,
    load_twilio_connection, save_etsy_oauth,
)

# Python's bundled OpenSSL path can point at an expired machine-wide certificate
# bundle on Windows. Use certifi's maintained CA bundle and keep verification on.
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
CLIENT = urllib.request.build_opener(
    urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=TLS_CONTEXT)
)
ELEVENLABS_TWILIO_URL = "https://api.us.elevenlabs.io/twilio/inbound_call"
ETSY_REDIRECT_URI = "http://localhost:4783/api/connections/etsy/callback"
ETSY_SCOPES = "listings_r listings_w shops_r shops_w transactions_r"
ETSY_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"


class ConnectionError(RuntimeError):
    pass


def _json(req: urllib.request.Request, timeout: int = 20):
    try:
        with CLIENT.open(req, timeout=timeout) as response:
            return json.load(response), dict(response.headers)
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and "myshopify.com/admin/oauth/access_token" in req.full_url:
            raise ConnectionError("Shopify store address was not recognized. Use the exact .myshopify.com address.") from None
        raise ConnectionError(f"Provider rejected the connection ({exc.code}).") from None
    except urllib.error.URLError:
        raise ConnectionError("Provider could not be reached from this computer.") from None


def _twilio_number(values: dict[str, str]):
    sid = values.get("account_sid", "").strip()
    token = values.get("auth_token", "").strip()
    number = values.get("from_number", "").strip()
    if not (sid and token and number):
        return None, None, None
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
    query = urllib.parse.urlencode({"PhoneNumber": number, "PageSize": 1})
    req = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers.json?{query}",
        headers={"Authorization": f"Basic {auth}"},
    )
    data, _ = _json(req)
    records = data.get("incoming_phone_numbers", [])
    return (records[0] if records else None), sid, auth


def validate_twilio(values: dict[str, str] | None = None) -> dict:
    values = values or load_twilio_connection()
    if not all(values.get(key, "").strip() for key in ("account_sid", "auth_token", "from_number")):
        return {"configured": False, "verified": False, "phone_route": False}
    record, _, _ = _twilio_number(values)
    records = [record] if record else []
    voice_url = records[0].get("voice_url", "") if records else ""
    return {
        "configured": True,
        "verified": bool(records),
        "phone_route": voice_url.rstrip("/") == ELEVENLABS_TWILIO_URL.rstrip("/"),
        "phone_found": bool(records),
    }


def repair_twilio_route(values: dict[str, str]) -> dict:
    record, sid, auth = _twilio_number(values)
    if not record:
        raise ConnectionError("The configured Twilio phone number was not found in this account.")
    body = urllib.parse.urlencode({"VoiceUrl": ELEVENLABS_TWILIO_URL, "VoiceMethod": "POST"}).encode()
    req = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/IncomingPhoneNumbers/{record['sid']}.json",
        data=body, method="POST",
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"},
    )
    _json(req)
    return validate_twilio(values)


def validate_shopify(values: dict[str, str] | None = None) -> dict:
    values = values or load_shopify_connection()
    store = values.get("store", "").strip().removeprefix("https://").rstrip("/")
    client_id = values.get("client_id", "").strip()
    secret = values.get("client_secret", "").strip()
    if not (store and client_id and secret):
        return {"configured": False, "verified": False}
    token_req = urllib.request.Request(
        f"https://{store}/admin/oauth/access_token",
        data=urllib.parse.urlencode({
            "grant_type": "client_credentials", "client_id": client_id,
            "client_secret": secret,
        }).encode(),
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token_data, _ = _json(token_req)
    token = token_data.get("access_token")
    if not token:
        raise ConnectionError("Shopify did not return an access token.")
    query = json.dumps({"query": "{ shop { name } products(first:1) { nodes { id } } }"}).encode()
    req = urllib.request.Request(
        f"https://{store}/admin/api/2026-07/graphql.json", data=query, method="POST",
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token},
    )
    data, _ = _json(req)
    if data.get("errors"):
        raise ConnectionError("Shopify accepted the connection but rejected the catalog check.")
    return {"configured": True, "verified": bool(data.get("data", {}).get("shop")),
            "catalog_read": "products" in data.get("data", {})}


def shopify_catalog_summary() -> dict:
    """Read the live Shopify catalog and summarize active greeting-card listings."""
    values = load_shopify_connection()
    store = values.get("store", "").strip().removeprefix("https://").rstrip("/")
    client_id = values.get("client_id", "").strip()
    secret = values.get("client_secret", "").strip()
    if not (store and client_id and secret):
        raise ConnectionError("Shopify is not configured.")
    token_req = urllib.request.Request(
        f"https://{store}/admin/oauth/access_token",
        data=urllib.parse.urlencode({"grant_type": "client_credentials",
                                    "client_id": client_id,
                                    "client_secret": secret}).encode(),
        method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token_data, _ = _json(token_req)
    token = token_data.get("access_token")
    if not token:
        raise ConnectionError("Shopify did not return an access token.")
    query = json.dumps({"query": "{ products(first:250) { nodes { title status productType tags totalInventory } } }"}).encode()
    req = urllib.request.Request(
        f"https://{store}/admin/api/2026-07/graphql.json", data=query, method="POST",
        headers={"Content-Type": "application/json", "X-Shopify-Access-Token": token},
    )
    data, _ = _json(req)
    if data.get("errors"):
        raise ConnectionError("Shopify accepted the connection but rejected the catalog read.")
    products = data.get("data", {}).get("products", {}).get("nodes", [])
    active = [item for item in products if item.get("status") == "ACTIVE"]
    cards = [item for item in active if item.get("productType", "").strip().lower() == "greeting card"]
    return {
        "verified": True,
        "active_products": len(active),
        "active_greeting_cards": len(cards),
        "card_titles": [item.get("title", "") for item in cards],
        "digital_inventory_note": "These greeting cards are digital products, so Shopify reports inventory as zero rather than a physical stock count.",
    }


def validate_etsy(values: dict[str, str] | None = None) -> dict:
    values = values or load_etsy_connection()
    key = values.get("keystring", "").strip()
    secret = values.get("shared_secret", "").strip()
    shop_id = values.get("shop_id", "").strip()
    if not (key and secret and shop_id):
        return {"configured": False, "verified": False, "private_access": False}
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{urllib.parse.quote(shop_id)}",
        headers={"x-api-key": f"{key}:{secret}"},
    )
    data, _ = _json(req)
    result = {"configured": True, "verified": str(data.get("shop_id", "")) == shop_id,
              "private_access": False,
              "note": "Authorize the Etsy shop to enable private listings and shop changes."}
    oauth = load_etsy_oauth()
    if oauth:
        try:
            token = etsy_access_token(values, oauth)
            auth_req = urllib.request.Request(
                f"https://openapi.etsy.com/v3/application/shops/{urllib.parse.quote(shop_id)}",
                headers={"x-api-key": f"{key}:{secret}", "Authorization": f"Bearer {token}"},
            )
            auth_data, _ = _json(auth_req)
            result["private_access"] = str(auth_data.get("shop_id", "")) == shop_id
            result["note"] = "Private Etsy authorization is active." if result["private_access"] else result["note"]
        except (ConnectionError, ValueError, OSError):
            result["note"] = "Etsy authorization expired. Authorize the shop again."
    return result


def begin_etsy_oauth() -> tuple[str, dict[str, str]]:
    values = load_etsy_connection()
    key = values.get("keystring", "").strip()
    if not key:
        raise ConnectionError("Save and verify the Etsy Keystring and Shared Secret first.")
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(32)
    query = urllib.parse.urlencode({
        "response_type": "code", "redirect_uri": ETSY_REDIRECT_URI,
        "scope": ETSY_SCOPES, "client_id": key, "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    })
    flow = {"state": state, "verifier": verifier, "created_at": str(int(time.time()))}
    return f"https://www.etsy.com/oauth/connect?{query}", flow


def finish_etsy_oauth(code: str, flow: dict[str, str]) -> dict:
    values = load_etsy_connection()
    key = values.get("keystring", "").strip()
    if not key or not code or not flow.get("verifier"):
        raise ConnectionError("The Etsy authorization request is incomplete. Start it again from Draeven.")
    body = urllib.parse.urlencode({
        "grant_type": "authorization_code", "client_id": key,
        "redirect_uri": ETSY_REDIRECT_URI, "code": code,
        "code_verifier": flow["verifier"],
    }).encode()
    req = urllib.request.Request(ETSY_TOKEN_URL, data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    data, _ = _json(req)
    _save_etsy_token(data)
    result = validate_etsy(values)
    if not result.get("private_access"):
        raise ConnectionError("Etsy authorized the app, but the private shop check failed.")
    return result


def _save_etsy_token(data: dict) -> None:
    access = str(data.get("access_token", "")).strip()
    refresh = str(data.get("refresh_token", "")).strip()
    scope = str(data.get("scope", "")).strip()
    if not access or not refresh:
        raise ConnectionError("Etsy did not return the required authorization tokens.")
    expires_at = str(int(time.time()) + max(60, int(data.get("expires_in", 3600))) - 60)
    save_etsy_oauth({"access_token": access, "refresh_token": refresh,
                     "expires_at": expires_at, "scope": scope})


def etsy_access_token(values: dict[str, str] | None = None,
                      oauth: dict[str, str] | None = None) -> str:
    values = values or load_etsy_connection()
    oauth = oauth or load_etsy_oauth()
    if not oauth.get("access_token"):
        raise ConnectionError("Etsy private authorization is not configured.")
    if int(oauth.get("expires_at", "0") or 0) > int(time.time()):
        return oauth["access_token"]
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token", "client_id": values.get("keystring", ""),
        "refresh_token": oauth.get("refresh_token", ""),
    }).encode()
    req = urllib.request.Request(ETSY_TOKEN_URL, data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    data, _ = _json(req)
    if not data.get("scope"):
        data["scope"] = oauth.get("scope", "")
    _save_etsy_token(data)
    return str(data["access_token"])


def status() -> dict:
    result = {}
    for name, validator in (("twilio", validate_twilio), ("shopify", validate_shopify), ("etsy", validate_etsy)):
        try:
            result[name] = validator()
        except ConnectionError as exc:
            configured = bool({"twilio": load_twilio_connection, "shopify": load_shopify_connection,
                               "etsy": load_etsy_connection}[name]())
            result[name] = {"configured": configured, "verified": False, "error": str(exc)}
    return result
