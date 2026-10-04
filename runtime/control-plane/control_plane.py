#!/usr/bin/env python3
"""Approval-gated local control plane for O&L production jobs."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional

from providers.openai_provider import OpenAIImageProvider, ImageGenerationRequest

ROOT = Path(__file__).parent
JOBS = ROOT / "jobs"
APPROVERS = {"Semaj"}
CARD_ROLES = {"front", "inside", "back"}
EQP_REFERENCE_ROLES = {
    "locked_copy",
    "component_manifest",
    "visual_spec",
    "brand_style_reference",
    "modern_arcane_reference",
    "official_logo",
    "font_manifest",
}
EQP_PROOF_ROLES = {
    "proof_01_pdf", "proof_01_png",
    "proof_02_pdf", "proof_02_png",
    "proof_03_pdf", "proof_03_png",
}
EQP_ROLES = EQP_REFERENCE_ROLES | EQP_PROOF_ROLES

SHOPIFY_PRODUCT_GID = re.compile(r"^gid://shopify/Product/\d+$")


def new_listing() -> dict[str, Any]:
    """The listing block every job starts with.

    `shopify_product_gid` records which live Shopify product a job became.
    It is a factual link, not an approval, so it carries no approver gate --
    `publish_authorized` records Semaj's approval. PUBLISHED additionally
    requires a verified provider receipt; approval alone is not proof of action.
    """
    return {"etsy_listing_id": None, "shopify_product_gid": None, "publish_authorized": False,
            "provider_receipt": None}

CANONICAL_REFERENCE_HASHES = {
    "brand_style_reference": "e70d6af85b58398fc7536f5b105e53285b66d61e035deff0ce46dcbad5ed62c8",
    "modern_arcane_reference": "73d06f5ce7cf4dad6860c02bbabb70e9e8816cc8646ce808a540db5571ff99cb",
    "official_logo": "c40eb53d0e56ef4e60dff85670d3f600a782316086a1f5326a038de8a8364ad2",
}

CARD_FORWARD = {
    "BRIEF_DRAFT": {"BRIEF_APPROVED"},
    "BRIEF_APPROVED": {"ASSET_PRODUCTION"},
    "ASSET_PRODUCTION": {"QA_PENDING"},
    "QA_PENDING": {"QA_FAILED", "READY_FOR_SEMAJ_APPROVAL"},
    "QA_FAILED": {"ASSET_PRODUCTION"},
    "READY_FOR_SEMAJ_APPROVAL": {"APPROVED_FOR_LISTING"},
    "APPROVED_FOR_LISTING": {"LISTING_STAGED"},
    "LISTING_STAGED": {"PUBLISHED"},
    "PUBLISHED": set(),
}

EQP_FORWARD = {
    "BLUEPRINT_APPROVED": {"REFERENCE_BINDING"},
    "REFERENCE_BINDING": {"REFERENCE_READY"},
    "REFERENCE_READY": {"PROOF_PRODUCTION"},
    "PROOF_PRODUCTION": {"PROOF_QA_PENDING"},
    "PROOF_QA_PENDING": {"PROOF_QA_FAILED", "READY_FOR_SEMAJ_VISUAL_REVIEW"},
    "PROOF_QA_FAILED": {"PROOF_PRODUCTION"},
    "READY_FOR_SEMAJ_VISUAL_REVIEW": {"VISUAL_SYSTEM_APPROVED"},
    "VISUAL_SYSTEM_APPROVED": {"COMPONENT_PRODUCTION"},
    "COMPONENT_PRODUCTION": {"PACKAGE_QA_PENDING"},
    "PACKAGE_QA_PENDING": {"PACKAGE_QA_FAILED", "READY_FOR_SEMAJ_PACKAGE_APPROVAL"},
    "PACKAGE_QA_FAILED": {"COMPONENT_PRODUCTION"},
    "READY_FOR_SEMAJ_PACKAGE_APPROVAL": {"PACKAGE_APPROVED"},
    "PACKAGE_APPROVED": {"LISTING_STAGED"},
    "LISTING_STAGED": {"PUBLISHED"},
    "PUBLISHED": set(),
}


class ControlPlaneError(RuntimeError):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def job_path(job_id: str) -> Path:
    if not job_id or any(char in job_id for char in "\\/:"):
        raise ControlPlaneError("Job ID must be a non-empty safe folder name.")
    return JOBS / job_id / "job.json"


def load(job_id: str) -> dict[str, Any]:
    path = job_path(job_id)
    if not path.is_file():
        raise ControlPlaneError(f"No job named {job_id}.")
    return json.loads(path.read_text(encoding="utf-8"))


def save(job: dict[str, Any]) -> None:
    path = job_path(job["job_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job, indent=2) + "\n", encoding="utf-8")


def event(job: dict[str, Any], actor: str, action: str, detail: str) -> None:
    job["audit_log"].append({"at": now(), "actor": actor, "action": action, "detail": detail})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_card(args: argparse.Namespace) -> None:
    path = job_path(args.sku)
    if path.exists():
        raise ControlPlaneError(f"Job already exists: {args.sku}.")
    job = {
        "job_id": args.sku,
        "venture": "out-legendary",
        "lane": "digital-card",
        "title": args.title,
        "state": "BRIEF_DRAFT",
        "assets": [],
        "listing": new_listing(),
        "audit_log": [],
    }
    event(job, "Jarvis", "JOB_CREATED", "Digital-card job created; publication is disabled by default.")
    save(job)
    print(f"Created {args.sku} in BRIEF_DRAFT.")


def create_eqp(args: argparse.Namespace) -> None:
    if args.actor not in APPROVERS:
        raise ControlPlaneError("An EQP job may begin at BLUEPRINT_APPROVED only from Semaj's approval.")
    path = job_path(args.sku)
    if path.exists():
        raise ControlPlaneError(f"Job already exists: {args.sku}.")
    job = {
        "job_id": args.sku,
        "venture": "out-legendary",
        "lane": "event-quest-pack",
        "title": args.title,
        "state": "BLUEPRINT_APPROVED",
        "assets": [],
        "listing": new_listing(),
        "audit_log": [],
    }
    event(job, args.actor, "JOB_CREATED", "Approved EQP blueprint entered the fail-closed visual-production lane.")
    save(job)
    print(f"Created {args.sku} in BLUEPRINT_APPROVED.")


def add_asset(args: argparse.Namespace) -> None:
    job = load(args.job)
    if job["state"] in {"APPROVED_FOR_LISTING", "LISTING_STAGED", "PUBLISHED"}:
        raise ControlPlaneError("Approved/listed work is immutable. Reopen it explicitly before changing assets.")
    roles = CARD_ROLES if job["lane"] == "digital-card" else EQP_ROLES
    if args.role not in roles:
        raise ControlPlaneError(f"Asset role must be one of: {', '.join(sorted(roles))}.")
    asset = Path(args.path).resolve()
    if not asset.is_file():
        raise ControlPlaneError(f"Asset file not found: {asset}")
    if any(item["role"] == args.role for item in job["assets"]):
        raise ControlPlaneError(f"A {args.role} asset is already recorded; replace is intentionally not automatic.")
    digest = sha256(asset)
    expected = CANONICAL_REFERENCE_HASHES.get(args.role)
    if expected and digest != expected:
        raise ControlPlaneError(
            f"{args.role} hash does not match the approved reference. Expected {expected}; got {digest}."
        )
    job["assets"].append({"role": args.role, "path": str(asset), "sha256": digest})
    event(job, args.actor, "ASSET_RECORDED", f"{args.role}: {asset.name}")
    save(job)
    print(f"Recorded {args.role} asset for {args.job}.")


def replace_asset(args: argparse.Namespace) -> None:
    """Swap a recorded asset for a different file, keeping the old one on record.

    `add-asset` deliberately refuses a role that is already recorded, so a
    genuine correction had no route through the tool and the only options were
    to hand-edit job.json or leave the job wrong. This is the card lane's
    equivalent of the EQP lane's reopen: the superseded asset is preserved in
    `superseded_assets` and named in the audit log, never quietly overwritten.

    Immutability after approval still holds. A reason is mandatory.
    """
    job = load(args.job)
    if job["state"] in {"APPROVED_FOR_LISTING", "LISTING_STAGED", "PUBLISHED"}:
        raise ControlPlaneError(
            "Approved/listed work is immutable. Reopen it explicitly before changing assets."
        )
    roles = CARD_ROLES if job["lane"] == "digital-card" else EQP_ROLES
    if args.role not in roles:
        raise ControlPlaneError(f"Asset role must be one of: {', '.join(sorted(roles))}.")
    existing = next((item for item in job["assets"] if item["role"] == args.role), None)
    if existing is None:
        raise ControlPlaneError(f"No {args.role} asset is recorded; use add-asset.")
    asset = Path(args.path).resolve()
    if not asset.is_file():
        raise ControlPlaneError(f"Asset file not found: {asset}")
    digest = sha256(asset)
    if digest == existing["sha256"]:
        raise ControlPlaneError(f"That file is already recorded as {args.role}; nothing to replace.")
    expected = CANONICAL_REFERENCE_HASHES.get(args.role)
    if expected and digest != expected:
        raise ControlPlaneError(
            f"{args.role} hash does not match the approved reference. Expected {expected}; got {digest}."
        )
    job.setdefault("superseded_assets", []).append(
        {"at": now(), "reason": args.reason, "asset": existing}
    )
    job["assets"] = [item for item in job["assets"] if item["role"] != args.role]
    job["assets"].append({"role": args.role, "path": str(asset), "sha256": digest})
    event(job, args.actor, "ASSET_REPLACED",
          f"{args.role}: {Path(existing['path']).name} -> {asset.name}. {args.reason}")
    save(job)
    print(f"Replaced {args.role} for {args.job}; the superseded asset is retained on the job.")


def transition(args: argparse.Namespace) -> None:
    job = load(args.job)
    old = job["state"]
    graph = CARD_FORWARD if job["lane"] == "digital-card" else EQP_FORWARD
    if args.to not in graph.get(old, set()):
        raise ControlPlaneError(f"Illegal transition {old} -> {args.to}.")
    approval_states = {
        "BRIEF_APPROVED", "APPROVED_FOR_LISTING", "PUBLISHED",
        "VISUAL_SYSTEM_APPROVED", "PACKAGE_APPROVED",
    }
    if args.to in approval_states and args.actor not in APPROVERS:
        raise ControlPlaneError(f"{args.to} requires an explicit Semaj approval event.")
    if job["lane"] == "event-quest-pack" and args.to == "REFERENCE_READY":
        missing = EQP_REFERENCE_ROLES - {asset["role"] for asset in job["assets"]}
        if missing:
            raise ControlPlaneError(f"REFERENCE_READY blocked; missing: {', '.join(sorted(missing))}.")
    if args.to == "PUBLISHED":
        listing = job.get("listing", {})
        receipt = listing.get("provider_receipt")
        if not listing.get("publish_authorized"):
            raise ControlPlaneError("PUBLISHED blocked: Semaj's explicit publication approval is required.")
        # This installation has no live Etsy/Shopify verification adapter.
        # A hand-entered JSON object or listing ID cannot serve as its receipt.
        if not isinstance(receipt, dict) or receipt.get("source") != "provider_api" or not receipt.get("verified_at"):
            raise ControlPlaneError(
                "PUBLISHED blocked: no verified Etsy/Shopify provider receipt is recorded. "
                "The current pipeline has no live publishing connector; status remains LISTING_STAGED."
            )
        raise ControlPlaneError(
            "PUBLISHED blocked: this installation has no live provider verification adapter. "
            "A provider receipt must be fetched and verified by an enabled Etsy/Shopify connector."
        )
    job["state"] = args.to
    event(job, args.actor, "STATE_TRANSITION", f"{old} -> {args.to}: {args.reason}")
    save(job)
    print(f"{args.job}: {old} -> {args.to}")


def qa_card(args: argparse.Namespace) -> None:
    job = load(args.job)
    if job["state"] != "QA_PENDING":
        raise ControlPlaneError("Card QA may run only from QA_PENDING.")
    roles = {asset["role"] for asset in job["assets"]}
    missing = CARD_ROLES - roles
    if missing:
        target = "QA_FAILED"
        detail = f"Missing required buyer/delivery assets: {', '.join(sorted(missing))}."
    else:
        target = "READY_FOR_SEMAJ_APPROVAL"
        detail = "Manifest complete: one Front, Inside, and Back asset is hash-recorded. Visual and listing review still require Semaj."
    job["state"] = target
    event(job, "Jarvis", "CARD_PACKAGE_QA", detail)
    save(job)
    print(f"{args.job}: QA_PENDING -> {target}. {detail}")


def qa_eqp_proofs(args: argparse.Namespace) -> None:
    job = load(args.job)
    if job["lane"] != "event-quest-pack" or job["state"] != "PROOF_QA_PENDING":
        raise ControlPlaneError("EQP proof QA may run only from PROOF_QA_PENDING in the EQP lane.")
    by_role = {asset["role"]: asset for asset in job["assets"]}
    missing = EQP_ROLES - set(by_role)
    failures = []
    if missing:
        failures.append(f"missing roles: {', '.join(sorted(missing))}")
    for role, expected in CANONICAL_REFERENCE_HASHES.items():
        item = by_role.get(role)
        if item and (not Path(item["path"]).is_file() or sha256(Path(item["path"])) != expected):
            failures.append(f"approved reference drift: {role}")
    for role, item in by_role.items():
        path = Path(item["path"])
        if not path.is_file() or sha256(path) != item["sha256"]:
            failures.append(f"asset missing or changed: {role}")
    if failures:
        target = "PROOF_QA_FAILED"
        detail = "; ".join(failures) + "."
    else:
        target = "READY_FOR_SEMAJ_VISUAL_REVIEW"
        detail = (
            "Reference hashes, locked documents, font manifest, and all three PDF/PNG proof pairs verified. "
            "Customer-facing visual approval still requires Semaj."
        )
    job["state"] = target
    event(job, "Jarvis", "EQP_PROOF_PACKAGE_QA", detail)
    save(job)
    print(f"{args.job}: PROOF_QA_PENDING -> {target}. {detail}")


def reject_eqp_proofs(args: argparse.Namespace) -> None:
    job = load(args.job)
    if args.actor not in APPROVERS:
        raise ControlPlaneError("Only Semaj may reject a proof set and reopen reference binding.")
    if job["lane"] != "event-quest-pack" or job["state"] != "READY_FOR_SEMAJ_VISUAL_REVIEW":
        raise ControlPlaneError("EQP rejection requires READY_FOR_SEMAJ_VISUAL_REVIEW.")
    job.setdefault("rejected_asset_sets", []).append({
        "at": now(), "reason": args.reason, "assets": job["assets"]
    })
    job["assets"] = []
    old = job["state"]
    job["state"] = "REFERENCE_BINDING"
    event(job, args.actor, "PROOF_SET_REJECTED", f"{old} -> REFERENCE_BINDING: {args.reason}")
    save(job)
    print(f"{args.job}: Revision rejected; reference binding reopened.")


def reopen_eqp_binding(args: argparse.Namespace) -> None:
    job = load(args.job)
    if args.actor not in APPROVERS:
        raise ControlPlaneError("Only Semaj may reopen an EQP job after review-ready state.")
    if job["lane"] != "event-quest-pack" or job["state"] != "READY_FOR_SEMAJ_VISUAL_REVIEW":
        raise ControlPlaneError("EQP rebinding requires READY_FOR_SEMAJ_VISUAL_REVIEW.")
    job.setdefault("superseded_bindings", []).append({"at": now(), "reason": args.reason, "assets": job["assets"]})
    job["assets"] = []
    job["state"] = "REFERENCE_BINDING"
    event(job, args.actor, "INPUT_BINDING_REOPENED", args.reason)
    save(job)
    print(f"{args.job}: input binding reopened without rejecting the proof artwork.")


def authorize_publish(args: argparse.Namespace) -> None:
    job = load(args.job)
    if args.actor not in APPROVERS:
        raise ControlPlaneError("Only Semaj may authorize publishing.")
    if job["state"] != "LISTING_STAGED":
        raise ControlPlaneError("Publishing authorization requires a staged listing.")
    job["listing"]["publish_authorized"] = True
    job["listing"]["etsy_listing_id"] = args.etsy_listing_id
    event(job, args.actor, "PUBLISH_AUTHORIZED", f"Staged Etsy listing: {args.etsy_listing_id}")
    save(job)
    print(f"Publishing authorization recorded for {args.job}; no Etsy action was taken.")


def set_shopify(args: argparse.Namespace) -> None:
    """Record which Shopify product this job became.

    Recording the link is a statement of fact, not an approval, so any actor
    may do it in any state. It does not authorize publication: PUBLISHED still
    requires `authorize-publish` from Semaj.
    """
    job = load(args.job)
    if not SHOPIFY_PRODUCT_GID.match(args.gid):
        raise ControlPlaneError(
            "Shopify product GID must look like gid://shopify/Product/<numeric id>."
        )
    listing = job.setdefault("listing", new_listing())
    for key, default in new_listing().items():
        listing.setdefault(key, default)
    previous = listing.get("shopify_product_gid")
    if previous and previous != args.gid and not args.replace:
        raise ControlPlaneError(
            f"{args.job} is already linked to {previous}. Pass --replace to change it."
        )
    listing["shopify_product_gid"] = args.gid
    detail = args.gid if not previous or previous == args.gid else f"{args.gid} (replaced {previous})"
    event(job, args.actor, "SHOPIFY_PRODUCT_LINKED", detail)
    save(job)
    print(f"{args.job}: linked to {args.gid}")


def status(args: argparse.Namespace) -> None:
    job = load(args.job)
    print(json.dumps(job, indent=2))


def generate_image(args: argparse.Namespace) -> None:
    """
    Generate an image using OpenAI provider and record it as a JARVIS asset.

    This command:
    - Calls OpenAI Images API with the provided prompt and optional reference image
    - Writes the generated image to the job's asset folder
    - Computes and records SHA-256
    - Records generation metadata in the job
    - Logs the generation event
    - DOES NOT change job state

    Responsibility separation:
    - Provider: API call only, returns bytes + metadata
    - Control plane: asset storage, SHA-256, registry, audit logging, state preservation
    """
    job = load(args.job)

    # Validate state - generation can happen in ASSET_PRODUCTION or QA_FAILED
    if job["state"] not in {"ASSET_PRODUCTION", "QA_FAILED"}:
        raise ControlPlaneError(
            f"Image generation can only occur in ASSET_PRODUCTION or QA_FAILED states. "
            f"Current state: {job['state']}"
        )

    # Validate asset role
    roles = CARD_ROLES if job["lane"] == "digital-card" else EQP_ROLES
    if args.role not in roles:
        raise ControlPlaneError(f"Asset role must be one of: {', '.join(sorted(roles))}.")

    # Check if asset already exists
    if any(item["role"] == args.role for item in job["assets"]):
        raise ControlPlaneError(f"A {args.role} asset already exists; replace is intentionally not automatic.")

    # Prepare asset output path
    asset_dir = job_path(args.job).parent / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    asset_file = asset_dir / f"{args.role}.png"

    if asset_file.exists():
        raise ControlPlaneError(f"Asset file already exists: {asset_file}")

    try:
        # Initialize provider and build request
        provider = OpenAIImageProvider()

        reference_path: Optional[Path] = None
        if args.reference_image:
            reference_path = Path(args.reference_image).resolve()
            if not reference_path.is_file():
                raise ControlPlaneError(f"Reference image not found: {reference_path}")

        generation_request = ImageGenerationRequest(
            model=args.model or "gpt-image-2.5-sunburst",
            prompt=args.prompt,
            size=args.size or "1024x1536",
            quality=args.quality or "hd",
            n=1,
            reference_image_path=reference_path,
        )

        # Call provider to generate image
        result = provider.generate(generation_request)

        # Write image to asset folder
        asset_file.write_bytes(result.image_bytes)

        # Compute SHA-256 of written file
        digest = sha256(asset_file)

        # Record asset in job
        job["assets"].append({
            "role": args.role,
            "path": str(asset_file),
            "sha256": digest,
            "generated_by": "OpenAIImageProvider",
            "generated_at": now(),
            "model": result.model,
            "reference_image_used": result.reference_image_used,
        })

        # Log the generation event
        ref_info = f" (with reference image)" if result.reference_image_used else " (text-only)"
        event(
            job,
            "OpenAIImageProvider",
            "GENERATED_IMAGE_ASSET",
            f"{args.role}{ref_info}: {asset_file.name}, SHA-256: {digest[:16]}...",
        )

        # Save job - state is preserved
        save(job)

        print(f"Generated {args.role} image for {args.job} at {asset_file}")
        print(f"  SHA-256: {digest}")
        print(f"  Reference image: {result.reference_image_used}")
        print(f"  Model: {result.model}")
        print(f"  Job state preserved: {job['state']}")

    except ControlPlaneError:
        raise
    except Exception as exc:
        # Clean up partial writes on any error
        if asset_file.exists():
            asset_file.unlink()
        raise ControlPlaneError(f"Image generation failed: {exc}")


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    actions = cli.add_subparsers(dest="command", required=True)
    item = actions.add_parser("create-card")
    item.add_argument("--sku", required=True)
    item.add_argument("--title", required=True)
    item.set_defaults(func=create_card)
    item = actions.add_parser("create-eqp")
    item.add_argument("--sku", required=True)
    item.add_argument("--title", required=True)
    item.add_argument("--actor", required=True)
    item.set_defaults(func=create_eqp)
    item = actions.add_parser("add-asset")
    item.add_argument("--job", required=True)
    item.add_argument("--role", required=True)
    item.add_argument("--path", required=True)
    item.add_argument("--actor", default="Jarvis")
    item.set_defaults(func=add_asset)
    item = actions.add_parser("replace-asset")
    item.add_argument("--job", required=True)
    item.add_argument("--role", required=True)
    item.add_argument("--path", required=True)
    item.add_argument("--actor", default="Jarvis")
    item.add_argument("--reason", required=True, help="Why the recorded asset is being superseded.")
    item.set_defaults(func=replace_asset)
    item = actions.add_parser("transition")
    item.add_argument("--job", required=True)
    item.add_argument("--to", required=True, choices=sorted(set(CARD_FORWARD) | set(EQP_FORWARD)))
    item.add_argument("--actor", required=True)
    item.add_argument("--reason", required=True)
    item.set_defaults(func=transition)
    item = actions.add_parser("qa-card")
    item.add_argument("--job", required=True)
    item.set_defaults(func=qa_card)
    item = actions.add_parser("qa-eqp-proofs")
    item.add_argument("--job", required=True)
    item.set_defaults(func=qa_eqp_proofs)
    item = actions.add_parser("reject-eqp-proofs")
    item.add_argument("--job", required=True)
    item.add_argument("--actor", required=True)
    item.add_argument("--reason", required=True)
    item.set_defaults(func=reject_eqp_proofs)
    item = actions.add_parser("reopen-eqp-binding")
    item.add_argument("--job", required=True)
    item.add_argument("--actor", required=True)
    item.add_argument("--reason", required=True)
    item.set_defaults(func=reopen_eqp_binding)
    item = actions.add_parser("authorize-publish")
    item.add_argument("--job", required=True)
    item.add_argument("--actor", required=True)
    item.add_argument("--etsy-listing-id", required=True)
    item.set_defaults(func=authorize_publish)
    item = actions.add_parser("generate-image")
    item.add_argument("--job", required=True, help="Job ID")
    item.add_argument("--role", required=True, help="Asset role (front, inside, back, etc.)")
    item.add_argument("--prompt", required=True, help="Visual generation prompt")
    item.add_argument("--model", default="gpt-image-2.5-sunburst", help="OpenAI model (default: gpt-image-2.5-sunburst)")
    item.add_argument("--size", default="1024x1536", help="Image size (default: 1024x1536)")
    item.add_argument("--quality", default="hd", help="Image quality (default: hd)")
    item.add_argument("--reference-image", help="Optional path to reference/master image")
    item.set_defaults(func=generate_image)
    item = actions.add_parser("set-shopify")
    item.add_argument("--job", required=True)
    item.add_argument("--gid", required=True, help="gid://shopify/Product/<numeric id>")
    item.add_argument("--actor", default="Jarvis")
    item.add_argument("--replace", action="store_true", help="Overwrite an existing link.")
    item.set_defaults(func=set_shopify)
    item = actions.add_parser("status")
    item.add_argument("--job", required=True)
    item.set_defaults(func=status)
    return cli


if __name__ == "__main__":
    try:
        args = parser().parse_args()
        args.func(args)
    except ControlPlaneError as exc:
        raise SystemExit(f"BLOCKED: {exc}")
