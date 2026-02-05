# Story 3.1: Pre-Commit Layer

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Epic 1

---

## Objetivo

Implementar Layer 1 do Quality Gates: pre-commit hooks.

## Tasks

### Task 1: Pre-Commit Hook Runner

**Arquivo:** `src/aios/quality/precommit.py`

Checks:
- ruff check
- mypy --strict
- pytest (fast tests only)
- security quick scan

### Task 2: Gate Configuration

**Arquivo:** `src/aios/quality/config.py`

Configurar thresholds e behavior.

### Task 3: Testes

**Arquivo:** `tests/test_quality/test_precommit.py`

---

## Blocking Rules

```
CRITICAL security finding → BLOCK commit
ruff error → BLOCK commit
mypy error → BLOCK commit
Test failure → BLOCK commit
```

---

## Validação Final

- [ ] Pre-commit hooks funcionando
- [ ] Blocking correto
- [ ] Fast execution (<10s)
- [ ] Testes com 80%+ coverage
