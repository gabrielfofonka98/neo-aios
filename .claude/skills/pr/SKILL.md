---
description: "Workflow completo: Commit + Push + PR. Entrega de ponta a ponta."
user_invocable: true
---

# /pr - Criar Pull Request

**Agente:** Gage (DevOps)

## Lógica Inteligente

O comando detecta o estado atual e faz só o necessário:

```
1. Já tem PR aberto?      → Mostra link
2. Já fez push?           → Só cria PR
3. Tem commits locais?    → Push + PR
4. Tem mudanças staged?   → Commit + Push + PR
5. Tem mudanças unstaged? → Stage + Commit + Push + PR
```

## Fluxo

### 1. DETECTAR ESTADO
```bash
BRANCH=$(git branch --show-current)

# Verificar se está na main
if [ "$BRANCH" = "main" ]; then
  echo "⚠️ Está na main"
fi

# Verificar se já tem PR
gh pr view --json url 2>/dev/null

# Verificar commits não pushed
git log origin/$BRANCH..HEAD --oneline 2>/dev/null

# Verificar mudanças locais
git status --short
```

### 2. AÇÕES POR ESTADO

**Se está na main:**
```
⚠️ Você está na main. Precisa criar uma branch primeiro.

Nome da branch: ___
```
```bash
git checkout -b nome-da-branch
```

**Se já tem PR:**
```
✅ PR já existe!

PR #123: título do PR
URL: https://github.com/user/repo/pull/123
Status: Open / Draft / Ready for review

Quer atualizar? (adicionar commits ao PR existente)
```

**Se já fez push (sem PR):**
```bash
gh pr create --title "tipo(escopo): descrição" --body "$(cat <<'EOF'
## Summary
- O que foi feito

## Test plan
- [ ] Testes passam
- [ ] Build OK

🤖 Generated with Claude Code
EOF
)"
```

**Se tem commits locais:**
```bash
git push -u origin $BRANCH
# depois cria PR
```

**Se tem mudanças (staged ou não):**
```bash
git add -A
git commit -m "tipo(escopo): descrição

Co-Authored-By: Claude <noreply@anthropic.com>"
git push -u origin $BRANCH
# depois cria PR
```

### 3. OUTPUT FINAL
Sempre mostrar o link do PR no final.

## Regras
- NUNCA criar PR direto da main (criar branch primeiro)
- SEMPRE mostrar o que vai fazer antes de executar
- SEMPRE usar conventional commits
- SEMPRE incluir link do PR no final
- Se já tem PR, perguntar se quer atualizar
