# Story 2.4: Validator Orchestration

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Story 2.2, Story 2.3

---

## Objetivo

Criar o sistema de orquestração que permite Quinn coordenar os 18 sub-agents de segurança.

## Tasks

### Task 1: Security Orchestrator

**Arquivo:** `src/aios/security/orchestrator.py`

- Coordenar execução de validators
- Suportar execução paralela
- Quick scan vs full audit
- Agregar resultados

### Task 2: Scan Manager

**Arquivo:** `src/aios/security/scan_manager.py`

- Gerenciar histórico de scans
- Lógica de blocking (commit/merge)
- Summaries para reports

### Task 3: Testes

**Arquivo:** `tests/test_security/test_orchestrator.py`

---

## Scan Types

### Quick Scan (pre-commit)
- sec-secret-scanner
- sec-xss-hunter
- sec-injection-detector
- Fast (<5s)

### Full Audit (PR)
- All 18 validators
- Thorough
- Parallel execution

## Blocking Logic

```
CRITICAL findings → Block commit
CRITICAL or HIGH → Block merge
MEDIUM/LOW → Warning only
```

---

## Validação Final

- [ ] Orchestrator coordena validators
- [ ] Parallel execution funcionando
- [ ] Quick scan vs full audit
- [ ] Blocking logic correto
- [ ] Testes com 90%+ coverage

## Notas para Ralph

- Parallel execution melhora performance
- Quinn usa orchestrator para coordenar
- Cada validator é sub-agent único - não pode simular outro
