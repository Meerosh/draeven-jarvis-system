# Agents & Skills Quick Reference

## Ask Draeven Anything

The integrated system automatically selects the right specialist and workflow for your request.

### Example Requests

**Engineering & Architecture**
```
"Design a microservices architecture for handling 1M daily users"
→ Routes to: Codex Engineer (planning + ralplan skill)

"Debug this concurrency issue in the thread pool"
→ Routes to: Codex Engineer (execution + ralph skill)

"Set up automated deployment pipeline"
→ Routes to: Hermes System (local execution, systems automation)
```

**Strategy & Research**
```
"Research the current landscape of AI developer tools"
→ Routes to: Sonnet Strategist (research + deep-research skill)

"What should our Q4 product roadmap focus on?"
→ Routes to: Sonnet Strategist (planning + ralplan skill)

"Analyze market trends in cloud infrastructure"
→ Routes to: Sonnet Strategist (research + deep-research skill)
```

**Design & Creative**
```
"Create a visual brand identity for a tech startup"
→ Routes to: Haiku Creator (execution + ralph skill)

"Design a user-friendly dashboard for analytics"
→ Routes to: Haiku Creator (execution + ralph skill)

"Generate marketing copy for our new product launch"
→ Routes to: Haiku Creator (execution + ralph skill)
```

**Security**
```
"Audit our authentication system for vulnerabilities"
→ Routes to: Security Expert (planning + ralplan skill)

"What are the security implications of using X approach?"
→ Routes to: Security Expert (planning skill)
```

**Project Management**
```
"Triage our GitHub issues and prioritize by impact"
→ Routes to: PM Coordinator (triage + triage skill)

"What's our delivery status for the current sprint?"
→ Routes to: PM Coordinator (execution skill)
```

## Agent Personas at a Glance

| Name | Specialty | Cost | Best For |
|------|-----------|------|----------|
| **Codex Engineer** | Operations & Architecture | $$ | Complex engineering decisions, system design, implementation |
| **Sonnet Strategist** | Research & Analysis | $$$ | Strategic planning, market research, complex analysis |
| **Haiku Creator** | Creative & Rapid Iteration | $ | UI/UX design, marketing, quick creative work |
| **Hermes System** | Automation & Local Execution | $ | Systems automation, privacy-critical operations |
| **Security Expert** | Security & Threat Modeling | $$ | Security audits, vulnerability analysis, threat modeling |
| **PM Coordinator** | Delivery & Team Coordination | $ | Project tracking, team coordination, issue prioritization |

## Workflow Skills Cheat Sheet

### Single-Phase Workflows

**Need Research?**
- Keyword: `research`, `investigate`, `explore`, `understand`, `background`
- Skill: `omh-deep-research`
- Output: Comprehensive report with verified citations

**Need Planning?**
- Keyword: `plan`, `design`, `architecture`, `strategy`, `decide`
- Skill: `omh-ralplan`
- Output: Consensus plan with architect review

**Need Execution?**
- Keyword: `build`, `implement`, `create`, `execute`, `write`
- Skill: `omh-ralph`
- Output: Implemented solution with verification

**Need Triage?**
- Keyword: `triage`, `sort`, `prioritize`, `organize`, `backlog`
- Skill: `omh-triage`
- Output: Prioritized issue list with consensus

### Multi-Phase Workflows

**Full Project Pipeline** (unfamiliar domain)
```
Research → Interview → Planning → Execution
```
- Skill: `omh-autopilot`
- Use when: Starting in an unfamiliar domain with vague requirements
- Time: 2-4 hours depending on complexity

**Research + Planning** (familiar domain, no implementation yet)
```
Research → Planning
```
- Skills: `omh-deep-research`, `omh-ralplan`
- Use when: Gathering background, then planning architecture

**Interview + Planning** (vague requirements, familiar domain)
```
Interview → Planning
```
- Skills: `omh-deep-interview`, `omh-ralplan`
- Use when: Requirements are unclear, need to clarify scope

**Planning + Execution** (clear requirements, need to build)
```
Planning → Execution
```
- Skills: `omh-ralplan`, `omh-ralph`
- Use when: Requirements are clear, ready to implement

## How Draeven Routes Your Request

1. **Analyze**: Draeven examines your request to identify:
   - What you're trying to do (task_type: research, planning, execution, triage)
   - What domain it's in (engineering, strategy, design, security, etc.)
   - How complex it is (low, medium, high)

2. **Select**: Draeven picks the best specialist:
   - Matches domain to agent (engineering → Codex, design → Haiku, etc.)
   - Selects persona based on task type
   - Considers complexity and cost tiers

3. **Plan**: Draeven determines the workflow:
   - Which OMH skills will be needed
   - What phases to execute in order
   - Output format and success criteria

