---
description: "Sincroniza com remote. Backup → Pull → Resolve conflitos → Verifica → Limpa backup."
user_invocable: true
---

# /sync - Sincronização Segura com Remote

**Agente:** Gage (DevOps)

## Fluxo Obrigatório

### 1. BACKUP (antes de qualquer coisa)
```bash
git stash push -m "backup-sync-$(date +%Y%m%d-%H%M%S)" --include-untracked
```

### 2. FETCH + STATUS
```bash
git fetch origin
git status
git log --oneline HEAD..origin/main | head -10
```

Mostrar ao usuário:
- Quantos commits atrás está
- Se há conflitos potenciais

### 3. PULL (com rebase)
```bash
git pull --rebase origin main
```

Se houver conflitos:
- Listar arquivos em conflito
- Mostrar cada conflito
- Ajudar a resolver UM POR UM
- `git add` após cada resolução
- `git rebase --continue`

### 4. VERIFICAÇÃO
Perguntar ao usuário:
```
Sync completo. Verificações:
- [ ] Código compila? (build)
- [ ] Testes passam?
- [ ] Tudo funcionando?

Confirma que está OK? (sim/não)
```

### 5. LIMPEZA
Se usuário confirmar OK:
```bash
git stash drop
```

Se NÃO estiver OK:
```bash
git rebase --abort
git stash pop
```

## Regras
- NUNCA pular o backup
- NUNCA forçar resolução de conflito
- SEMPRE pedir verificação antes de limpar backup
- Se der qualquer erro, restaurar backup automaticamente
