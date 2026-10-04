from __future__ import annotations

import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import control_plane as cp


class EqPLaneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.jobs = Path(self.temp.name) / "jobs"
        self.jobs_patch = patch.object(cp, "JOBS", self.jobs)
        self.jobs_patch.start()
        self.addCleanup(self.jobs_patch.stop)

    def test_only_semaj_can_create_approved_eqp_job(self) -> None:
        with self.assertRaises(cp.ControlPlaneError):
            cp.create_eqp(Namespace(sku="OAL-EQP-TEST", title="Test", actor="Jarvis"))

    def test_reference_hash_mismatch_is_blocked(self) -> None:
        cp.create_eqp(Namespace(sku="OAL-EQP-TEST", title="Test", actor="Semaj"))
        asset = Path(self.temp.name) / "wrong.png"
        asset.write_bytes(b"wrong reference")
        with self.assertRaises(cp.ControlPlaneError):
            cp.add_asset(Namespace(
                job="OAL-EQP-TEST", role="modern_arcane_reference", path=str(asset), actor="Jarvis"
            ))

    def test_reference_ready_requires_complete_binding(self) -> None:
        cp.create_eqp(Namespace(sku="OAL-EQP-TEST", title="Test", actor="Semaj"))
        cp.transition(Namespace(
            job="OAL-EQP-TEST", to="REFERENCE_BINDING", actor="Jarvis", reason="test"
        ))
        with self.assertRaises(cp.ControlPlaneError):
            cp.transition(Namespace(
                job="OAL-EQP-TEST", to="REFERENCE_READY", actor="Jarvis", reason="test"
            ))

    def test_semaj_rejection_preserves_assets_and_reopens_binding(self) -> None:
        cp.create_eqp(Namespace(sku="OAL-EQP-TEST", title="Test", actor="Semaj"))
        job = cp.load("OAL-EQP-TEST")
        job["state"] = "READY_FOR_SEMAJ_VISUAL_REVIEW"
        job["assets"] = [{"role": "proof_01_pdf", "path": "old.pdf", "sha256": "old"}]
        cp.save(job)
        cp.reject_eqp_proofs(Namespace(job="OAL-EQP-TEST", actor="Semaj", reason="Visual system rejected"))
        reopened = cp.load("OAL-EQP-TEST")
        self.assertEqual(reopened["state"], "REFERENCE_BINDING")
        self.assertEqual(reopened["assets"], [])
        self.assertEqual(reopened["rejected_asset_sets"][0]["assets"][0]["role"], "proof_01_pdf")


class ReplaceAssetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.jobs = Path(self.temp.name) / "jobs"
        self.jobs_patch = patch.object(cp, "JOBS", self.jobs)
        self.jobs_patch.start()
        self.addCleanup(self.jobs_patch.stop)
        cp.create_card(Namespace(sku="OAL-CARD-TEST", title="Test"))
        self.first = Path(self.temp.name) / "first.png"
        self.first.write_bytes(b"first back")
        self.second = Path(self.temp.name) / "second.png"
        self.second.write_bytes(b"second back")
        cp.add_asset(Namespace(job="OAL-CARD-TEST", role="back",
                               path=str(self.first), actor="Jarvis"))

    def swap(self, path: Path, reason: str = "hall corrected") -> None:
        cp.replace_asset(Namespace(job="OAL-CARD-TEST", role="back", path=str(path),
                                   actor="Jarvis", reason=reason))

    def test_replacement_records_new_hash_and_retains_the_old(self) -> None:
        before = cp.load("OAL-CARD-TEST")["assets"][0]["sha256"]
        self.swap(self.second)
        job = cp.load("OAL-CARD-TEST")
        backs = [a for a in job["assets"] if a["role"] == "back"]
        self.assertEqual(len(backs), 1)
        self.assertNotEqual(backs[0]["sha256"], before)
        self.assertEqual(job["superseded_assets"][0]["asset"]["sha256"], before)
        self.assertEqual(job["audit_log"][-1]["action"], "ASSET_REPLACED")

    def test_replacing_with_the_same_file_is_blocked(self) -> None:
        with self.assertRaises(cp.ControlPlaneError):
            self.swap(self.first)

    def test_replacing_a_role_that_was_never_recorded_is_blocked(self) -> None:
        with self.assertRaises(cp.ControlPlaneError):
            cp.replace_asset(Namespace(job="OAL-CARD-TEST", role="front",
                                       path=str(self.second), actor="Jarvis", reason="x"))

    def test_approved_work_stays_immutable(self) -> None:
        job = cp.load("OAL-CARD-TEST")
        job["state"] = "APPROVED_FOR_LISTING"
        cp.save(job)
        with self.assertRaises(cp.ControlPlaneError):
            self.swap(self.second)


class ShopifyLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.jobs = Path(self.temp.name) / "jobs"
        self.jobs_patch = patch.object(cp, "JOBS", self.jobs)
        self.jobs_patch.start()
        self.addCleanup(self.jobs_patch.stop)
        cp.create_card(Namespace(sku="OAL-CARD-TEST", title="Test"))

    def link(self, gid: str, replace: bool = False) -> None:
        cp.set_shopify(Namespace(job="OAL-CARD-TEST", gid=gid, actor="Jarvis", replace=replace))

    def test_new_card_starts_with_an_empty_shopify_link(self) -> None:
        self.assertIsNone(cp.load("OAL-CARD-TEST")["listing"]["shopify_product_gid"])

    def test_valid_gid_is_recorded_and_audited(self) -> None:
        gid = "gid://shopify/Product/8557766148166"
        self.link(gid)
        job = cp.load("OAL-CARD-TEST")
        self.assertEqual(job["listing"]["shopify_product_gid"], gid)
        self.assertEqual(job["audit_log"][-1]["action"], "SHOPIFY_PRODUCT_LINKED")

    def test_malformed_gid_is_blocked(self) -> None:
        for bad in ("8557766148166", "gid://shopify/Variant/1", "gid://shopify/Product/abc", ""):
            with self.assertRaises(cp.ControlPlaneError):
                self.link(bad)

    def test_relinking_requires_replace(self) -> None:
        first = "gid://shopify/Product/1111111111"
        second = "gid://shopify/Product/2222222222"
        self.link(first)
        with self.assertRaises(cp.ControlPlaneError):
            self.link(second)
        self.link(second, replace=True)
        self.assertEqual(cp.load("OAL-CARD-TEST")["listing"]["shopify_product_gid"], second)

    def test_linking_does_not_authorize_publication(self) -> None:
        self.link("gid://shopify/Product/1111111111")
        job = cp.load("OAL-CARD-TEST")
        self.assertFalse(job["listing"]["publish_authorized"])
        self.assertEqual(job["state"], "BRIEF_DRAFT")

    def test_legacy_job_without_the_field_is_upgraded(self) -> None:
        job = cp.load("OAL-CARD-TEST")
        job["listing"] = {"etsy_listing_id": None, "publish_authorized": False}
        cp.save(job)
        gid = "gid://shopify/Product/3333333333"
        self.link(gid)
        self.assertEqual(cp.load("OAL-CARD-TEST")["listing"]["shopify_product_gid"], gid)


class PublicationEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.jobs_patch = patch.object(cp, "JOBS", Path(self.temp.name) / "jobs")
        self.jobs_patch.start()
        self.addCleanup(self.jobs_patch.stop)
        cp.create_card(Namespace(sku="OAL-CARD-TEST", title="Test"))
        job = cp.load("OAL-CARD-TEST")
        job["state"] = "LISTING_STAGED"
        job["listing"]["publish_authorized"] = True
        cp.save(job)

    def test_approval_and_manually_entered_id_are_not_publication_evidence(self) -> None:
        with self.assertRaisesRegex(cp.ControlPlaneError, "no verified Etsy/Shopify provider receipt"):
            cp.transition(Namespace(job="OAL-CARD-TEST", to="PUBLISHED", actor="Semaj", reason="test"))
        self.assertEqual(cp.load("OAL-CARD-TEST")["state"], "LISTING_STAGED")

    def test_locally_entered_receipt_claim_cannot_unlock_published_state(self) -> None:
        job = cp.load("OAL-CARD-TEST")
        job["listing"]["provider_receipt"] = {
            "provider": "Etsy", "external_id": "listing-123", "verified_at": cp.now(),
            "source": "manual"
        }
        cp.save(job)
        with self.assertRaisesRegex(cp.ControlPlaneError, "no verified Etsy/Shopify provider receipt"):
            cp.transition(Namespace(job="OAL-CARD-TEST", to="PUBLISHED", actor="Semaj", reason="manual ID"))
        self.assertEqual(cp.load("OAL-CARD-TEST")["state"], "LISTING_STAGED")


if __name__ == "__main__":
    unittest.main()
