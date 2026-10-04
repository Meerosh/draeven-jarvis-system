"""Set the approved Wright receptionist voice without exposing credentials."""
import json
import urllib.request
from pathlib import Path

import eleven_voice

AGENT_ID = "agent_8901m3bcq8k4etqbty3aa6k0jnxs"
LIAM_ID = "TX3LPaxmHKxFdv7VOQHJ"
URL = f"https://api.elevenlabs.io/v1/convai/agents/{AGENT_ID}"


def request(key, method="GET", payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL, data=data, method=method,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


key = eleven_voice.get_key()
if not key:
    raise SystemExit("ElevenLabs is not configured.")
current = request(key)
backup = Path(__file__).with_name("wright_agent_before_voice_fix.json")
if not backup.exists():
    backup.write_text(json.dumps(current, indent=2), encoding="utf-8")

payload = {
    "conversation_config": {
        "tts": {
            "voice_id": LIAM_ID,
            "speed": 0.92,
            "stability": 0.55,
            "similarity_boost": 0.8,
        },
        "agent": {
            "first_message": (
                "Thank you for calling Wright Connector. I'm Jarvis, your "
                "demonstration receptionist. This is a demo, so I won't dispatch "
                "or book a real service call. What kind of business would you "
                "like to test today?"
            )
        },
    },
    "version_description": "Use approved Liam voice and concise demo greeting",
}
updated = request(key, "PATCH", payload)
tts = updated["conversation_config"]["tts"]
print(json.dumps({
    "updated": True,
    "voice_is_liam": tts.get("voice_id") == LIAM_ID,
    "speed": tts.get("speed"),
    "first_message": updated["conversation_config"]["agent"]["first_message"],
}))
