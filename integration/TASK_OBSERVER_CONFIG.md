# Task Observer Integration into JARVIS

## Architecture
Task Observer is a meta-skill that monitors JARVIS operations, identifies patterns, and generates skill improvements and optimization suggestions using Augmented Expertise methodology.

## Integration Points

### 1. Installation
```bash
# Option A: Claude app (web/desktop/mobile)
# 1. Download .skill bundle from latest release
# 2. Settings → Customize → Upload

# Option B: Claude Code
# 1. Clone/download module
# 2. Copy to ~/.claude/skills/task-observer/
# 3. Preserve references/ and scripts/ subfolders
```

### 2. Activation in JARVIS
Add to `.claude/CLAUDE.md`:
```markdown
@task-observer

## Monitor and Optimize
Automatically observe JARVIS operations and identify:
- Repeating patterns ripe for skill extraction
- Corrections that indicate skill gaps
- Performance bottlenecks
- Token usage optimization opportunities
```

### 3. What It Observes
Task Observer logs:

**A) Corrections & Adjustments**
- When you redirect JARVIS responses
- When manual fixes are applied
- When workarounds are used
- **Action**: Suggests skill updates or new skills

**B) Gaps in Coverage**
- Repetitive manual tasks not covered by skills
- Cross-cutting concerns across multiple sessions
- Edge cases not handled
- **Action**: Flags skill candidates

**C) Performance Issues**
- Slow response times
- Token usage spikes
- Provider fallback patterns
- **Action**: Suggests optimization strategies

**D) Cross-Cutting Principles**
- Patterns that apply across multiple skills
- Configuration conflicts
- Architectural decisions
- **Action**: Creates shared configuration rules

### 4. Observation Log Format
Task Observer produces structured logs:
```json
{
  "session_id": "uuid",
  "timestamp": "2026-10-05T20:26:00Z",
  "observations": [
    {
      "type": "correction",
      "skill_affected": "omniroute-routing",
      "description": "User redirected provider selection to fallback",
      "severity": "medium",
      "suggested_action": "Add fallback detection to routing skill"
    },
    {
      "type": "pattern",
      "frequency": 3,
      "description": "Claude Mem not retrieving session context in cold starts",
      "skill_affected": "claude-mem-integration",
      "suggested_action": "Improve warm-start detection logic"
    }
  ],
  "cross_cutting": [
    "Quota-aware routing should be checked by all model-selection skills",
    "Session memory should always be loaded before provider initialization"
  ]
}
```

### 5. Review Cycle
Task Observer suggests changes but requires approval:

**Interactive Review**
```bash
# Review observations
jarvis skills review task-observer

# Approve/reject each suggestion
# Accepted changes staged in temporary copies
# Install approved bundle when ready
```

**Scheduled Review**
```
# Daily review at 2 AM
# Automatically stages low-risk improvements
# Requires manual approval for anything touching core logic
# Email digest of findings sent to you
```

### 6. Integration with JARVIS Workflows
Task Observer monitors:
- **Agent assignments**: Which agents are invoked for which tasks
- **Model selection**: How OmniRoute chooses providers
- **Memory access patterns**: When Claude Mem context is used
- **Skill execution**: When skills succeed/fail
- **Token usage**: Efficiency of each operation
- **Error recovery**: How fallbacks are triggered

### 7. Skill Generation
When patterns emerge, Task Observer suggests skills:
```markdown
## Candidate Skill: Quota-Aware Provider Routing

**Frequency**: 4 corrections in last 7 sessions
**Impact**: Prevents unnecessary provider exhaustion
**Complexity**: Medium

**Suggested Conditions**:
- Route requests through OmniRoute quota endpoint first
- Check remaining tokens per provider
- Sort providers by available quota
- Force fallback when primary exhausted

**Would Save**: ~5-10K tokens/week
```

### 8. Performance Metrics
Task Observer tracks:
```
- Skills created from observations: [count]
- Average skill quality improvement: [%]
- Patterns identified: [per week]
- Token savings from optimizations: [cumulative]
- Error rate reduction: [%]
```

### 9. Configuration
Create `~/.task-observer/config.json`:
```json
{
  "enabled": true,
  "monitoring_scope": ["jarvis"],
  "log_level": "info",
  "observation_triggers": {
    "corrections": true,
    "patterns": true,
    "gaps": true,
    "performance": true
  },
  "review_mode": "scheduled",
  "review_schedule": "0 2 * * *",
  "skill_auto_create": false,
  "cross_cutting_rules": true,
  "retention_days": 90
}
```

### 10. Database
Observations stored in:
```
~/.task-observer/observations.db
~/.task-observer/skills-registry.json
~/.task-observer/cross-cutting-rules.md
```

## Benefits for JARVIS

1. **Skill Discovery**: Automated identification of repeating patterns
2. **Continuous Improvement**: Skills evolve based on actual usage
3. **Performance Optimization**: Identifies bottlenecks automatically
4. **Knowledge Capture**: Documents best practices from your sessions
5. **Self-Improvement**: Task Observer improves its own methodology over time

## Integration with Other Components

**With Claude Mem**:
- Observations include memory access patterns
- Suggests memory improvements based on retrieval efficiency

**With OmniRoute**:
- Monitors provider selection patterns
- Suggests routing rule optimizations
- Tracks which providers work best for which tasks

**With Head Room**:
- Correlates quota usage with skill performance
- Suggests optimizations when quota pressures detected
- Tracks which skills burn tokens fastest

## Implementation Timeline

1. **Week 1**: Install Task Observer, observe JARVIS baseline
2. **Week 2**: Review initial observations, create first skills
3. **Week 3+**: Continuous improvement cycle, accumulated benefits
