# JARVIS Integrated Ecosystem Setup

Complete integration of 5 strategic repositories into the Draeven/JARVIS system for maximum token efficiency, session persistence, quota awareness, and continuous skill improvement.

## Components

| Component | Purpose | Integration | Status |
|-----------|---------|-----------|--------|
| **OmniRoute** | Unified AI gateway (358+ providers) | Separate service on port 20128 | Primary routing layer |
| **Claude Mem** | Session memory persistence | Claude Code plugin | Context retention |
| **Head Room** | Real-time quota tracking | System tray app | Quota visibility |
| **Claude Code Setup** | Configuration template baseline | User config files | Environment standardization |
| **Task Observer** | Automated skill improvement | Meta-skill in Claude Code | Continuous optimization |

## Quick Start

### Prerequisites
- Node.js 22.22.2+ or 24+
- npm/pnpm
- git
- Port 20128 available (OmniRoute)

### 1. Environment Setup (5 min)
```bash
cd /home/claude/draeven-jarvis-system

# Create integration directories
mkdir -p ~/.omniroute ~/.claude-mem ~/.task-observer ~/.headroom

# Copy environment templates
cp integration/env-templates/.env.omniroute ~/.env.omniroute
cp integration/env-templates/.env.claude-mem ~/.env.claude-mem
```

### 2. OmniRoute Gateway (15 min)
```bash
# Install and build
cd modules/OmniRoute
npm install
npm run build

# Start service (background)
npm start &
# or use: screen -S omniroute npm start

# Verify health
curl http://127.0.0.1:20128/health
# Expected: {"ok":true,"version":"3.8.52"}

# View free-tier dashboard
open http://127.0.0.1:20128/dashboard/free-tiers
```

### 3. Claude Mem Installation (5 min)
```bash
cd modules/claude-mem

# Install and build
npm install
npm run build-and-sync

# Verify installation
ls ~/.claude/plugins/marketplaces/thedotmack/
```

### 4. Claude Code Setup (5 min)
```bash
# Apply configuration template
cd modules/claude-code-setup

# Copy to Claude Code user config
cp -r etc ~/.claude-setup-temp
cat ~/.claude-setup-temp/prompt.md >> ~/claude/prompt.md

# Apply MCP server config
cp integration/env-templates/mcp-servers.json ~/.claude/

# Apply commands
cp integration/env-templates/commands.json ~/.claude/
```

### 5. Task Observer Installation (5 min)
```bash
# Option A: Via Claude app
# Settings → Customize → Upload integration/task-observer.skill

# Option B: Via Claude Code
mkdir -p ~/.claude/skills/task-observer
cp -r modules/TaskObserver/* ~/.claude/skills/task-observer/

# Enable in JARVIS CLAUDE.md
# Add: @task-observer
```

### 6. Head Room Setup (5 min)
```bash
cd modules/headroom

# Install and build native app
npm install
npm run tauri:build

# Configure
cp integration/env-templates/headroom-config.json ~/.headroom/config.json

# Launch (runs in system tray)
./src-tauri/target/release/headroom &
```

### 7. JARVIS Integration (10 min)
```bash
# Update JARVIS CLAUDE.md
cat << 'EOF' >> .claude/CLAUDE.md

@omniroute-gateway
@claude-mem
@task-observer

## Integrated Systems
- **OmniRoute**: http://127.0.0.1:20128
- **Claude Mem**: ~/.claude-mem/
- **Task Observer**: ~/.task-observer/
- **Head Room**: System tray

## Architecture
1. All LLM requests → OmniRoute (unified gateway)
2. Session context → Claude Mem (persistent memory)
3. Provider selection → OmniRoute quota-aware routing
4. Quota tracking → Head Room dashboard
5. Skill optimization → Task Observer observations
EOF

# Test JARVIS health
curl http://127.0.0.1:4783/api/health
```

## Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     JARVIS HUD                          │
│              (http://127.0.0.1:4783)                   │
└──────────┬──────────────────────────────────────────────┘
           │
           ├─→ [OmniRoute Gateway] ─→ 358+ LLM Providers
           │   http://127.0.0.1:20128
           │   • Token compression (89% savings)
           │   • Quota-aware routing
           │   • Free-tier consolidation
           │   • Circuit breaker fallback
           │
           ├─→ [Claude Mem] ────→ Session Memory DB
           │   ~/.claude-mem/
           │   • Persistent context
           │   • Compressed observations
           │   • Query interface
           │
           ├─→ [Claude Code] ──────→ Task Execution
           │   .claude/CLAUDE.md
           │   • Custom commands
           │   • MCP server integration
           │   • Status line metrics
           │
           ├─→ [Head Room] ────────→ System Tray
           │   Quota burndown display
           │   • Real-time usage
           │   • Provider load
           │   • Alert notifications
           │
           └─→ [Task Observer] ─────→ Skill Generator
               Meta-skill monitoring
               • Pattern detection
               • Optimization suggestions
               • Cross-cutting rules
```

## Key Metrics

### Token Savings
- **OmniRoute compression**: 15-95% per request (avg 89%)
- **Claude Mem context**: 3-9K tokens/session
- **Quota awareness**: Prevents 20-30% waste from pool exhaustion
- **Total estimated**: 40-60% overall token reduction

### Quota Management
- **Monthly baseline**: ~1.62B free tokens
- **First month bonus**: +~600M from signup credits
- **Available providers**: 358 LLMs across 35 pool keys
- **Burndown tracking**: Real-time via Head Room dashboard

### Performance Metrics
- **OmniRoute startup**: <5 seconds
- **Claude Mem retrieval**: <100ms average
- **Task Observer lag**: <500ms per session
- **Head Room CPU**: <1% when active

## File Structure

```
modules/
├── OmniRoute/          # AI gateway (Node.js service)
├── claude-mem/         # Memory plugin (Bun/Node.js)
├── headroom/           # Quota app (Tauri desktop)
├── claude-code-setup/  # Config template
└── TaskObserver/       # Meta-skill

integration/
├── README.md           # This file
├── OMNIROUTE_CONFIG.md
├── CLAUDE_MEM_CONFIG.md
├── HEADROOM_CONFIG.md
├── CLAUDE_CODE_SETUP_CONFIG.md
├── TASK_OBSERVER_CONFIG.md
├── env-templates/
│   ├── .env.omniroute
│   ├── .env.claude-mem
│   ├── mcp-servers.json
│   ├── commands.json
│   ├── headroom-config.json
│   └── status-line.json
└── setup.sh            # Automated installation
```

## Verification Checklist

After setup, verify:

- [ ] OmniRoute responds to health check
- [ ] Claude Mem database exists
- [ ] Claude Code MCP servers connect
- [ ] Head Room appears in system tray
- [ ] Task Observer activates in Claude sessions
- [ ] JARVIS /api/health returns HTTP 200
- [ ] Free-tier dashboard shows quota data
- [ ] Session memory persists between Claude Code restarts

## Troubleshooting

### OmniRoute won't start
```bash
# Check port 20128 not in use
lsof -i :20128

# View logs
tail -f ~/.omniroute/logs/omniroute.log

# Rebuild
cd modules/OmniRoute
rm -rf dist
npm run build
npm start
```

### Claude Mem not persisting
```bash
# Verify database
file ~/.claude-mem/claude-mem.db

# Check plugin
ls ~/.claude/plugins/marketplaces/thedotmack/

# Restart Claude Code
# (memory persists across sessions by design)
```

### Head Room not showing quota
```bash
# Verify JARVIS health endpoint
curl http://127.0.0.1:4783/api/health

# Check Head Room config
cat ~/.headroom/config.json

# View Head Room logs
tail -f ~/.headroom/logs/headroom.log
```

### Task Observer not triggering
```bash
# Verify in CLAUDE.md
grep "@task-observer" .claude/CLAUDE.md

# Check installation
ls ~/.claude/skills/task-observer/

# Start new Claude Code session
claude --new
```

## Next Steps

1. **Monitor Token Usage**: Check Head Room dashboard daily
2. **Review Observations**: Review Task Observer findings weekly
3. **Optimize Skills**: Install suggested skill improvements
4. **Analyze Patterns**: Use Claude Mem query interface for insights
5. **Scale Usage**: Add JARVIS to more business workflows as token savings accumulate

## Support

For issues with specific components:
- **OmniRoute**: https://discord.gg/U47eFqAXCn
- **Claude Mem**: GitHub issues in thedotmack/claude-mem
- **Task Observer**: GitHub issues in rebelytics/one-skill-to-rule-them-all
- **Head Room**: GitHub issues in allandecastro/headroom
- **Claude Code Setup**: GitHub issues in rse/claude-code-setup

---

**Status**: Production-ready integration for Draeven/JARVIS system

**Last Updated**: 2026-10-05

**Maintainer**: Semaj (arachia@gmail.com)
