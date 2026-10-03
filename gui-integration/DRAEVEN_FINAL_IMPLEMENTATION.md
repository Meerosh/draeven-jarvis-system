# Draeven HUD + Jarvis Backend Integration
## EXACT Implementation for Your Current Setup

**Your HUD Location:** `C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud\`  
**Your Current Server:** `http://127.0.0.1:4783/` via `serve.py`  
**Jarvis Backend:** `http://localhost:8000/api/chat`  
**Current Serve Port:** 4783  
**Backend Port:** 8000

---

## The Problem ChatGPT Identified

Your current handler matches words anywhere in the input. So:
- ✅ "show tasks" → opens Tasks (correct)
- ❌ "What's my top priority?" → ALSO opens Tasks (wrong! should go to backend)
- ❌ "Plan my week" → tries to open something (wrong! should go to backend)

The fix: **Explicit command matching first, then route everything else to backend.**

---

## Step 1: Update Your `serve.py`

Replace your entire `serve.py` with this version. It adds CORS and proxy support:

```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
from pathlib import Path
import os

class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler with CORS and proxy support."""

    def end_headers(self):
        # CORS headers (localhost only)
        self.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:4783')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        """Proxy POST requests to Jarvis backend."""
        if self.path == '/api/chat':
            self._proxy_to_jarvis()
        else:
            self.send_error(404)

    def do_GET(self):
        """Serve static files."""
        super().do_GET()

    def _proxy_to_jarvis(self):
        """Forward request to local Jarvis backend."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        try:
            req = urllib.request.Request(
                'http://localhost:8000/api/chat',
                data=body,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(response_data.encode('utf-8'))
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error = json.dumps({
                'reply': f'Backend unavailable. Is Jarvis running on localhost:8000? Error: {str(e)}',
                'provider': 'error',
                'session_id': 'error'
            })
            self.wfile.write(error.encode('utf-8'))

    def log_message(self, format, *args):
        print(f'[{self.client_address[0]}] {format % args}')


if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    server = HTTPServer(('127.0.0.1', 4783), CORSHTTPRequestHandler)
    print('\n' + '='*60)
    print('Draeven HUD Server (with Jarvis Backend Proxy)')
    print('='*60)
    print('HUD URL:     http://127.0.0.1:4783/')
    print('Backend:     http://localhost:8000/api/chat')
    print('Status:      Running... Press Ctrl+C to stop')
    print('='*60 + '\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n\nShutting down...')
        server.shutdown()
```

---

## Step 2: Update Your `js/main.js`

This is the key change. Replace your entire `js/main.js` with this version:

