# Story 3.2: PR Automation Layer

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Story 3.1, Epic 2

---

## Objetivo

Implementar Layer 2 do Quality Gates: PR automation.

## Tasks

### Task 1: PR Checker

**Arquivo:** `src/aios/quality/pr_checker.py`

Checks:
- Full security audit (all 18 validators)
- CodeRabbit integration
- QA agent (Codex) review trigger

### Task 2: GitHub Actions Integration

**Arquivo:** `.github/workflows/pr-check.yml`

CI/CD pipeline configuration.

### Task 3: Testes

**Arquivo:** `tests/test_quality/test_pr_checker.py`

---

## Blocking Rules

```
CRITICAL or HIGH security → BLOCK merge
Codex review required → BLOCK until approved
```

---

## Validação Final

- [ ] PR checker funcionando
- [ ] GitHub Actions integration
- [ ] Blocking correto
- [ ] Testes com 80%+ coverage
