# Draeven Integration Guide: Agents Agency + Oh My Hermes

## Overview

This integration connects three powerful systems:
- **Agents Agency**: 277 specialized AI agent personalities across 22 domains
- **Oh My Hermes (OMH)**: Multi-agent orchestration skills for workflows
- **Draeven Core**: Tool-first routing with provider personas

## Architecture

### Component Layers

```
┌─────────────────────────────────────────────────────────┐
│  Draeven Core (hud/draeven_core.py)                     │
│  - Tool-first request routing                           │
│  - Agent orchestration analysis                         │
│  - Provider persona selection                           │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────▼──────────┐
        │  Agent Orchestrator │ (agents_agency_bridge.py)
        │  - Task analysis    │
        │  - Domain detection │
        │  - Agent selection  │
        └─────────┬──────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
┌───▼──────────┐    ┌──────────▼────┐
│ Agents Agency │    │ OMH Skills     │
│ (277 agents) │    │ (6 skills)     │
│ (22 domains) │    │ (workflow mgt) │
└──────────────┘    └────────────────┘
```

### Flow Diagram

```
User Request
    │
    ▼
Draeven Core (Tool-first routing)
    │
    ├─ [Shopify/Etsy/Wright/Repository tools] ──→ Verified execution
    │
    └─ [General task] ──→ Analyze with Orchestrator
       │
       ├─ Extract task_type (research|planning|execution|triage)
       ├─ Extract domain (engineering|strategy|design|security|...)
       ├─ Extract complexity (low|medium|high)
       │
       ▼
       Select Agent Persona
       │
       ├─ engineering-architect → Codex (operations)
       ├─ strategy-lead → Claude Sonnet (research)
       ├─ creative-director → Claude Haiku (rapid iteration)
       ├─ systems-automator → Local Hermes (systems)
       ├─ security-auditor → Codex (security-first)
       └─ project-coordinator → Claude Haiku (delivery)
       │
       ▼
       Get Workflow Skills
       │
       ├─ Research → omh-deep-research
       ├─ Planning → omh-ralplan
       ├─ Execution → omh-ralph
       ├─ Triage → omh-triage
       └─ Full Pipeline → omh-autopilot
       │
       ▼
       Route to Provider with Context
       │
       ├─ Agent prompt override
       ├─ Workflow skills list
       ├─ Domain context
       └─ Complexity signals
       │
       ▼
       Provider Response
```

## Integration Points

### 1. Draeven Core (`hud/draeven_core.py`)

#### Initialization
```python
def __init__(self, history_path: Path):
    # ...existing code...
    self.orchestrator = None
    self.agent_config = None
    self._load()
    self._load_orchestrator()  # NEW: Initialize orchestrator
```

#### Task Analysis
```python
def _analyze_task_type(self, text: str) -> tuple[str, str, str]:
    """
    Analyzes request to extract:
    - task_type: research, planning, execution, triage, general
    - domain: engineering, strategy, design, security, project-management, marketing, finance
    - complexity: low, medium, high
    """
```

#### Agent Selection
```python
def _select_agent(self, task_type: str, domain: str, complexity: str) -> dict:
    """
    Returns selected agent persona with:
    - name: Display name
    - provider: Cloud provider (claude-sonnet, codex, haiku, hermes)
    - domain: Agent domain
    - cost_tier: Billing tier (premium, standard, economy, local)
    - prompt_override: Specialized instruction for the agent
    """
```

#### Workflow Skills
```python
def _get_workflow_skills(self, task_type: str) -> list[str]:
    """
    Returns OMH skills appropriate for task type.
    Examples:
    - "research" → ["omh-deep-research"]
    - "full_project" → ["omh-deep-research", "omh-deep-interview", "omh-ralplan", "omh-ralph"]
    """
```

#### Request Routing
In the `respond()` method, requests now include agent context:
```python
request_data = {
    'text': text,
    'agent': agent,
    'context': context,
    'selected_agent': selected_agent,      # NEW: Agent selection result
    'task_type': task_type,                # NEW: Extracted task type
    'domain': domain,                      # NEW: Extracted domain
    'complexity': complexity,              # NEW: Complexity assessment
    'workflow_skills': workflow_skills,    # NEW: Recommended OMH skills
}
```

### 2. Agent Orchestration (`integrations/agents_agency_bridge.py`)

#### AgentsAgencyBridge Class
Loads and indexes agent personalities from Agents Agency repository:
- `_load_divisions()`: Loads divisions.json configuration
- `_load_tools()`: Loads tools.json configuration
- `_index_agents()`: Scans all agent markdown files by domain
- `get_agents_by_domain()`: Retrieves agents in specific domain
- `get_all_domains()`: Lists all available domains

#### DraevenAgentOrchestrator Class
Orchestrates agent selection and routing:
```python
select_agent_for_task(task_type, domain, complexity) → JarvisPersona
get_workflow_skills(workflow_type) → List[str]
export_agent_config(output_path) → Path to JSON config
```

#### Persona Mappings
Maps domain-specific agents to JARVIS provider personas:

| Key | Agent Name | Provider | Domain | Cost Tier | Purpose |
|-----|-----------|----------|--------|-----------|---------|
| engineering-architect | Codex Engineer | codex | engineering | standard | Architecture decisions |
| strategy-lead | Sonnet Strategist | claude-sonnet | strategy | premium | Strategic research |
| creative-director | Haiku Creator | claude-haiku | design | economy | Creative iteration |
| systems-automator | Hermes System | hermes | engineering | local | Systems automation |
| security-auditor | Security Expert | codex | security | standard | Security-first decisions |
| project-coordinator | PM Coordinator | claude-haiku | project-management | economy | Delivery tracking |

#### Skill Mappings
Maps OMH skills to workflow stages:

