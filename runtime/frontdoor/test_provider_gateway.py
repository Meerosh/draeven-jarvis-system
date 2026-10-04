from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from provider_gateway import ProviderGateway, ProviderGatewayError


class ProviderGatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        policy = {
            "limits": {"max_input_chars": 20, "max_output_chars": 12, "estimated_chars_per_token": 4,
                       "max_cloud_calls_per_request": 1, "max_fallbacks_per_request": 0,
                       "daily_cloud_call_limit": 2},
            "providers": {
                "claude": {"enabled": True, "cloud": True, "default_model": "haiku", "complex_model": "sonnet"},
                "codex": {"enabled": True, "cloud": True, "default_model": None},
                "hermes": {"enabled": False, "cloud": False, "default_model": "local"},
                "openai_images": {"enabled": False, "cloud": True},
                "midjourney_manual": {"enabled": True, "cloud": False},
            },
        }
        (self.root / "provider_policy.json").write_text(json.dumps(policy), encoding="utf-8")
        self.gateway = ProviderGateway(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_code_uses_codex_and_standard_work_uses_cheap_claude(self):
        self.assertEqual(self.gateway.choose("code_or_system", "fix code"), ("codex", None))
        self.assertEqual(self.gateway.choose("recall", "answer this"), ("claude", "haiku"))
        self.assertEqual(self.gateway.choose("recall", "status", status_request=True), ("claude", "sonnet"))

    def test_disabled_hermes_is_not_selected(self):
        self.assertEqual(self.gateway.choose("do_work", "research this"), ("claude", "haiku"))

    def test_one_runner_call_and_usage_record(self):
        runner = Mock(return_value="short answer")
        result = self.gateway.run("claude", "small prompt", runner, model="haiku")
        runner.assert_called_once_with("small prompt", "haiku")
        self.assertEqual(result.cloud_calls, 1)
        self.assertEqual(len((self.root / "provider_usage.jsonl").read_text().splitlines()), 1)
        self.assertEqual(self.gateway.usage_status()["cloud_calls_remaining"], 1)

    def test_input_and_daily_limits_fail_before_calling_provider(self):
        runner = Mock(return_value="answer")
        with self.assertRaises(ProviderGatewayError):
            self.gateway.run("claude", "x" * 21, runner)
        self.gateway.run("claude", "one", runner)
        self.gateway.run("claude", "two", runner)
        with self.assertRaises(ProviderGatewayError):
            self.gateway.run("claude", "three", runner)
        self.assertEqual(runner.call_count, 2)

    def test_output_is_capped(self):
        result = self.gateway.run("claude", "small", lambda _prompt, _model: "x" * 30)
        self.assertIn("Response shortened", result.answer)

    def test_local_provider_does_not_consume_cloud_allowance(self):
        self.gateway.policy["providers"]["hermes"]["enabled"] = True
        result = self.gateway.run("hermes", "small", lambda _prompt, _model: "local", model="local")
        self.assertEqual(result.cloud_calls, 0)
        self.assertEqual(self.gateway.usage_status()["cloud_calls_remaining"], 2)


if __name__ == "__main__":
    unittest.main()
