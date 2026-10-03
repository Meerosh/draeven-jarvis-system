# Troubleshooting

This file is here to reduce the number of things you need to remember.

---

## Problem: `quick-start.bat` fails because Python isn't found

Fix:
- install Python 3.11+
- restart PowerShell
- try again

You can confirm it is installed by running:

```powershell
python --version
```

---

## Problem: the API does not start

Try this manually:

```powershell
cd C:\path\to\draeven-jarvis-system
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python api\server.py
```

---

## Problem: `http://localhost:8000/docs` does not open

Check if the server is running in the console.

If it is not, look for Python or dependency errors in the terminal.

Common causes:
- bad environment file
- missing Python packages
- port 8000 already used by something else

---

## Problem: Ollama is not responding

Make sure you have Ollama installed and running.

Then test the local endpoint:

```text
http://localhost:11434
```

If you do not want to use Ollama yet, leave `DEFAULT_LLM` as default and use only your cloud models after adding keys.

---

## Problem: the API returns an error about model routing

This is usually because the model provider is not configured.

Check your `.env` file.

If you do not want to use a provider, leave it blank and the router will fall back to the next available model.

---

## Problem: the front end cannot reach the API

This is usually because the path is wrong.

Use:

```text
http://localhost:8000/api/chat
```

not a different port or a local file path.

---

## Problem: you want to reset and start from scratch

Run:

```powershell
rmdir /s /q .venv
del .env
quick-start.bat
```

---

## Problem: you want to use Obsidian notes as memory

Check this in `.env`:

```env
OBSIDIAN_ENABLED=true
OBSIDIAN_VAULT_PATH=C:\Users\YourName\Documents\YourVault
```

Then restart the server.

---

## Problem: you forgot how to open Docker

You can open Docker Desktop by clicking the desktop icon or searching for:

```text
Docker Desktop
```

---

## Problem: you want to keep it even simpler

If the setup still feels too much, the easiest approach is:
- run `quick-start.bat`
- ignore all advanced providers at first
- use only Ollama locally
- then add the extra providers later once the basics are working

That is the least stressful path for your brain and your time.
