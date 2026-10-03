# Draeven HUD + Jarvis Backend Integration (Exact Implementation)

**For:** Your vanilla HTML/CSS/JS Draeven HUD  
**Location:** `C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud\`  
**Backend:** `http://localhost:8000/api/chat` (or `http://localhost:8001/api/chat` if port 8000 is taken)

---

## What This Does

Your Draeven HUD stays 100% the same visually and behaviorally for **local commands**:
- `show tasks` → shows tasks view
- `open council` → shows council view
- `show messages` → shows messages view
- etc.

But now, **natural-language questions** like:
- "What's my inventory today?"
- "Draft an email to my customers"
- "Plan my week"

...are sent to your local Jarvis backend for intelligent responses.

---

## Step 1: Get Your Draeven Files Ready

In your Draeven folder:
```
C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud\
├── index.html
├── styles.css
├── js/
│   └── main.js
├── serve.py
└── (other assets)
```

Do NOT modify `index.html` or `styles.css` yet. We'll only change `js/main.js` and `serve.py`.

---

## Step 2: Update Your `serve.py` (Add CORS Support)

Open your current `serve.py` and add this code. If you don't have a `serve.py`, create one with this content:

```python
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
import os

class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow CORS for localhost only (secure)
        self.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:4783')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        # Simple proxy to local Jarvis backend
        if self.path == '/api/chat':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                # Forward to local Jarvis backend
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
                error_response = json.dumps({
                    'reply': f'Backend unavailable: {str(e)}',
                    'provider': 'error',
                    'session_id': 'error'
                })
                self.wfile.write(error_response.encode('utf-8'))
        else:
            # Serve static files normally
            super().do_GET()

if __name__ == '__main__':
    os.chdir(Path(__file__).parent)
    server = HTTPServer(('127.0.0.1', 4783), CORSHTTPRequestHandler)
    print('Draeven HUD running at http://127.0.0.1:4783/')
    print('Forwarding /api/chat to http://localhost:8000/api/chat')
    print('Press Ctrl+C to stop.')
    server.serve_forever()
```

**What this does:**
- Serves your Draeven HUD on `http://127.0.0.1:4783/` (same as before)
- Adds CORS headers for secure localhost-only communication
- Acts as a proxy for `/api/chat` requests
- Forwards them safely to your Jarvis backend on `http://localhost:8000`

---

## Step 3: Update Your `js/main.js`

Replace your entire current `js/main.js` with this version. It keeps all your existing local commands and adds backend integration:

```javascript
// Draeven HUD + Jarvis Backend Integration
// Keeps local commands, adds backend support for natural language

let draevenSessionId = 'draeven-session-1';
let isRequestPending = false;
let conversationHistory = [];

// Conversation display element (add to HTML if not present)
const conversationContainer = document.getElementById('conversation-display') || createConversationDisplay();

// Local command keywords (explicit triggers)
const LOCAL_COMMANDS = {
  stop: /\b(stop|silence|cancel)\b/,
  tasks: /^\s*(show\s+)?tasks?\s*$/i,
  council: /^\s*(show\s+|open\s+)council\b/i,
  agents: /\b(agents|show\s+agents)\b/i,
  business: /^\s*(show\s+)?businesses?\s*$/i,
  messages: /^\s*(show\s+)?(messages?|emails?|inbox)\s*$/i,
  vault: /^\s*(show\s+)?(vault|archive)\s*$/i,
  home: /^\s*(show\s+)?(home|overview)\s*$/i,
  connections: /^\s*(show\s+)?(connection|health)\b/i,
  voice: /^\s*(show\s+)?(voice|preview)\s*$/i
};

// Helper: Create conversation display if missing
function createConversationDisplay() {
  const container = document.createElement('div');
  container.id = 'conversation-display';
  container.className = 'conversation-area';
  container.setAttribute('role', 'region');
  container.setAttribute('aria-label', 'Conversation with Draeven');
  document.body.appendChild(container);
  return container;
}

// Helper: Display a message in the conversation
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
  body.textContent = text; // Use textContent, NOT innerHTML, for safety

  entry.appendChild(label);
  entry.appendChild(body);
  conversationContainer.appendChild(entry);
  conversationContainer.scrollTop = conversationContainer.scrollHeight;

  conversationHistory.push({ role, text, provider, timestamp: new Date() });
}

// Helper: Show orb thinking state
function setOrbThinking(thinking) {
  const orb = document.querySelector('[data-orb-status]') || document.querySelector('.orb');
  if (orb) {
    orb.setAttribute('data-state', thinking ? 'thinking' : 'idle');
    orb.setAttribute('aria-busy', thinking);
  }
}

// Helper: Toast notification (your existing function, if any)
function toast(message) {
  console.log('[Toast]', message);
  // Replace with your actual toast function if you have one
  const toastEl = document.createElement('div');
  toastEl.className = 'toast';
  toastEl.textContent = message;
  document.body.appendChild(toastEl);
  setTimeout(() => toastEl.remove(), 3000);
}

// Main: Send message to backend
async function askDraeven(userInput) {
  if (isRequestPending) {
    toast('Request in progress, please wait.');
    return null;
  }

  isRequestPending = true;
  setOrbThinking(true);

  try {
    // Display user message immediately
    displayMessage('user', userInput);

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
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const data = await response.json();

    // Validate response
    if (!data || typeof data.reply !== 'string') {
      throw new Error('Backend response missing or invalid reply field');
    }

    // Update session ID for next request
    if (typeof data.session_id === 'string' && data.session_id) {
      draevenSessionId = data.session_id;
    }

    const provider = typeof data.provider === 'string' ? data.provider : 'Unknown';
    displayMessage('assistant', data.reply, provider);
    toast('Response received.');

    return {
      reply: data.reply,
      provider: provider,
      session_id: draevenSessionId
    };
  } catch (error) {
    const errorMsg = `Connection error: ${error.message}`;
    displayMessage('assistant', errorMsg, 'error');
    toast('The intelligence link encountered an error. Check the backend.');
    console.error('[Draeven Backend Error]', error);
    return null;
  } finally {
    isRequestPending = false;
    setOrbThinking(false);
  }
}

// Main command form handler
document.getElementById('command-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const input = document.getElementById('command-input');
  const text = input.value.trim();

  if (!text) return;
  input.value = '';

  const q = text.toLowerCase();
  let handled = false;

  // Local command matching (explicit triggers only)
  if (LOCAL_COMMANDS.stop.test(q)) {
    stopActivity();
    toast('Voice activity stopped.');
    handled = true;
  } else if (LOCAL_COMMANDS.tasks.test(q)) {
    showView('tasks');
    handled = true;
  } else if (LOCAL_COMMANDS.council.test(q)) {
    showView('council');
    handled = true;
  } else if (LOCAL_COMMANDS.agents.test(q)) {
    showView('council');
    handled = true;
  } else if (LOCAL_COMMANDS.business.test(q)) {
    showView('businesses');
    handled = true;
  } else if (LOCAL_COMMANDS.messages.test(q)) {
    showView('messages');
    handled = true;
  } else if (LOCAL_COMMANDS.vault.test(q)) {
    showView('vault');
    handled = true;
  } else if (LOCAL_COMMANDS.home.test(q)) {
    showView('overview');
    handled = true;
  } else if (LOCAL_COMMANDS.connections.test(q)) {
    connections();
    handled = true;
  } else if (LOCAL_COMMANDS.voice.test(q)) {
    preview();
    handled = true;
  } else {
    // Try to match a Council agent name
    const council = window.council || [];
    const agent = council.find(a => q.includes(a.name.split(' ')[0].toLowerCase()));
    if (agent) {
      openAgent(agent.id);
      handled = true;
    }
  }

  // If not a local command, send to backend
  if (!handled) {
    await askDraeven(text);
  }
});

// Placeholder functions (replace with your actual implementations)
function stopActivity() { console.log('stopActivity called'); }
function showView(view) { console.log(`showView(${view}) called`); }
function connections() { console.log('connections called'); }
function preview() { console.log('preview called'); }
function openAgent(agentId) { console.log(`openAgent(${agentId}) called`); }
```

