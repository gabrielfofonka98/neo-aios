# github-devops-git-diagnose.md

**Task**: Diagnostico de Praticas de Engenharia

**Purpose**: Analisar praticas de desenvolvimento, identificar padroes e anti-padroes, e oferecer feedback construtivo e acionavel para evolucao do desenvolvedor.

**When to use**: Via `@devops *diagnose` para autoavaliacao, melhoria continua, ou preparacao para code review.

**Template Reference**: `.aios-core/development/templates/git-diagnose-prompt-v1.md`

---

## Objetivo

Produzir diagnostico completo de praticas de engenharia analisando:

1. **Qualidade dos commits** — mensagens, atomicidade, coesao
2. **Estrategia de branches** — uso adequado, oportunidades perdidas
3. **Padrao de trabalho** — distribuicao temporal, picos, consistencia
4. **Divida tecnica** — tratada, identificada, introduzida
5. **Versionamento de dados** — migrations, seeds, reproducibilidade
6. **Conformidade com padroes** — conventional commits, CI/CD, testes

---

## Principios

1. **Construtivo, nunca punitivo** — objetivo e melhoria
2. **Baseado em evidencias** — toda afirmacao tem dado de suporte
3. **Acionavel** — cada problema tem recomendacao
4. **Contextualizado** — considera momento do projeto
5. **Priorizado** — distingue urgente de importante
6. **Educativo** — explica o "por que" de cada pratica
7. **Sem emojis**

---

## Task Definition

```yaml
task: githubDevopsGitDiagnose()
responsável: Gage (Operator)
version: 1.0.0

**Entrada:**
- campo: period
  tipo: string
  validação: N days|week|month
  default: "7 days"

- campo: output
  tipo: string
  validação: terminal|file
  default: "terminal"
```

---

## Estrutura do Diagnostico

### SUMARIO EXECUTIVO

1. **Contexto** — Repo, branch, periodo, commits, momento do projeto
2. **Painel de Saude** — Score 1-10 para 6 dimensoes
3. **Top 3 Pontos Fortes** — Com evidencias
4. **Top 3 Oportunidades** — Com acoes recomendadas

### ANALISE DETALHADA (6 Dimensoes)

#### 1. Qualidade das Mensagens
- Metricas (descritivas, prefixos, referencias, genericas)
- Distribuicao por tipo (feat/fix/refactor/docs/chore)
- Exemplos de boas mensagens
- Mensagens que precisam melhorar (com sugestao)

#### 2. Atomicidade dos Commits
- Metricas de tamanho (arquivos/linhas por commit)
- Distribuicao (micro/pequeno/medio/grande/muito grande)
- Commits que deveriam ser divididos
- Analise de coesao (areas misturadas)

#### 3. Estrategia de Branches
- Commits direto na main vs feature branches
- Branches abandonadas
- Oportunidades perdidas de usar branch

#### 4. Consistencia Temporal
- Distribuicao por dia
- Analise de picos
- Commits fora de horario

#### 5. Versionamento de Dados
- Migrations versionadas
- Seeds reproduziveis
- Rollback documentado

#### 6. Gestao de Divida Tecnica
- Tratada (com ROI)
- Identificada (backlog)
- Introduzida (consciente)

### EXTRAS

- **Hotspots de Codigo** — Arquivos mais alterados
- **Conformidade com Padroes** — Gap vs industria
- **Recomendacoes Priorizadas** — Alta/Media/Baixa com "como implementar"
- **Sintese do Diagnostico** — 3-4 paragrafos de fechamento

---

## Coleta de Dados

```bash
# Commits com estatisticas
git log --since="{N} days ago" --date=short --pretty=format:"%H|%ad|%an|%s" --shortstat

# Apenas mensagens
git log --since="{N} days ago" --pretty=format:"%s"

# Arquivos por commit
git log --since="{N} days ago" --pretty=format:"%H" --numstat

# Branches
git branch -a --list
git log --since="{N} days ago" --merges --pretty=format:"%s"

# Hotspots
git log --since="{N} days ago" --pretty=format: --name-only | sort | uniq -c | sort -rn | head -20

# Migrations
find . -path "*/migrations/*" -name "*.sql" 2>/dev/null

# Seeds
find . -name "*seed*" -type f 2>/dev/null
```

---

## Benchmarks de Referencia

### Mensagens de Commit

| Metrica | Benchmark |
|---------|-----------|
| Mensagens descritivas (>20 chars) | >80% |
| Usa prefixo de tipo | >90% |
| Usa escopo | >50% |
| Referencias ticket/issue | >30% |
| Mensagens genericas | <10% |

### Atomicidade

| Metrica | Benchmark |
|---------|-----------|
| Media de arquivos/commit | <10 ideal, <20 aceitavel |
| Media de linhas/commit | <200 ideal, <500 aceitavel |
| Commits com 1-5 arquivos | >60% |
| Commits com >50 arquivos | <2% |

### Branches

| Metrica | Benchmark |
|---------|-----------|
| Commits direto na main | <20% ideal, <40% aceitavel |
| Branches abandonadas | 0 |
| Media commits/branch | 3-15 |

### Distribuicao

| Metrica | Benchmark |
|---------|-----------|
| Commits/dia (dias ativos) | 3-15 |
| Maior pico | <30 commits |
| Commits fim de semana | <10% |

---

## Criterios de Score

| Score | Significado |
|-------|-------------|
| 9-10 | Excelente - praticas de referencia |
| 7-8 | Bom - pequenos ajustes necessarios |
| 5-6 | Regular - melhorias importantes |
| 3-4 | Precisa atencao - riscos significativos |
| 1-2 | Critico - acao imediata necessaria |

---

## Exemplos de Uso

```bash
# Diagnostico da ultima semana
@devops *diagnose

# Diagnostico dos ultimos 14 dias
@devops *diagnose 14 days

# Diagnostico do ultimo mes
@devops *diagnose month
```

---

## Diferenca entre *report e *diagnose

| Aspecto | *report | *diagnose |
|---------|---------|-----------|
| **Publico** | Gestores, stakeholders | Desenvolvedores |
| **Foco** | Valor entregue | Praticas de engenharia |
| **Tom** | Defesa de entregas | Mentoria construtiva |
| **Output** | O que foi feito | Como foi feito |
| **Objetivo** | Comunicar progresso | Melhorar processo |

---

## Metadata

```yaml
version: 1.0.0
created_at: 2025-12-29
updated_at: 2025-12-29
author: AIOS Developer + Joao
template: git-diagnose-prompt-v1.md
tags:
  - diagnostico
  - praticas
  - mentoria
  - git
  - devops
```

---

## Integration

Called via `@devops *diagnose` command.

**Aliases:**
- `*diagnose` - Default (7 dias)
- `*diagnose {N} days` - Ultimos N dias
- `*diagnose week` - Ultima semana
- `*diagnose month` - Ultimo mes
