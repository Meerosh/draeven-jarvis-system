# Deployment Checklist: Agents Integration

This checklist verifies that the Agents Agency + Oh My Hermes + Draeven integration is properly deployed and functional on the Windows system.

## Pre-Deployment Verification (Linux Container)

- [x] Agents Agency repository cloned: `/home/claude/msitarzewski/agency-agents/`
- [x] Oh My Hermes repository cloned: `/home/claude/witt3rd/oh-my-hermes/`
- [x] agents_agency_bridge.py created: `integrations/agents_agency_bridge.py`
- [x] Agent configuration generated: `integrations/agent_config.json`
- [x] draeven_core.py updated with orchestration methods
- [x] Integration tests created and passing (7/7)
- [x] Documentation complete:
  - [x] INTEGRATION_GUIDE.md
  - [x] INTEGRATION_COMPLETE.md
  - [x] AGENTS_QUICK_REFERENCE.md

## Windows Deployment Steps

### Step 1: Copy Repositories to Windows

```powershell
# From Windows PowerShell with Draeven repository access
# Copy Agents Agency
Copy-Item -Path "\\source\msitarzewski\agency-agents" `
          -Destination "C:\Users\Arach\Documents\Jarvis\Citadel\repositories\agency-agents" `
          -Recurse

# Copy Oh My Hermes
Copy-Item -Path "\\source\witt3rd\oh-my-hermes" `
          -Destination "C:\Users\Arach\Documents\Jarvis\Citadel\repositories\oh-my-hermes" `
          -Recurse
```

**Verification:**
```powershell
# Verify repository paths exist
Test-Path "C:\Users\Arach\Documents\Jarvis\Citadel\repositories\agency-agents\divisions.json"
Test-Path "C:\Users\Arach\Documents\Jarvis\Citadel\repositories\oh-my-hermes\README.md"
```

Expected: `True` for both

### Step 2: Update draeven_core.py Path References

In `C:\Users\Arach\my-agent\jarvis-frontdoor\hud\draeven_core.py`:

**Current (Linux-style):**
```python
sys.path.insert(0, str(Path(__file__).parent.parent / "integrations"))
from agents_agency_bridge import DraevenAgentOrchestrator
```

**Verify:** No changes needed - relative paths work on Windows too

**Verify:** `service_connections.py` imports work correctly
```powershell
# Test import
python -c "import sys; sys.path.insert(0, 'C:\Users\Arach\my-agent\jarvis-frontdoor\hud'); from draeven_core import DraevenCore"
```

Expected: No errors

### Step 3: Copy Integration Files

```powershell
# Copy agents_agency_bridge.py
Copy-Item -Path "C:\path\to\draeven-jarvis-system\integrations\agents_agency_bridge.py" `
          -Destination "C:\Users\Arach\my-agent\jarvis-frontdoor\integrations\agents_agency_bridge.py"

# Copy agent_config.json
Copy-Item -Path "C:\path\to\draeven-jarvis-system\integrations\agent_config.json" `
          -Destination "C:\Users\Arach\my-agent\jarvis-frontdoor\integrations\agent_config.json"

# Copy test suite
Copy-Item -Path "C:\path\to\draeven-jarvis-system\integrations\test_integration.py" `
          -Destination "C:\Users\Arach\my-agent\jarvis-frontdoor\integrations\test_integration.py"
```

**Verification:**
```powershell
Test-Path "C:\Users\Arach\my-agent\jarvis-frontdoor\integrations\agents_agency_bridge.py"
Test-Path "C:\Users\Arach\my-agent\jarvis-frontdoor\integrations\agent_config.json"
```

Expected: `True` for both

### Step 4: Update draeven_core.py Agent Paths

In the `_load_orchestrator()` method, verify paths:

```python
def _load_orchestrator(self):
    """Initialize agent orchestration system if available."""
    if DraevenAgentOrchestrator is None:
        return
    try:
        self.orchestrator = DraevenAgentOrchestrator()
        config_path = Path(__file__).parent.parent / "integrations" / "agent_config.json"
        if config_path.exists():
            self.agent_config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Warning: Could not load agent orchestrator: {e}")
```

**Update if needed:** Adjust config_path if integrations folder is in different location

### Step 5: Verify Agents Agency Bridge Configuration

Update path references in `agents_agency_bridge.py` if needed:

**Current (Linux-style):**
```python
AGENCY_ROOT = Path("/home/claude/msitarzewski/agency-agents")
```

**Windows Update:**
```python
AGENCY_ROOT = Path(r"C:\Users\Arach\Documents\Jarvis\Citadel\repositories\agency-agents")
```

**Or use environment variable:**
```python
import os
AGENCY_ROOT = Path(os.getenv("AGENCY_AGENTS_PATH", 
                             r"C:\Users\Arach\Documents\Jarvis\Citadel\repositories\agency-agents"))
```

### Step 6: Test Integration on Windows

```powershell
# Set working directory
cd "C:\Users\Arach\my-agent\jarvis-frontdoor"

# Run integration test
python integrations/test_integration.py

