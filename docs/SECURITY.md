# Security

## Credential storage

Production credentials are stored outside Git. Draeven uses Windows Credential Manager bundles for OpenAI, ElevenLabs, Twilio, Shopify and Etsy where supported. Environment variables and `.env` files are private fallbacks.

Never commit:

- API keys, secrets, access tokens or recovery codes.
- `.env` files.
- Provider configuration exports or agent snapshots.
- Phone numbers, customer data or call transcripts.
- Logs, webhook payloads, evidence databases or generated job folders.

## External actions

Publishing, sending, spending, deleting and customer-data changes require explicit approval and provider evidence. A local record is not evidence that a provider accepted or completed an action.

## Before every push

Run:

```powershell
python tests\verify_repository.py
git diff --check
git status --short
```

Inspect every newly tracked file. If a credential may have entered Git history, rotate it at the provider before attempting history cleanup.
