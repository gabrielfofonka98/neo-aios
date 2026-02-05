# Check PRD - Análise de Compatibilidade

**Comando:** `*check-prd {prd_file} [--focus=compatibility]`
**Agente:** @architect
**Versão:** 1.0.0
**Criado:** 2026-01-16

---

## Objetivo

Validar automaticamente a compatibilidade de um PRD com o sistema existente, gerando relatório estruturado com score, riscos e recomendações.

---

## Filosofia

> **"Gastar tokens e tempo AGORA para evitar debug e refatoração DEPOIS."**

Este comando SEMPRE executa análise profunda e completa. Não existe modo "quick" ou "shallow".

**Racional:**
- O trabalho da IA é devolver tempo ao humano
- 30 min de análise agora = 10h de debug evitado depois
- Relatório completo reduz carga cognitiva do decisor
- Atalhos criam débito técnico invisível

**Não otimize para:**
- ❌ Menos tokens
- ❌ Menos tempo de execução
- ❌ Relatório mais curto

**Otimize para:**
- ✅ Decisão informada
- ✅ Riscos identificados
- ✅ Ações claras e priorizadas

**Ferramenta, não oráculo:**
Este comando DETECTA conflitos. O HUMANO DECIDE se são bloqueantes.
Score alto com conflitos críticos ainda requer decisão humana.

---

## Parâmetros

| Parâmetro | Tipo | Obrigatório | Default | Descrição |
|-----------|------|-------------|---------|-----------|
| `prd_file` | string | ✅ | - | Caminho ou nome do PRD (busca em `docs/prd/`) |
| `--focus` | enum | ❌ | compatibility | `compatibility` \| `completeness` \| `feasibility` |
| `--output` | string | ❌ | auto | Caminho do relatório de saída |

---

## Execução

### Passo 1: Localizar PRD

```yaml
steps:
  - name: Resolve PRD path
    action: |
      1. Se prd_file é caminho absoluto → usar direto
      2. Se prd_file é nome → buscar em docs/prd/
      3. Se não encontrar → fuzzy match (ex: "crm" → PRD_CRM_*.md)
      4. Se múltiplos matches → listar opções para usuário
```

### Passo 2: Coletar Contexto do Sistema

```yaml
required_files:
  - supabase/docs/SCHEMA.md           # Schema atual do banco
  - app/package.json                   # Tech stack frontend
  - docs/architecture/**/*.md          # Arquitetura existente
  - .claude/CLAUDE.md                  # Regras e padrões do projeto

optional_files:
  - docs/architecture/tech-stack.md    # Stack documentado
  - supabase/migrations/*.sql          # Migrations existentes
```

### Passo 3: Análise de Compatibilidade

```yaml
checklist:
  tech_stack:
    - name: Database Match
      check: PRD usa mesmo SGBD (Supabase/PostgreSQL)?
      weight: 20

    - name: Frontend Framework
      check: PRD especifica framework diferente do atual?
      weight: 15

    - name: Auth System
      check: PRD usa Supabase Auth ou sistema próprio?
      weight: 15

  schema_conflicts:
    - name: Table Name Collision
      critical: true  # 80/20: Este check gera maioria das decisões
      check: |
        Extrair nomes de tabelas do PRD
        Comparar com tabelas em SCHEMA.md
        Listar colisões potenciais
      weight: 25

    - name: Naming Convention
      check: |
        Verificar se PRD segue snake_case
        Verificar padrão de slugs
        Verificar timestamps (created_at, updated_at)
      weight: 10

  patterns:
    - name: UUID Primary Keys
      check: PRD usa UUID v4 como PKs?
      weight: 5

    - name: Soft Delete
      check: PRD usa deleted_at para soft delete?
      weight: 5

    - name: RLS Ready
      check: PRD menciona Row Level Security?
      weight: 5

  integration:
    - name: RBAC Compatibility
      critical: true  # 80/20: Overlap de RBAC causa conflitos arquiteturais
      check: |
        Sistema atual tem RBAC?
        PRD propõe RBAC próprio ou usa existente?
      weight: 10

    - name: Shared Tables
      critical: true  # 80/20: Integração com auth.users é decisão arquitetural chave
      check: |
        Identificar tabelas que precisam relacionar
        com módulos existentes (auth.users, etc.)
      weight: 10
```

