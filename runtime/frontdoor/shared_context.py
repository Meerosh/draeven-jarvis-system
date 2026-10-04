"""Small, secret-free operating context shared by every Draeven text provider."""
from __future__ import annotations

from pathlib import Path


CONTEXT_PATH = Path(r"C:\Users\Arach\Documents\Jarvis\DRAEVEN-SHARED-CONTEXT.md")
MAX_CONTEXT_CHARS = 6_000
FALLBACK_CONTEXT = (
    "Draeven shared context is unavailable. Do not infer connection or execution status. "
    "Read JARVIS-BOOT-BRIEF.md, Active Priorities.md, and MASTER_CONTEXT.md when file access is available."
)


def load_shared_context(path: Path = CONTEXT_PATH) -> str:
    """Return the bounded shared context without blocking a request on file errors."""
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return FALLBACK_CONTEXT
    return text[:MAX_CONTEXT_CHARS] if text else FALLBACK_CONTEXT


def with_shared_context(prompt: str) -> str:
    return f"<draeven_shared_context>\n{load_shared_context()}\n</draeven_shared_context>\n\n{prompt}"


def shared_context_status(path: Path = CONTEXT_PATH) -> dict:
    """Expose only readiness metadata; never return context contents over health."""
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        text = ""
    return {"ready": bool(text), "characters": min(len(text), MAX_CONTEXT_CHARS)}
