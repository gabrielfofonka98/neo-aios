# NEO-AIOS - Environments & CI/CD

**Versao:** 1.0.0
**Data:** 2026-02-04
**Stack:** GitHub + Supabase + Vercel

---

## Visao Geral dos Ambientes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUXO DE AMBIENTES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LOCAL          PREVIEW           STAGING           PRODUCTION             │
│  ─────          ───────           ───────           ──────────             │
│                                                                             │
│  ┌────────┐    ┌────────┐       ┌────────┐        ┌────────┐              │
│  │ Dev    │    │ PR     │       │ Main   │        │ Prod   │              │
│  │ Machine│───▶│ Preview│──────▶│ Branch │───────▶│ Release│              │
│  └────────┘    └────────┘       └────────┘        └────────┘              │
│       │             │                │                  │                  │
│       ▼             ▼                ▼                  ▼                  │
│  ┌────────┐    ┌────────┐       ┌────────┐        ┌────────┐              │
│  │Supabase│    │Supabase│       │Supabase│        │Supabase│              │
│  │ Local  │    │ Preview│       │ Staging│        │  Prod  │              │
│  │(Docker)│    │(Branch)│       │(Project)│       │(Project)│             │
│  └────────┘    └────────┘       └────────┘        └────────┘              │
│                                                                             │
│  Testes:        Testes:          Testes:           Testes:                 │
│  - Unit         - Integration    - E2E             - Smoke                 │
│  - Integration  - Preview URL    - Performance     - Synthetic             │
│                                  - Security        - Canary                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Estrutura de Projeto

```
project/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # Testes em PR
│   │   ├── staging.yml         # Deploy staging
│   │   ├── production.yml      # Deploy prod
│   │   └── scheduled.yml       # Testes agendados
│   ├── CODEOWNERS
│   └── pull_request_template.md
│
├── apps/
│   ├── web/                    # Frontend Next.js
│   │   ├── src/
│   │   ├── public/
│   │   ├── next.config.js
│   │   └── package.json
│   └── api/                    # Se tiver API separada
│
├── packages/
│   ├── ui/                     # Componentes compartilhados
│   ├── utils/                  # Utilities
│   └── config/                 # Configs compartilhadas
│
├── supabase/
│   ├── migrations/             # SQL migrations
│   │   ├── 20240101000000_initial.sql
│   │   └── 20240115000000_add_feature.sql
│   ├── seeds/                  # Dados de seed
│   │   ├── development.sql
│   │   └── staging.sql
│   ├── functions/              # Edge Functions
│   │   └── webhook/
│   │       └── index.ts
│   └── config.toml             # Config local
│
├── tests/
│   ├── unit/                   # Testes unitarios
│   ├── integration/            # Testes de integracao
│   ├── e2e/                    # Testes end-to-end
│   └── fixtures/               # Dados de teste
│
├── scripts/
│   ├── setup-local.sh          # Setup ambiente local
│   ├── reset-db.sh             # Reset banco local
│   └── seed-data.sh            # Popular dados
│
├── docs/
│   ├── architecture/
│   ├── runbooks/
│   └── api/
│
├── .env.example                # Template de env vars
├── .env.local                  # Local (git ignored)
├── turbo.json                  # Turborepo config
├── package.json
└── vercel.json
```

---

## 2. Configuracao por Ambiente

### Environment Variables Template

```bash
# .env.example

# ===========================================
# SUPABASE
# ===========================================
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
DATABASE_URL=postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres

# ===========================================
# VERCEL
# ===========================================
VERCEL_ENV=development|preview|production
VERCEL_URL=xxx.vercel.app

# ===========================================
# APLICACAO
# ===========================================
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_ENABLE_FEATURE=true

# ===========================================
# INTEGRACOES
# ===========================================
API_KEY=xxx
WEBHOOK_SECRET=xxx
SENTRY_DSN=xxx

# ===========================================
# TESTES
# ===========================================
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=xxx
```

### Projetos Supabase

