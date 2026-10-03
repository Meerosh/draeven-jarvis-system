# Draeven Jarvis System 🚀

Welcome to your local Jarvis and business command center.

This repo is designed to help you integrate your favorite Dragon/HUD front end (Draeven) with a local multi-model AI system that can:

- handle business tasks
- check Shopify/Etsy inventory and orders
- send and manage email drafts
- generate graphics for cards and packaging
- help with coding and app building
- keep your Obsidian notes as context
- route work to the right model without wasting tokens

This is made for a Windows setup with:
- vanilla HTML/CSS/JavaScript front end
- local Python backend
- Ollama as the default local brain
- optional ChatGPT / Claude / Gemini routing
- Docker support if you want to expand later

---

## What you are getting

This repo includes:
- a local FastAPI server
- a smart router that chooses the best LLM for each job
- sample config files for business, email, design, and developer agents
- a Windows quick-start launcher
- a Draeven integration example you can plug into your existing HUD

---

## Quickest path

### Option 1: easiest for you
1. Open PowerShell
2. Go to a folder you want to use, for example:
   `cd Desktop`
3. Run:
   `git clone https://github.com/Meerosh/draeven-jarvis-system.git`
4. Then:
   `cd draeven-jarvis-system`
5. Double-click:
   `quick-start.bat`

If you do not use Git, just download the ZIP from the repo page and extract it. Then open the extracted folder and double-click `quick-start.bat`.

---

## What the startup script does

`quick-start.bat` will:
- create a local virtual environment
- install the required Python packages
- copy `.env.example` to `.env` if needed
- start the Jarvis API server locally on port 8000

Then you point your Draeven UI at the local backend instead of sending everything straight to the public model APIs.

---

## Default architecture

```text
Draeven HUD (your existing UI)
        |
        v
Local Jarvis/API server
        |
        v
Smart router
        +--> Ollama (default local brain)
        +--> ChatGPT (for coding / difficult reasoning)
        +--> Claude (for long-context work)
        +--> Gemini (for creative / quick fallback)
```

---

## How to connect your HUD

Your front end can send requests like this:

```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: userInput,
    session_id: 'draeven-session-1'
  })
});

const data = await response.json();
console.log(data.reply);
```

See `gui-integration/DRAEVEN_SETUP.md` for the exact instructions for your existing Draeven HTML/JS setup.

---

## Required tools

You already have a lot of this:
- Windows
- Docker
- Ollama
- Python
- your own Draeven GUI

You will also need API keys if you want to use ChatGPT, Claude, or Gemini. Those are optional; your system still works with Ollama alone.

---

## Repo structure

```text
.
├─ README.md
├─ SETUP_GUIDE.md
├─ TROUBLESHOOTING.md
├─ quick-start.bat
├─ docker-compose.yml
├─ requirements.txt
├─ .env.example
├─ .gitignore
├─ config/
│  ├─ jarvis-config.yaml
│  ├─ llm-routing.yaml
│  └─ agents-config.yaml
├─ api/
│  └─ server.py
├─ gui-integration/
│  ├─ DRAEVEN_SETUP.md
│  └─ draeven-integration.js
└─ .venv/
```

---

## Example use cases

### Business operations
- "Summarize my sales and flag what needs my attention"
- "Check all pending orders and tell me which need approval"
- "Review customer emails and draft replies"

### E-commerce
- "Check Shopify and Etsy inventory totals"
- "Find low-stock items and suggest restock priorities"
- "Create a marketing plan for my top products"

### Design
- "Generate a product card concept with my brand colors"
- "Create packaging label copy for my bestselling item"
- "Write a product blurb for Etsy and Shopify"

### Coding
- "Write a Python script to sync inventory"
- "Create a small webhook receiver for orders"
- "Build a lightweight internal tool for my business"

---

## Token-saving strategy

This is a very important part of your setup.

You do not want to burn your paid model quota on simple work.

This system routes work like this:
- simple tasks -> Ollama locally
- long document analysis -> Claude
- coding tasks -> ChatGPT
- creative work -> Gemini or local models

That keeps your expensive subscriptions from getting used up too quickly.

---

## Security and privacy

This local system keeps your business logic on your machine.

The backend is local-first, and you can configure which external providers you want to use.

---

## Next steps

1. Start with `quick-start.bat`
2. Read `SETUP_GUIDE.md`
3. Connect Draeven using `gui-integration/DRAEVEN_SETUP.md`
4. Add your API keys if you want fallback providers
5. Test a few tasks and then expand with your own workflows

---

## Notes

This is intentionally designed to be simple, because you said you wanted easier setup and less copy-paste pain.

The goal is:
- keep your GUI beautiful
- keep your logic local and structured
- avoid token waste
- give you a working local command center

---

If you want the fastest possible setup, do this:
- run `quick-start.bat`
- open the server docs at `http://localhost:8000/docs`
- then follow the Draeven integration guide

You are ready to go. 🚀
