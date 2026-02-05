---
description: "Limpa o agente ativo e volta pro Claude padrão"
user_invocable: true
---

# /clear-agent - Desativar Agente

Desativa qualquer agente NEO-AIOS ativo e volta ao comportamento padrão do Claude.

## O que fazer

1. Escrever no arquivo de sessão:
```json
// Write to .aios/session-state.json:
{
  "activeAgent": null,
  "agentFile": null,
  "activatedAt": null,
  "lastActivity": null,
  "currentTask": null,
  "projectContext": { "project": null, "epic": null, "story": null }
}
```

2. Informar: "Agente desativado. Agora sou o Claude padrão. O que precisa?"
