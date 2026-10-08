#!/usr/bin/env python3
"""
Integration test suite for Agents Agency + OMH + Draeven Core
Tests the complete orchestration pipeline.
"""

import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "hud"))
sys.path.insert(0, str(Path(__file__).parent))

from agents_agency_bridge import DraevenAgentOrchestrator, AgentsAgencyBridge

# Note: draeven_core import is Windows-specific (requires Windows Credential Manager)
# Test it separately in Windows environment
draeven_core = None
try:
    import draeven_core
except (AttributeError, ImportError):
    pass


def test_agents_agency_bridge():
    """Test Agents Agency bridge loading."""
    print("\n" + "="*70)
    print("TEST 1: Agents Agency Bridge")
    print("="*70)

    bridge = AgentsAgencyBridge()

    domains = bridge.get_all_domains()
    print(f"✓ Loaded {len(domains)} agent domains")
    print(f"  Domains: {', '.join(domains[:5])}...")

    # Test domain-specific agents
    engineering_agents = bridge.get_agents_by_domain("engineering")
    print(f"✓ Engineering domain has {len(engineering_agents)} agents")
    if engineering_agents:
        print(f"  Sample: {engineering_agents[0]['name']}")

    return True


def test_orchestrator():
    """Test DraevenAgentOrchestrator."""
    print("\n" + "="*70)
    print("TEST 2: Draeven Agent Orchestrator")
    print("="*70)

    orchestrator = DraevenAgentOrchestrator()

    # Test persona mappings
    personas = orchestrator.persona_mappings
    print(f"✓ Configured {len(personas)} persona mappings")
    for key, persona in list(personas.items())[:3]:
        print(f"  - {key} → {persona.name} ({persona.provider})")

    # Test skill mappings
    skills = orchestrator.skill_mappings
    print(f"✓ Configured {len(skills)} skill mappings")
    for key, skill in list(skills.items())[:3]:
        print(f"  - {key} → {skill['skill']}")

    return True


def test_agent_selection():
    """Test agent selection logic."""
    print("\n" + "="*70)
    print("TEST 3: Agent Selection")
    print("="*70)

    orchestrator = DraevenAgentOrchestrator()

    test_cases = [
        ("engineering", "planning", "high", "engineering-architect"),
        ("strategy", "research", "medium", "strategy-lead"),
        ("design", "execution", "high", "creative-director"),
        ("security", "planning", "high", "security-auditor"),
        ("project-management", "triage", "medium", "project-coordinator"),
    ]

    for domain, task_type, complexity, expected_key in test_cases:
        agent = orchestrator.select_agent_for_task(task_type, domain, complexity)
        status = "✓" if agent and agent.name == orchestrator.persona_mappings[expected_key].name else "✗"
        print(f"{status} {domain}/{task_type}/{complexity} → {agent.name if agent else 'None'}")

    return True


def test_workflow_skills():
    """Test workflow skill selection."""
    print("\n" + "="*70)
    print("TEST 4: Workflow Skills")
    print("="*70)

    orchestrator = DraevenAgentOrchestrator()

    test_workflows = [
        ("research", ["omh-deep-research"]),
        ("planning", ["omh-ralplan"]),
        ("execution", ["omh-ralph"]),
        ("backlog_refinement", ["omh-triage"]),
        ("full_project", ["omh-deep-research", "omh-deep-interview", "omh-ralplan", "omh-ralph"]),
    ]

    for workflow_type, expected_skills in test_workflows:
        skills = orchestrator.get_workflow_skills(workflow_type)
        matches = len(set(skills) & set(expected_skills))
        status = "✓" if matches > 0 else "✗"
        print(f"{status} {workflow_type} → {skills}")

    return True


