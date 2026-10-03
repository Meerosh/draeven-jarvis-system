# Draeven integration guide

This is the easiest way to make your existing Draeven HUD talk to your local Jarvis.

---

## Goal

Instead of sending every message directly to an external AI API, your Draeven UI sends requests to your local server:

```text
http://localhost:8000/api/chat
```

This makes your local system behave like a smart middleware layer.

---

## Step 1: Start the backend

Open PowerShell in the project folder and run:

```powershell
quick-start.bat
```

Once it starts, open:

```text
http://localhost:8000/docs
```

That page shows the live API.

---

## Step 2: Find the existing request in your Draeven app

Look for the part of your JavaScript that sends a prompt to an external AI endpoint. It may look like this:

```javascript
fetch('https://api.openai.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + OPENAI_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4',
    messages: [{ role: 'user', content: message }]
  })
})
```

---

## Step 3: Replace it with the local Jarvis call

Use the file in this repo at:

```text
gui-integration/draeven-integration.js
```

Or paste this code directly:

```javascript
async function sendToJarvis(message) {
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: message,
      session_id: 'draeven-session-1',
      task_type: 'general'
    })
  });

  const data = await response.json();
  return data.reply;
}
```

Then call it like this:

```javascript
const reply = await sendToJarvis(userInput);
renderMessage(reply);
```

---

## Step 4: Keep the same GUI

Your graphics, layout, and HUD design can remain exactly the same.

Only the networking layer changes.

That means you keep the look you love while making the logic smarter and more local.

---

## Step 5: Optional task routing

If you want to be extra clear, you can send a task type:

```javascript
body: JSON.stringify({
  message: userInput,
  task_type: 'coding'
})
```

Possible values:
- `general`
- `business`
- `coding`
- `creative`
- `marketing`
- `analysis`

That lets the local router decide which model should handle it.

---

## Step 6: Test it

Open the browser console and send a test message like:

```text
Give me a small plan for my next Etsy launch week
```

You should get a reply from the local Jarvis server.

---

## Important note

If your current Draeven app uses a generated snapshot file or a local Python server, keep that. The backend API is an additional layer that sits behind your UI.

This is the cleanest setup for you because it does not force you to rebuild the entire front end.
