# Draeven JARVIS System

This repository is the recovery and review source for the Draeven system running on Semaj's Windows computer.

It replaces the earlier port-8000 FastAPI prototype. That prototype remains available in Git history through commit `d3c38c7`.

## Current architecture

| Component | Repository path | Live location | Port |
|---|---|---|---:|
| Draeven HUD | `hud/` | `C:\Users\Arach\Documents\Jarvis\Citadel\desktop\draeven-jarvis-system\hud` | 4783 |
| Front Door | `runtime/frontdoor/` | `C:\Users\Arach\my-agent\jarvis-frontdoor` | 4719 |
| Laya router | `runtime/laya-engine/` | `C:\Users\Arach\my-agent\laya-engine` | 8090 |
| Wright tools | `runtime/control-plane/` | `C:\Users\Arach\my-agent\jarvis-control-plane` | 8091 |
| Ollama | external local service | installed separately | 11434 |

`hud/draeven_core.py` is the operating layer above the model Front Door. It routes verified tools first, preserves a bounded local conversation, uses at most one model route when no tool matches, and owns approval-gated executable tools.

The knowledge vault is deliberately separate from this code repository. Its live location is `C:\Users\Arach\Documents\Jarvis`.

## Provider routing

- Lucien Voss: Claude Sonnet for strategy and research.
- Garrick Thorne: Codex for operations and delivery.
- Vaelis Nightweave: Claude Haiku for creative work.
- Azrath Veyr: local Hermes for systems and automation.
- Jev/OpenRouter and local Laya handle low-cost routing decisions.

All text providers receive the same bounded, secret-free operating context. Paid cloud requests are limited to one provider call per request and a configured daily ceiling.

## Security model

- Production credentials belong in Windows Credential Manager.
- `.env` is a fallback and is ignored by Git.
- The repository excludes logs, provider usage, call jobs, webhook events, databases, provider snapshots and generated output.
- External actions require approval and provider evidence before Draeven reports success.

## Verification

Run from PowerShell:

```powershell
python tests\verify_repository.py
python -m unittest discover -s runtime\frontdoor -p "test_*.py"
python -m unittest discover -s runtime\control-plane -p "test_*.py"
python -m unittest discover -s hud -p "test_*.py"
node --check hud\js\main.js
node --check hud\js\voice.js
```

See [Recovery](docs/RECOVERY.md), [Architecture](docs/ARCHITECTURE.md), and [Security](docs/SECURITY.md).

## Repository worker

Draeven now has an approval-gated repository worker. Its managed checkouts live outside the runtime at `C:\Users\Arach\Documents\Jarvis\Citadel\repositories`.

Use these phrases in Draeven:

```text
repo list
repo clone https://github.com/owner/repository
repo inspect repository
repo implement repository: describe the requested change
repo publish repository: concise commit message
```

Listing and inspection are read-only. Clone, implementation and publication show a confirmation button. Implementation uses an isolated Codex run with workspace-only write access and leaves changes uncommitted for review. Publication scans for common credential files and high-confidence secret patterns before committing and pushing.

## Current limitations

- Shopify live catalog reads and approval-gated product status changes are registered Draeven Core tools.
- Etsy private OAuth listing reads are registered Draeven Core tools.
- Repository inspection and approval-gated implementation/publication use the managed repository worker.
- General model providers remain advisory. Draeven Core never treats a model claim as tool execution.
- Email and calendar remain unavailable until a provider OAuth connection is added.
