# Recovery

This guide restores the source layout after a computer replacement or damaged checkout. It does not restore private credentials or the business vault.

## Prerequisites

- Windows 11
- Git
- Python 3.11 or newer
- Node.js for JavaScript checks
- Ollama and the approved local model
- Claude Code, Codex CLI and Hermes CLI when those providers are used
- A separate restored copy of the Jarvis vault

## Restore source

1. Clone this repository into a temporary recovery folder.
2. Run `python tests\verify_repository.py`.
3. Copy `runtime\frontdoor` to `C:\Users\Arach\my-agent\jarvis-frontdoor`.
4. Copy `runtime\control-plane` to `C:\Users\Arach\my-agent\jarvis-control-plane`.
5. Copy `runtime\laya-engine` to `C:\Users\Arach\my-agent\laya-engine`.
6. Copy `runtime\jev_openrouter.py` to `C:\Users\Arach\my-agent`.
7. Use `hud` in this repository as the one HUD copy. Start it from `hud\Open Draeven.vbs`, and point the desktop Draeven shortcut at that file.
8. Restore `DRAEVEN-SHARED-CONTEXT.md` from the vault. The file in `docs` is only a safe example.
9. Install Python dependencies with `python -m pip install -r requirements.txt`.
10. Recreate credentials directly in Windows Credential Manager or the provider dashboards. Never restore credentials from Git.

## Validate

Run the verification commands in the root README. Then start Draeven with the HUD launcher and confirm:

- Front Door health on port 4719.
- HUD health on port 4783.
- Laya health on port 8090.
- Wright tool health on port 8091.
- Ollama on port 11434.

Provider health is separate from end-to-end business verification. Confirm Shopify, Etsy and Twilio through read-only provider checks before authorizing writes or customer-facing actions.
