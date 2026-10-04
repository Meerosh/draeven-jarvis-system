from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "hud/index.html",
    "hud/serve.py",
    "hud/js/main.js",
    "hud/js/voice.js",
    "runtime/frontdoor/server.py",
    "runtime/frontdoor/provider_gateway.py",
    "runtime/frontdoor/shared_context.py",
    "runtime/frontdoor/repository_worker.py",
    "runtime/control-plane/control_plane.py",
    "runtime/control-plane/wright_tools_server.py",
    "runtime/laya-engine/laya_engine_server.py",
    "runtime/jev_openrouter.py",
    "docs/RECOVERY.md",
)
FORBIDDEN_NAMES = {".env", "provider_usage.jsonl"}
FORBIDDEN_PARTS = {"__pycache__", ".venv", "raw_webhook_events", "jobs"}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return [ROOT / line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    for path in tracked_files():
        relative = path.relative_to(ROOT)
        lower_parts = {part.lower() for part in relative.parts}
        if path.name.lower() in FORBIDDEN_NAMES or lower_parts & FORBIDDEN_PARTS:
            errors.append(f"forbidden tracked path: {relative}")
            continue
        if path.suffix.lower() in {".png", ".ico"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"possible secret in tracked file: {relative}")
                break

    if errors:
        print("Repository verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository verification passed: required files present and no high-confidence secrets tracked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
