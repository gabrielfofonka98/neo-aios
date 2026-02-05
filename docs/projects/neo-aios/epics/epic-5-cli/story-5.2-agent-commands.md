# Story 5.2: Agent Commands

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Story 5.1

---

## Objetivo

Implementar comandos de agent management na CLI.

## Tasks

### Task 1: Agent Activate

**Arquivo:** `src/aios/cli/commands/agent.py`

```bash
aios agent activate dev
aios agent activate architect
```

### Task 2: Agent Status

```bash
aios agent status
# Output: Currently active: Dex (dev)
```

### Task 3: Agent List

```bash
aios agent list
# Output: Available agents table
```

### Task 4: Testes

**Arquivo:** `tests/test_cli/test_agent_commands.py`

---

## Commands

| Command | Description |
|---------|-------------|
| `activate <id>` | Ativar agente |
| `deactivate` | Desativar agente ativo |
| `list` | Listar agentes disponíveis |
| `status` | Mostrar agente ativo |

---

## Validação Final

- [ ] Activate funcionando
- [ ] Deactivate funcionando
- [ ] List mostrando todos os agentes
- [ ] Status mostrando agente ativo
- [ ] Testes com 80%+ coverage
