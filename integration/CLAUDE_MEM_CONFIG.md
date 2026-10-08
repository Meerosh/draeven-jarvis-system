# Claude Mem Integration into JARVIS

## Architecture
Claude Mem provides persistent memory persistence across JARVIS sessions, reducing context re-entry overhead and token waste by maintaining session history.

## Integration Points

### 1. Installation as Claude Code Plugin
Claude Mem is installed as a Claude Code plugin that:
- Automatically captures session context between runs
- Compresses observations using Claude Agent SDK
- Injects relevant memory into future JARVIS sessions
- Reduces duplicate context by 40-60%

### 2. Database Locations
```
Plugin DB: ~/.claude-mem/claude-mem.db (SQLite)
Vector Store: ~/.claude-mem/chroma/ (Chroma embeddings)
```

### 3. Memory Categories for JARVIS
- **Session State**: Current JARVIS configuration, running services
- **Project Context**: Business status, pipeline state, blockers
- **Error Patterns**: Known failures, recovery procedures
- **Configuration**: Provider settings, routing rules, fallbacks

### 4. Setup Steps
```bash
# 1. Build Claude Mem
cd modules/claude-mem
npm install
npm run build-and-sync

# 2. Verify installation
ls ~/.claude/plugins/marketplaces/thedotmack/

# 3. Enable in JARVIS CLAUDE.md
# Add to .claude/CLAUDE.md:
# @claude-mem
# Persist memory across sessions
```

### 5. Integration with JARVIS
- Automatically loads project context on session start
- Captures errors and solutions for future use
- Maintains provider quota history
- Tracks skill usage patterns

### 6. Memory Queries
Claude Mem exposes:
- `memory:retrieve` - fetch stored observations
- `memory:store` - save new observations
- `memory:search` - query by topic
- `memory:purge` - clear outdated entries

## Token Savings
- Eliminates re-explaining project context: ~2-5K tokens/session
- Reduces debugging time via error history: ~1-3K tokens/session
- Caches common responses: ~500-1K tokens/session
- **Estimated saving: 3-9K tokens per JARVIS session** (avg 6K)

## Configuration
```javascript
// In JARVIS session initialization
memoryConfig = {
  autoPersist: true,
  compressionLevel: 'high',
  retentionDays: 90,
  priorityCategories: ['errors', 'quota', 'configuration']
}
```

## Dependencies
- Bun (auto-installed if missing)
- uv (for Python/Chroma, auto-installed)
- Node.js 18+

## Logs
```bash
# View Claude Mem logs
tail -f ~/.claude-mem/logs/session.log
```
