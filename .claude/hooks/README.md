# NEO-AIOS Hooks

Sistema de hooks para automação e governança do sistema de agentes.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    HOOK LIFECYCLE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SessionStart ─────────────────────────────────────────────────┐│
│       │ (startup/resume/compact)                               ││
│       │                                                        ││
│       ▼                                                        ││
│  ┌─────────────────────────────────────────────────────────┐   ││
│  │ LOOP:                                                    │   ││
│  │   UserPromptSubmit → PreToolUse → Tool → PostToolUse    │   ││
│  │         │                │                               │   ││
│  │         │                └── scope-enforcer.sh           │   ││
│  │         └── pre-prompt-context.sh                        │   ││
│  └─────────────────────────────────────────────────────────┘   ││
│       │                                                        ││
│       ▼                                                        ││
│     Stop ──────────────────────────────────────────────────────┘│
│       │ post-response-update.sh                                 │
│       ▼                                                         │
│  SessionEnd                                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Hooks Implementados

### 1. restore-agent-state.sh
**Event:** `SessionStart` (matcher: `compact`)
**Comportamento:** INJETA contexto

Restaura o agente ativo após compactação do contexto. Garante que Claude continue como o agente correto.

**Output injetado:**
```
═══════════════════════════════════════════════════════════════
🔄 CONTEXT RESTORED AFTER COMPACTION
═══════════════════════════════════════════════════════════════

Active Agent: @dev
Current Task: implementing-feature-x

INSTRUCTION: Continue as @dev persona.
- Do NOT greet or re-introduce yourself
- Do NOT ask 'how can I help' - continue the previous work
═══════════════════════════════════════════════════════════════
```

### 2. pre-prompt-context.sh
**Event:** `UserPromptSubmit`
**Comportamento:** INJETA contexto (minimal)

Injeta contexto mínimo antes de cada prompt do usuário. Útil para lembrar o Claude de tarefas em andamento.

**Output injetado (se houver task ativa):**
```
[Context: @dev | Task: implementing-feature-x]
```

### 3. post-response-update.sh
**Event:** `Stop`
**Comportamento:** ATUALIZA estado (silencioso)

Atualiza o `lastActivity` no session-state.json após cada resposta. Roda silenciosamente.

### 4. scope-enforcer.sh
**Event:** `PreToolUse` (matcher: `Bash`)
**Comportamento:** BLOQUEIA (exit 2)

Enforce de regras de escopo dos agentes:

| Regra | Bloqueado se |
|-------|--------------|
| `git push` | Agente ≠ devops |
| `gh pr create` | Agente ≠ devops |
| DDL (CREATE/ALTER/DROP) | Agente ≠ data-engineer |

**Exemplo de bloqueio:**
```
🚫 SCOPE VIOLATION: git push

Only @devops (Gage) can push to remote repositories.
Current agent: @dev

To push changes, activate DevOps:
  /devops
  *push
```

### 5. agent-delegation-tracker.sh
**Event:** `SubagentStart`
**Comportamento:** LOG (silencioso)

Registra todas as delegações de agentes em `.aios/delegation-log.jsonl`:
```json
{"timestamp":"2026-02-05T15:00:00Z","parent":"master","subagent":"Explore","description":"Find security validators"}
```

## Configuração

Os hooks são configurados em `.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "compact", "hooks": [{ "type": "command", "command": "bash restore-agent-state.sh" }] }
    ],
    "UserPromptSubmit": [
      { "matcher": "", "hooks": [{ "type": "command", "command": "bash pre-prompt-context.sh" }] }
    ],
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "bash scope-enforcer.sh" }] }
    ],
    "Stop": [
      { "matcher": "", "hooks": [{ "type": "command", "command": "bash post-response-update.sh" }] }
    ],
    "SubagentStart": [
      { "matcher": "", "hooks": [{ "type": "command", "command": "bash agent-delegation-tracker.sh" }] }
    ]
  }
}
```

## Exit Codes

| Code | Significado |
|------|-------------|
| 0 | Permitido (operação continua) |
| 2 | Bloqueado (operação cancelada, stderr mostrado) |
| Outro | Erro não-bloqueante |

## Debugging

Testar hooks manualmente:

```bash
# Testar restore-agent-state
echo '{"source": "compact"}' | bash .claude/hooks/restore-agent-state.sh

# Testar scope-enforcer
echo '{"tool_name": "Bash", "tool_input": {"command": "git push origin main"}}' | bash .claude/hooks/scope-enforcer.sh
echo $?  # Deve retornar 2 se agente não for devops
```

## Variáveis de Ambiente

| Variável | Descrição |
|----------|-----------|
| `CLAUDE_PROJECT_DIR` | Diretório raiz do projeto |
| `CLAUDE_SESSION_ID` | ID da sessão atual |

---

*NEO-AIOS Hooks v1.0*
*Created: 2026-02-05*
