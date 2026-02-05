# github-devops-git-report.md

**Task**: Generate Git Activity Reports (Executive & Operational)

**Purpose**: Produzir relatorios que protegem o profissional, explicitam handoffs, reduzem riscos organizacionais e transformam esforco tecnico em narrativa de valor.

**When to use**: Via `@devops *report` para daily standups, apresentacoes para gestao, sprint reviews, ou defesa de entregas.

**Template Reference**: `.aios-core/development/templates/git-report-prompt-v3.md`

---

## Principios Inegociaveis

1. **Resumo Executivo combina texto corrido + tabelas** — narrativa para contexto, tabelas para evidencia
2. **Nenhum hash de commit no corpo principal** — so no apendice
3. **Todo termo tecnico traduzido** para impacto de negocio na primeira mencao
4. **Tabelas de metricas apoiam a narrativa**, nunca substituem
5. **Handoffs explicitos** em cada dia e no resumo
6. **Respostas prontas** para questionamentos comuns obrigatorias
7. **Trabalho invisivel vira explicito**: decisoes, preparacao, risco evitado
8. Se algo **nao foi concluido**: explicar valor do que ja esta pronto
9. **Working tree suja** = "trabalho em progresso para proximo ciclo"
10. **Sem emojis** no relatorio
11. **Sintese Final funciona como defesa autonoma**

---

## Task Definition

```yaml
task: githubDevopsGitReport()
responsável: Gage (Operator)
version: 3.0.0

**Entrada:**
- campo: period
  tipo: string
  validação: today|yesterday|week|N days|YYYY-MM-DD..YYYY-MM-DD
  default: "yesterday"

- campo: format
  tipo: string
  validação: executive|detailed|minimal
  default: "executive"

- campo: output
  tipo: string
  validação: terminal|markdown|file
  default: "terminal"
```

---

## Estrutura do Relatorio (Executive v3.0)

O relatorio tem duas camadas:

### Camada 1: RESUMO EXECUTIVO (primeira dobra)

Permite decisao sem ler o resto:

1. **Contexto** — Tabela com repo, branch, periodo, momento do projeto, working tree
2. **Painel de Metricas** — Commits, linhas +/-, arquivos, areas, contribuidor
3. **O Que Foi Entregue** — Texto corrido (4-6 linhas) em linguagem de resultado
4. **Entregas Estrategicas** — Tabela com impacto para o negocio
5. **Por Que Esse Periodo Foi Importante** — Texto corrido respondendo "o que teria dado errado?"
6. **Handoffs e Continuidade** — Texto corrido sobre documentacao e perfil tecnico
7. **Riscos Mitigados** — Tabela com status (Eliminado/Reduzido)
8. **Reducao de Divida Tecnica** — Tabela Antes/Depois
9. **Respostas Rapidas para Questionamentos** — 5 perguntas comuns com respostas prontas

### Camada 2: RELATORIO COMPLETO (por dia)

Para cada dia com atividade:

1. **Narrativa do Dia** — Texto corrido (3-4 linhas)
2. **Metricas do Dia** — Tabela commits, linhas, arquivos
3. **Entregas do Dia** — Tabela com "O Que Mudou" e "Por Que Agora"
4. **Valor Concreto** — Bullets com metricas tangiveis
5. **Banco de Dados** — Tabela CREATE/DROP/ALTER (se aplicavel)
6. **Handoff do Dia** — Tabela com status
7. **Avaliacao Qualitativa** — Tabela tipo/impacto/riscos/divida
8. **Proximos Passos Naturais** — Bullets

### Camada 3: SINTESE FINAL — DEFESA DE VALOR

Tres paragrafos que funcionam como defesa autonoma:

1. **Relevancia do periodo** — O que esses dias transformaram
2. **Consequencias evitadas** — O que teria dado errado
3. **Demonstracao de competencia** — Que tipo de profissional isso demonstra

### Camada 4: APENDICE

- Comandos git utilizados
- Criterio de datas
- Working tree status
- Arquivos alterados por area
- Distribuicao de commits

---

## Coleta de Dados

### Step 1: Context

```bash
git rev-parse --abbrev-ref HEAD
git remote get-url origin 2>/dev/null || echo "local"
git status --porcelain=v1
```

### Step 2: Global Metrics

```bash
# Commits no periodo
git log --since="{start}" --until="{end}" --oneline | wc -l

# Linhas +/-
git log --since="{start}" --until="{end}" --shortstat --format="" | \
  awk '/files? changed/ {f+=$1; i+=$4; d+=$6} END {print "files:"f" ins:"i" del:"d}'

# Arquivos unicos
git log --since="{start}" --until="{end}" --name-only --format="" | sort -u | wc -l

# Commits por dia
git log --since="{start}" --until="{end}" --format="%ad" --date=short | sort | uniq -c

# Contribuidores
git log --since="{start}" --until="{end}" --format="%an" | sort -u
```

### Step 3: Per-Day Analysis

```bash
# Para cada dia:
git log --since="{date} 00:00" --until="{date} 23:59" --format="%h|%s" --shortstat

# Areas impactadas
git log --since="{date} 00:00" --until="{date} 23:59" --name-only --format="" | \
  cut -d'/' -f1-2 | sort | uniq -c | sort -rn | head -5
```