```javascript
// Draeven HUD with Jarvis Backend Integration
// Keep local commands, add natural-language backend routing

let draevenSessionId = 'draeven-session-1';
let isRequestPending = false;

// === CONVERSATION DISPLAY ===
const conversationContainer = document.getElementById('conversation-display') || createConversationDisplay();

function createConversationDisplay() {
  const container = document.createElement('div');
  container.id = 'conversation-display';
  container.className = 'conversation-area';
  container.setAttribute('role', 'region');
  container.setAttribute('aria-label', 'Conversation with Draeven');
  const commandForm = document.getElementById('command-form');
  if (commandForm && commandForm.parentNode) {
    commandForm.parentNode.insertBefore(container, commandForm.nextSibling);
  }
  return container;
}

function displayMessage(role, text, provider = null) {
  const entry = document.createElement('div');
  entry.className = `conversation-entry role-${role}`;

  const label = document.createElement('div');
  label.className = 'message-label';
  label.textContent = role === 'user' ? 'You' : 'Draeven';
  if (provider && role === 'assistant') {
    label.textContent += ` (${provider})`;
  }

  const body = document.createElement('div');
  body.className = 'message-body';
  body.textContent = text; // SAFE: textContent prevents XSS

  entry.appendChild(label);
  entry.appendChild(body);
  conversationContainer.appendChild(entry);
  conversationContainer.scrollTop = conversationContainer.scrollHeight;
}

// === ORB STATE ===
function setOrbThinking(thinking) {
  const orb = document.querySelector('[data-orb-status]') || document.querySelector('.orb');
  if (orb) {
    orb.setAttribute('data-state', thinking ? 'thinking' : 'idle');
    orb.setAttribute('aria-busy', thinking);
  }
}

// === TOAST NOTIFICATIONS ===
function toast(message) {
  console.log('[Draeven]', message);
  const toastEl = document.createElement('div');
  toastEl.className = 'toast';
  toastEl.textContent = message;
  document.body.appendChild(toastEl);
  setTimeout(() => toastEl.remove(), 3000);
}

// === BACKEND REQUEST ===
async function askJarvis(userInput) {
  if (isRequestPending) {
    toast('Request in progress, please wait.');
    return null;
  }

  isRequestPending = true;
  setOrbThinking(true);

  try {
    // Show user message immediately
    displayMessage('user', userInput);

    // Send to backend via local proxy
    const response = await fetch('http://127.0.0.1:4783/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userInput,
        session_id: draevenSessionId,
        task_type: 'general'
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    // Validate response
    if (!data || typeof data.reply !== 'string') {
      throw new Error('Invalid response from backend');
    }

    // Update session ID
    if (data.session_id) {
      draevenSessionId = data.session_id;
    }

    const provider = data.provider || 'unknown';
    displayMessage('assistant', data.reply, provider);
    toast('Response received.');

    return data;
  } catch (error) {
    const errorMsg = `Connection error: ${error.message}`;
    displayMessage('assistant', errorMsg, 'error');
    toast('Backend unavailable. Check if Jarvis is running.');
    console.error('[Draeven Error]', error);
    return null;
  } finally {
    isRequestPending = false;
    setOrbThinking(false);
  }
}

// === EXPLICIT LOCAL COMMANDS ===
// Narrower matching: exact phrase starts or full word boundary
const EXPLICIT_COMMANDS = [
  { regex: /^\s*(show\s+)?tasks?\s*$/i, action: () => showView('tasks') },
  { regex: /^\s*(show\s+|open\s+)?council\s*$/i, action: () => showView('council') },
  { regex: /^\s*(show\s+)?agents\s*$/i, action: () => showView('council') },
  { regex: /^\s*(show\s+)?businesses?\s*$/i, action: () => showView('businesses') },
  { regex: /^\s*(show\s+)?(messages?|emails?|inbox)\s*$/i, action: () => showView('messages') },
  { regex: /^\s*(show\s+)?(vault|archive)\s*$/i, action: () => showView('vault') },
  { regex: /^\s*(show\s+)?(home|overview)\s*$/i, action: () => showView('overview') },
  { regex: /^\s*(show\s+)?(connection|health|connections)\s*$/i, action: () => connections() },
  { regex: /^\s*(show\s+)?(voice|preview)\s*$/i, action: () => preview() },
  { regex: /^\s*(stop|silence|cancel)\s*$/i, action: () => { stopActivity(); toast('Voice activity stopped.'); } }
];

// === MAIN COMMAND HANDLER ===
document.getElementById('command-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const input = document.getElementById('command-input');
  const text = input.value.trim();

  if (!text) return;
  input.value = '';

  // Try explicit local commands first
  for (const cmd of EXPLICIT_COMMANDS) {
    if (cmd.regex.test(text)) {
      cmd.action();
      return; // Local command matched, don't send to backend
    }
  }

  // Try to match agent names
  if (typeof council !== 'undefined' && Array.isArray(council)) {
    const lowerText = text.toLowerCase();
    for (const agent of council) {
      if (lowerText.includes(agent.name.split(' ')[0].toLowerCase())) {
        openAgent(agent.id);
        return; // Agent matched, don't send to backend
      }
    }
  }

  // Nothing matched locally → send to backend
  await askJarvis(text);
});

// === PLACEHOLDER FUNCTIONS ===
// Replace these with your actual implementations from the original main.js
function stopActivity() { console.log('stopActivity'); }
function showView(view) { console.log('showView(' + view + ')'); }
function connections() { console.log('connections'); }
function preview() { console.log('preview'); }
function openAgent(id) { console.log('openAgent(' + id + ')'); }
```

