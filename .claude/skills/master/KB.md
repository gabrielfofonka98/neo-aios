# AIOS Master — Extended Knowledge Base

Loaded on demand via `*kb` command. Not part of activation context.

---

## Full Command Reference

### Core
| Command | Description |
|---------|-------------|
| `*help` | Show all available commands |
| `*kb` | Toggle KB mode (loads this file) |
| `*status` | Show current context and progress |
| `*guide` | Show comprehensive usage guide |
| `*yolo` | Toggle confirmation skipping |
| `*exit` | Exit agent mode |

### Framework Development
| Command | Description |
|---------|-------------|
| `*create` | Create AIOS component (agent, task, workflow, template, checklist) |
| `*modify` | Modify existing AIOS component |
| `*update-manifest` | Update team manifest |
| `*validate-component` | Validate component security and standards |
| `*deprecate-component` | Deprecate component with migration path |
| `*propose-modification` | Propose framework modifications |
| `*undo-last` | Undo last framework modification |
| `*analyze-framework` | Analyze framework structure and patterns |
| `*list-components` | List all framework components |
| `*test-memory` | Test memory layer connection |

### Task Execution
| Command | Description |
|---------|-------------|
| `*task` | Execute specific task (or list available) |
| `*execute-checklist {name}` | Run checklist (or list available) |
| `*workflow {name}` | Start workflow (or list available) |
| `*plan [create\|status\|update]` | Workflow planning |

### Document Operations
| Command | Description |
|---------|-------------|
| `*create-doc {template}` | Create document from template |
| `*doc-out` | Output complete document |
| `*shard-doc {doc} {dest}` | Break document into parts |
| `*document-project` | Generate project documentation |
| `*create-next-story` | Create next user story |

### Facilitation
| Command | Description |
|---------|-------------|
| `*advanced-elicitation` | Execute advanced elicitation |
| `*chat-mode` | Start conversational assistance |

### Utilities
| Command | Description |
|---------|-------------|
| `*agent {name}` | Get info about specialized agent |
| `*correct-course` | Analyze and correct deviations |
| `*index-docs` | Index documentation for search |

---

## Dependencies

### Tasks
- advanced-elicitation.md, analyze-framework.md, correct-course.md
- create-agent.md, create-deep-research-prompt.md, create-doc.md
- create-next-story.md, create-task.md, create-workflow.md
- deprecate-component.md, document-project.md, execute-checklist.md
- improve-self.md, index-docs.md, kb-mode-interaction.md
- modify-agent.md, modify-task.md, modify-workflow.md
- propose-modification.md, shard-doc.md, undo-last.md, update-manifest.md

### Templates
- agent-template.yaml, architecture-tmpl.yaml, brownfield-architecture-tmpl.yaml
- brownfield-prd-tmpl.yaml, competitor-analysis-tmpl.yaml
- front-end-architecture-tmpl.yaml, front-end-spec-tmpl.yaml
- fullstack-architecture-tmpl.yaml, market-research-tmpl.yaml
- prd-tmpl.yaml, project-brief-tmpl.yaml, story-tmpl.yaml
- task-template.md, workflow-template.yaml

### Workflows
- brownfield-fullstack.md, brownfield-service.md, brownfield-ui.md
- greenfield-fullstack.md, greenfield-service.md, greenfield-ui.md

### Checklists
- architect-checklist.md, change-checklist.md, pm-checklist.md
- po-master-checklist.md, story-dod-checklist.md, story-draft-checklist.md

### Data
- aios-kb.md, brainstorming-techniques.md
- elicitation-methods.md, technical-preferences.md

---

## Security Rules

- Check user permissions before component creation
- Require confirmation for manifest modifications
- Sanitize all user inputs, validate YAML before saving
- Check for path traversal attempts

---

## Agent Collaboration

**Delegated responsibilities:**
- Epic/Story creation -> @pm
- Brainstorming -> @oracle
- Test suite creation -> @qa
- AI prompt generation -> @architect

**Specialist agents:**
- @doc (Sage) -- Technical documentation
- @ux (Pixel) -- UX/UI design, wireframes
- @spec (Rune) -- Ultra-detailed specs for Ralph Loop
- @sre (Ops) -- Monitoring, incident response

---

## Usage Guide

### When to Use Me
- Creating/modifying AIOS framework components
- Orchestrating multi-agent workflows
- Executing any task from any agent directly
- Framework development and meta-operations

### Typical Workflow
1. `*create` or `*modify` for framework components
2. `*task {name}` to run any task directly
3. `*workflow {name}` for multi-step processes
4. `*plan` before complex operations
5. `*validate-component` for security/standards

### Common Pitfalls
- Using for routine tasks (use specialized agents instead)
- Not enabling KB mode when modifying framework
- Skipping component validation
- Modifying components without propose-modify workflow