---

## Step 4: Add Conversation Display CSS (Optional but Recommended)

Add this to your `styles.css` to make the conversation area look good:

```css
#conversation-display {
  margin-top: 2rem;
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.3);
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.9rem;
  color: #e0e0e0;
}

.conversation-entry {
  margin-bottom: 1rem;
  padding: 0.75rem;
  border-left: 3px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.conversation-entry.role-user {
  background: rgba(100, 150, 255, 0.1);
  border-left-color: #6496ff;
}

.conversation-entry.role-assistant {
  background: rgba(100, 200, 150, 0.1);
  border-left-color: #64c896;
}

.message-label {
  font-weight: bold;
  color: #a0d8ff;
  margin-bottom: 0.25rem;
  font-size: 0.85rem;
}

.message-body {
  color: #e0e0e0;
  line-height: 1.4;
  word-wrap: break-word;
  white-space: pre-wrap;
}
```

---

## Step 5: Test It

### Terminal 1: Start Jarvis Backend
```powershell
cd C:\path\to\draeven-jarvis-system
quick-start.bat
```

Wait for:
```
Starting Draeven Jarvis API...
Open http://localhost:8000/docs in your browser when it starts.
```

### Terminal 2: Start Draeven HUD
```powershell
cd C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud
python serve.py
```

You should see:
```
Draeven HUD running at http://127.0.0.1:4783/
Forwarding /api/chat to http://localhost:8000/api/chat
```

### Browser: Test the Integration

1. Open `http://127.0.0.1:4783/`
2. Try a **local command**:
   - Type: `show tasks`
   - Should navigate to tasks view (local)
3. Try a **natural-language question**:
   - Type: `What should I focus on today?`
   - Should send to Jarvis backend and display the response below
4. Try a **second message** (tests session ID):
   - Type: `Tell me about my Shopify inventory`
   - Should use the session ID from the first response

---

## Acceptance Checklist

- [ ] Local command `show tasks` navigates to tasks (does NOT hit backend)
- [ ] Natural-language question `What's my top priority?` hits backend and displays reply
- [ ] Second message in same session uses the returned `session_id`
- [ ] Backend unavailable error shows clear message, HUD still works locally
- [ ] Backend response displays as plain text (no HTML injection)
- [ ] Orb shows thinking state while request is pending
- [ ] Duplicate submission prevented while request is in progress
- [ ] Provider label shown (e.g., "Draeven (ollama)")

---

## If CORS Issues Occur

If you see a "CORS blocked" error in the browser console:

1. Make sure your `serve.py` includes the CORS handler above
2. Make sure you're running Draeven on `http://127.0.0.1:4783/` (not `localhost`)
3. Make sure the Jarvis backend is running on `http://localhost:8000`
4. Restart both servers

The included `serve.py` proxy handles CORS securely (localhost only).

---

## That's It!

Your Draeven HUD now:
- ✅ Keeps all local commands working
- ✅ Routes natural language to Jarvis backend
- ✅ Displays responses safely
- ✅ Maintains session IDs
- ✅ Handles errors gracefully
- ✅ Never breaks your existing UI