4. **Execute**: Draeven routes to the provider:
   - Sends your request with specialist prompt
   - Includes workflow skills list
   - Provides domain context and complexity signals

5. **Report**: Draeven returns results:
   - Shows which specialist handled it
   - Reports cost tier used
   - Includes any generated artifacts

## Cost Tips

**Save Money** 💰
- Use Haiku Creator for rapid iteration (economy tier)
- Use Hermes System for automation (local, no cloud cost)
- Combine requests to minimize provider calls

**Get Premium Results** 💎
- Use Sonnet Strategist for complex analysis (worth the cost)
- Use Codex Engineer for critical architecture (standard tier)
- Security Expert included for security-critical work

**Daily Ceiling**: One cloud model call per request (verified tools don't count)

## Asking for Best Results

### ✅ Good Requests
```
"Design a caching strategy for a high-traffic API"
→ Clear domain (engineering), task (planning), complexity (high)
→ Draeven knows: Use Codex + ralplan skill

"Research open-source alternatives to Datadog"
→ Clear domain (strategy), task (research)
→ Draeven knows: Use Sonnet + deep-research skill

"Create a logo concept for our new product"
→ Clear domain (design), task (execution)
→ Draeven knows: Use Haiku + ralph skill
```

### ⚠️ Vague Requests
```
"Help me with this project"
→ Too vague, might not route to specialist
→ Better: "Design the database schema for our e-commerce platform"

"What should we do?"
→ Too general
→ Better: "Plan our security audit strategy for Q4"
```

## When to Use Each Specialist

### Codex Engineer
**Use When:**
- Designing system architecture
- Making operational decisions
- Implementing complex features
- Troubleshooting technical issues

**Avoid:**
- Quick creative brainstorms (use Haiku)
- Strategic planning (use Sonnet)
- Security-specific work (use Security Expert)

### Sonnet Strategist
**Use When:**
- Researching markets or technologies
- Making strategic decisions
- Analyzing complex problems
- Planning roadmaps

**Avoid:**
- Quick creative work (use Haiku)
- Operational implementation (use Codex)
- Automated tasks (use Hermes)

### Haiku Creator
**Use When:**
- Rapid iteration needed
- Creative/design work
- UI/UX decisions
- Marketing content

**Avoid:**
- Deep research (use Sonnet)
- Critical architecture (use Codex)
- Security decisions (use Security Expert)

### Hermes System
**Use When:**
- Automating workflows
- Privacy-critical operations
- Systems administration
- Local-only execution needed

**Avoid:**
- Cloud-dependent analysis (use appropriate provider)
- Creative work (use Haiku)
- Strategic research (use Sonnet)

### Security Expert
**Use When:**
- Auditing security
- Threat modeling
- Vulnerability analysis
- Security architecture decisions

**Avoid:**
- General engineering (use Codex)
- Operations (use Codex)
- Non-security strategic planning (use Sonnet)

### PM Coordinator
**Use When:**
- Triaging issue backlogs
- Tracking project progress
- Prioritizing work
- Coordinating teams

**Avoid:**
- Deep technical implementation (use Codex)
- Research (use Sonnet)
- Creative work (use Haiku)

## Advanced: Available Agent Domains

Draeven has access to 277 specialized agents across 22 domains:

- **Academic** (9 agents): Research methodology, thesis advising, curriculum design
- **Design** (12 agents): UX, branding, visual design, interaction design
- **Engineering** (65 agents): Backend, frontend, DevOps, systems, architecture
- **Finance** (8 agents): Budgeting, analysis, forecasting, accounting
- **Game Development** (6 agents): Game design, mechanics, asset creation
- **GIS** (3 agents): Geospatial analysis, mapping, location services
- **Healthcare** (5 agents): Medical practice, patient care, health tech
- **Marketing** (8 agents): Content, campaigns, analytics, growth
- **Paid Media** (4 agents): Advertising, campaign management
- **Product** (12 agents): Product management, strategy, roadmap
- **Project Management** (11 agents): Planning, coordination, delivery
- **Research** (8 agents): Data analysis, methodology, insights
- **Sales** (8 agents): Pipeline, negotiation, forecasting
- **Security** (14 agents): Auditing, threat modeling, compliance
- **Strategy** (9 agents): Business strategy, planning, analysis
- **Support** (7 agents): Customer service, documentation, issue resolution
- **Testing** (6 agents): QA, test automation, quality assurance
- **Spatial Computing** (3 agents): AR/VR, 3D, immersive tech
- **And more...**

The 6 main persona mappings above represent the most commonly used specialists across these domains.

---

**Pro Tip:** You don't need to worry about which agent to use. Just describe what you need, and Draeven's orchestrator automatically selects the perfect specialist! 🎯