| Ambiente | Projeto | URL | Proposito |
|----------|---------|-----|-----------|
| Local | Docker | http://localhost:54321 | Desenvolvimento |
| Preview | {project}-preview | https://{ref}.supabase.co | PRs |
| Staging | {project}-staging | https://{ref}.supabase.co | QA |
| Production | {project}-prod | https://{ref}.supabase.co | Usuarios reais |

---

## 3. GitHub Actions

### CI - Testes em Pull Request

```yaml
# .github/workflows/ci.yml

name: CI

on:
  pull_request:
    branches: [main, staging]
  push:
    branches: [main, staging]

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm type-check

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm test:unit --coverage

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
      - run: supabase start && supabase db reset
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
      - run: pnpm install --frozen-lockfile
      - run: pnpm test:integration
      - run: supabase stop
        if: always()

  validate-migrations:
    name: Validate Migrations
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
      - run: supabase start
      - run: supabase db reset && supabase db lint
      - run: supabase stop
        if: always()

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
```

### Deploy Staging

```yaml
# .github/workflows/staging.yml

name: Deploy Staging

on:
  push:
    branches: [staging]

jobs:
  migrate:
    name: Migrate Database
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
      - run: supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
      - run: supabase db push

  deploy:
    name: Deploy to Vercel
    needs: migrate
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          alias-domains: staging.app.com

  e2e-tests:
    name: E2E Tests
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec playwright install --with-deps
      - run: pnpm test:e2e
        env:
          BASE_URL: https://staging.app.com
```

### Deploy Production

```yaml
# .github/workflows/production.yml

name: Deploy Production

on:
  push:
    branches: [main]

jobs:
  backup:
    name: Backup Database
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Trigger Backup
        run: |
          curl -X POST \
            -H "Authorization: Bearer ${{ secrets.SUPABASE_ACCESS_TOKEN }}" \
            "https://api.supabase.com/v1/projects/${{ secrets.PROJECT_REF }}/database/backups"

  migrate:
    name: Migrate Database
    needs: backup
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1
      - run: supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
      - run: supabase db push

  deploy-canary:
    name: Deploy Canary (10%)
    needs: migrate
    runs-on: ubuntu-latest
    environment: production-canary
    steps:
      - uses: actions/checkout@v4
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-args: '--prod'
      - name: Wait and Monitor
        run: sleep 300  # 5 minutos

  validate-canary:
    name: Validate Canary
    needs: deploy-canary
    runs-on: ubuntu-latest
    steps:
      - name: Check Error Rate
        run: |
          # Verifica metricas do canary
          # Se error rate > 1%, falha

  deploy-full:
    name: Deploy Full (100%)
    needs: validate-canary
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Promote to 100%
        run: echo "Canary promoted"

  rollback:
    name: Auto Rollback
    needs: deploy-full
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - name: Rollback
        run: echo "Rolling back..."
      - name: Alert Team
        run: echo "Alerting..."
```

---

## 4. Estrutura de Testes

### Testes Unitarios (Vitest)

```typescript
// tests/unit/services/example.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ExampleService } from '@/services/example';

describe('ExampleService', () => {
  let service: ExampleService;

  beforeEach(() => {
    service = new ExampleService();
  });

  it('should do something', async () => {
    const result = await service.doSomething('input');
    expect(result).toBe('expected');
  });

  it('should handle errors', async () => {
    await expect(service.doSomething('')).rejects.toThrow('Invalid input');
  });
});
```

### Testes de Integracao

```typescript
// tests/integration/api/example.test.ts

import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { createClient } from '@supabase/supabase-js';

describe('Example API Integration', () => {
  let supabase: ReturnType<typeof createClient>;

  beforeAll(async () => {
    supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!
    );
  });

  it('should create and retrieve', async () => {
    // Arrange
    const data = { name: 'test' };

    // Act
    const { data: created } = await supabase
      .from('table')
      .insert(data)
      .select()
      .single();

    // Assert
    expect(created.name).toBe('test');
  });
});
```

