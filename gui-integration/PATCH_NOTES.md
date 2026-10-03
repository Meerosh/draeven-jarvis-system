# Quick Patch: From ChatGPT's Findings

**Problem Identified:**
Your current handler matches words anywhere in input. So "What's my top priority?" triggers Tasks because it contains "priority".

**Solution:**
Use explicit command matching with stricter regex patterns that require exact phrase starts or word boundaries.

**Files to Update:**
1. `serve.py` - Add CORS and proxy
2. `js/main.js` - Narrow command matching, add backend routing
3. `index.html` - Add conversation display div
4. `styles.css` - Add conversation styling

**Exact Changes:**

### In `js/main.js`, the command matching must change from:
```javascript
// OLD: Matches words anywhere
if (/\b(task|tasks|priorit|priority)\b/.test(q)) showView('tasks');
```

To:
```javascript
// NEW: Exact phrase or anchored match
if (/^\s*(show\s+)?tasks?\s*$/i.test(text)) showView('tasks');
```

This means:
- `show tasks` ✅ matches
- `tasks` ✅ matches  
- `What's my top priority?` ❌ does NOT match

Then that question goes to the backend instead.

---

See `DRAEVEN_FINAL_IMPLEMENTATION.md` for the complete replacement code.
