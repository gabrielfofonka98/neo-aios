---
tools:
  - file-system
utils:
  - template-engine
---

# Discovery Session - Research Synthesis Mode

## Purpose

Interactive mode for consolidating external research (Perplexity, ChatGPT, docs, competitors) into actionable insights, gaps, and questions for product development.

## Execution Modes

### Subcommands

| Command | Description |
|---------|-------------|
| `*discovery start {project}` | Start new session, create document |
| `*discovery add` | Add research/information to active session |
| `*discovery status` | Show current state (insights, gaps, questions) |
| `*discovery synthesize` | Generate synthesis, patterns, new questions |
| `*discovery close` | Close session, consolidate, suggest next steps |

---

## Task Definition

```yaml
task: discoverySession()
responsável: John (PM)
responsavel_type: Agente
atomic_layer: Workflow

**Entrada:**
- campo: project_name
  tipo: string
  origem: User Input
  obrigatório: true (for start)
  validação: kebab-case, non-empty

- campo: research_content
  tipo: string
  origem: User Input (paste)
  obrigatório: true (for add)
  validação: Non-empty text

- campo: source_label
  tipo: string
  origem: User Input
  obrigatório: false
  validação: Optional label for source (e.g., "Perplexity", "Tally Docs")

**Saída:**
- campo: discovery_document
  tipo: file
  destino: docs/prd/{project}-discovery.md
  persistido: true

- campo: session_state
  tipo: object
  destino: Memory (in-conversation)
  persistido: false
```

---

## Workflow: `*discovery start {project}`

### Step 1: Initialize Session

```yaml
action: create_document
template: discovery-tmpl.md
destination: docs/prd/{project}-discovery.md
```

**Agent Actions:**
1. Create document from template
2. Initialize in-memory session state:
   ```yaml
   session:
     project: {project}
     document: docs/prd/{project}-discovery.md
     started_at: {timestamp}
     research_count: 0
     insights: []
     gaps: []
     questions: []
     decisions: []
   ```
3. Confirm to user: "🔬 Discovery session started for **{project}**"
4. Show quick guide:
   ```
   📥 Paste research anytime, I'll consolidate
   📊 *discovery status - see current state
   🧠 *discovery synthesize - generate insights
   ✅ *discovery close - finish and prepare for PRD
   ```

---

## Workflow: `*discovery add`

### Step 1: Receive Research

**Prompt user:**
```
📥 Paste your research below.

Optional: Start with a source label like:
`[Perplexity]` or `[Tally Docs]` or `[Competitor: Typeform]`

Then paste the content.
```

### Step 2: Process & Categorize

**Agent Actions:**
1. Parse content for:
   - **Features** → Add to Feature Matrix
   - **Insights** → Add to Insights section
   - **Questions raised** → Add to Open Questions
   - **Competitor info** → Add to Competitor Analysis

2. Update document with new information

3. Generate immediate observations:
   ```
   ✅ Added to Feature Matrix: {count} items
   💡 New insight identified: "{insight_summary}"
   ❓ Question raised: "{question}"
   ```

4. Increment `research_count`

### Step 3: Confirm & Continue

```
📊 Research #{n} processed and consolidated.

Paste more research, or:
- *discovery status - see full state
- *discovery synthesize - analyze patterns
```

---

## Workflow: `*discovery status`

### Display Current State

```markdown
# 🔬 Discovery Session: {project}

**Started:** {timestamp}
**Research items:** {count}
**Document:** docs/prd/{project}-discovery.md

## 📊 Feature Matrix
| Feature | Source 1 | Source 2 | Our Decision | Status |
|---------|----------|----------|--------------|--------|
| {feature} | {info} | {info} | {decision} | ⏳/✅/❓ |

## 💡 Insights Collected ({count})
1. {insight_1}
2. {insight_2}

## 🕳️ Gaps Identified ({count})
1. {gap_1}
2. {gap_2}

## ❓ Open Questions ({count})
1. {question_1}
2. {question_2}

## ✅ Decisions Made ({count})
1. {decision_1}

---
**Next:** Paste more research, *discovery synthesize, or *discovery close
```

---

## Workflow: `*discovery synthesize`

### Step 1: Pattern Analysis

**Agent Actions:**
1. Analyze all collected research for:
   - Common patterns across sources
   - Contradictions between sources
   - Missing information (gaps)
   - Emerging themes

2. Generate synthesis report:

```markdown
# 🧠 Synthesis Report

## Patterns Identified
1. **{pattern_name}**: {description}
   - Evidence: {sources}

## Contradictions Found
1. **{topic}**: Source A says X, Source B says Y
   - Recommendation: {recommendation}

## Critical Gaps
1. **{gap}**: We don't have information about...
   - Suggested research: {suggestion}

## Emerging Themes
1. **{theme}**: {description}

## New Questions Generated
1. {question_1}
2. {question_2}
```

### Step 2: Decision Prompts

**Present decisions needed:**
```
Based on this synthesis, here are decisions for you:

1. **{decision_topic_1}**
   - Option A: {option}
   - Option B: {option}
   - Your choice: ___

2. **{decision_topic_2}**
   ...

Type your decisions or ask me to elaborate on any topic.
```

### Step 3: Update Document

After user provides decisions, update:
- Decisions Made section
- Feature Matrix (Our Decision column)
- Close relevant Open Questions

---

## Workflow: `*discovery close`

### Step 1: Final Consolidation

**Agent Actions:**
1. Review all sections for completeness
2. Generate executive summary
3. Identify remaining gaps/blockers

### Step 2: Readiness Assessment

```markdown
# 📋 Discovery Session Complete

## Summary
- **Research items processed:** {count}
- **Features mapped:** {count}
- **Decisions made:** {count}
- **Open questions remaining:** {count}

## Readiness for PRD
{assessment}

## Remaining Gaps (if any)
1. {gap}

## Recommended Next Steps
1. {next_step_1}
2. {next_step_2}
```

### Step 3: Transition Options

```
Discovery session closed. Document saved to:
📄 docs/prd/{project}-discovery.md

**Next steps:**
1. *create-prd - Start PRD using this discovery as input
2. *discovery start {project} - Reopen for more research
3. Review document manually first
```

---

## Document Structure (discovery-tmpl.md)

The discovery document maintains these sections:

1. **Header** - Project name, session info
2. **Feature Matrix** - Comparative table of features across sources
3. **Insights Collected** - Key learnings from research
4. **Gaps Identified** - Missing information
5. **Open Questions** - Questions needing answers
6. **Decisions Made** - Choices with rationale
7. **Research Log** - Chronological log of added research
8. **Synthesis Notes** - Pattern analysis results

---

## Integration with PRD Creation

When user runs `*create-prd` after discovery:

1. Load discovery document
2. Pre-populate PRD sections with:
   - Feature decisions → Requirements
   - Insights → Context/Background
   - Gaps → Risks/Assumptions
   - Decisions → Scope decisions

---

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| No active session | User runs add/status without start | Prompt to start session first |
| Document not found | File was deleted | Offer to recreate from memory state |
| Parse failure | Research content unclear | Ask user to clarify or categorize manually |

---

## Metadata

```yaml
version: 1.0.0
created_at: 2026-01-13
author: Orion (AIOS Master)
tags:
  - discovery
  - research
  - synthesis
  - pm
```
