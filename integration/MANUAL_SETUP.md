# JARVIS Integration Manual Setup Guide

Complete step-by-step instructions for manually installing and configuring all integration components without using automation scripts.

**Estimated time: 45-60 minutes**

## Prerequisites

Verify you have:
- Node.js 22.22.2+ (`node -v`)
- npm (`npm -v`)
- git (`git -v`)
- Port 20128 available for OmniRoute
- ~2GB free disk space

## Step 1: Create Integration Directories (5 min)

Create all necessary directories in your home folder:

```bash
# OmniRoute data directories
mkdir -p ~/.omniroute/logs
mkdir -p ~/.omniroute/backups

# Claude Mem storage
mkdir -p ~/.claude-mem/chroma

# Head Room configuration
mkdir -p ~/.headroom/logs

# Task Observer observations
mkdir -p ~/.task-observer/observations

# Claude Code plugin directory
mkdir -p ~/.claude/skills/task-observer
mkdir -p ~/.claude/plugins
```

Verify:
```bash
ls -la ~/.omniroute ~/.claude-mem ~/.headroom ~/.task-observer ~/.claude/
```

## Step 2: Copy Environment Files (5 min)

Copy all configuration templates from the integration directory:

```bash
# Copy OmniRoute configuration
cp ~/draeven-jarvis-system/integration/env-templates/.env.omniroute ~

# Copy Claude Mem configuration
cp ~/draeven-jarvis-system/integration/env-templates/.env.claude-mem ~

# Copy Head Room configuration
cp ~/draeven-jarvis-system/integration/env-templates/headroom-config.json ~/.headroom/config.json

# Copy Claude Code configurations
cp ~/draeven-jarvis-system/integration/env-templates/mcp-servers.json ~/.claude/
cp ~/draeven-jarvis-system/integration/env-templates/commands.json ~/.claude/
cp ~/draeven-jarvis-system/integration/env-templates/status-line.json ~/.claude/
```

Verify:
```bash
ls -la ~/{.env.omniroute,.env.claude-mem}
ls -la ~/.headroom/config.json
ls -la ~/.claude/{mcp-servers.json,commands.json,status-line.json}
```

## Step 3: Install and Build OmniRoute (15 min)

Navigate to the OmniRoute module and build:

```bash
cd ~/draeven-jarvis-system/modules/OmniRoute

# Install dependencies
npm install

# Build the service
npm run build
```

Verify:
```bash
ls -la dist/omniroute.mjs
echo "OmniRoute build successful"
```

### Start OmniRoute

Start the service in the background:

```bash
# Option 1: Simple background process
npm start &

# Option 2: Using screen (detachable session)
screen -S omniroute npm start

# Option 3: Using tmux
tmux new-session -d -s omniroute 'cd ~/draeven-jarvis-system/modules/OmniRoute && npm start'
```

Test health endpoint:

```bash
# Wait 5 seconds for startup
sleep 5

# Check health
curl http://127.0.0.1:20128/health

# Expected response:
# {"ok":true,"version":"3.8.52"}
```

If health check fails:
```bash
# Check if port is in use
lsof -i :20128

# View logs
tail -f ~/.omniroute/logs/omniroute.log

# Try rebuilding
cd ~/draeven-jarvis-system/modules/OmniRoute
npm run build
npm start
```

## Step 4: Install Claude Mem (10 min)

Build Claude Mem plugin:

```bash
cd ~/draeven-jarvis-system/modules/claude-mem

# Install dependencies
npm install

# Build the plugin
npm run build-and-sync
```

Verify:
```bash
ls -la dist/
echo "Claude Mem build successful"
```

### Install as Claude Plugin

The Claude Mem plugin needs to be installed in the Claude application:

**Method 1: Via Claude App (Recommended)**
1. Open Claude app
2. Go to Settings → Customize
3. Click "Upload plugin/skill"
4. Select folder: `~/draeven-jarvis-system/modules/claude-mem/dist/`
5. Click "Install"

**Method 2: Manual Plugin Installation**
```bash
# Copy plugin to Claude plugins directory
mkdir -p ~/.claude/plugins/claude-mem
cp -r ~/draeven-jarvis-system/modules/claude-mem/dist/* ~/.claude/plugins/claude-mem/

# Restart Claude Code to load plugin
```

Verify installation:
```bash
ls ~/.claude-mem/claude-mem.db  # Database will be created on first use
echo "Claude Mem ready"
```

