"""Jev AI via OpenRouter - Real Llama 3.3 70B routing decisions.
Integrated into jarvis-frontdoor/server.py as PRIMARY routing engine.
Fallback: Local Laya on port 8090.
"""
import json
import os
import re
import urllib.request
from urllib.error import URLError, HTTPError
import datetime

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-3.3-70b-instruct"
LOG_FILE = r"C:\Users\Arach\my-agent\jev_debug.log"

def _log(msg):
    """Log to file and console."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_msg + "\n")
    except:
        pass

def _extract_json(text):
    """Extract JSON object from text, handling markdown and formatting issues."""
    text = text.strip()

    # Remove markdown code blocks
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:].lstrip("\n")
        text = text.strip()

    # Try to find JSON object within the text
    # Look for the first { and last }
    start = text.find("{")
    if start == -1:
        return None

    end = text.rfind("}")
    if end == -1:
        return None

    json_str = text[start:end+1]

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

_missing_key_logged = False

def call_jev(state, questions):
    """Route request via OpenRouter Llama 3.3 70B.

    Args:
        state: dict with "request" and optionally "note"
        questions: dict of {field: {"type": "choice"|"noul", "instructions": str, ...}}

    Returns:
        dict of {field: {"choice"|"noul": value, "confidence": float}}
        or None on failure (fall back to Laya)
    """
    if not OPENROUTER_API_KEY:
        global _missing_key_logged
        if not _missing_key_logged:
            _missing_key_logged = True
            _log("INFO: OPENROUTER_API_KEY not set - routing via Laya (logged once)")
        return None

    # Build the routing prompt
    request = state.get("request", "")
    note_snippet = state.get("note", "")

    prompt_lines = [
        "You are a routing decision engine. Analyze the request and respond ONLY with valid JSON.",
        "Do not include markdown, explanations, or any text outside the JSON object.",
        "",
        f"Request: {request}",
    ]
    if note_snippet:
        prompt_lines.append(f"Relevant note: {note_snippet}")

    prompt_lines.append("")
    prompt_lines.append("Return a JSON object with these fields (use the exact structure below):")

    for field, q in questions.items():
        if q["type"] == "choice":
            choices = list(q["criteria"].keys())
            prompt_lines.append(f'  "{field}": {{"choice": "<one of: {", ".join(choices)}>", "confidence": <0.0-1.0>}}')
        else:  # noul (0-1 scale)
            prompt_lines.append(f'  "{field}": {{"noul": <0.0-1.0>, "confidence": <0.0-1.0>}}')

    prompt_lines.append("")
    prompt_lines.append("Example JSON (adapt to the actual request):")
    prompt_lines.append('{"business": {"choice": "jarvis_system", "confidence": 0.95}, "stakes": {"noul": 0.1, "confidence": 0.8}}')

    prompt = "\n".join(prompt_lines)

    try:
        # Prepare request
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        body = json.dumps({
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 1024,
        }).encode('utf-8')

        req = urllib.request.Request(OPENROUTER_ENDPOINT, data=body, headers=headers, method="POST")

        _log(f"Calling OpenRouter with model {MODEL}...")

        # Call OpenRouter
        with urllib.request.urlopen(req, timeout=30) as response:
            resp_data = json.loads(response.read().decode('utf-8'))

        # Extract text response
        text = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        if not text:
            _log("ERROR: Empty response from OpenRouter")
            return None

        # Parse JSON from response - now more robust
        parsed = _extract_json(text)

        if not parsed:
            _log(f"ERROR: Could not extract JSON from response: {text[:100]}")
            return None

        _log(f"SUCCESS: Jev returned {parsed}")

        # Convert to expected format (match Laya's output structure)
        answers = {}
        for field, q in questions.items():
            if field in parsed:
                answers[field] = parsed[field]
            else:
                # Default fallback
                if q["type"] == "choice":
                    first_choice = next(iter(q["criteria"].keys()))
                    answers[field] = {"choice": first_choice, "confidence": 0.0}
                else:
                    answers[field] = {"noul": 0.5 if field == "stakes" else 0.0, "confidence": 0.0}

        return answers

    except HTTPError as e:
        error_body = e.read().decode()[:200]
        _log(f"ERROR: HTTPError {e.code} from OpenRouter - {error_body}")
        return None
    except URLError as e:
        _log(f"ERROR: URLError from OpenRouter - {e.reason}")
        return None
    except Exception as e:
        _log(f"ERROR: Unexpected error - {type(e).__name__}: {str(e)}")
        return None

if __name__ == "__main__":
    # Test call
    if OPENROUTER_API_KEY:
        test_state = {"request": "What is my top priority?"}
        test_questions = {
            "business": {
                "type": "choice",
                "criteria": {"jarvis_system": "...", "other": "..."}
            },
            "stakes": {"type": "noul"}
        }
        result = call_jev(test_state, test_questions)
        print(json.dumps(result, indent=2))
    else:
        print("OPENROUTER_API_KEY not set")
