---
description: "Commit local com conventional commits. Não faz push."
user_invocable: true
---

# /commit - Commit Local

**Agente:** Gage (DevOps)

## Fluxo

### 1. STATUS
```bash
git status
git diff --stat
```

Mostrar ao usuário o que será commitado.

### 2. STAGED FILES
Se não houver arquivos staged:
```
Nenhum arquivo staged. Opções:
1. Stage all (git add -A)
2. Stage específicos (listar arquivos para escolher)
3. Cancelar
```

### 3. COMMIT MESSAGE
Gerar mensagem seguindo Conventional Commits:

```
Tipos:
- feat: nova funcionalidade
- fix: correção de bug
- docs: documentação
- style: formatação
- refactor: refatoração
- test: testes
- chore: manutenção

Formato: tipo(escopo): descrição curta

Exemplos:
- feat(auth): add login with Google
- fix(api): handle null response
- docs(readme): update installation steps
```

Mostrar sugestão e perguntar se quer editar.

### 4. EXECUTAR COMMIT
```bash
git commit -m "$(cat <<'EOF'
tipo(escopo): descrição

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 5. CONFIRMAR
```bash
git log -1 --oneline
```

## Regras
- NUNCA fazer push (isso é /push)
- SEMPRE usar conventional commits
- SEMPRE mostrar o que vai ser commitado antes
- SEMPRE incluir Co-Authored-By
