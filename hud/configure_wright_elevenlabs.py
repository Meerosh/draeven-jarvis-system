"""Configure Wright's ElevenLabs webhook tools without printing secrets."""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import eleven_voice
from private_credentials import load_wright_token


API_ROOT = "https://api.elevenlabs.io/v1/convai/tools"
PUBLIC_ROOT = "https://dancing-stumbling-try.ngrok-free.dev"
HEADER_NAME = "X-Draeven-Tool-Token"
TOOLS = {
    "tool_8101m3bd4f7vfgxs4pvmg7vzn8k9": "load_industry_profile",
    "tool_3101m3bdf5zre2rtyb2551cesyvq": "get_business_information",
    "tool_3701m3be5b40fvnsc2jvjwsbp10x": "capture_lead",
    "tool_4401m3bebhz9eh7a7y0wn7nqeh9f": "check_demo_availability",
    "tool_4101m3begbrzffwv963y56qyg8p7": "request_demo_appointment",
    "tool_6201m3bekzscfw8vjqb3xpa5p6ds": "send_demo_customer_sms",
    "tool_0901m3beratsfdrt1vgf7g2ycswx": "send_demo_owner_alert",
    "tool_3601m3bewbbwfgqreqmzpnaqph30": "escalate_to_demo_human",
    "tool_2201m3bf02bqeyn8zfw3ggbay8kb": "record_demo_receipt",
}


def request(api_key: str, tool_id: str, method: str = "GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_ROOT}/{tool_id}",
        data=data,
        method=method,
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=len(TOOLS))
    args = parser.parse_args()
    api_key = eleven_voice.get_key()
    token = load_wright_token()
    if not api_key or not token:
        raise SystemExit("Required private credentials are not configured.")

    records = []
    for tool_id, expected_name in TOOLS.items():
        item = request(api_key, tool_id)
        config = item.get("tool_config", {})
        schema = config.get("api_schema", {})
        if config.get("name") != expected_name:
            raise SystemExit(f"Unexpected tool name for {tool_id}.")
        if schema.get("url") != f"{PUBLIC_ROOT}/tools/{expected_name}":
            raise SystemExit(f"Unexpected URL for {expected_name}.")
        records.append({"id": tool_id, "name": expected_name, "tool_config": config})

    backup_path = Path(__file__).with_name("wright_elevenlabs_tools_backup.json")
    if not backup_path.exists():
        backup_path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    updated = []
    for record in records[: max(0, min(args.limit, len(records)))]:
        config = record["tool_config"]
        config["api_schema"]["request_headers"] = {HEADER_NAME: token}
        request(api_key, record["id"], "PATCH", {"tool_config": config})
        checked = request(api_key, record["id"])
        headers = checked.get("tool_config", {}).get("api_schema", {}).get("request_headers", {})
        if HEADER_NAME not in headers:
            raise SystemExit(f"Header verification failed for {record['name']}.")
        updated.append(record["name"])

    print(json.dumps({"ok": True, "updated": updated, "count": len(updated)}))
    if len(updated) == len(TOOLS):
        marker = {
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "public_url": PUBLIC_ROOT,
            "tool_count": len(updated),
            "header": HEADER_NAME,
        }
        Path(__file__).with_name("wright_elevenlabs_tools_verified.json").write_text(
            json.dumps(marker, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
