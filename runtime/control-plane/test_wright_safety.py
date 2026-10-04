from __future__ import annotations

import hashlib
import hmac
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import wright_control_plane as wcp
import wright_tools_server as server
import card_orchestrator as cards


class WrightSmsIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.jobs_patch = patch.object(wcp, "JOBS", Path(self.temp.name) / "jobs")
        self.jobs_patch.start()
        self.addCleanup(self.jobs_patch.stop)

    def make_sms_job(self, call_id: str) -> dict:
        job = wcp.new_job(call_id)
        job["industry_profile"] = "hvac"
        job["state"] = "LEAD_CAPTURED"
        job["caller_fields"] = {"sms_consent": True, "callback_number": "+15555550123"}
        wcp.save(job)
        return job

    def test_failed_or_uncertain_attempt_is_never_reported_as_sent(self) -> None:
        self.make_sms_job("uncertain")
        uncertain = {"sent": False, "outcome_unknown": True, "reason": "timeout"}
        with patch.object(wcp, "send_sms", return_value=uncertain) as send:
            first = wcp.tool_send_demo_customer_sms("uncertain")
            retry = wcp.tool_send_demo_customer_sms("uncertain")
        self.assertEqual(first["status"], "needs_human_review")
        self.assertEqual(retry["status"], "needs_human_review")
        self.assertEqual(send.call_count, 1)

    def test_confirmed_send_is_reported_sent_without_resending(self) -> None:
        self.make_sms_job("sent")
        receipt = {"sent": True, "sid": "SM-test", "twilio_status": "queued"}
        with patch.object(wcp, "send_sms", return_value=receipt) as send:
            first = wcp.tool_send_demo_customer_sms("sent")
            retry = wcp.tool_send_demo_customer_sms("sent")
        self.assertEqual(first["status"], "sent")
        self.assertEqual(retry["status"], "sent")
        self.assertEqual(send.call_count, 1)

    def test_unconfigured_provider_is_truthfully_failed_and_can_be_retried(self) -> None:
        self.make_sms_job("unconfigured")
        with patch.object(wcp, "send_sms", return_value={"sent": False, "reason": "twilio_not_configured"}) as send:
            first = wcp.tool_send_demo_customer_sms("unconfigured")
            second = wcp.tool_send_demo_customer_sms("unconfigured")
        self.assertEqual(first["status"], "failed")
        self.assertEqual(second["status"], "failed")
        self.assertEqual(send.call_count, 2)
        receipt = wcp.tool_record_demo_receipt("unconfigured")
        self.assertEqual(receipt["evidence_receipt"]["final_status"], "failed")


class WebhookAuthenticationTests(unittest.TestCase):
    def test_missing_protected_token_fails_closed(self) -> None:
        with patch.object(server, "protected_tool_token", return_value=""):
            self.assertFalse(server.tool_request_authorized(None))

    def test_matching_protected_token_is_accepted(self) -> None:
        with patch.object(server, "protected_tool_token", return_value="test-secret"):
            self.assertTrue(server.tool_request_authorized("test-secret"))
            self.assertFalse(server.tool_request_authorized("wrong"))


class CardApprovalBoundaryTests(unittest.TestCase):
    def test_resume_with_complete_assets_does_not_self_approve(self) -> None:
        job = {
            "state": "BRIEF_DRAFT", "type": "greeting",
            "assets": [{"role": role} for role in ("front", "inside", "back")],
        }
        with patch.object(cards, "load_job", return_value=job), \
             patch.object(cards, "approve_brief") as approve, \
             patch.object(cards, "log_event"):
            self.assertEqual(cards.resume("OAL-CARD-TEST"), "OAL-CARD-TEST")
        approve.assert_not_called()

    def test_local_publish_command_is_blocked_without_provider_connector(self) -> None:
        with patch.object(cards, "log_event"), \
             self.assertRaisesRegex(cards.OrchestratorError, "no Etsy publishing connector"):
            cards.publish("OAL-CARD-TEST", "manual-listing-id")


if __name__ == "__main__":
    unittest.main()
