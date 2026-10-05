"""
Agents Agency Bridge for JARVIS/Draeven

Integrates msitarzewski/agency-agents specialized AI personas with JARVIS provider routing.
Maps domain-specific agents to provider personas and orchestration workflows.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Load Agents Agency divisions
AGENCY_ROOT = Path("/home/claude/msitarzewski/agency-agents")
DIVISIONS_CONFIG = AGENCY_ROOT / "divisions.json"
TOOLS_CONFIG = AGENCY_ROOT / "tools.json"


@dataclass
class AgentPersonality:
    """Agent personality descriptor from Agents Agency"""
    name: str
    domain: str
    role: str
    expertise: List[str]
    personality: Dict[str, Any]
    deliverables: List[str]
    communication_style: str
    agent_file: Path


@dataclass
class JarvisPersona:
    """JARVIS provider persona mapping"""
    name: str
    provider: str  # claude-sonnet, codex, hermes, haiku
    agent_domain: str  # domain from agents_agency
    prompt_override: Optional[str] = None
    tools: List[str] = None
    cost_tier: str = "standard"


class AgentsAgencyBridge:
    """Bridge between Agents Agency and JARVIS provider routing"""

    def __init__(self):
        self.agency_root = AGENCY_ROOT
        self.agents = {}
        self.divisions = {}
        self.tools = {}
        self._load_divisions()
        self._load_tools()
        self._index_agents()

    def _load_divisions(self):
        """Load divisions.json configuration"""
        if DIVISIONS_CONFIG.exists():
            with open(DIVISIONS_CONFIG) as f:
                self.divisions = json.load(f)

    def _load_tools(self):
        """Load tools.json configuration"""
        if TOOLS_CONFIG.exists():
            with open(TOOLS_CONFIG) as f:
                self.tools = json.load(f)

    def _index_agents(self):
        """Index all agent markdown files by domain"""
        for domain_path in self.agency_root.iterdir():
            if domain_path.is_dir() and not domain_path.name.startswith(('.', '_')):
                domain = domain_path.name
                self.agents[domain] = []

                for agent_file in domain_path.glob("*.md"):
                    self.agents[domain].append({
                        'file': agent_file,
                        'name': agent_file.stem,
                        'domain': domain
                    })

    def get_agents_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all agents in a specific domain"""
        return self.agents.get(domain, [])

    def get_all_domains(self) -> List[str]:
        """Get all available agent domains"""
        return sorted(self.agents.keys())

    def create_jarvis_mapping(self) -> Dict[str, JarvisPersona]:
        """
        Create recommended JARVIS persona mappings for key agent domains.
        Maps specialized agents to provider personas.
        """
        mappings = {
            # Engineering domain -> Codex (operations and delivery)
            "engineering-architect": JarvisPersona(
                name="Codex Engineer",
                provider="codex",
                agent_domain="engineering",
                cost_tier="standard",
                prompt_override="Apply engineering domain expertise with focus on architecture decisions"
            ),

            # Strategy domain -> Claude Sonnet (strategy and research)
            "strategy-lead": JarvisPersona(
                name="Sonnet Strategist",
                provider="claude-sonnet",
                agent_domain="strategy",
                cost_tier="premium",
                prompt_override="Apply strategic thinking with comprehensive research foundation"
            ),

            # Creative domain -> Claude Haiku (creative work)
            "creative-director": JarvisPersona(
                name="Haiku Creator",
                provider="claude-haiku",
                agent_domain="design",
                cost_tier="economy",
                prompt_override="Apply creative expertise with rapid iteration"
            ),

            # Systems automation -> Local Hermes
            "systems-automator": JarvisPersona(
                name="Hermes System",
                provider="hermes",
                agent_domain="engineering",
                cost_tier="local",
                prompt_override="Apply systems thinking with local execution capabilities"
            ),

            # Security -> Specialized security agent
            "security-auditor": JarvisPersona(
                name="Security Expert",
                provider="codex",
                agent_domain="security",
                cost_tier="standard",
                prompt_override="Apply security-first mindset to all architectural decisions"
            ),

            # Project management coordination
            "project-coordinator": JarvisPersona(
                name="PM Coordinator",
                provider="claude-haiku",
                agent_domain="project-management",
                cost_tier="economy",
                prompt_override="Coordinate across teams with focus on delivery timelines"
            ),
        }
        return mappings

    def get_agent_prompt(self, agent_file: Path) -> str:
        """Extract and parse agent personality from markdown file"""
        if agent_file.exists():
            return agent_file.read_text()
        return ""

    def create_hermes_skill_mapping(self) -> Dict[str, Dict[str, Any]]:
        """
        Map Oh My Hermes skills to JARVIS workflow stages.
        Defines how OMH skills integrate with JARVIS orchestration.
        """
        return {
            "research_phase": {
                "skill": "omh-deep-research",
                "trigger": "unfamiliar_domain",
                "output": ".omh/research/{slug}-report.md",
                "description": "Multi-phase web research: decompose → parallel search → synthesize → verify"
            },
            "planning_phase": {
                "skill": "omh-ralplan",
                "trigger": "needs_architecture",
                "output": ".omh/plan/{slug}-consensus.md",
                "description": "Consensus planning: Planner → Architect → Critic until agreement"
            },
            "interview_phase": {
                "skill": "omh-deep-interview",
                "trigger": "vague_requirements",
                "output": ".omh/interview/{slug}-requirements.md",
                "description": "Socratic requirements interview with coverage tracking"
            },
            "execution_phase": {
                "skill": "omh-ralph",
                "trigger": "ready_to_implement",
                "output": ".omh/execution/{slug}-result.md",
                "description": "Verified execution: implement → verify → iterate until done"
            },
            "triage_phase": {
                "skill": "omh-triage",
                "trigger": "backlog_review",
                "output": ".omh/triage/{slug}-consensus.md",
                "description": "Multi-role consensus triage of issue backlog"
            },
            "autopilot": {
                "skill": "omh-autopilot",
                "trigger": "end_to_end_workflow",
                "output": ".omh/autopilot/{slug}-complete.md",
                "description": "Full pipeline: research → interview → planning → execution"
            }
        }


