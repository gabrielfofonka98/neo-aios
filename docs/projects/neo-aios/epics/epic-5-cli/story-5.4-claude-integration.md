# Story 5.4: Claude Code Integration

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Story 5.1, 5.2, 5.3

---

## Objetivo

Integrar NEO-AIOS com Claude Code via skills e hooks.

## Tasks

### Task 1: Agent Skills

**Diretório:** `.claude/skills/`

Criar skills para ativação de agentes:
- `/dev` → ativa Dex
- `/devops` → ativa Gage
- `/qa` → ativa Quinn
- etc.

### Task 2: Security Hooks

**Diretório:** `.claude/hooks/`

Hooks existentes devem integrar com AIOS:
- Scope enforcement
- SQL governance
- Write path validation

### Task 3: Session Persistence Integration

Garantir que session-state.json é lido/escrito corretamente pelo AIOS.

### Task 4: Testes

**Arquivo:** `tests/test_integration/test_claude.py`

---

## Skills Structure

```
.claude/skills/
├── dev/
│   └── SKILL.md
├── devops/
│   └── SKILL.md
├── qa/
│   └── SKILL.md
└── ...
```

## Hooks Integration

```python
# Hook deve chamar AIOS para verificação
from aios.scope.enforcer import scope_enforcer
result = scope_enforcer.check(current_agent, action)
```

---

## Validação Final

- [ ] Skills funcionando
- [ ] Hooks integrados
- [ ] Session persistence
- [ ] Testes de integração
