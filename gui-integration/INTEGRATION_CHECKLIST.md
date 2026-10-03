# Draeven + Jarvis Integration Checklist

Use this to verify the integration is working correctly.

---

## Pre-Flight Checks

### Setup
- [ ] Jarvis backend is running on `http://localhost:8000`
- [ ] Draeven HUD is running on `http://127.0.0.1:4783`
- [ ] `serve.py` is the new version with CORS/proxy support
- [ ] `js/main.js` is the new version with backend integration
- [ ] Conversation display div added to `index.html`
- [ ] Conversation styling added to `styles.css`
- [ ] Browser console has no CORS warnings

---

## Local Command Tests

These should **NOT** hit the backend. They should only navigate locally.

### Test 1: Show Tasks
- [ ] Type: `show tasks`
- [ ] Expected: Tasks view opens
- [ ] Browser network tab: NO POST to `/api/chat`

### Test 2: Open Council
- [ ] Type: `open council`
- [ ] Expected: Council view opens
- [ ] Browser network tab: NO POST to `/api/chat`

### Test 3: Show Messages
- [ ] Type: `show messages`
- [ ] Expected: Messages view opens
- [ ] Browser network tab: NO POST to `/api/chat`

### Test 4: Show Vault
- [ ] Type: `show vault`
- [ ] Expected: Vault/archive view opens
- [ ] Browser network tab: NO POST to `/api/chat`

### Test 5: Show Home
- [ ] Type: `show home`
- [ ] Expected: Overview/home view opens
- [ ] Browser network tab: NO POST to `/api/chat`

---

## Backend Integration Tests

These should hit the backend and display responses.

### Test 6: Simple Question
- [ ] Type: `What's my top priority?`
- [ ] Expected:
  - Orb enters "thinking" state
  - Message appears in conversation
  - Response appears below
  - Orb returns to idle
  - Toast shows "Response received"
- [ ] Browser network tab: POST to `/api/chat` with `message`, `session_id`, `task_type`
- [ ] Response: JSON with `reply`, `provider`, `session_id`
- [ ] Rendered as plain text (no HTML execution)

### Test 7: Business Query
- [ ] Type: `Plan my week`
- [ ] Expected:
  - Message and response appear
  - Provider label shown (e.g., "Draeven (ollama)")

### Test 8: Second Message (Session Persistence)
- [ ] Type: `Tell me about my inventory`
- [ ] Expected:
  - Request includes the `session_id` from Test 6
  - Response includes same or new `session_id`
  - Session ID is preserved for next request
- [ ] Browser network tab: Session ID matches previous response

### Test 9: Natural Language vs Local Commands
- [ ] Type: `Show me the tasks for today`
- [ ] Expected:
  - Goes to backend (not local command match)
  - Receives intelligent response about tasks
  - NOT just opening the tasks view

---

## Error Handling Tests

### Test 10: Backend Unavailable
- [ ] Stop the Jarvis backend
- [ ] Type a question: `What time is it?`
- [ ] Expected:
  - Clear error message in conversation: "Cannot reach Jarvis backend..."
  - Toast shows error
  - Orb returns to idle
  - Draeven still works for local commands
  - NO error page or crash

### Test 11: Duplicate Submission Prevention
- [ ] Type a question: `What's the weather?`
- [ ] Immediately type another: `Show me tasks`
- [ ] Expected:
  - Toast: "Request in progress, please wait"
  - Only first request sent
  - Second input NOT processed until first completes

### Test 12: Invalid Response Handling
- [ ] In dev tools, mock a bad response: `{"error":"test"}`
- [ ] Type a question
- [ ] Expected:
  - Error message in conversation: "Backend response missing..."
  - No crash or stuck state

---

## Security Tests

### Test 13: XSS Prevention (HTML Injection)
- [ ] Mock a backend response containing HTML: `"reply":"<img onerror=alert('XSS')>test"`
- [ ] Expected:
  - HTML rendered as plain text (no image, no alert)
  - Conversation shows: `<img onerror=alert('XSS')>test`
- [ ] Verify in code: response uses `textContent`, not `innerHTML`

### Test 14: CORS Security
- [ ] Check browser console
- [ ] Expected: NO CORS blocked errors
- [ ] Verify `serve.py` only allows `http://127.0.0.1:4783`
- [ ] Try accessing from another origin (should fail silently)

---

## Accessibility Tests

### Test 15: Conversation Region
- [ ] Open browser accessibility inspector
- [ ] Check `#conversation-display`
- [ ] Expected:
  - Has `role="region"`
  - Has `aria-label="Conversation with Draeven"`
  - Screen reader announces new messages

### Test 16: Orb State
- [ ] Type a question
- [ ] Check orb element
- [ ] Expected:
  - `aria-busy="true"` while pending
  - `aria-busy="false"` when complete
  - `data-state` attribute changes

---

## Performance Tests

### Test 17: Response Time
- [ ] Type a simple question
- [ ] Measure time from submission to response
- [ ] Expected: < 10 seconds (depends on model)
- [ ] Browser network tab: Check latency

### Test 18: Multiple Turns
- [ ] Have a 5-turn conversation
- [ ] Expected:
  - No slowdown
  - No memory leaks
  - Conversation display scrolls smoothly
  - Session IDs persist correctly

---

## Final Sign-Off

If all tests pass:

- [ ] Integration is production-ready
- [ ] Local commands work perfectly
- [ ] Backend integration is solid
- [ ] Error handling is robust
- [ ] Security is verified
- [ ] Accessibility is checked
- [ ] Performance is acceptable

---

## Notes

- Keep browser console open during testing to spot errors
- Test on different browsers (Chrome, Firefox, Edge) if possible
- Test on different network speeds if possible
- Document any issues for future improvements