## Step 5: Build Head Room (10 min)

Head Room requires platform-specific native builds using Tauri:

```bash
cd ~/draeven-jarvis-system/modules/headroom

# Install dependencies
npm install

# Build native application (platform-specific)
npm run tauri:build
```

This will build:
- **Linux**: Binary at `src-tauri/target/release/headroom`
- **macOS**: App at `src-tauri/target/release/bundle/macos/Head Room.app`
- **Windows**: Installer at `src-tauri/target/release/bundle/msi/`

### Launch Head Room

```bash
# Linux
./src-tauri/target/release/headroom &

# macOS
open src-tauri/target/release/bundle/macos/Head\ Room.app

# Windows (Run from Command Prompt)
src-tauri\target\release\headroom.exe
```

Head Room will appear in your system tray. Verify by checking:
- System tray for Head Room icon
- Logs: `tail -f ~/.headroom/logs/headroom.log`

## Step 6: Apply Claude Code Configuration (5 min)

Update your Claude Code configuration with integration settings:

### Option 1: Automated (Recommended)
The MCP servers and commands are already copied in Step 2.
Just restart Claude Code.

### Option 2: Manual Configuration

If you want to manually merge configurations:

**Update CLAUDE.md**
Add this to `~/.claude/CLAUDE.md` or create it:

```markdown
# JARVIS Integrated System

@omniroute-gateway
@claude-mem
@task-observer

## Integrated Components
- **OmniRoute**: http://127.0.0.1:20128 (AI gateway)
- **Claude Mem**: ~/.claude-mem/ (persistent memory)
- **Task Observer**: ~/.task-observer/ (skill optimization)
- **Head Room**: System tray (quota tracking)

## Architecture
1. All LLM requests → OmniRoute (quota-aware routing)
2. Session context → Claude Mem (token savings)
3. Provider selection → OmniRoute (compression: 89% avg)
4. Quota tracking → Head Room dashboard
5. Skill optimization → Task Observer observations
```

### Verify MCP Configuration

Check that configurations are valid JSON:

```bash
# Validate MCP servers
python3 -m json.tool ~/.claude/mcp-servers.json

# Validate commands
python3 -m json.tool ~/.claude/commands.json

# Validate status line
python3 -m json.tool ~/.claude/status-line.json
```

All should output formatted JSON with no errors.

## Step 7: Install Task Observer (10 min)

Build Task Observer meta-skill:

```bash
cd ~/draeven-jarvis-system/modules/TaskObserver

# Install dependencies
npm install

# Build skill
npm run build
```

Copy to Claude Code:

```bash
# Copy built skill to Claude Code skills directory
mkdir -p ~/.claude/skills/task-observer
cp -r dist/* ~/.claude/skills/task-observer/

# Verify
ls ~/.claude/skills/task-observer/
```

### Install as Claude Skill

**Via Claude App**
1. Open Claude app
2. Go to Settings → Customize
3. Click "Upload skill"
4. Select folder: `~/.claude/skills/task-observer/`
5. Click "Install"

Verify in CLAUDE.md that `@task-observer` is referenced:

```bash
grep "@task-observer" ~/.claude/CLAUDE.md
```

## Step 8: Restart Claude Code

For all integrations to take effect, restart Claude Code:

```bash
# Close Claude Code completely

# Restart Claude Code
claude --new

# Or via Claude app: Restart the session
```

## Step 9: Verification (5 min)

Run comprehensive verification:

```bash
# Run verification script
bash ~/draeven-jarvis-system/integration/verify.sh
```

Manual checks:

```bash
# 1. Check directories
ls -la ~/.omniroute ~/.claude-mem ~/.headroom ~/.task-observer

# 2. Check OmniRoute health
curl http://127.0.0.1:20128/health

# 3. Check JARVIS HUD
curl http://127.0.0.1:4783/api/health

# 4. Check Claude Mem database
file ~/.claude-mem/claude-mem.db

# 5. Check Claude Code configuration
ls -la ~/.claude/{mcp-servers.json,commands.json,status-line.json}

# 6. Check Task Observer
ls -la ~/.claude/skills/task-observer/

# 7. Check Head Room
ps aux | grep headroom
```

## Troubleshooting

