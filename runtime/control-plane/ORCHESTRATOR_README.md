# Card Orchestrator — O&L Workflow Automation

The Card Orchestrator (`card_orchestrator.py`) is the automation layer for the Out & Legendary product pipeline. It translates natural-language commands into control-plane state transitions, manages asset validation, and enforces approval gates.

## Quick Start

```bash
cd C:\Users\Arach\my-agent\jarvis-control-plane
python card_orchestrator.py <command> [options]
```

## Commands

### Create a New Card

```bash
python card_orchestrator.py create \
  --title "Get Well Soon" \
  --type greeting \
  --sku OAL-CARD-018 \
  --front <path-to-front-image> \
  --inside <path-to-inside-image> \
  --back <path-to-back-image>
```

**Output:** Card moves to `BRIEF_DRAFT` state. Rook/Semaj reviews the brief and approves (or makes changes) before production begins.

**Asset Types:**
- `greeting` — requires front, inside, back
- `celebration` — requires front, inside, back
- `event-quest-pack` (EQP) — requires locked_copy, component_manifest, visual_spec, brand_style_reference, modern_arcane_reference, official_logo, font_manifest, plus proof PDFs/PNGs

### Approve Brief & Start Production

```bash
python card_orchestrator.py approve --sku OAL-CARD-018 --brief
```

**Transitions:** `BRIEF_DRAFT` → `BRIEF_APPROVED` → `ASSET_PRODUCTION` → `QA_PENDING` → `READY_FOR_SEMAJ_APPROVAL`

Stops at `READY_FOR_SEMAJ_APPROVAL` for final visual review.

### Approve Final Design & Stage for Publishing

```bash
python card_orchestrator.py approve --sku OAL-CARD-018 --final
```

**Transitions:** `READY_FOR_SEMAJ_APPROVAL` → `APPROVED_FOR_LISTING` → `LISTING_STAGED`

Awaits publishing authorization.

### Authorize & Publish to Etsy/Shopify

```bash
python card_orchestrator.py publish --sku OAL-CARD-018 --etsy-id <listing-id>
```

**Transitions:** `LISTING_STAGED` → `PUBLISHED`

Records Etsy listing ID and marks ready for publication.

### Reject & Return to Production

```bash
python card_orchestrator.py reject --sku OAL-CARD-018 --reason "Adjust color on front panel"
```

**Transitions:** `READY_FOR_SEMAJ_APPROVAL` → `ASSET_PRODUCTION`

Returns the card for design revision without losing approval history.

### Check Card Status

```bash
python card_orchestrator.py status --sku OAL-CARD-018
```

Displays current state, assets, and complete audit log.

### Resume Workflow (Pending Assets)

```bash
python card_orchestrator.py resume --sku OAL-CARD-018 --front <new-path>
```

Continues workflow if assets were pending Semaj input.

## State Machine Reference

### Digital Card States

```
BRIEF_DRAFT
  ↓ [Semaj approves]
BRIEF_APPROVED
  ↓ [Auto]
ASSET_PRODUCTION
  ↓ [Auto]
QA_PENDING
  ↓ [Auto, validates all assets present]
READY_FOR_SEMAJ_APPROVAL
  ↓ [Semaj approves] OR [Semaj rejects] → ASSET_PRODUCTION
APPROVED_FOR_LISTING
  ↓ [Auto]
LISTING_STAGED
  ↓ [Semaj authorizes publish]
PUBLISHED
```

### Event Quest Pack (EQP) States

```
BLUEPRINT_APPROVED [created at this state by Semaj]
  ↓ [Auto]
REFERENCE_BINDING
  ↓ [All reference assets added]
REFERENCE_READY
  ↓ [Auto]
PROOF_PRODUCTION
  ↓ [Auto]
PROOF_QA_PENDING
  ↓ [Auto, validates all proof assets + reference hashes]
READY_FOR_SEMAJ_VISUAL_REVIEW
  ↓ [Semaj approves] OR [Semaj rejects] → REFERENCE_BINDING
VISUAL_SYSTEM_APPROVED
  ↓ [Auto]
COMPONENT_PRODUCTION
  ↓ [Auto]
PACKAGE_QA_PENDING
  ↓ [Auto, validates component manifest + package integrity]
READY_FOR_SEMAJ_PACKAGE_APPROVAL
  ↓ [Semaj approves]
PACKAGE_APPROVED
  ↓ [Auto]
LISTING_STAGED
  ↓ [Semaj authorizes publish]
PUBLISHED
```

## Asset Requirements

**Greeting Cards:**
- `front` — Primary cover image (PNG/JPEG)
- `inside` — Interior fold image (PNG/JPEG)
- `back` — Back cover image (PNG/JPEG)

