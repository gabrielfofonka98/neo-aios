# Story 4.1: Auto-Fix Framework

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Epic 2

---

## Objetivo

Criar framework base para auto-fix de issues de segurança e qualidade.

## Tasks

### Task 1: Fix Protocol

**Arquivo:** `src/aios/autofix/protocol.py`

Define protocolo para fixers:
- Input: SecurityFinding
- Output: FixResult (success/failure + patched code)

### Task 2: Fix Engine

**Arquivo:** `src/aios/autofix/engine.py`

Engine que:
- Recebe finding
- Encontra fixer apropriado
- Aplica fix
- Valida resultado

### Task 3: Testes

**Arquivo:** `tests/test_autofix/test_engine.py`

---

## Fix Protocol

```python
class Fixer(Protocol):
    def can_fix(self, finding: SecurityFinding) -> bool: ...
    def fix(self, finding: SecurityFinding, content: str) -> FixResult: ...
```

---

## Validação Final

- [ ] Protocol definido
- [ ] Engine funcionando
- [ ] Fixer registry
- [ ] Testes com 85%+ coverage
