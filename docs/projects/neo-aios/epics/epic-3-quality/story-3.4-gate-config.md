# Story 3.4: Gate Configuration

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Story 3.1, 3.2, 3.3

---

## Objetivo

Criar sistema de configuração flexível para Quality Gates.

## Tasks

### Task 1: Configuration Model

**Arquivo:** `src/aios/quality/gate_config.py`

YAML-based configuration para:
- Thresholds por severity
- Paths com regras especiais
- Bypass rules (emergência)

### Task 2: Configuration Loader

**Arquivo:** `config/quality-gates.yaml`

Default configuration file.

### Task 3: Testes

**Arquivo:** `tests/test_quality/test_config.py`

---

## Configuration Example

```yaml
quality_gates:
  precommit:
    block_on: [critical]
    skip_paths: [tests/fixtures/*]
  pr:
    block_on: [critical, high]
    require_approval: true
```

---

## Validação Final

- [ ] Configuration model
- [ ] YAML loader
- [ ] Flexible overrides
- [ ] Testes com 80%+ coverage
