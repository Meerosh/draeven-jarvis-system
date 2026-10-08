# OmniRoute Integration into JARVIS

## Architecture
OmniRoute acts as the unified AI gateway for JARVIS, handling provider routing, token optimization, and fallback chains across 358+ LLM providers.

## Integration Points

### 1. Service Configuration
```
Service Name: omniroute-gateway
Port: 20128 (default)
Protocol: HTTP/REST + OpenAI-compatible API
Database: SQLite (OmniRoute manages)
```

### 2. JARVIS Integration
- **Routing**: JARVIS frontend sends all LLM requests to OmniRoute instead of direct providers
- **MCP Server**: OmniRoute's 110 tools exposed via MCP for agent selection
- **A2A Protocol**: Cloud agents coordinate through OmniRoute A2A endpoint
- **Compression**: RTK + Caveman compression saves 15-95% tokens (~89% avg)

### 3. Free Tier Consolidation
- Stacks 489 free-tier entries across 35 provider pool keys
- ~1.62B free tokens/month baseline
- Up to ~2.22B in first month with signup credits
- Dashboard at: http://127.0.0.1:20128/dashboard/free-tiers

### 4. Environment Setup
Create `.env.omniroute` in project root:
```
OMNIROUTE_PORT=20128
OMNIROUTE_HOST=127.0.0.1
OMNIROUTE_DB_PATH=~/.omniroute/
OMNIROUTE_LOG_LEVEL=info
```

### 5. Startup
```bash
cd modules/OmniRoute
npm install
npm run build
npm start
```

### 6. Health Check
```
GET http://127.0.0.1:20128/health
Expected: { ok: true, version: "3.8.52" }
```

## Token Savings
- Replaces direct provider calls with consolidated free-tier routing
- Automatic fallback when primary provider quota exhausted
- Compression reduces average token usage by 89%
- Pools tokens across 35 provider keys

## Quota Tracking
- Dashboard at /dashboard/free-tiers shows live usage
- Quota-Share feature tracks per-model consumption
- Alerts when approaching pool limits

## Circuit Breaker
OmniRoute includes built-in circuit breaker for provider reliability:
- Detects failing providers
- Routes around them automatically
- Cooldown periods before retry
- Manual override capability
