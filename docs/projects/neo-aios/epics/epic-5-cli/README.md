# Epic 5: CLI & Integration

**Status:** Ready for Execution
**Prioridade:** P1
**Dependências:** Epic 1, Epic 2, Epic 3

---

## Objetivo

Implementar a CLI do NEO-AIOS e integração com Claude Code.

## Stories

| Story | Nome | Complexidade | Status |
|-------|------|--------------|--------|
| S5.1 | CLI Base | Média | [ ] Pending |
| S5.2 | Agent Commands | Média | [ ] Pending |
| S5.3 | Health & Status | Média | [ ] Pending |
| S5.4 | Claude Code Integration | Alta | [ ] Pending |

## CLI Commands

```bash
# Agent management
aios agent activate <agent-id>
aios agent deactivate
aios agent list
aios agent status

# Health checks
aios health
aios health --check <check-name>

# Security scan
aios scan [path]
aios scan --validator <validator-name>

# Quality gates
aios gate pre-commit
aios gate pr-check

# Session
aios session status
aios session clear
```

## Claude Code Integration

### Skills (em .claude/skills/)
- `/dev` - Ativa Dex
- `/devops` - Ativa Gage
- `/qa` - Ativa Quinn
- etc.

### Hooks (em .claude/hooks/)
- Pre-read validation
- Write path validation
- SQL governance
- Scope enforcement

## Ordem de Execução

```
S5.1 (CLI Base) → S5.2 (Agent Commands) → S5.3 (Health) → S5.4 (Claude Integration)
```

## Definition of Done

- [ ] CLI funcionando
- [ ] Todos os comandos implementados
- [ ] Skills integrados
- [ ] Hooks funcionando
- [ ] Testes com 80%+ coverage
