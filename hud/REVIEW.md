# Draeven verification — 2026-10-03

## Verified

- Python snapshot export completed: 28 open records from Active Priorities.md; source unchanged.
- JavaScript syntax check passed.
- Local HTTP preview served successfully on 127.0.0.1:4783.
- Browser rendered overview, castle background, Council portraits, names, purpose labels, and saved-task count.
- Council profile dialogs opened for Lucien and Azrath, showing intended responsibilities and disconnected execution state.
- Task navigation and SKU-000 search returned the corresponding saved task.
- Unmatched search displayed an explicit empty state.
- Text command “show council” navigated to the Council view.
- Thinking preview entered the labeled demonstration state; “stop” returned to AT REST.
- Mobile viewport at 390 x 844 showed no horizontal document overflow.
- Browser console reported no captured warnings or errors during these interactions.

## Limits

- Microphone permission and real capture were not activated during automated review. Implementation is present; actual microphone behavior needs a user device check.
- Browser speech depends on OS/browser voice availability. No custom Draeven voice has been installed or verified.
- No commerce/email/agent integration was tested because none is connected in this preview.
- The preview server currently runs for this review; after a reboot use Open Draeven.vbs. No startup automation was installed.
- The launcher code exists; an actual reboot recovery cycle has not been tested.
- Generated raster assets use the built-in imagegen tool. Full prompts are recorded in ART_DIRECTION.md.

## Preservation

Hermes implementation preserved in ../hermes-backup-20261003-052456/. Existing operational frontdoor files unchanged.
- Additional browser checks passed: priorities button, SoulSmith filter (6 saved records), unavailable inbox state, connection ledger, reduced-motion toggle.

## Council improvement verification

- Full-height original portraits verified in browser; uncropped group viewer opened correctly.
- Lucien introduction reached Preview finished. Garrick introduction reported Speaking using Microsoft David. Stop, replay, and dialog close exercised. Audio timbre was not independently evaluated.
- Character playback handlers are cleared on cancellation to prevent an older utterance from interrupting a new one. Closing the generic animation-preview dialog does not cancel its demonstration.
- Available Windows voices observed: David, Mark, Zira. Race-specific sound quality remains provisional; custom produced voices are not connected.
- JavaScript syntax passed; no captured browser warnings/errors during this review.
- At mobile viewport 390 x 844, document content width equaled client width (375 CSS pixels); no horizontal overflow. Desktop viewport restored.
- Screenshot: council-preview.png. Pre-update copy: ../draeven-before-council-update-20261003-054915/.
- Gstack official setup exited 0, reported ready, and generated Codex skill links and browse.exe. No end-to-end Gstack skill workflow was run.

## Front Door connection repair verification — 2026-10-03

These results supersede the earlier disconnected-chat state above.

- Source backup verified with matching hashes before edits: `../draeven-before-connection-repair-20261003-142309/`.
- JavaScript syntax and both Python source syntax checks passed.
- Eight adapter tests passed: response mapping, rejection of client routing overrides, offline failures, input validation, foreign-origin/host rejection, blocked private files and action endpoints, concurrent request rejection, empty-answer failure, and health-versus-model distinction (related cases grouped in eight tests).
- Front Door answered a direct read-only priority question via Claude status-file routing. Its OAL-EQP-001 priority matched the actual first open task in Active Priorities.md.
- Browser end-to-end: typed priority question -> HUD /api/chat -> canonical Front Door /ask -> Claude answer -> visible response. Actual provider label was `claude (status files)`.
- Browser navigation to Tasks and Lucien profile passed. Four business rows and four Council cards rendered. No remaining backslashes in class attributes. No captured browser console errors after the repaired server loaded.
- Answer text remained visible and no horizontal overflow was observed at desktop and narrow browser widths. The requested 390px browser resize was clamped to 500px by this browser, so a 390px check was not established during this repair.
- Launcher tests: healthy services reused without duplicate starts; unidentified occupied port rejected; both repair-started services stopped and successfully started again through launch.pyw. Browser-open call was mocked during this cold-start test; browser rendering was checked separately.
- Both services listen on 127.0.0.1 only. The HUD server now takes exclusive Windows port ownership. Old duplicate listeners were identified by process and matching served source before stopping them.
- GitHub latest commit d3c38c7 matched the local clone; clone working tree remained clean. No push, commit, or repository deletion performed.

Remaining limits: Council agents, live commerce, inbox and speech-to-text are not connected. Existing Front Door remains in plan mode; proposals are not executed. Each question is independent; conversation history is not supplied to the model. Reboot recovery itself was not tested, though cold process startup was. Canonical runtime source was not changed.

## Voice implementation — 2026-10-03

- JavaScript syntax checks passed for main.js and voice.js; eight adapter tests remain passing.
- Nine controlled voice behavior tests passed (test_voice.cjs).
- Browser exposes webkitSpeechRecognition and speechSynthesis; David, Mark and Zira voices enumerated.
- Typed questions and recognized final transcripts share the same command submission path. No ElevenLabs integration or credentials were added.
- Real microphone recognition is unverified pending a user-spoken test; constructor availability alone is insufficient proof. Unsupported, denied, no-speech and network-error states are explicit.
- Live browser playback check passed: submitted Hello through the HUD, received the actual Front Door greeting, and observed speech start/end events for all three playback chunks. Voice status reached Finished speaking. This verifies playback events, not independently heard audio or microphone transcription.

## ElevenLabs preparation verification — 2026-10-03

- User confirmed browser speech was audible.
- Nine existing voice behavior checks and eight adapter checks remain passing.
- Seven new checks passed: Windows encryption roundtrip, missing key sends no network request, invalid/oversized speech does not generate, documented TTS request contract, redacted authentication errors without retries, requested voice direction sorting, non-audio rejection and lock release.
- Automatic speech defaults off. Test voice and Read last reply require a user click; no automated audio playback or paid generation was performed in this update.
- Live ElevenLabs authentication, voice selection and speech remain unverified until user enters the key locally and requests a sample.

## Approved ElevenLabs voice cast — 2026-10-03

Lucien Voss: Callum. Garrick Thorne: Chris. Azrath Veyr: George. Vaelis Nightweave: Charlie. Draeven: Liam. All five IDs were verified through the connected account voice list, with no speech generated. Council Hear buttons now use these ElevenLabs voices for their scripted introductions; closing the dialog cancels playback. Draeven defaults to Liam on the first load of this casting update in each browser. Automatic speech stays off by default. Source mapping is approvedVoiceCast in js/main.js.
