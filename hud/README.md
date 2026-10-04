# Draeven — The Obsidian Citadel

Implemented 2026-10-03 by Codex at Semaj's request. This is the standalone HUD project. It is not an Obsidian theme. Read this file before continuing work.

## Open

Double-click **Open Draeven.vbs** to supervise Laya, Wright tools, the canonical JARVIS Front Door, and the loopback-only HUD, then open a browser. It uses the existing Python installation at C:\Python314\pythonw.exe. No startup registration is installed.

Preview: http://127.0.0.1:4783/

Use the launcher for chat. Opening index.html directly only provides the offline interface, not the JARVIS connection.

## Implemented

- Obsidian, bronze, crimson design with generated castle and Council artwork stored locally.
- Animated CSS core and rings, state previews, reduced-motion option, responsive layout.
- Named Council profiles: Lucien Voss (Strategy & foresight), Garrick Thorne (Operations & delivery), Vaelis Nightweave (Creative & storytelling), Azrath Veyr (Systems & automation).
- Business views, 28 open task records exported from Active Priorities.md, search/filter, task details, source/freshness display, snapshot download.
- Local text navigation commands: show tasks, council, businesses, messages, archive, connections, voice preview, stop, and Council member first names.
- Click-to-talk browser recognition: click Talk, allow microphone access, speak, then pause. The final transcript is sent once through the same JARVIS text path. Browser recognition may process audio online.
- Browser speech sample. Animation follows playback state; it is not amplitude-synchronized output. Voice depends on available browser/OS voices.

## JARVIS connection

The HUD sends same-origin `/api/chat` requests to `serve.py`, which translates them to `http://127.0.0.1:4719/ask` with `{"text": "..."}`. This is the existing canonical runtime at `C:\Users\Arach\my-agent\jarvis-frontdoor\server.py`. Its `answer` and `route` become the displayed reply and provider. Its plan-mode behavior is preserved. A health check means the service is reachable; a completed answer verifies the response path separately.

Each question is independent. The existing Front Door does not pass prior conversation turns to its model. Include context in follow-up questions. Conversation is displayed for the current page session, and Front Door exchanges are logged by the existing service in the vault JARVIS Log. Reloading the HUD clears its visible conversation.

The adapter waits up to 12 minutes for the existing backend and shows failures explicitly. Only one HUD question runs at a time. No automatic retries send a duplicate request. Closing the browser does not cancel a backend request already in progress.

## Operational boundaries

Council routing is connected: Lucien uses Claude Sonnet, Garrick uses Codex, Vaelis uses Claude Haiku, and Azrath uses local Hermes. Council replies are advice or drafts. Inbox and commerce metrics still require account-specific connectors. Publish/send/purchase/delete actions remain approval-gated and require a real provider receipt before the system reports execution.

Wright local tools require the custom header `X-Draeven-Tool-Token`. Generate or rotate its value in Draeven's Connections dialog; it is stored as `Draeven/Wright/Tool-Token` in Windows Credential Manager and displayed once for copying into ElevenLabs. The public tunnel checked on 2026-10-04 was `https://dancing-stumbling-try.ngrok-free.dev`. Each ElevenLabs webhook tool needs its path under that base URL and the shared custom header before inbound tool calls are operational.

Task notes may contain old operational claims; they are shown as saved notes, not live facts. The legacy parent hud-data.json has contradictory totals and is not consumed.

To refresh the task export: run `python build_snapshot.py`, then reload. This reads but does not modify Active Priorities.md.

## Recovery / ownership

Hermes stopped work before Codex took over, as confirmed by Semaj. The prior implementation was preserved at:
../hermes-backup-20261003-052456/

The existing operational front door was not modified. This preview uses port 4783. No Hermes↔Codex automatic connection was established. This README is a recovery entry point, not proof that another assistant auto-loads it.

## Project files

index.html: interface structure
styles.css: visual treatment, animation, responsive rules
js/main.js: interactions and states
snapshot.js: generated local priority export
build_snapshot.py: read-only export script
serve.py: loopback-only static allowlist and Front Door adapter
test_connection.py: controlled adapter failure/safety checks
launch.pyw / Open Draeven.vbs: preview launcher
assets/council.png: four-panel portrait atlas
assets/citadel.png: architectural background
ART_DIRECTION.md: generation prompts and provenance
REVIEW.md: verification and known limitations

Keep this project local. The snapshot contains private business notes and is not prepared for public hosting.

## Council update — 2026-10-03

Council cards and profile portraits preserve the complete 3:8 panel from the original artwork. The complete-artwork button opens the uncropped four-member composition. Names and purposes sit beneath the artwork.

Open a Council profile to hear its scripted introduction. Each character has a pace and pitch profile, an available-voice selector saved locally, and a stop control. Closing the profile stops its speech. These are browser voice approximations, not custom fantasy voice models or live agent replies.

Gstack 1.91.15 was installed for Codex. Runtime: C:/Users/Arach/.gstack/repos/gstack. Official setup completed with `gstack ready (codex)`; Codex skills were linked into C:/Users/Arach/.codex/skills. Bun and the browser build completed. New skills may require a fresh Codex session to appear. This does not connect Hermes to Codex.

## Connection repair — 2026-10-03

Status: verified locally. Eight adapter checks passed. A real browser question returned a vault-backed Claude answer, with no captured browser console errors. Cold startup and healthy-service reuse passed.

