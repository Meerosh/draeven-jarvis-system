# Wright Connector Tool Server — Setup (Phase 3 vertical slice, HVAC only)

Companion to the vault docs `Wright Connector Demo - Build Brief.md` and
`Wright Connector - Phase 2 Design.md`. This is the Python side: the nine
tools an ElevenLabs Conversational AI agent calls mid-call. Tested working
end-to-end 2026-09-24 (see the job files under `jobs/WRIGHT-CALL-*` from that
test run — safe to delete, they're demo data).

## 1. Install the one new dependency

```bash
pip install twilio
```

Without it, the server still runs fine — SMS sends just report
`{"sent": false, "reason": "twilio_not_configured"}` instead of erroring.

## 2. Environment variables

Same `.env` pattern as `Wright-AI-Receptionist-Demo`. Set these before
starting the server (PowerShell: `$env:NAME = "value"`; or use a `.env` file
with `python-dotenv` if you prefer — not wired in yet, plain env vars for now):

| Variable | Required? | Purpose |
|---|---|---|
| `TWILIO_ACCOUNT_SID` | for real SMS | Your existing Twilio account |
| `TWILIO_AUTH_TOKEN` | for real SMS | " |
| `TWILIO_FROM_NUMBER` | for real SMS | Twilio Number A (public demo number) |
| `TWILIO_OWNER_NUMBER` | for owner alerts | Twilio Number B (private, never public) |
| `ELEVENLABS_WEBHOOK_SECRET` | strongly recommended | Enables webhook signature verification — see the warning below |
| `WRIGHT_TOOLS_PORT` | no (defaults to 8091) | Local port the server binds |

**Never paste real values for these into chat with me.** Set them directly in
your own shell/`.env`.

## 3. Run the server

```bash
cd C:\Users\Arach\my-agent\jarvis-control-plane
python wright_tools_server.py
```

Confirm it's up: `curl http://127.0.0.1:8091/health`

## 4. Tunnel it with ngrok

```bash
ngrok http 8091
```

Copy the `https://...ngrok-free.app` URL it prints. **This URL changes every
time you restart ngrok on the free tier** — you'll need to re-paste it into
the ElevenLabs agent's tool config (step 5) after every restart.

## 5. Configure the ElevenLabs agent (manual — do this in their dashboard)

Add these as **server tools** (webhook tools) on your ElevenLabs
Conversational AI agent. For each one: method `POST`, URL
`<your-ngrok-url>/tools/<tool-name>`, and the parameter schema below.
`call_id` is required on every tool — use ElevenLabs' call/conversation ID
variable so every tool call in one phone call shares the same ID.

| Tool name | Parameters (besides `call_id`) |
|---|---|
| `load_industry_profile` | `industry` (string) |
| `get_business_information` | `question` (string) |
| `capture_lead` | `fields` (object — any of: name, callback_number, service_address, issue, urgency, email, preferred_time, sms_consent) |
| `check_demo_availability` | `preferred_time` (string) |
| `request_demo_appointment` | `confirmed_time` (string) |
| `send_demo_customer_sms` | *(none)* |
| `send_demo_owner_alert` | `reason` (string) |
| `escalate_to_demo_human` | `reason` (string) |
| `record_demo_receipt` | *(none)* |

If ElevenLabs' current dashboard fields (auth header name, schema format)
differ from what's assumed here, adjust there — the design doc already
flagged this as unverified against your live account. If they use a
different signing-secret header name than `X-ElevenLabs-Signature`, update
that header name in `wright_tools_server.py`'s `verify_signature()`.

Also set the agent's system prompt to open with the profile's
`demonstration_disclaimer` and `greeting` (returned by `load_industry_profile`),
and to never state anything in a profile's `prohibited_claims`.

## 6. Twilio Number A → ElevenLabs

Import/connect your existing Twilio Number A to the ElevenLabs agent as its
phone number (ElevenLabs has a "connect your own Twilio number" flow). This
is the number that answers real calls with the agent above.

## 7. What's deliberately untouched

`Wright-AI-Receptionist-Demo/index.html` and `server.js` are unchanged —
kept exactly as-is as a browser-widget fallback, per Semaj's decision. They
don't talk to this new server at all; they're a fully separate path (browser
mic + Claude conversation) that still works independently.

## 8. Before treating this as more than a test

Per the Build Brief: Twilio Number A goes live/public only after Phase 4
testing (the test matrix in the Phase 2 design doc) passes, and only with
Semaj's explicit approval.