class DraevenAgentOrchestrator:
    """Orchestrates agent selection and routing within Draeven"""

    def __init__(self):
        self.bridge = AgentsAgencyBridge()
        self.persona_mappings = self.bridge.create_jarvis_mapping()
        self.skill_mappings = self.bridge.create_hermes_skill_mapping()

    def select_agent_for_task(
        self,
        task_type: str,
        domain: str,
        complexity: str = "medium"
    ) -> Optional[JarvisPersona]:
        """
        Select appropriate agent persona for a task using intelligent matching.

        Args:
            task_type: Type of task (research, planning, execution, triage, general)
            domain: Specific domain (engineering, design, security, strategy, etc.)
            complexity: Task complexity (low, medium, high)

        Returns:
            Selected JarvisPersona or None if no match found
        """
        # Intelligent selection based on domain + task type + complexity

        # Domain-to-persona mappings
        domain_mappings = {
            "engineering": "engineering-architect",
            "design": "creative-director",
            "strategy": "strategy-lead",
            "security": "security-auditor",
            "project-management": "project-coordinator",
        }

        # For systems/automation, prefer Hermes
        if domain in ["engineering"] and any(kw in task_type.lower() for kw in ["system", "automat", "infra"]):
            return self.persona_mappings.get("systems-automator")

        # Default to domain-specific mapping
        persona_key = domain_mappings.get(domain)
        if persona_key:
            return self.persona_mappings.get(persona_key)

        # Fallback: match based on task type across any domain
        task_to_persona = {
            "research": "strategy-lead",      # Research → Strategy
            "planning": "engineering-architect",  # Planning → Engineering
            "execution": "creative-director",  # Execution → Creative (rapid iteration)
            "triage": "project-coordinator",   # Triage → PM
        }

        fallback_key = task_to_persona.get(task_type, "strategy-lead")
        return self.persona_mappings.get(fallback_key)

    def get_workflow_skills(self, workflow_type: str) -> List[str]:
        """Get OMH skills needed for a workflow"""
        skills = []

        if workflow_type == "full_project":
            skills = ["omh-deep-research", "omh-deep-interview", "omh-ralplan", "omh-ralph"]
        elif workflow_type == "research":
            skills = ["omh-deep-research"]
        elif workflow_type == "planning":
            skills = ["omh-ralplan"]
        elif workflow_type == "execution":
            skills = ["omh-ralph"]
        elif workflow_type == "backlog_refinement":
            skills = ["omh-triage"]

        return skills

    def export_agent_config(self, output_path: Path):
        """Export agent configuration for Draeven integration"""
        config = {
            "personas": {k: asdict(v) for k, v in self.persona_mappings.items()},
            "skill_mappings": self.skill_mappings,
            "available_domains": self.bridge.get_all_domains(),
            "agent_count": sum(len(agents) for agents in self.bridge.agents.values())
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2, default=str)

        return output_path


if __name__ == "__main__":
    # Initialize and test integration
    orchestrator = DraevenAgentOrchestrator()

    print("=== Agents Agency Bridge Status ===")
    print(f"Available domains: {orchestrator.bridge.get_all_domains()}")
    print(f"Total agents loaded: {sum(len(agents) for agents in orchestrator.bridge.agents.values())}")
    print(f"\nPersona mappings configured: {len(orchestrator.persona_mappings)}")
    print(f"OMH skills available: {len(orchestrator.skill_mappings)}")

    # Export configuration
    config_path = Path("/home/claude/draeven-jarvis-system/integrations/agent_config.json")
    exported = orchestrator.export_agent_config(config_path)
    print(f"\n✓ Agent configuration exported to: {exported}")
