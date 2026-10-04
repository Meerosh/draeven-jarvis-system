#!/usr/bin/env python3
"""
O&L Card Orchestrator: Full pipeline automation for Out & Legendary card creation.
Handles natural-language input, asset resolution, control plane integration, and approval gating.

Usage:
    python card_orchestrator.py create --title "Get Well" --type greeting
    python card_orchestrator.py create --title "Happy Birthday" --type celebration --assets-provided
    python card_orchestrator.py status --sku OAL-CARD-018
    python card_orchestrator.py approve --sku OAL-CARD-018 --actor Semaj
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent
CONTROL_PLANE = ROOT / "control_plane.py"
JOBS = ROOT / "jobs"
ORCHESTRATOR_LOG = ROOT / "orchestration.log"

# Approved O&L branding assets and metadata
APPROVED_ASSETS = {
    "modern_arcane_reference": "73d06f5ce7cf4dad6860c02bbabb70e9e8816cc8646ce808a540db5571ff99cb",
    "brand_style_reference": "e70d6af85b58398fc7536f5b105e53285b66d61e035deff0ce46dcbad5ed62c8",
    "official_logo": "c40eb53d0e56ef4e60dff85670d3f600a782316086a1f5326a038de8a8364ad2",
}

# Existing product templates (from 17 approved products)
PRODUCT_TEMPLATES = {
    "greeting": {
        "name": "Greeting Card",
        "default_size": "A5",
        "roles_required": ["front", "inside", "back"],
        "description": "Standard 5x7 greeting card with front, inside, back",
    },
    "celebration": {
        "name": "Celebration Card",
        "default_size": "A5",
        "roles_required": ["front", "inside", "back"],
        "description": "Celebration card from the LGBTQIA+ geek collection",
    },
    "event-quest-pack": {
        "name": "Event Quest Pack",
        "default_size": "A4",
        "roles_required": ["front", "back"],
        "description": "Event-specific quest pack with locked references",
    },
}

class OrchestratorError(RuntimeError):
    pass


def log_event(message: str) -> None:
    """Log an orchestration event."""
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    with open(ORCHESTRATOR_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[LOG] {message}")


def generate_sku(card_type: str) -> str:
    """Generate the next SKU for a card type."""
    # Pattern: OAL-CARD-NNN for standard cards
    job_folders = list(JOBS.glob("OAL-CARD-*"))
    if not job_folders:
        return "OAL-CARD-001"

    numbers = [int(f.name.split("-")[-1]) for f in job_folders if f.name.startswith("OAL-CARD-")]
    next_num = max(numbers) + 1 if numbers else 1
    return f"OAL-CARD-{next_num:03d}"


def resolve_assets(sku: str, card_type: str, provided_paths: dict[str, str] | None = None) -> dict[str, str]:
    """
    Resolve asset paths for the card.

    If provided_paths supplied: use those.
    Otherwise: return a spec for Semaj to provide them.
    """
    template = PRODUCT_TEMPLATES.get(card_type)
    if not template:
        raise OrchestratorError(f"Unknown card type: {card_type}")

    required_roles = template["roles_required"]
    assets = {}

    if provided_paths:
        for role in required_roles:
            if role not in provided_paths:
                raise OrchestratorError(f"Missing required asset: {role}")
            assets[role] = provided_paths[role]
        log_event(f"{sku}: Assets provided by user for {', '.join(required_roles)}")
    else:
        log_event(f"{sku}: Asset spec created; waiting for Semaj to provide {', '.join(required_roles)}")
        # Return a placeholder spec that Semaj fills in
        assets = {role: f"[PENDING: {role} asset path]" for role in required_roles}

    return assets


def create_card(
    title: str,
    card_type: str = "greeting",
    sku: str | None = None,
    provided_paths: dict[str, str] | None = None,
) -> str:
    """Create a new O&L card job and run through QA to READY_FOR_SEMAJ_APPROVAL."""

    # Generate SKU if not provided
    if not sku:
        sku = generate_sku(card_type)

    log_event(f"START: Create card {sku} ({card_type}): {title}")

    # Resolve assets
    assets = resolve_assets(sku, card_type, provided_paths)
    for role in assets:
        if assets[role].startswith("[PENDING"):
            log_event(f"{sku}: ⚠️  ASSET PENDING: Semaj must provide {role}")

    # Step 1: Create card via control_plane
    cmd = [
        "py", str(CONTROL_PLANE), "create-card",
        "--sku", sku,
        "--title", title,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_event(f"{sku}: FAILED at create-card: {result.stderr}")
        raise OrchestratorError(f"create-card failed: {result.stderr}")
    log_event(f"{sku}: Job created in BRIEF_DRAFT")

    # Step 2: Add assets if available
    for role, path in assets.items():
        if path.startswith("[PENDING"):
            log_event(f"{sku}: Skipping {role} (waiting for Semaj)")
            continue

        cmd = [
            "py", str(CONTROL_PLANE), "add-asset",
            "--job", sku,
            "--role", role,
            "--path", path,
            "--actor", "Jarvis",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log_event(f"{sku}: WARNING at add-asset ({role}): {result.stderr}")
        else:
            log_event(f"{sku}: Asset added ({role})")

    # Step 3: Move to BRIEF_APPROVED (Jarvis can do this; it's not an approval state)
    # Actually, looking at control_plane.py line 180: BRIEF_APPROVED is in approval_states
    # So we need Semaj's approval to move to BRIEF_APPROVED
    # Instead, we'll move to QA_PENDING directly if assets are ready, or wait if not

    # Check if all assets are present
    job = load_job(sku)
    template = PRODUCT_TEMPLATES[card_type]
    asset_roles = {a["role"] for a in job["assets"]}
    missing = set(template["roles_required"]) - asset_roles

    if missing:
        log_event(f"{sku}: ⚠️  WAITING FOR ASSETS: {', '.join(missing)}")
        print(f"\n{'='*70}")
        print(f"CARD {sku} CREATED — WAITING FOR ASSETS")
        print(f"{'='*70}")
        print(f"Title: {title}")
        print(f"Type: {card_type}")
        print(f"Missing assets: {', '.join(missing)}")
        print(f"\nAdd assets with:")
        for role in missing:
            print(f"  py control_plane.py add-asset --job {sku} --role {role} --path <path>")
        print(f"\nThen resume with:")
        print(f"  python card_orchestrator.py resume --sku {sku}")
        print(f"{'='*70}\n")
        return sku

    # Step 4: Transition through states to READY_FOR_SEMAJ_APPROVAL
    # BRIEF_DRAFT -> BRIEF_APPROVED (requires Semaj)
    # So we'll transition to ASSET_PRODUCTION first (Jarvis can do this)
    # Actually, looking at the state machine: BRIEF_DRAFT only goes to BRIEF_APPROVED
    # So we need Semaj's approval first

    # Let's present to Semaj for BRIEF_APPROVED
    log_event(f"{sku}: All assets present; ready for BRIEF_APPROVED approval")
    print(f"\n{'='*70}")
    print(f"CARD {sku} READY FOR BRIEF APPROVAL")
    print(f"{'='*70}")
    print(f"Title: {title}")
    print(f"Type: {card_type}")
    print(f"Assets: {', '.join(asset_roles)}")
    print(f"\nApprove brief with:")
    print(f"  python card_orchestrator.py approve --sku {sku} --brief")
    print(f"{'='*70}\n")

    return sku


def load_job(sku: str) -> dict[str, Any]:
    """Load a job from control_plane."""
    cmd = ["py", str(CONTROL_PLANE), "status", "--job", sku]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise OrchestratorError(f"Failed to load job {sku}: {result.stderr}")
    return json.loads(result.stdout)


def approve_brief(sku: str) -> str:
    """Approve brief and move card through asset production to READY_FOR_SEMAJ_APPROVAL."""
    log_event(f"APPROVE_BRIEF: {sku}")

    # Transition BRIEF_DRAFT -> BRIEF_APPROVED
    cmd = [
        "py", str(CONTROL_PLANE), "transition",
        "--job", sku,
        "--to", "BRIEF_APPROVED",
        "--actor", "Semaj",
        "--reason", "Brief approved by Semaj; proceeding to asset production",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_event(f"{sku}: FAILED at transition to BRIEF_APPROVED: {result.stderr}")
        raise OrchestratorError(f"Transition failed: {result.stderr}")
    log_event(f"{sku}: Moved to BRIEF_APPROVED")

    # Transition BRIEF_APPROVED -> ASSET_PRODUCTION (Jarvis can do this)
    cmd = [
        "py", str(CONTROL_PLANE), "transition",
        "--job", sku,
        "--to", "ASSET_PRODUCTION",
        "--actor", "Jarvis",
        "--reason", "Brief approved; moving to asset production",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_event(f"{sku}: WARNING at transition to ASSET_PRODUCTION: {result.stderr}")
    else:
        log_event(f"{sku}: Moved to ASSET_PRODUCTION")

    # Transition ASSET_PRODUCTION -> QA_PENDING (Jarvis can do this)
    cmd = [
        "py", str(CONTROL_PLANE), "transition",
        "--job", sku,
        "--to", "QA_PENDING",
        "--actor", "Jarvis",
        "--reason", "Assets ready; moving to QA",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_event(f"{sku}: WARNING at transition to QA_PENDING: {result.stderr}")
    else:
        log_event(f"{sku}: Moved to QA_PENDING")

    # Run QA
    cmd = ["py", str(CONTROL_PLANE), "qa-card", "--job", sku]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_event(f"{sku}: FAILED at QA: {result.stderr}")
        raise OrchestratorError(f"QA failed: {result.stderr}")
    log_event(f"{sku}: QA passed; moved to READY_FOR_SEMAJ_APPROVAL")

    # Display card for approval
    job = load_job(sku)
    print(f"\n{'='*70}")
    print(f"CARD {sku} READY FOR FINAL APPROVAL")
    print(f"{'='*70}")
    print(f"Title: {job['title']}")
    print(f"State: {job['state']}")
    print(f"Assets:")
    for asset in job["assets"]:
        print(f"  - {asset['role']}: {Path(asset['path']).name}")
    print(f"\nApprove for listing with:")
    print(f"  python card_orchestrator.py approve --sku {sku} --final")
    print(f"\nReject and return to asset production:")
    print(f"  python card_orchestrator.py reject --sku {sku}")
    print(f"{'='*70}\n")

    return sku


def approve_final(sku: str) -> str:
    """Approve card for listing and move to LISTING_STAGED."""
    log_event(f"APPROVE_FINAL: {sku}")

    # Transition READY_FOR_SEMAJ_APPROVAL -> APPROVED_FOR_LISTING
    cmd = [
        "py", str(CONTROL_PLANE), "transition",
        "--job", sku,
        "--to", "APPROVED_FOR_LISTING",
        "--actor", "Semaj",
        "--reason", "Card approved; ready for listing",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_event(f"{sku}: FAILED at approve for listing: {result.stderr}")
        raise OrchestratorError(f"Approval failed: {result.stderr}")
    log_event(f"{sku}: Approved for listing")

    # Transition APPROVED_FOR_LISTING -> LISTING_STAGED
    cmd = [
        "py", str(CONTROL_PLANE), "transition",
        "--job", sku,
        "--to", "LISTING_STAGED",
        "--actor", "Jarvis",
        "--reason", "Listing staged for publication",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_event(f"{sku}: WARNING at stage listing: {result.stderr}")
    else:
        log_event(f"{sku}: Listing staged")

    print(f"\n{'='*70}")
    print(f"CARD {sku} STAGED FOR PUBLICATION")
    print(f"{'='*70}")
    print("\nLive Etsy publishing is not connected. The job remains LISTING_STAGED until a real provider integration is implemented and returns a verifiable receipt.")
    print(f"{'='*70}\n")

    return sku


def publish(sku: str, etsy_id: str) -> str:
    """Stop local state from claiming an Etsy publication that never occurred."""
    del etsy_id  # A caller-supplied ID is not a provider receipt.
    log_event(f"{sku}: BLOCKED publication request; no live Etsy connector is implemented")
    raise OrchestratorError(
        f"{sku} remains LISTING_STAGED. This installation has no Etsy publishing connector, "
        "so it cannot publish or verify a listing. Do not mark it PUBLISHED based on a manually supplied ID."
    )


def reject(sku: str) -> str:
    """Reject card at READY_FOR_SEMAJ_APPROVAL and return to ASSET_PRODUCTION."""
    log_event(f"REJECT: {sku}")

    cmd = [
        "py", str(CONTROL_PLANE), "transition",
        "--job", sku,
        "--to", "QA_FAILED",
        "--actor", "Semaj",
        "--reason", "Rejected; returning to asset production",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_event(f"{sku}: FAILED at reject: {result.stderr}")
        raise OrchestratorError(f"Rejection failed: {result.stderr}")
    log_event(f"{sku}: Rejected; moved to ASSET_PRODUCTION")

    print(f"\nCard {sku} rejected and returned to ASSET_PRODUCTION.\n")
    return sku


def status(sku: str) -> None:
    """Display card job status."""
    job = load_job(sku)
    print(f"\n{'='*70}")
    print(f"CARD {sku} STATUS")
    print(f"{'='*70}")
    print(f"Title: {job['title']}")
    print(f"State: {job['state']}")
    print(f"Venture: {job['venture']}")
    print(f"Assets:")
    for asset in job["assets"]:
        print(f"  - {asset['role']}: {Path(asset['path']).name} (sha256: {asset['sha256'][:16]}...)")
    print(f"\nAudit Log:")
    for entry in job["audit_log"][-5:]:  # Last 5 entries
        print(f"  [{entry['at']}] {entry['actor']}: {entry['action']} — {entry['detail']}")
    print(f"{'='*70}\n")


def resume(sku: str) -> str:
    """Resume orchestration for a card that was waiting on assets."""
    log_event(f"RESUME: {sku}")
    job = load_job(sku)

    if job["state"] != "BRIEF_DRAFT":
        log_event(f"{sku}: Not in BRIEF_DRAFT; cannot resume asset waiting")
        raise OrchestratorError(f"Card is in {job['state']}, not BRIEF_DRAFT")

    template = PRODUCT_TEMPLATES.get(job.get("type", "greeting"))
    if not template:
        raise OrchestratorError("Card type unknown")

    asset_roles = {a["role"] for a in job["assets"]}
    missing = set(template["roles_required"]) - asset_roles

    if missing:
        log_event(f"{sku}: Still waiting for: {', '.join(missing)}")
        raise OrchestratorError(f"Missing assets: {', '.join(missing)}")

    # Asset completeness is not user approval. Keep the job in BRIEF_DRAFT.
    print(f"\nCARD {sku} has all required assets and remains in BRIEF_DRAFT.")
    print(f"Review the brief, then explicitly approve with: python card_orchestrator.py approve --sku {sku} --brief")
    return sku


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(
        description="O&L Card Orchestrator: Full pipeline for card creation, approval, and publication."
    )
    subparsers = cli.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a new O&L card")
    create.add_argument("--title", required=True, help="Card title/description")
    create.add_argument("--type", default="greeting", help="Card type (greeting, celebration, event-quest-pack)")
    create.add_argument("--sku", help="SKU (auto-generated if omitted)")
    create.add_argument("--front", help="Path to front asset")
    create.add_argument("--inside", help="Path to inside asset")
    create.add_argument("--back", help="Path to back asset")
    create.set_defaults(func=create)

    approve_brief = subparsers.add_parser("approve", help="Approve card at review point")
    approve_brief.add_argument("--sku", required=True, help="Card SKU")
    approve_brief.add_argument("--brief", action="store_true", help="Approve brief (move to QA)")
    approve_brief.add_argument("--final", action="store_true", help="Approve final card (move to listing)")
    approve_brief.set_defaults(func=approve_brief)

    reject = subparsers.add_parser("reject", help="Reject card and return to asset production")
    reject.add_argument("--sku", required=True, help="Card SKU")
    reject.set_defaults(func=reject)

    publish = subparsers.add_parser("publish", help="Blocked: this installation has no live Etsy publishing connector")
    publish.add_argument("--sku", required=True, help="Card SKU")
    publish.add_argument("--etsy-id", required=True, help="This ID is not treated as proof that a listing was published")
    publish.set_defaults(func=publish)

    status = subparsers.add_parser("status", help="Display card status")
    status.add_argument("--sku", required=True, help="Card SKU")
    status.set_defaults(func=status)

    resume = subparsers.add_parser("resume", help="Resume card that was waiting on assets")
    resume.add_argument("--sku", required=True, help="Card SKU")
    resume.set_defaults(func=resume)

    return cli


def main() -> None:
    args = parser().parse_args()

    try:
        if args.command == "create":
            assets = {}
            if args.front:
                assets["front"] = args.front
            if args.inside:
                assets["inside"] = args.inside
            if args.back:
                assets["back"] = args.back
            sku = create_card(
                title=args.title,
                card_type=args.type,
                sku=args.sku,
                provided_paths=assets if assets else None,
            )
            print(f"Created: {sku}")
        elif args.command == "approve":
            if args.brief:
                approve_brief(args.sku)
            elif args.final:
                approve_final(args.sku)
            else:
                raise OrchestratorError("Specify --brief or --final")
        elif args.command == "reject":
            reject(args.sku)
        elif args.command == "publish":
            publish(args.sku, args.etsy_id)
        elif args.command == "status":
            status(args.sku)
        elif args.command == "resume":
            resume(args.sku)
    except OrchestratorError as e:
        log_event(f"ERROR: {e}")
        raise SystemExit(f"BLOCKED: {e}")


if __name__ == "__main__":
    main()