**IMPORTANT:** Look at your current `js/main.js` and find the real implementations of:
- `stopActivity()`
- `showView()`
- `connections()`
- `preview()`
- `openAgent()`

Copy those function bodies into the placeholders at the bottom of the code above.

---

## Step 3: Update Your `index.html`

Add this div **right after your `#command-form`** and **before** the closing `</body>` tag:

```html
<!-- Conversation display area for Jarvis responses -->
<div id="conversation-display" class="conversation-area" role="region" aria-label="Conversation with Draeven"></div>
```

---

## Step 4: Update Your `styles.css`

Add this CSS (your exact theme colors, adjust if needed):

```css
/* Conversation Display Area */
#conversation-display {
  margin-top: 2rem;
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.3);
  max-height: 500px;
  min-height: 200px;
  overflow-y: auto;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.9rem;
  color: #e0e0e0;
  line-height: 1.5;
}

.conversation-entry {
  margin-bottom: 1.5rem;
  padding: 0.75rem 1rem;
  border-left: 4px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.conversation-entry.role-user {
  background: rgba(100, 150, 255, 0.08);
  border-left-color: #6496ff;
  margin-left: 1rem;
}

.conversation-entry.role-assistant {
  background: rgba(100, 200, 150, 0.08);
  border-left-color: #64c896;
  margin-right: 1rem;
}

.message-label {
  font-weight: bold;
  color: #a0d8ff;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.conversation-entry.role-assistant .message-label {
  color: #64c896;
}

.message-body {
  color: #e0e0e0;
  line-height: 1.5;
  word-wrap: break-word;
  white-space: pre-wrap;
}

/* Toast notifications */
.toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  background: rgba(0, 0, 0, 0.9);
  color: #e0e0e0;
  padding: 1rem 1.5rem;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 0.9rem;
  z-index: 9999;
  animation: toastSlide 0.3s ease-out;
}

@keyframes toastSlide {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}
```

---

## Step 5: Copy Your Real Functions

Open your current `js/main.js` and find these functions:
- `stopActivity()`
- `showView(view)`
- `connections()`
- `preview()`
- `openAgent(id)`

Copy their COMPLETE implementations and paste them into the new `js/main.js` where it says `// Replace these with your actual implementations`.

---

## Step 6: Test It

### Terminal 1: Start Jarvis Backend
```powershell
cd C:\path\to\draeven-jarvis-system
quick-start.bat
```

### Terminal 2: Start Draeven HUD
```powershell
cd C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud
python serve.py
```

### Browser: Test
1. Open `http://127.0.0.1:4783/`
2. Try: `show tasks` → Should navigate locally (NO backend call)
3. Try: `What's my top priority?` → Should hit backend and show response
4. Try: `open council` → Should navigate locally (NO backend call)
5. Try: `Plan my week` → Should hit backend and show response

---

## Verification Checklist

- [ ] `serve.py` runs without errors
- [ ] Draeven HUD loads at `http://127.0.0.1:4783/`
- [ ] Local command `show tasks` works (navigates, no backend call)
- [ ] Natural question `What's my priority?` hits backend and shows reply
- [ ] Conversation display appears below the command form
- [ ] Second message preserves session ID
- [ ] Backend unavailable shows clear error
- [ ] Orb enters thinking state during request
- [ ] No HTML injection (responses show as plain text)

---

## That's It!

Your Draeven HUD now seamlessly integrates with Jarvis while keeping all local commands working perfectly.

**Key differences from before:**
- Local commands use exact phrase matching (narrower)
- Natural language goes to backend
- Responses appear in conversation area
- Session IDs persist across requests
- Clear error handling
- Safe DOM rendering
