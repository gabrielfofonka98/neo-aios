---
description: "Sincroniza ~/.claude para iCloud. Envia histórico e configs para o outro Mac."
user_invocable: true
---

# /sync-icloud - Sync Claude para iCloud

Sincroniza a pasta `~/.claude` para o iCloud. Útil para ter histórico e configs disponíveis em outro Mac.

## O que fazer

1. Rode o comando rsync:
```bash
rsync -av --delete ~/.claude/ ~/Library/Mobile\ Documents/com~apple~CloudDocs/claude-sync/
```

2. Informe o resultado ao usuário:
   - Quantos arquivos foram sincronizados
   - Se deu tudo certo

## Contexto

- Destino: `~/Library/Mobile Documents/com~apple~CloudDocs/claude-sync/`
- O outro Mac lê essa pasta via iCloud (somente leitura)
- Sync é unidirecional: daqui → iCloud