### Passo 4: Calcular Score

```yaml
scoring:
  formula: |
    score = Σ (item_passed × item_weight) / Σ (all_weights) × 100

  thresholds:
    high: score >= 80      # Alta compatibilidade
    medium: score >= 60    # Compatível com ajustes
    low: score < 60        # Requer mudanças significativas

  # MARGIN OF SAFETY: Score alto não significa "pronto para implementar"
  critical_override: |
    Se QUALQUER check com critical=true falhar:
    - Exibir WARNING mesmo com score alto
    - Listar decisões arquiteturais pendentes
    - Não permitir "passar" sem resolução explícita
```

### Passo 5: Gerar Relatório

```yaml
output:
  path: docs/reports/{date}_{prd_slug}-compatibility-report.md

  sections:
    - Executive Summary
    - Compatibility Score (com breakdown)
    - Tech Stack Analysis
    - Schema Conflict Detection
    - Pattern Compliance
    - Integration Points
    - Risks & Mitigations
    - Recommendations (Must-Do, Should-Do, Nice-to-Have)
    - Next Steps
```

---

## Exemplo de Uso

```bash
# Análise completa de compatibilidade
*check-prd PRD_CRM_Academia_Lendaria_V2.md

# Análise focada em completude
*check-prd docs/prd/new-feature.md --focus=completeness

# Com output customizado
*check-prd crm --output=docs/reports/crm-v2-check.md
```

---

## Output Esperado

```markdown
# Relatório de Compatibilidade: {PRD_NAME}

## Score: 85% ✅ ALTA COMPATIBILIDADE

### Breakdown
| Categoria | Score | Peso |
|-----------|-------|------|
| Tech Stack | 95% | 20% |
| Schema | 80% | 25% |
| Patterns | 100% | 15% |
| Integration | 75% | 20% |
| RBAC | 70% | 10% |

### Conflitos Detectados
- ⚠️ Tabela `users` conflita com `auth.users`
- ⚠️ Tabela `roles` conflita com RBAC existente

### Recomendações
1. Usar prefixo `{module}_` para todas as tabelas
2. Estender RBAC existente ao invés de criar novo
...
```

---

## Integração com Agente

Adicionar ao arquivo do agente @architect:

```yaml
commands:
  - check-prd {prd_file}: Analisa compatibilidade de PRD com sistema atual

dependencies:
  tasks:
    - check-prd.md
```

---

## Referências

- Checklist base: `.aios-core/product/checklists/architect-checklist.md`
- Padrões do projeto: `.claude/CLAUDE.md`
- Schema atual: `supabase/docs/SCHEMA.md`

---

## Manutenção e Evolução

**Owner:** @architect

**Revisão obrigatória:**
- Quando SCHEMA.md for atualizado significativamente
- Quando novo módulo for adicionado ao sistema
- A cada 6 meses (revisar weights e checks)

**Sinais de que precisa atualização:**
- Check que sempre passa (provavelmente obsoleto)
- Check que sempre falha (peso muito alto ou irrelevante)
- Conflitos descobertos em produção que check não detectou

**Histórico de análises:**
- Manter relatórios em `docs/reports/` para referência futura
- Padrões recorrentes indicam checks que precisam de ajuste

---

## Metadata

```yaml
task: check-prd
version: 1.1.0
created_at: 2026-01-16
updated_at: 2026-01-16
created_by: @architect (Aria)
tags:
  - compatibility
  - prd
  - architecture
  - validation
changelog:
  - v1.1.0: Aplicadas lições do Multi-Lens Analysis (80/20, Margin of Safety, Regret Minimization)
  - v1.0.0: Versão inicial
```
