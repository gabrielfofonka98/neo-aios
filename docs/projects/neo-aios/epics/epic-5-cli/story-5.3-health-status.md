# Story 5.3: Health & Status Commands

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Story 5.1, Epic 1 (S1.6)

---

## Objetivo

Implementar comandos de health check e status na CLI.

## Tasks

### Task 1: Health Command

**Arquivo:** `src/aios/cli/commands/health.py`

```bash
aios health
# Runs all health checks

aios health --check agent_registry
# Run specific check
```

### Task 2: Session Status

```bash
aios session status
aios session clear
```

### Task 3: Testes

**Arquivo:** `tests/test_cli/test_health_commands.py`

---

## Health Output

```
═══════════════════════════════════════
          AIOS HEALTH STATUS
═══════════════════════════════════════

  ✅ agent_registry      HEALTHY
  ✅ session_persistence HEALTHY
  ⚠️  configuration      DEGRADED
  ✅ agent_identity      HEALTHY

  Overall: DEGRADED
═══════════════════════════════════════
```

---

## Validação Final

- [ ] Health command funcionando
- [ ] Specific check funcionando
- [ ] Session commands
- [ ] Output visual
- [ ] Testes com 80%+ coverage
