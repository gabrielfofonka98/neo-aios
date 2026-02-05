---
description: "Deploy para Vercel/produção com confirmação de ambiente."
user_invocable: true
---

# /deploy - Deploy

**Agente:** Gage (DevOps)

## Fluxo

### 1. DETECTAR AMBIENTE
Verificar:
- `vercel.json` → Vercel
- `netlify.toml` → Netlify
- `fly.toml` → Fly.io
- `Dockerfile` → Docker
- `railway.json` → Railway

### 2. MENU DE AMBIENTE

```
Ambiente de deploy:

1. Preview/Staging (Recomendado)
2. Produção (requer confirmação)
```

### 3. PRE-CHECKS
```bash
# Build local primeiro (detecta framework)
npm run build  # ou uv run pytest, etc.
```

Se build falhar:
- Mostrar erro
- Perguntar se quer corrigir antes

### 4. DEPLOY

**Vercel Preview:**
```bash
vercel
```

**Vercel Produção:**
```
⚠️ DEPLOY PARA PRODUÇÃO

Isso vai:
- Atualizar o site em produção
- Usuários reais serão afetados

Checklist:
- [ ] Testes passaram?
- [ ] Build local OK?
- [ ] PR foi aprovado?

Confirma? (sim/não)
```

Se confirmar:
```bash
vercel --prod
```

### 5. VERIFICAR
- Mostrar URL do deploy
- Verificar se está online (curl)

## Regras
- NUNCA deploy prod sem confirmação
- SEMPRE rodar build local antes
- SEMPRE mostrar URL final
- SEMPRE informar como fazer rollback
