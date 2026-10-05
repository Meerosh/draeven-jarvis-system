# Quick Reference: Next Steps After Dinner

**All automated setup is complete. Here's what you need to do next:**

---

## Step 1: Build Head Room (5 minutes)
Open terminal and run:
```bash
cd /home/claude/draeven-jarvis-system/modules/headroom
npm run tauri:build
```

This compiles the quota tracking application for your system.

**Wait for it to finish.** You'll see a message saying "Building..." then completion.

---

## Step 2: Install Plugins in Claude App (5 minutes)

### Install Claude Mem Plugin
1. Open Claude application
2. Click **Settings** (gear icon)
3. Click **Customize**
4. Click **Upload plugin/skill** button
5. Navigate to and select: `/home/claude/draeven-jarvis-system/modules/claude-mem/dist/`
6. Click **Upload**
7. Wait for success message

### Install Task Observer Skill
1. Still in Customize → **Skills** tab
2. Click **Upload skill** button
3. Navigate to and select: `~/.claude/skills/task-observer/`
4. Click **Upload**
5. Wait for success message

---

## Step 3: Close and Restart Claude Code (2 minutes)

1. **Close Claude Code completely** (exit the application)
2. Wait 3 seconds
3. **Open Claude Code again**

Claude Code will automatically load:
- OmniRoute with 358+ LLM providers (110 tools)
- Claude Mem with persistent memory (8 tools)
- Status line showing real-time metrics (8 segments)
- 8 custom JARVIS commands in command palette

---

## Step 4: Start OmniRoute Gateway (2 minutes)

Open a new terminal and run:
```bash
cd /home/claude/draeven-jarvis-system/modules/OmniRoute
npm start &
```

Wait ~5 seconds, then verify:
```bash
curl http://127.0.0.1:20128/health
```

You should see: `{"ok":true,"version":"3.8.52"}`

---

## Step 5: Start Head Room (1 minute)

In terminal, run:
```bash
cd /home/claude/draeven-jarvis-system/modules/headroom
./src-tauri/target/release/headroom &
```

Look for **Head Room icon in your system tray** (top right on most systems).

---

## Step 6: Verify Everything Works

Click on the Head Room system tray icon → should show quota dashboard

In Claude Code:
- Command palette (Cmd/Ctrl+Shift+P) → type `jarvis:` 
- Should see 8 JARVIS commands available

In Claude Code status bar (bottom):
- Should see 8 segments: OmniRoute health, memory, tokens, compression, providers, cache, observer, timer

---

## Done! 🎉

You're now running:
- ✓ OmniRoute Gateway (358+ providers, 89% compression)
- ✓ Claude Mem (persistent memory, 3-9K tokens/session saved)
- ✓ Head Room (real-time quota tracking)
- ✓ Task Observer (automatic skill improvements)
- ✓ Status line (real-time metrics)
- ✓ 8 custom JARVIS commands

**Expected token savings: 40-60% reduction**

---

## Dashboards & Access Points

Once running:
- **OmniRoute Dashboard**: http://127.0.0.1:20128/
- **JARVIS HUD**: http://127.0.0.1:4783/
- **Head Room**: Click system tray icon
- **Claude Mem**: View in Claude Code
- **Task Observer**: In Claude Code and `~/.task-observer/`

---

## If Something Goes Wrong

See `AUTOMATION_COMPLETE.md` → "Troubleshooting Guide" section for specific issues.

Most common fixes:
- OmniRoute not starting? → Kill port 20128: `pkill -f "npm start"` then restart
- MCP not connecting? → Restart Claude Code
- Claude Mem missing? → Restart Claude app
- Status line not showing? → Restart Claude Code

---

**Estimated time for all steps: 20-30 minutes**

**Then you can enjoy token savings of 40-60%! 🚀**