**Event Quest Packs:**
- Reference assets: locked_copy, component_manifest, visual_spec, brand_style_reference, modern_arcane_reference, official_logo, font_manifest
- Proof assets: proof_01_pdf, proof_01_png, proof_02_pdf, proof_02_png, proof_03_pdf, proof_03_png

Reference hashes are validated against canonical approved versions (see `control_plane.py` for hash definitions).

## Logging

All operations are logged to `orchestration.log` with timestamps and actor attribution:

```
[2026-09-18 14:22:15] CREATE: OAL-CARD-018 ("Get Well Soon") created in BRIEF_DRAFT
[2026-09-18 14:23:42] APPROVE_BRIEF: OAL-CARD-018 transitioned BRIEF_DRAFT → BRIEF_APPROVED
[2026-09-18 14:23:43] AUTO_TRANSITION: OAL-CARD-018 BRIEF_APPROVED → ASSET_PRODUCTION
...
```

## Integration with Control Plane

The orchestrator wraps `control_plane.py` CLI calls. Each command translates to one or more control-plane operations:

- `create` → `control_plane.py create-card` + asset recording
- `approve --brief` → series of `control_plane.py transition` calls
- `approve --final` → series of `control_plane.py transition` calls
- `publish` → `control_plane.py authorize-publish` + final transition
- `reject` → `control_plane.py transition` back to production
- `status` → reads job.json directly

All state transitions are validated by the control plane; the orchestrator enforces approval gates on top.

## ECC Integration

When creating a card with `create`, if assets are not immediately available, the orchestrator can note them as pending. Rook (via ECC agents) can then:

1. Use ECC's **Planning Agent** to decompose the design work
2. Use ECC's **Documentation Skill** to generate brand guidelines from reference assets
3. Use ECC's **Review Agent** to validate proof sets against brand standards

Once assets are ready, use `resume` to continue the workflow.

## Approval Gates

Only **Semaj** can approve state transitions marked as approval states in `control_plane.py`:

- `BRIEF_APPROVED`
- `APPROVED_FOR_LISTING`
- `PUBLISHED`
- (EQP) `VISUAL_SYSTEM_APPROVED`
- (EQP) `PACKAGE_APPROVED`

All other transitions are automatic once assets are validated.

## Example: Full Greeting Card Workflow

```bash
# 1. Create a new greeting card with assets provided
python card_orchestrator.py create \
  --title "Happy Birthday" \
  --type greeting \
  --sku OAL-CARD-020 \
  --front ./assets/bday_front.png \
  --inside ./assets/bday_inside.png \
  --back ./assets/bday_back.png

# 2. Brief is created; Semaj reviews and approves
python card_orchestrator.py status --sku OAL-CARD-020

# 3. Approve brief, moves through production pipeline
python card_orchestrator.py approve --sku OAL-CARD-020 --brief

# 4. Waits at READY_FOR_SEMAJ_APPROVAL for visual sign-off
python card_orchestrator.py status --sku OAL-CARD-020

# 5. Semaj approves final design
python card_orchestrator.py approve --sku OAL-CARD-020 --final

# 6. Card is staged; get Etsy listing ID from O&L shop
# (Assume listing ID = 1234567890)

# 7. Authorize publishing
python card_orchestrator.py publish --sku OAL-CARD-020 --etsy-id 1234567890

# 8. Card is live on Etsy
python card_orchestrator.py status --sku OAL-CARD-020
```

## Troubleshooting

**"No job named X"** → SKU doesn't exist. Check spelling or create with `create` command.

**"Illegal transition X → Y"** → State machine doesn't allow that transition. Check current state with `status`.

**"Missing required assets"** → Card is missing one or more required asset roles. Check asset types for your card type.

**"A <role> asset is already recorded"** → Asset role already exists. The orchestrator intentionally does not auto-replace; manually correct in control_plane.py if needed.

For deeper debugging, inspect the job's audit log: `status --sku <SKU>` shows full event history.

## Command Reference

```
create          Create new card with assets
approve         Approve brief or final design
publish         Authorize publication + publish
reject          Return card to production
resume          Continue workflow with pending assets
status          Display card state and audit log
```

## Files & Paths

- **Orchestrator:** `C:\Users\Arach\my-agent\jarvis-control-plane\card_orchestrator.py`
- **Control Plane:** `C:\Users\Arach\my-agent\jarvis-control-plane\control_plane.py`
- **Jobs Storage:** `C:\Users\Arach\my-agent\jarvis-control-plane\jobs\`
- **Logs:** `C:\Users\Arach\my-agent\jarvis-control-plane\orchestration.log`
- **JARVIS Vault:** `C:\Users\Arach\Documents\Jarvis\`

---

**Version:** 1.0
**Date:** 2026-09-18
**Status:** Deployed, integrated with ECC
**Author:** Rook (via Claude Code + ECC agents)
