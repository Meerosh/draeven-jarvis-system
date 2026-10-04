# Architecture

## Request path

```text
Draeven HUD :4783
  -> JARVIS Front Door :4719
     -> Jev/OpenRouter or local Laya :8090 for routing
     -> Claude, Codex or local Hermes for one response
     -> Windows Credential Manager for private provider credentials
     -> approval and evidence gates for consequential actions

ElevenLabs / Twilio
  -> public tunnel
  -> Wright tools :8091
  -> Wright control plane and evidence records
```

## Sources of truth

1. Current user instruction.
2. The vault's `Active Priorities.md`.
3. `JARVIS-BOOT-BRIEF.md` and `MASTER_CONTEXT.md`.
4. Approved specifications and locked decisions.
5. Historical notes and archived code.

The live runtime resides in `C:\Users\Arach\my-agent`. The vault and HUD live under `C:\Users\Arach\Documents\Jarvis`. The repository mirrors source code for recovery; it does not include credentials or live business records.

## Execution boundary

Claude runs in plan mode and ordinary Codex answers run ephemerally with a read-only sandbox. Repository work uses a separate managed workspace and explicit confirmation gates:

1. Clone requires confirmation and accepts only credential-free HTTPS GitHub URLs.
2. Inspection is read-only.
3. Implementation requires confirmation, runs Codex with workspace-only write access, and leaves a reviewable uncommitted diff.
4. Publication requires a second confirmation, scans for common credential material, then commits and pushes.

Managed repositories live at `C:\Users\Arach\Documents\Jarvis\Citadel\repositories` and cannot escape that root through repository names.