### OmniRoute won't start
```bash
# Check if port is already in use
lsof -i :20128

# Kill existing process
pkill -f "omniroute"

# Check logs
tail -f ~/.omniroute/logs/omniroute.log

# Rebuild from clean
cd ~/draeven-jarvis-system/modules/OmniRoute
rm -rf dist node_modules
npm install
npm run build
npm start
```

### Claude Mem not persisting
```bash
# Restart Claude Code (sessions share memory)
# Check database exists
ls -la ~/.claude-mem/claude-mem.db

# Check permissions
chmod 755 ~/.claude-mem
chmod 755 ~/.claude-mem/chroma

# View logs
tail -f ~/.claude-mem/logs/claude-mem.log
```

### Head Room not showing quota
```bash
# Verify JARVIS is running
curl http://127.0.0.1:4783/api/health

# Check Head Room config
cat ~/.headroom/config.json

# Kill and restart Head Room
pkill -f "headroom"
sleep 2
./src-tauri/target/release/headroom &
```

### Task Observer not triggering
```bash
# Verify skill installed
ls ~/.claude/skills/task-observer/

# Check CLAUDE.md includes reference
grep "@task-observer" ~/.claude/CLAUDE.md

# Restart Claude Code session
# Task Observer activates on new sessions
```

### MCP servers not connecting
```bash
# Validate configuration
python3 -m json.tool ~/.claude/mcp-servers.json

# Check server definitions
cat ~/.claude/mcp-servers.json

# Restart Claude Code
```

## Next Steps

1. **Monitor Token Usage**
   - Open Head Room dashboard (system tray)
   - Track daily burndown

2. **Test OmniRoute**
   - Visit http://127.0.0.1:20128/dashboard
   - Check free-tier consolidation
   - Review provider routing

3. **Use Custom Commands**
   - `jarvis:status` - Check JARVIS health
   - `jarvis:quota` - View quota breakdown
   - `jarvis:memory` - Query session memory
   - `jarvis:headroom` - Open quota dashboard

4. **Review Observations**
   - Check Task Observer pending observations
   - Approve skill improvements
   - Monitor optimization suggestions

5. **Enable Status Line**
   - Open Claude Code
   - View status line showing:
     - OmniRoute health
     - Token quota
     - Compression ratio
     - Active providers
     - Session memory size

## Integration Architecture

```
┌─────────────────────────────────────────────────────┐
│                  JARVIS HUD                         │
│           (http://127.0.0.1:4783)                  │
└──────────┬──────────────────────────────────────────┘
           │
           ├─→ [OmniRoute Gateway]  (port 20128)
           │    • 358+ providers
           │    • 89% token compression
           │    • Quota-aware routing
           │    • Circuit breaker fallback
           │
           ├─→ [Claude Mem]
           │    • Persistent memory
           │    • Automatic compression
           │    • Query interface
           │
           ├─→ [Claude Code]
           │    • MCP server integration
           │    • Custom commands
           │    • Status line metrics
           │
           ├─→ [Head Room]
           │    • System tray quota display
           │    • Real-time burndown
           │    • Provider load metrics
           │
           └─→ [Task Observer]
                • Pattern detection
                • Skill generation
                • Performance optimization
```

## Support

For detailed component documentation:
- **OmniRoute**: `~/draeven-jarvis-system/integration/OMNIROUTE_CONFIG.md`
- **Claude Mem**: `~/draeven-jarvis-system/integration/CLAUDE_MEM_CONFIG.md`
- **Head Room**: `~/draeven-jarvis-system/integration/HEADROOM_CONFIG.md`
- **Task Observer**: `~/draeven-jarvis-system/integration/TASK_OBSERVER_CONFIG.md`
- **Claude Code Setup**: `~/draeven-jarvis-system/integration/CLAUDE_CODE_SETUP_CONFIG.md`

## Completion Checklist

After following all steps, verify:

- [ ] All directories created
- [ ] Environment files copied
- [ ] OmniRoute built and running
- [ ] OmniRoute health check passing
- [ ] Claude Mem built and plugin installed
- [ ] Claude Mem database created
- [ ] Head Room built (native app)
- [ ] Head Room running in system tray
- [ ] Claude Code configuration files copied
- [ ] Task Observer built and installed
- [ ] Claude Code restarted
- [ ] Verification script passes
- [ ] Custom commands available in Claude Code
- [ ] Status line showing metrics
- [ ] MCP servers connecting
- [ ] Task Observer observations accumulating

**Status**: Integration ready for use

**Estimated daily token savings**: 40-60% reduction through compression + quota awareness
