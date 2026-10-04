"""Read-only validation for Draeven's private external-service connections."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request

from private_credentials import (
    load_etsy_connection, load_shopify_connection, load_twilio_connection,
)

CLIENT = urllib.request.build_opener()
ELEVENLABS_TWILIO_URL = "https://api.us.elevenlabs.io/twilio/inbound_call"


class ConnectionError(RuntimeError):
    pass


def _json(req: urllib.request.Request, timeout: int = 20):
    try:
        with CLIENT.open(req, timeout=timeout) as response:
            return json.load(response), dict(response.headers)
    except urllib.error.HTTPError as exc:
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
    return {"configured": True, "verified": str(data.get("shop_id", "")) == shop_id,
            "private_access": False,
            "note": "OAuth is still required for private listings and shop changes."}


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
