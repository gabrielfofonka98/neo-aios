---
name: staging
description: "Setup de staging completo. Ativa o DevOps (Gage) para configurar Vercel, GitHub e Supabase com staging-first strategy. Pede credenciais interativamente e salva no .env e credentials.yaml."
---

# Staging Setup

Configura toda a infraestrutura de staging do projeto.

## Pré-requisitos

Este skill ativa o agente **Gage (DevOps)** para executar o setup. Apenas o DevOps pode configurar infraestrutura.

## Instruções

Quando este skill for invocado:

### 1. Ativar Gage (DevOps)
- Persista em `.aios/session-state.json`:
  ```json
  {
    "activeAgent": "devops",
    "agentFile": ".claude/skills/devops/SKILL.md",
    "activatedAt": "<now>",
    "lastActivity": "<now>",
    "currentTask": "staging-setup"
  }
  ```

### 2. Verificar Credenciais Existentes
Leia AMBOS os arquivos:
- `.env` (se existir)
- `config/credentials.yaml` (se existir)

Identifique o que já está preenchido vs o que falta.

### 3. Coletar Credenciais Faltantes

Peça ao usuário APENAS as credenciais que faltam, na seguinte ordem:

#### GitHub
```
1. GitHub Username
2. GitHub Personal Access Token (scopes: repo, workflow, admin:repo_hook)
   → Gerar em: https://github.com/settings/tokens
```

#### Vercel
```
3. Vercel Token
   → Gerar em: https://vercel.com/account/tokens
4. Vercel Team ID (opcional)
5. Vercel Project ID (se já existir)
```

#### Supabase - Staging
```
6. Supabase Staging Project Ref
7. Supabase Staging URL
8. Supabase Staging Anon Key
9. Supabase Staging Service Role Key
10. Supabase Staging DB Password
```

#### Supabase - Production (opcional)
```
11-15. Mesmos campos para production (perguntar se quer configurar agora)
```

### 4. Salvar Credenciais
- Salvar em `.env` (formato KEY=VALUE)
- Salvar em `config/credentials.yaml` (formato YAML estruturado)
- Confirmar que ambos os arquivos estão no `.gitignore`

### 5. Configurar GitHub
```bash
# Verificar autenticação
gh auth status

# Configurar branch protection
gh api repos/{owner}/{repo}/branches/main/protection -X PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint","typecheck","test"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}'

# Configurar branch staging
git checkout -b staging || git checkout staging
git push -u origin staging

# Proteger branch staging
gh api repos/{owner}/{repo}/branches/staging/protection -X PUT \
  --field required_status_checks='{"strict":true,"contexts":["lint","typecheck","test"]}'
```

### 6. Configurar Vercel
```bash
# Verificar CLI
vercel --version || npm i -g vercel

# Login
vercel login

# Link ao projeto (ou criar)
vercel link

# Configurar ambientes
vercel env add SUPABASE_URL staging
vercel env add SUPABASE_ANON_KEY staging
vercel env add SUPABASE_SERVICE_ROLE_KEY staging
```

### 7. Criar GitHub Actions Workflows

Criar `.github/workflows/ci.yml`:
```yaml
name: CI
on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main, staging]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --extra dev
      - run: uv run ruff check src/ tests/
      - run: uv run ruff format --check src/ tests/

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --extra dev
      - run: uv run mypy --strict src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --extra dev
      - run: uv run pytest --cov=aios --cov-report=xml
```

Criar `.github/workflows/deploy-staging.yml`:
```yaml
name: Deploy Staging
on:
  push:
    branches: [staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

### 8. Atualizar Configs do Projeto

Atualizar `.aios-custom/config/deployment-strategy.yaml` com refs reais.
Atualizar `.aios-custom/config/core-config.yaml` com URLs de staging.

### 9. Verificar Setup
```bash
# Verificar GitHub
gh auth status
gh repo view

# Verificar branches
git branch -a

# Verificar Vercel
vercel ls

# Verificar Supabase
supabase status
```

### 10. Relatório Final

Apresentar checklist:
```
[x] GitHub autenticado
[x] Branch protection configurada (main, staging)
[x] Vercel conectado ao projeto
[x] Variáveis de ambiente no Vercel
[x] Supabase staging configurado
[x] GitHub Actions CI workflow
[x] GitHub Actions deploy-staging workflow
[x] Credenciais salvas em .env e credentials.yaml
[x] Git branch strategy: feature → staging → main
```

## Regras

- Linguagem: Português BR
- NUNCA commitar credenciais
- Confirmar com o usuário antes de cada etapa destrutiva
- Se algum serviço não estiver disponível, pular e documentar
- Salvar credenciais em AMBOS `.env` e `credentials.yaml`