- Fixed the broken apostrophe and double-escaped HTML attributes in copied main.js.
- Connected to the existing vault-aware Front Door instead of the separate generic API on port 8000.
- Added reachable/offline states, readable errors, request-in-progress controls and an in-layout conversation area.
- Updated the launcher to start both required services, reuse healthy processes and report occupied ports without killing unrelated processes.
- Restricted static serving to presentation files and assets; source, backups and logs are not served. Rejected foreign browser origins and unsupported actions.
- Preserved source backup with matching hashes: `../draeven-before-connection-repair-20261003-142309/`.
- GitHub `Meerosh/draeven-jarvis-system` latest commit was verified as `d3c38c7`, matching the local clone. Its separate API/config/integration examples remain intact. Its README describes business capabilities that its generic chat implementation does not currently provide. It is not used by this HUD connection, and no GitHub changes were published by this repair.

Troubleshooting: Open Draeven.vbs; check Connections; inspect preview-server.log and jarvis-start.log locally. Do not start the port-8000 clone to use this HUD. The earlier repair found two old static servers sharing 4783; both were identified and stopped. The new server requests exclusive port ownership on Windows.

Historical COPILOT-* exports in this folder describe earlier source or the superseded port-8000 proposal. Use this README and the actual source files for the current implementation.

## Voice controls — 2026-10-03

Refresh the HUD once after this update. Click **Talk** and allow microphone access, speak one question, then pause. **Cancel** discards capture without sending it. The final transcript appears in the conversation. Do not begin a second question while JARVIS is answering.

**Speak replies** controls automatic reading. **Read last reply** retries playback if the browser blocks automatic audio. **Stop voice** cancels listening/playback and suppresses an upcoming spoken answer, but does not cancel an already submitted JARVIS request. Text answers remain visible. Switching away from the page stops voice activity.

Choose a browser voice in the conversation controls. The default prefers an English male voice where available. This is not a custom ElevenLabs voice. No ElevenLabs key or paid integration was added. If this browser does not support recognition or its speech service fails, a visible message directs you to try Chrome/Edge or type instead. An API being present is not proof the provider can transcribe.

Voice source: js/voice.js. Behavior checks: node test_voice.cjs. Nine controlled tests cover final/interim transcripts, duplicate prevention, cancellation, permission denial, unsupported recognition, timeout, speech errors and cancelled speech queues. Actual microphone transcription still needs a user-spoken test.

Backup: ../draeven-before-voice-20261003-144408/.

## ElevenLabs preparation — 2026-10-03

Status: implementation and silent checks complete; live provider connection awaits the user's key and chosen voice. The user confirmed hearing the previous browser voice. No ElevenLabs speech has been generated during this setup.

1. Open **Connect ElevenLabs** on the Windows desktop. Enter the API key in that masked window, never in chat. The key needs Voices read and Text to Speech permissions.
2. Verify and save. This checks the voice list only. The key is encrypted with Windows DPAPI for the current account at `~/.config/draeven/elevenlabs.key`, outside the served HUD and GitHub clone. Existing `ELEVENLABS_API_KEY` process environment takes precedence if set.
3. Refresh Draeven, select **ElevenLabs**, then choose a voice. The first page of account voices is sorted toward male, deep, calm and warm descriptions; the descriptions are not proof of the actual sound. A notice appears if more voices exist beyond the first 100.
4. Click **Test voice** when ready to hear it. This sends a short sample to ElevenLabs and uses account credits. Voice choice is saved in the browser. Automatic speech starts unchecked every page load; enable **Speak replies** only when wanted.

Speech uses `eleven_multilingual_v2` and MP3 output, via the local server. Keys are never returned to browser JavaScript. The spoken reply text is sent to ElevenLabs; browser microphone recognition remains a separate browser service. Stop voice cancels local playback and browser waiting, but an already submitted generation may still use credits. There are no automatic paid retries. The last successful audio blob is cached only in this page's memory for replay; no audio files are saved. Replies over 5000 characters require a shorter answer.

Files: eleven_voice.py (provider and encrypted credential handling), connect_elevenlabs.pyw (private setup), test_eleven_voice.py (seven controlled checks). New routes: GET /api/voice/voices and POST /api/voice/speak, behind existing loopback/origin checks. Source and credential files remain outside the static file allowlist.

Docs checked: https://elevenlabs.io/docs/api-reference/text-to-speech/convert and https://elevenlabs.io/docs/api-reference/voices/search.
Backup: ../draeven-before-elevenlabs-20261003-193453/.

## Approved ElevenLabs voice cast — 2026-10-03

Lucien Voss: Callum. Garrick Thorne: Chris. Azrath Veyr: George. Vaelis Nightweave: Charlie. Draeven: Liam. All five IDs were verified through the connected account voice list, with no speech generated. Council Hear buttons now use these ElevenLabs voices for their scripted introductions; closing the dialog cancels playback. Draeven defaults to Liam on the first load of this casting update in each browser. Automatic speech stays off by default. Source mapping is approvedVoiceCast in js/main.js.

## Wright ElevenLabs tools — 2026-10-04

All nine webhook tools on `Wright Connector Demo Receptionist` use the live ngrok address and the protected `X-Draeven-Tool-Token` header. Each definition was updated through the ElevenLabs API and read back successfully. The token remains in Windows Credential Manager and is never written to this README or returned by status endpoints. Draeven reports this connection ready only while the verified tunnel URL is active. A real inbound phone call remains the final end-to-end check.