### Testes E2E (Playwright)

```typescript
// tests/e2e/flows/example.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Example Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('complete flow', async ({ page }) => {
    // Step 1
    await page.getByRole('button', { name: 'Start' }).click();

    // Step 2
    await page.fill('[name="input"]', 'value');

    // Step 3
    await page.getByRole('button', { name: 'Submit' }).click();

    // Assert
    await expect(page.getByText('Success')).toBeVisible();
  });
});
```

---

## 5. Supabase Migrations

### Template de Migration

```sql
-- supabase/migrations/YYYYMMDD_description.sql

-- ============================================
-- UP Migration
-- ============================================

CREATE TABLE table_name (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  column1 TYPE NOT NULL,
  column2 TYPE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_table_column ON table_name(column1);

-- RLS
ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own"
  ON table_name FOR SELECT
  USING (user_id = auth.uid());

-- ============================================
-- DOWN Migration (comentado)
-- ============================================
/*
DROP POLICY IF EXISTS "Users can view own" ON table_name;
DROP TABLE IF EXISTS table_name;
*/
```

---

## 6. Scripts de Automacao

### Setup Local

```bash
#!/bin/bash
# scripts/setup-local.sh

set -e

echo "Setting up local environment..."

# Verifica dependencias
command -v node >/dev/null 2>&1 || { echo "Node.js required"; exit 1; }
command -v pnpm >/dev/null 2>&1 || { echo "pnpm required"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker required"; exit 1; }
command -v supabase >/dev/null 2>&1 || { echo "Supabase CLI required"; exit 1; }

# Instala dependencias
pnpm install

# Copia env
[ ! -f .env.local ] && cp .env.example .env.local

# Inicia Supabase
supabase start
supabase db reset

# Gera tipos
supabase gen types typescript --local > lib/database.types.ts

echo "Setup complete!"
```

---

## 7. Configuracao para Agentes

```yaml
# config/environments.yaml

environments:
  local:
    url: "http://localhost:3000"
    supabase: "http://localhost:54321"
    features:
      debug_mode: true
      mock_external: true
    testing: [unit, integration]

  preview:
    url: "https://{branch}.vercel.app"
    supabase: "{project}-preview"
    features:
      debug_mode: true
    testing: [unit, integration, e2e]

  staging:
    url: "https://staging.app.com"
    supabase: "{project}-staging"
    features:
      debug_mode: false
      feature_flags: true
    testing: [unit, integration, e2e, performance]

  production:
    url: "https://app.com"
    supabase: "{project}-prod"
    features:
      feature_flags: true
      canary: true
    testing: [smoke, synthetic]

deployment_rules:
  to_staging:
    trigger: "push to staging"
    requires: [ci_passing, migrations_valid]
    steps: [migrate, deploy, e2e]

  to_production:
    trigger: "push to main"
    requires: [ci_passing, staging_e2e_passing]
    steps: [backup, migrate, canary, validate, full_deploy, smoke]
    rollback: [revert, alert]

testing_matrix:
  unit: { framework: vitest, coverage: 80 }
  integration: { framework: vitest, requires: supabase }
  e2e: { framework: playwright, browsers: [chromium, firefox, webkit] }
  performance: { framework: k6, thresholds: { p95: 500ms } }
```

---

## Checklists

### Antes de PR

- [ ] Testes unitarios passando
- [ ] Lint sem erros
- [ ] Types sem erros
- [ ] Migration reversivel
- [ ] Sem secrets hardcoded
- [ ] PR description completa

### Antes de Merge Staging

- [ ] CI passou
- [ ] Code review aprovado
- [ ] Migration testada localmente

### Antes de Merge Production

- [ ] Staging E2E passando
- [ ] Staging funcionando 24h+
- [ ] Rollback plan documentado

### Pos-Deploy Production

- [ ] Smoke tests passando
- [ ] Metricas normais
- [ ] Sem alerts novos

---

*NEO-AIOS Environment Configuration*
*"Staging-first, canary-always"*
