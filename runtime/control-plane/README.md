# Jarvis Production Control Plane

The approval-gated operational layer for Semaj's ventures.

## Lane 1: O&L digital cards

This first implementation creates an auditable job folder for each card and refuses to move it past an approval boundary without an explicit Semaj approval event. It deliberately does **not** connect to Etsy or publish anything.

```
BRIEF_DRAFT
  -> BRIEF_APPROVED
  -> ASSET_PRODUCTION
  -> QA_PENDING
  -> READY_FOR_SEMAJ_APPROVAL
  -> APPROVED_FOR_LISTING
  -> LISTING_STAGED
  -> PUBLISHED
```

`QA_FAILED` returns to `ASSET_PRODUCTION`. `PUBLISHED` requires `--actor Semaj`, so the command line cannot mistake an agent recommendation for publication approval.

## Use

Run from this folder with the system Python:

```powershell
py control_plane.py create-card --sku OAL-CARD-017 --title "Working title"
py control_plane.py add-asset --job OAL-CARD-017 --role front --path "C:\path\front.png"
py control_plane.py add-asset --job OAL-CARD-017 --role inside --path "C:\path\inside.png"
py control_plane.py add-asset --job OAL-CARD-017 --role back --path "C:\path\back.png"
py control_plane.py transition --job OAL-CARD-017 --to BRIEF_APPROVED --actor Semaj --reason "Brief approved"
py control_plane.py set-shopify --job OAL-CARD-017 --gid "gid://shopify/Product/8557764280390"
py control_plane.py status --job OAL-CARD-017
```

Assets are hash-recorded. The `qa-card` command requires exactly one Front, Inside, and Back artifact before it can put a job in `READY_FOR_SEMAJ_APPROVAL`.

`add-asset` refuses a role that is already recorded, so a genuine correction goes through `replace-asset`, which takes a mandatory `--reason`:

```powershell
py control_plane.py replace-asset --job OAL-CARD-018 --role back --path "C:\path\house-back.png" --reason "Collection ruling: this card is Rainbow & Ruin, so it takes the house back"
```

The superseded file is retained on the job under `superseded_assets` and named in the audit log, never quietly overwritten. This is the card lane's equivalent of the EQP lane's `reopen-eqp-binding`. Immutability after approval still applies: once a job reaches `APPROVED_FOR_LISTING` it is refused.

`set-shopify` records which live Shopify product a job became, in `listing.shopify_product_gid`. That link is a statement of fact rather than an approval, so any actor may set it in any state, and it does **not** authorize publication: `PUBLISHED` still requires `authorize-publish` from Semaj. Relinking to a different product requires `--replace`, so a mistyped SKU cannot silently repoint a card at another listing.

### Terminal state for Shopify-only products

**`LISTING_STAGED` is the stopping point for a card that exists only in Shopify.** Decided 2026-09-21.

`PUBLISHED` requires `publish_authorized`, which only `authorize-publish` sets, and that command demands an `--etsy-listing-id`. This lane was built when Etsy was the sales channel. A Shopify-only product has no Etsy ID to supply, so it cannot legitimately reach `PUBLISHED` and should not pretend to.

`LISTING_STAGED` is the honest description anyway: the product exists in Shopify as a draft and nothing is public. Revisit when a card is actually listed on Etsy and a real listing ID exists, or if Shopify becomes the primary channel and `authorize-publish` needs a Shopify mode.

This is intentionally the first control layer, not the renderer. The existing renderer and O&L canon/QA systems remain the specialist tools that produce and assess the work.

## Lane 2: O&L Event Quest Packs

The EQP lane prevents proof generation from starting until the approved copy, component manifest, visual specification, font manifest, official logo, brand sheet, and true Modern Arcane North Star are hash-bound to the job. Canonical visual references must match their approved SHA-256 values. A mislabeled or substituted reference fails closed.

```
BLUEPRINT_APPROVED
  -> REFERENCE_BINDING
  -> REFERENCE_READY
  -> PROOF_PRODUCTION
  -> PROOF_QA_PENDING
  -> READY_FOR_SEMAJ_VISUAL_REVIEW
  -> VISUAL_SYSTEM_APPROVED
  -> COMPONENT_PRODUCTION
```

Proof QA requires three PDF/PNG proof pairs. It verifies that every recorded file still exists and still matches its recorded hash. Only Semaj can approve the visual system, approve the finished package, authorize publication, or mark it published.

The renderer may use AI only for atmospheric art. Customer copy, typography, logo placement, grids, borders, cut marks, QR zones, and final page composition remain deterministic layers.

```powershell
py control_plane.py create-eqp --sku OAL-EQP-001 --title "Modern Arcane Reception Quest Games" --actor Semaj
py control_plane.py transition --job OAL-EQP-001 --to REFERENCE_BINDING --actor Jarvis --reason "Binding approved production inputs"
py control_plane.py add-asset --job OAL-EQP-001 --role modern_arcane_reference --path "C:\path\approved-reference.png"
py control_plane.py qa-eqp-proofs --job OAL-EQP-001
```