### Step 4: Database Detection

```bash
# Arquivos de banco
git log --since="{start}" --until="{end}" --name-only --format="" | \
  grep -E "(migration|seed|\.sql|prisma|supabase)" | sort -u

# Schema changes
git log --since="{start}" --until="{end}" -p -- "*.sql" | \
  grep -E "^[\+\-].*(CREATE|DROP|ALTER)\s+(TABLE|INDEX|VIEW)" | head -20
```

### Step 5: Qualitative Sources

```bash
# Handoffs
ls docs/*/handoffs/*{date}* 2>/dev/null

# Stories
ls docs/stories/*.md 2>/dev/null

# Logs
ls docs/logs/*{date}* 2>/dev/null
```

---

## Respostas Rapidas (Obrigatorias)

O relatorio DEVE incluir respostas para:

| Pergunta | Template de Resposta |
|----------|---------------------|
| "Por que demorou {N} dias?" | Trabalho fundacional que resolve causa raiz e evita retrabalho futuro. Cada item entregue multiplica velocidade de entregas subsequentes. |
| "Quantas features novas?" | Foco em criar condicoes para entregas futuras serem mais rapidas e seguras. {X e Y} sao features visiveis; o resto habilita features. |
| "Qual o impacto real?" | Reducao de risco operacional, aumento de previsibilidade, desbloqueio de proximos passos. {Exemplo concreto}. |
| "Outro dev continua?" | Sim. Handoffs claros no codigo. Padroes documentados em {arquivos}. |
| "Nao poderia ser mais simples?" | A solucao parece simples depois de pronta. O resultado e essa simplicidade - antes havia {problema}. |

---

## Transformacao Tecnico → Negocio

### Exemplos de Traducao

| Termo Tecnico | Impacto de Negocio |
|---------------|-------------------|
| "TypeScript strict mode" | Bugs detectados em compilacao, nao em producao |
| "Lazy loading 40 templates" | App carrega mais rapido, melhor experiencia |
| "DROP TABLE obsoleta" | Schema mais simples, manutencao mais facil |
| "CI/CD automatizado" | Qualidade garantida em cada deploy |
| "35/35 testes passando" | Sistema confiavel, pronto para producao |
| "Migration aplicada" | Base de dados evoluiu sem perda de dados |

### Regra de Ouro

Nunca dizer "implementei X" — sempre dizer "O sistema agora consegue Y".

---

## Period Options

| Option | Description |
|--------|-------------|
| `today` | Dia atual |
| `yesterday` | Dia anterior (default) |
| `week` | Ultimos 7 dias |
| `N days` | Ultimos N dias |
| `YYYY-MM-DD..YYYY-MM-DD` | Range customizado |

---

## Format Options

| Format | Uso |
|--------|-----|
| `executive` | Completo com defesa de valor (default) |
| `detailed` | Executive + todos os commits |
| `minimal` | Metricas + top 5 entregas |

---

## Checklist de Qualidade

Antes de entregar, verificar:

### Resumo Executivo
- [ ] Contexto com todos os campos?
- [ ] Metricas com numeros reais?
- [ ] Texto "O Que Foi Entregue" em linguagem de resultado?
- [ ] Entregas estrategicas com impacto?
- [ ] "Por Que Foi Importante" responde "o que teria dado errado"?
- [ ] Handoffs explicitos?
- [ ] Riscos mitigados?
- [ ] Tabela Antes/Depois?
- [ ] Respostas rapidas?

### Por Dia
- [ ] Narrativa em texto corrido?
- [ ] Tabela de metricas?
- [ ] Entregas com "O Que Mudou" e "Por Que Agora"?
- [ ] Valor concreto em bullets?
- [ ] Banco de dados documentado?
- [ ] Handoff do dia?
- [ ] Avaliacao qualitativa?
- [ ] Proximos passos?

### Sintese Final
- [ ] Tres paragrafos: Relevancia, Consequencias, Competencia?
- [ ] Funciona como defesa autonoma?

### Regras Gerais
- [ ] Nenhum hash fora do apendice?
- [ ] Nenhum emoji?
- [ ] Termos tecnicos traduzidos?
- [ ] Gestor nao-tecnico entende o valor?

---

## Examples

```bash
# Relatorio dos ultimos 8 dias para apresentar ao chefe
@devops *report 8 days

# Relatorio da semana
@devops *report week

# Range especifico
@devops *report 2025-12-21..2025-12-28

# Update rapido do dia
@devops *report today --format=minimal
```

---

## Output Signature

```markdown
---

*Relatorio gerado em: {timestamp}*
*Repositorio: {owner}/{repo} @ {branch}*
```

---

## Metadata

```yaml
version: 3.0.0
created_at: 2025-12-29
updated_at: 2025-12-29
author: AIOS Developer + Joao (refinement v3)
template: git-report-prompt-v3.md
tags:
  - reporting
  - git
  - devops
  - executive
  - value-defense
```

---

## Integration

Called via `@devops *report` command.

**Aliases:**
- `*report` - Default (yesterday, executive)
- `*report today` - Today
- `*report week` - Last 7 days
- `*report {N} days` - Last N days
- `*report {date}..{date}` - Custom range

**Flags:**
- `--format=executive|detailed|minimal`
- `--output=terminal|file`