# Expected output:
# 🎉 Integration test suite PASSED!
# Total: 7/7 tests passed
```

**Troubleshooting if tests fail:**

```powershell
# Test individual components
python -c "from integrations.agents_agency_bridge import DraevenAgentOrchestrator; print('Bridge loaded')"
python -c "from hud.draeven_core import DraevenCore; print('Core loaded')"

# Check paths
python -c "from pathlib import Path; print(Path('integrations/agent_config.json').resolve())"
```

### Step 7: Verify Status in Draeven

```powershell
# Start Draeven if not running
cd "C:\Users\Arach\Documents\Jarvis\Citadel\desktop\jarvis-hud"
python run_hud.py

# In Draeven UI, say:
"what can you do"

# Expected response should include:
# "agent-orchestration: agent selection for tasks - ready"
# "omh-skills: workflow orchestration - ready"
# "agent_orchestration":
#   "orchestration": "ready",
#   "personas_available": 6,
#   "domains_available": 22,
#   "omh_skills_available": 6,
#   "total_agents_loaded": 277
```

### Step 8: Test Agent Selection

In Draeven UI, test requests that trigger agent selection:

**Test 1: Engineering Request**
```
"Design a microservices architecture for our API"
```
Expected route: "Draeven model route via Codex Engineer (codex)"

**Test 2: Strategy Request**
```
"Research current trends in AI development tools"
```
Expected route: "Draeven model route via Sonnet Strategist (claude-sonnet)"

**Test 3: Design Request**
```
"Create a visual mockup for our dashboard"
```
Expected route: "Draeven model route via Haiku Creator (claude-haiku)"

**Test 4: Security Request**
```
"Audit our authentication system for vulnerabilities"
```
Expected route: "Draeven model route via Security Expert (codex)"

### Step 9: Monitor Cost Tiers

Verify cost optimization is working:

```powershell
# In Draeven logs, check for:
# - Premium (Sonnet) calls: Strategic research only
# - Standard (Codex) calls: Architecture and security
# - Economy (Haiku) calls: Creative and rapid iteration
# - Local (Hermes) calls: Automation (no cloud cost)
```

### Step 10: Update Documentation

Copy documentation to Draeven docs folder:

```powershell
Copy-Item -Path "C:\path\to\draeven-jarvis-system\INTEGRATION_GUIDE.md" `
          -Destination "C:\Users\Arach\Documents\Jarvis\Citadel\documentation\INTEGRATION_GUIDE.md"

Copy-Item -Path "C:\path\to\draeven-jarvis-system\AGENTS_QUICK_REFERENCE.md" `
          -Destination "C:\Users\Arach\Documents\Jarvis\Citadel\documentation\AGENTS_QUICK_REFERENCE.md"

Copy-Item -Path "C:\path\to\draeven-jarvis-system\INTEGRATION_COMPLETE.md" `
          -Destination "C:\Users\Arach\Documents\Jarvis\Citadel\documentation\INTEGRATION_COMPLETE.md"
```

## Verification Checklist

- [ ] Agents Agency repository accessible at configured path
- [ ] Oh My Hermes repository accessible at configured path
- [ ] agents_agency_bridge.py imports successfully
- [ ] draeven_core.py loads orchestrator without errors
- [ ] Integration tests pass: 7/7
- [ ] Agent status shows "orchestration: ready"
- [ ] All 6 personas mapped correctly
- [ ] All 22 agent domains loaded (277 agents total)
- [ ] Task analysis correctly extracts task type/domain/complexity
- [ ] Agent selection routing works for all 5 test cases
- [ ] Cost tiers being respected (Sonnet→premium, Codex→standard, etc.)
- [ ] OMH skills loading correctly for workflows
- [ ] Documentation accessible to Draeven users

## Rollback Plan

If issues occur after deployment:

### Quick Rollback
```powershell
# Disable agent orchestration (draeven_core.py line ~15)
# Change:
from agents_agency_bridge import DraevenAgentOrchestrator
# To:
# from agents_agency_bridge import DraevenAgentOrchestrator
# DraevenAgentOrchestrator = None

# Restart Draeven HUD
Stop-Process -Name python -Force
# Then restart services normally
```

### Full Rollback
```powershell
# Restore original draeven_core.py from backup
# Remove integrations/agents_agency_bridge.py
# Remove integrations/agent_config.json
# Restart Draeven HUD
```

## Post-Deployment Monitoring

Monitor these metrics:

1. **Agent Selection Accuracy**: Are correct personas being selected?
2. **Workflow Completion Rate**: Do OMH skills complete successfully?
3. **Cost Efficiency**: Are cost tiers being respected?
4. **User Satisfaction**: Do specialist responses meet quality expectations?

## Support

If deployment issues occur:

1. Check Windows event logs for Python errors
2. Run integration tests: `python integrations/test_integration.py`
3. Check draeven_core.py imports separately
4. Verify file paths match your Windows configuration
5. Review INTEGRATION_GUIDE.md for architecture details

## Completion

Once all verification steps pass, the integration is complete and ready for production use.

**Deployment Date:** ________________  
**Verified By:** ________________  
**Notes:** ________________________________________________

---

**Next Step:** After successful Windows deployment, monitor logs for 1 week to ensure:
- Agent selection working correctly
- Cost optimization effective
- Workflow completions without errors
- User satisfaction with specialist responses