| Phase | OMH Skill | Trigger | Output Format |
|-------|-----------|---------|---------------|
| Research | omh-deep-research | unfamiliar_domain | `.omh/research/{slug}-report.md` |
| Interview | omh-deep-interview | vague_requirements | `.omh/interview/{slug}-requirements.md` |
| Planning | omh-ralplan | needs_architecture | `.omh/plan/{slug}-consensus.md` |
| Execution | omh-ralph | ready_to_implement | `.omh/execution/{slug}-result.md` |
| Triage | omh-triage | backlog_review | `.omh/triage/{slug}-consensus.md` |
| Autopilot | omh-autopilot | end_to_end_workflow | `.omh/autopilot/{slug}-complete.md` |

### 3. Agent Configuration (`integrations/agent_config.json`)

Generated configuration file containing:
- **personas**: 6 mapped provider personas with routing metadata
- **skill_mappings**: 6 OMH skill definitions with workflow triggers
- **available_domains**: 22 agent domains from Agents Agency
- **agent_count**: 277 total loaded agent personalities

## Workflow Examples

### Example 1: Architecture Question → Engineering Specialist

```
User: "Design an architecture for a microservices system with caching"

┌─ Task Analysis
│  ├─ task_type: "planning"
│  ├─ domain: "engineering"
│  └─ complexity: "high"
│
└─ Agent Selection
   ├─ Selected: "engineering-architect"
   ├─ Provider: Codex
   ├─ Prompt: "Apply engineering domain expertise with focus on architecture decisions"
   ├─ Skills: ["omh-ralplan", "omh-deep-interview"]
   │
   └─ Route: "Draeven model route via Codex Engineer (codex)"
```

### Example 2: Research Task → Strategy Lead

```
User: "Research market trends in AI-powered developer tools"

┌─ Task Analysis
│  ├─ task_type: "research"
│  ├─ domain: "strategy"
│  └─ complexity: "medium"
│
└─ Agent Selection
   ├─ Selected: "strategy-lead"
   ├─ Provider: Claude Sonnet
   ├─ Prompt: "Apply strategic thinking with comprehensive research foundation"
   ├─ Skills: ["omh-deep-research", "omh-ralplan"]
   │
   └─ Route: "Draeven model route via Sonnet Strategist (claude-sonnet)"
```

### Example 3: Creative Design → Creative Director

```
User: "Create a visual brand identity for a tech startup"

┌─ Task Analysis
│  ├─ task_type: "execution"
│  ├─ domain: "design"
│  └─ complexity: "high"
│
└─ Agent Selection
   ├─ Selected: "creative-director"
   ├─ Provider: Claude Haiku
   ├─ Prompt: "Apply creative expertise with rapid iteration"
   ├─ Skills: ["omh-ralph"]
   │
   └─ Route: "Draeven model route via Haiku Creator (claude-haiku)"
```

## Status and Capabilities

The integrated system reports:
```json
{
  "agent_orchestration": {
    "orchestration": "ready",
    "personas_available": 6,
    "domains_available": 22,
    "omh_skills_available": 6,
    "total_agents_loaded": 277
  },
  "tools": [
    {"name": "agent-orchestration", "mode": "agent selection for tasks", "ready": true},
    {"name": "omh-skills", "mode": "workflow orchestration", "ready": true}
  ]
}
```

## Cost Optimization

Provider routing follows cost tiers:
- **premium** (Sonnet): Strategic research and complex analysis
- **standard** (Codex): Engineering and security decisions
- **economy** (Haiku): Creative work and rapid iteration
- **local** (Hermes): Systems automation, privacy-critical operations

Cost ceiling: One provider call per request (verified tools only)

## Extending the System

### Adding New Agent Domains

1. Create domain directory in `/home/claude/msitarzewski/agency-agents/`
2. Add agent markdown files following Agents Agency format
3. Regenerate config: `python integrations/agents_agency_bridge.py`
4. DraevenCore automatically discovers new domains

### Adding New Persona Mappings

Edit `integrations/agents_agency_bridge.py`, in `DraevenAgentOrchestrator.create_jarvis_mapping()`:
```python
"your-specialist": JarvisPersona(
    name="Your Display Name",
    provider="claude-sonnet|codex|claude-haiku|hermes",
    agent_domain="your_domain",
    cost_tier="premium|standard|economy|local",
    prompt_override="Your specialized instruction"
)
```

### Using OMH Skills Directly

The orchestrator maps skills to workflow stages, but skills can also be invoked directly:
```python
orchestrator.get_workflow_skills("full_project")
# Returns: ["omh-deep-research", "omh-deep-interview", "omh-ralplan", "omh-ralph"]
```

## Integration Testing

Verify the integration is working:
```bash
# Check draeven_core imports correctly
cd /home/claude/draeven-jarvis-system
python -m py_compile hud/draeven_core.py

# Verify orchestrator generates config
python integrations/agents_agency_bridge.py

# Check agent config was created
cat integrations/agent_config.json | jq '.agent_orchestration'
```

## Documentation

- **Agents Agency**: `/home/claude/msitarzewski/agency-agents/README.md`
- **Oh My Hermes**: `/home/claude/witt3rd/oh-my-hermes/README.md`
- **Draeven Core**: `/home/claude/draeven-jarvis-system/README.md`
- **Integration**: This file

## Next Steps

1. ✅ Install Agents Agency and Oh My Hermes repositories
2. ✅ Create agents_agency_bridge.py integration layer
3. ✅ Update draeven_core.py with agent orchestration
4. ✅ Generate agent_config.json
5. 📋 Test with actual Draeven workflows
6. 📋 Monitor cost tiers and provider routing
7. 📋 Gather performance metrics for agent selection accuracy
8. 📋 Expand persona mappings based on usage patterns
