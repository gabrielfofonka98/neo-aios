# Story 5.1: CLI Base

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Epic 1

---

## Objetivo

Criar a CLI base do NEO-AIOS usando Click.

## Tasks

### Task 1: CLI Structure

**Arquivo:** `src/aios/cli/main.py`

CLI principal com grupos:
- `aios agent` - Agent management
- `aios scan` - Security scanning
- `aios health` - Health checks
- `aios gate` - Quality gates

### Task 2: Output Formatting

**Arquivo:** `src/aios/cli/output.py`

Rich output com:
- Colors
- Tables
- Progress bars
- Status indicators

### Task 3: Testes

**Arquivo:** `tests/test_cli/test_main.py`

---

## CLI Structure

```bash
aios
├── agent
│   ├── activate <id>
│   ├── deactivate
│   ├── list
│   └── status
├── scan
│   ├── quick
│   ├── full
│   └── --validator <id>
├── health
│   └── --check <name>
└── gate
    ├── precommit
    └── pr
```

---

## Validação Final

- [ ] CLI funcionando
- [ ] Help text para todos os comandos
- [ ] Output formatado com Rich
- [ ] Testes com 80%+ coverage
