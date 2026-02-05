---
description: "Push para remote com menu de seleção de branch."
user_invocable: true
---

# /push - Push para Remote

**Agente:** Gage (DevOps)

## Fluxo

### 1. STATUS ATUAL
```bash
git branch --show-current
git status
git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || echo "Branch nova"
```

Mostrar:
- Branch atual
- Commits pendentes de push

### 2. MENU DE DESTINO

Usar AskUserQuestion:

```
Destino do push:

1. Branch atual (feature/xyz) - Recomendado
2. Criar nova branch
3. Main (requer confirmação extra)
```

### 3. AÇÕES POR ESCOLHA

**Opção 1 - Branch atual:**
```bash
git push -u origin $(git branch --show-current)
```

**Opção 2 - Nova branch:**
Perguntar nome da branch:
```bash
git checkout -b nome-da-branch
git push -u origin nome-da-branch
```

**Opção 3 - Main:**
```
⚠️ ATENÇÃO: Push direto para main!

Confirma? Isso vai:
- Enviar commits direto para produção
- Sem PR review

Digite "CONFIRMO" para continuar:
```

Se confirmar:
```bash
git push origin main
```

### 4. VERIFICAR
```bash
git log origin/$(git branch --show-current) -1 --oneline
```

## Regras
- NUNCA usar --force (usar --force-with-lease se necessário)
- SEMPRE confirmar antes de push para main
- SEMPRE mostrar o que vai ser enviado
- SEMPRE usar -u para tracking
