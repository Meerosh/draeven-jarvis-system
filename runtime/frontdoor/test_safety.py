from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import server
import shared_context


class DraftOnlyFrontDoorTests(unittest.TestCase):
    def test_shared_context_is_added_to_every_provider_prompt(self) -> None:
        for provider in ("claude", "codex", "hermes"):
            with self.subTest(provider=provider):
                decision = {"lane": "code_or_system"}
                fake_result = type("Result", (), {
                    "provider": provider, "model": None, "elapsed_ms": 1,
                    "estimated_input_tokens": 10, "estimated_output_tokens": 2,
                    "cloud_calls": 0 if provider == "hermes" else 1, "answer": "ok",
                })()
                with patch.object(server.GATEWAY, "run", return_value=fake_result) as run, \
                     patch.object(shared_context, "load_shared_context", return_value="safe shared facts"):
                    server.provider_answer("request", decision, "original prompt", provider=provider)
                sent_prompt = run.call_args.args[1]
                self.assertIn("<draeven_shared_context>", sent_prompt)
                self.assertIn("safe shared facts", sent_prompt)
                self.assertTrue(sent_prompt.endswith("original prompt"))

    def test_claude_command_never_grants_automatic_edit_permission(self) -> None:
        completed = type("Completed", (), {"stdout": "draft", "stderr": ""})()
        with patch.object(server.shutil, "which", return_value="claude"), \
             patch.object(server.subprocess, "run", return_value=completed) as run:
            self.assertEqual(server.ask_claude("write code"), "draft")
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--permission-mode") + 1], "plan")
        self.assertNotIn("acceptEdits", command)

    def test_code_lane_is_reported_as_draft_only(self) -> None:
        decision = {"lane": "code_or_system", "routine": 0.0, "is_code": 1.0, "stakes": 0.0}
        with patch.object(server, "provider_answer", return_value=("draft only", "codex")) as ask:
            result = server.handle("change a script", decision)
        self.assertEqual(result[1], "draft only")
        self.assertEqual(result[2], "codex (draft only)")
        prompt = ask.call_args.args[2]
        self.assertIn("Do not edit files", prompt)

    def test_codex_command_is_ephemeral_and_read_only(self) -> None:
        completed = type("Completed", (), {"stdout": "draft", "stderr": ""})()
        with patch.object(server.shutil, "which", return_value="codex"), \
             patch.object(server.subprocess, "run", return_value=completed) as run:
            self.assertEqual(server.ask_codex("review code"), "draft")
        command = run.call_args.args[0]
        self.assertIn("--ephemeral", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertIn("--ignore-rules", command)

    def test_hermes_command_uses_isolated_no_tools_profile(self) -> None:
        completed = type("Completed", (), {"stdout": "local", "stderr": ""})()
        with patch.object(server.shutil, "which", return_value="hermes"), \
             patch.object(server.subprocess, "run", return_value=completed) as run:
            self.assertEqual(server.ask_hermes("summarize", "ornith-final"), "local")
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("-p") + 1], "draeven")
        self.assertEqual(command[command.index("--provider") + 1], "ollama")
        self.assertEqual(command[command.index("--toolsets") + 1], "")
        self.assertIn("--ignore-rules", command)

    def test_selected_council_route_stays_advisory_and_uses_assigned_provider(self) -> None:
        decision = {"lane": "act (needs confirm)", "routine": 0.0, "is_code": 0.0, "stakes": 1.0}
        with patch.object(server, "provider_answer", return_value=("diagnosis", "hermes/ornith-final")) as ask:
            result = server.handle("diagnose the route", decision, "azrath")
        self.assertEqual(result[1], "diagnosis")
        self.assertIn("council:azrath; advice only", result[2])
        self.assertIsNone(result[3])
        self.assertEqual(ask.call_args.kwargs["provider"], "hermes")
        self.assertIn("Do not perform external actions", ask.call_args.args[2])


if __name__ == "__main__":
    unittest.main()
