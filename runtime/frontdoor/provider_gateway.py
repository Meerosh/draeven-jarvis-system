"""Cost-controlled provider selection and usage records for the JARVIS Front Door."""

from __future__ import annotations

import datetime as dt
import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Optional


class ProviderGatewayError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderResult:
    answer: str
    provider: str
    model: Optional[str]
    elapsed_ms: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    cloud_calls: int
    fallback_used: bool = False


class ProviderGateway:
    """Enforce one-provider routing, prompt limits, daily limits, and audit records."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.policy_path = self.root / "provider_policy.json"
        self.usage_path = self.root / "provider_usage.jsonl"
        self._lock = threading.Lock()
        self.policy = json.loads(self.policy_path.read_text(encoding="utf-8"))

    def status(self) -> dict:
        return {
            name: {"enabled": bool(config.get("enabled")), "reason": config.get("reason")}
            for name, config in self.policy["providers"].items()
        }

    def usage_status(self) -> dict:
        limit = int(self.policy["limits"]["daily_cloud_call_limit"])
        used = self._today_cloud_calls()
        return {
            "cloud_calls_today": used,
            "daily_cloud_call_limit": limit,
            "cloud_calls_remaining": max(0, limit - used),
            "max_cloud_calls_per_request": int(self.policy["limits"]["max_cloud_calls_per_request"]),
            "max_fallbacks_per_request": int(self.policy["limits"]["max_fallbacks_per_request"]),
        }

    def choose(self, lane: str, request: str, *, status_request: bool = False) -> tuple[str, Optional[str]]:
        providers = self.policy["providers"]
        low = request.lower()
        if lane == "code_or_system" and providers["codex"]["enabled"]:
            return "codex", providers["codex"].get("default_model")
        if any(word in low for word in ("research", "compare", "investigate", "find sources")):
            if providers["hermes"]["enabled"]:
                return "hermes", providers["hermes"].get("default_model")
        model_key = "complex_model" if status_request or len(request) > 1800 else "default_model"
        return "claude", providers["claude"].get(model_key)

    def run(
        self,
        provider: str,
        prompt: str,
        runner: Callable[[str, Optional[str]], str],
        *,
        model: Optional[str] = None,
    ) -> ProviderResult:
        config = self.policy["providers"].get(provider)
        if not config or not config.get("enabled"):
            raise ProviderGatewayError(f"Provider is unavailable: {provider}")
        limits = self.policy["limits"]
        prompt = prompt.strip()
        if not prompt:
            raise ProviderGatewayError("The provider prompt is empty.")
        if len(prompt) > int(limits["max_input_chars"]):
            raise ProviderGatewayError(
                f"Request exceeds the {limits['max_input_chars']}-character provider limit. Narrow the request first."
            )
        is_cloud = bool(config.get("cloud", True))
        with self._lock:
            if is_cloud and self._today_cloud_calls() >= int(limits["daily_cloud_call_limit"]):
                raise ProviderGatewayError("Daily cloud-call limit reached. Local and instant lanes remain available.")
        started = time.monotonic()
        answer = runner(prompt, model)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if not isinstance(answer, str) or not answer.strip():
            raise ProviderGatewayError(f"{provider} returned no answer.")
        answer = answer.strip()
        if len(answer) > int(limits["max_output_chars"]):
            answer = answer[: int(limits["max_output_chars"])].rstrip() + "\n\n[Response shortened by JARVIS usage controls.]"
        chars_per_token = max(1, int(limits["estimated_chars_per_token"]))
        result = ProviderResult(
            answer=answer,
            provider=provider,
            model=model,
            elapsed_ms=elapsed_ms,
            estimated_input_tokens=(len(prompt) + chars_per_token - 1) // chars_per_token,
            estimated_output_tokens=(len(answer) + chars_per_token - 1) // chars_per_token,
            cloud_calls=1 if is_cloud else 0,
        )
        with self._lock:
            self._record(result)
        return result

    def _today_cloud_calls(self) -> int:
        if not self.usage_path.exists():
            return 0
        today = dt.datetime.now(dt.timezone.utc).date().isoformat()
        count = 0
        for line in self.usage_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(item.get("at", "")).startswith(today):
                count += int(item.get("cloud_calls", 0))
        return count

    def _record(self, result: ProviderResult) -> None:
        record = {"at": dt.datetime.now(dt.timezone.utc).isoformat(), **asdict(result)}
        record.pop("answer", None)
        self.usage_path.parent.mkdir(parents=True, exist_ok=True)
        with self.usage_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
