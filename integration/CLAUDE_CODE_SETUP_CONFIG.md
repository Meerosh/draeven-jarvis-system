# Claude Code Setup Integration into JARVIS

## Architecture
Claude Code Setup is a configuration template that standardizes Claude Code environment, tool access, and custom commands across JARVIS development sessions.

## Integration Points

### 1. Installation
```bash
cd modules/claude-code-setup
# Copy configuration to Claude Code user config
cp -r etc ~/.claude/
cp -r .claude ./claude-code-setup-config
```

### 2. Central Prompt Configuration
Create `~/claude/prompt.md` with JARVIS-specific context:
```markdown
# JARVIS Agent Prompt

You are an AI assistant coordinating the Draeven/JARVIS system.

## Primary Goals
1. Save token usage through smart routing and memory
2. Maintain 4 active business verticals
3. Manage ~81 interdependent skills
4. Optimize provider selection via OmniRoute

## Architecture Awareness
- OmniRoute: AI gateway (358+ providers, token compression)
- Claude Mem: Session memory persistence
- Head Room: Quota tracking
- Task Observer: Skill improvement automation

## Hard Rules
- Never eval() user input - always validate with Zod
- Encrypt credentials at rest using blake3
- Sanitize all error messages (no PII leaks)
- Use worktree isolation for multi-session safety
- Always commit with proper attribution

## Memory-First Design
- Load session context from Claude Mem immediately
- Cache frequent responses to reduce token burn
- Defer non-critical calls to batch operations
- Compress observations before storing

## Provider Routing
- Prefer free tier providers via OmniRoute free-tier catalog
- Route through quota-aware scheduling
- Monitor burn rate and adjust batch sizes
- Switch providers when approaching quota
```

### 3. Custom Commands
Add to `.claude/commands.json`:
```json
{
  "commands": {
    "jarvis:status": {
      "description": "Check JARVIS system health and quota",
      "handler": "./scripts/jarvis-status.mjs",
      "icon": "🔍"
    },
    "jarvis:optimize": {
      "description": "Analyze token usage and suggest optimizations",
      "handler": "./scripts/jarvis-optimize.mjs",
      "icon": "⚡"
    },
    "jarvis:memory": {
      "description": "Query and manage session memory",
      "handler": "./scripts/jarvis-memory.mjs",
      "icon": "💾"
    },
    "jarvis:skills": {
      "description": "List, install, or update JARVIS skills",
      "handler": "./scripts/jarvis-skills.mjs",
      "icon": "🎯"
    },
    "jarvis:route": {
      "description": "Test OmniRoute provider routing",
      "handler": "./scripts/jarvis-route.mjs",
      "icon": "🛣️"
    }
  }
}
```

### 4. MCP Server Configuration
Configure in `~/.claude/mcp-servers.json`:
```json
{
  "omniroute-gateway": {
    "command": "node",
    "args": ["modules/OmniRoute/bin/omniroute.mjs", "mcp-server"],
    "env": {
      "OMNIROUTE_PORT": "20128",
      "OMNIROUTE_MCP_ENABLED": "true"
    }
  },
  "claude-mem": {
    "command": "node",
    "args": ["modules/claude-mem/dist/mcp-server.js"],
    "env": {
      "CLAUDE_MEM_DB": "~/.claude-mem/claude-mem.db"
    }
  }
}
```

### 5. Status Line Configuration
Create `~/.claude/status-line.json`:
```json
{
  "left": [
    "model",
    "session-tokens",
    "quota-burn-rate"
  ],
  "right": [
    "git-branch",
    "omniroute-status",
    "memory-status",
    "time"
  ],
  "refresh_interval": 30000,
  "theme": "discreet-blue"
}
```

### 6. Color Scheme
Add to `~/.claude/colors.json`:
```json
{
  "scheme": "discreet-blue-brown",
  "accent": "#2C5AA0",
  "background": "#1E1E1E",
  "foreground": "#E0E0E0",
  "warning": "#D4A574",
  "error": "#C74C3C",
  "success": "#2E8B57"
}
```

### 7. Context File Assembly
Configure `~/.claude/claude.config.json`:
```json
{
  "context_sources": [
    {
      "path": "~/.claude/prompt.md",
      "priority": "always",
      "weight": 1000
    },
    {
      "path": ".claude/CLAUDE.md",
      "priority": "project",
      "weight": 500
    },
    {
      "path": "etc/claude.md",
      "priority": "project",
      "weight": 300
    }
  ],
  "assembly": {
    "merge_order": ["always", "project"],
    "temp_location": "~/.claude/CLAUDE.md.tmp",
    "validate_frontmatter": true
  }
}
```

### 8. Integration with JARVIS CLAUDE.md
JARVIS project `.claude/CLAUDE.md` should include:
```markdown
# JARVIS System Context

@claude-mem
@task-observer
@omniroute-gateway

## Integration Status
- OmniRoute Gateway: http://127.0.0.1:20128
- Claude Mem: ~/.claude-mem/
- Task Observer: ~/.task-observer/
- Head Room: System tray app

## Available Commands
- `jarvis:status` - System health
- `jarvis:optimize` - Token optimization
- `jarvis:memory` - Memory management
- `jarvis:skills` - Skill operations
- `jarvis:route` - Provider routing

## Environment
- Node.js: 22.22.2+
- Working Directory: ~/.draeven-jarvis-system/
- Base Branch: main
- Worktree Strategy: Use .claude/worktrees/
```

## Configuration Verification

### Health Check Script
```bash
#!/bin/bash
# Check all Claude Code configuration

echo "=== Claude Code Setup Health Check ==="

# Verify prompt file
test -f ~/claude/prompt.md && echo "✓ Prompt configured" || echo "✗ Prompt missing"

# Verify commands
test -f ~/.claude/commands.json && echo "✓ Commands configured" || echo "✗ Commands missing"

# Verify MCP servers
test -f ~/.claude/mcp-servers.json && echo "✓ MCP servers configured" || echo "✗ MCP servers missing"

# Verify status line
test -f ~/.claude/status-line.json && echo "✓ Status line configured" || echo "✗ Status line missing"

# Test MCP server connectivity
curl -s http://localhost:20128/health && echo "✓ OmniRoute available" || echo "✗ OmniRoute offline"

# Verify Claude Mem
test -d ~/.claude-mem && echo "✓ Claude Mem installed" || echo "✗ Claude Mem missing"
```

## Customization Points

1. **Custom Commands**: Add project-specific commands in commands.json
2. **MCP Servers**: Register additional servers in mcp-servers.json
3. **Prompt**: Edit ~/claude/prompt.md for session-wide instructions
4. **Status Display**: Customize status-line.json for different layouts
5. **Color Theme**: Modify colors.json for your preferences

## Benefits for JARVIS

1. **Consistency**: Same environment across all JARVIS sessions
2. **Efficiency**: Pre-configured tools reduce setup overhead
3. **Automation**: Custom commands handle common workflows
4. **Integration**: MCP servers automatically available
5. **Visibility**: Status line shows real-time system metrics