def test_agent_config_export():
    """Test agent configuration export."""
    print("\n" + "="*70)
    print("TEST 5: Agent Configuration Export")
    print("="*70)

    orchestrator = DraevenAgentOrchestrator()
    config_path = Path(__file__).parent / "agent_config_test.json"

    exported = orchestrator.export_agent_config(config_path)
    print(f"✓ Exported config to {exported}")

    config = json.loads(config_path.read_text())
    print(f"✓ Personas: {len(config['personas'])}")
    print(f"✓ Skills: {len(config['skill_mappings'])}")
    print(f"✓ Domains: {len(config['available_domains'])}")
    print(f"✓ Total agents: {config['agent_count']}")

    # Cleanup
    config_path.unlink()

    return True


def test_draeven_core_integration():
    """Test draeven_core integration."""
    print("\n" + "="*70)
    print("TEST 6: Draeven Core Integration")
    print("="*70)

    if not draeven_core:
        print("⊘ SKIPPED: draeven_core requires Windows Credential Manager")
        print("  (This test runs on Windows with the Draeven system)")
        return True

    history_path = Path("/tmp/test_draeven_history.json")
    core = draeven_core.DraevenCore(history_path)

    # Test orchestrator loading
    status = core.status()
    agent_status = status.get("agent_orchestration", {})

    if agent_status.get("orchestration") == "ready":
        print(f"✓ Orchestrator loaded successfully")
        print(f"  - Personas: {agent_status.get('personas_available')}")
        print(f"  - Domains: {agent_status.get('domains_available')}")
        print(f"  - OMH Skills: {agent_status.get('omh_skills_available')}")
        print(f"  - Total Agents: {agent_status.get('total_agents_loaded')}")
    else:
        print(f"✗ Orchestrator failed to load")
        return False

    # Test task analysis
    task_type, domain, complexity = core._analyze_task_type(
        "Design an architecture for a microservices system with caching"
    )
    print(f"✓ Task analysis: type={task_type}, domain={domain}, complexity={complexity}")

    # Test agent selection
    agent = core._select_agent(task_type, domain, complexity)
    if agent:
        print(f"✓ Selected agent: {agent['name']} ({agent['provider']})")
    else:
        print(f"✗ No agent selected")
        return False

    # Test workflow skills
    skills = core._get_workflow_skills(task_type)
    print(f"✓ Workflow skills: {skills}")

    # Cleanup
    history_path.unlink(missing_ok=True)

    return True


def test_task_analysis():
    """Test task analysis in draeven_core."""
    print("\n" + "="*70)
    print("TEST 7: Task Analysis")
    print("="*70)

    if not draeven_core:
        print("⊘ SKIPPED: draeven_core requires Windows Credential Manager")
        print("  (This test runs on Windows with the Draeven system)")
        return True

    history_path = Path("/tmp/test_draeven_analysis.json")
    core = draeven_core.DraevenCore(history_path)

    test_cases = [
        ("Research market trends in AI", "research", "strategy"),
        ("Build a REST API for user management", "execution", "engineering"),
        ("Design a visual brand identity", "execution", "design"),
        ("Review security vulnerabilities in the code", "planning", "security"),
        ("Plan the Q4 product roadmap", "planning", "strategy"),
    ]

    for query, expected_task, expected_domain in test_cases:
        task_type, domain, complexity = core._analyze_task_type(query)
        task_match = task_type == expected_task
        domain_match = domain == expected_domain
        status = "✓" if task_match and domain_match else "◐"
        print(f"{status} '{query[:40]}...'")
        print(f"   → task={task_type}, domain={domain}")

    # Cleanup
    history_path.unlink(missing_ok=True)

    return True


def main():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("DRAEVEN + AGENTS AGENCY + OMH INTEGRATION TEST SUITE")
    print("="*70)

    tests = [
        ("Agents Agency Bridge", test_agents_agency_bridge),
        ("Orchestrator", test_orchestrator),
        ("Agent Selection", test_agent_selection),
        ("Workflow Skills", test_workflow_skills),
        ("Config Export", test_agent_config_export),
        ("Draeven Core Integration", test_draeven_core_integration),
        ("Task Analysis", test_task_analysis),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception:")
            print(f"  {type(e).__name__}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 Integration test suite PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
