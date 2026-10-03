// Draeven HUD + Jarvis Backend Integration
// Complete replacement for your js/main.js
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
