# Draeven Jarvis Setup Guide

This is the easiest path for your Windows setup.

---

## 1) Install the repo

Option A: with Git

```powershell
cd Desktop
git clone https://github.com/Meerosh/draeven-jarvis-system.git
cd draeven-jarvis-system
```

Option B: ZIP download
- go to GitHub repo
- click Code
- click Download ZIP
- extract it
- open the extracted folder

---

## 2) Open PowerShell in the project folder

From the repo folder, open PowerShell and run:

```powershell
quick-start.bat
```

If double-clicking doesn't work for you, open PowerShell manually:

```powershell
cd C:\path\to\draeven-jarvis-system
quick-start.bat
```

---

## 3) Wait for setup

The script will:
- create a virtual environment
- install Python packages
- create `.env` from the sample
- start the API server

When it finishes, your backend should be available here:

```text
http://localhost:8000/docs
```

If you see that in a browser, the local API is running.

---

## 4) Add your API keys (optional)

Open `.env` and fill in the values you want:

```env
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
GOOGLE_API_KEY=your-key
```

Leave any value blank if you do not want that provider active.

---

## 5) Point your Draeven HUD at the local API

Follow `gui-integration/DRAEVEN_SETUP.md`.

This is the one important UI change:
- instead of sending the prompt directly to OpenAI,
- send it to `http://localhost:8000/api/chat`

---

## 6) Test the backend

Open this in your browser:

```text
http://localhost:8000/docs
```

Then try the `/api/chat` endpoint with a sample prompt.

Example payload:

```json
{
  "message": "Give me a quick plan for my Shopify and Etsy launch week",
  "session_id": "demo-1"
}
```

---

## 7) Use Obsidian as memory

If you want your vault included as extra context, set:

```env
OBSIDIAN_ENABLED=true
OBSIDIAN_VAULT_PATH=C:\Users\YourName\Documents\YourVault
```

Then the backend can load your notes as context when needed.

---

## 8) Common issue

If the backend fails to start because it cannot find Python or packages, run:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python api\server.py
```

---

## 9) You are done

Once the backend is running and the Draeven UI points to it, you can start using the local Jarvis system.

This is the easiest version of the stack for your setup.
