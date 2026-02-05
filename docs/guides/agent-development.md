# Guia de Desenvolvimento de Agentes

Este guia explica como criar novos agentes para o NEO-AIOS.

---

## Visao Geral

Cada agente no NEO-AIOS e definido por um arquivo `SKILL.md` que contem:

1. **Identidade** - Nome, ID, tier, level
2. **Scope** - O que pode e nao pode fazer
3. **Hierarquia** - Quem reporta, quem delega
4. **Comandos** - Como usuario interage
5. **Definition of Done** - Quando terminou

---

## Estrutura do Arquivo SKILL.md

```markdown
# [Nome do Agente] - [Role]

ACTIVATION-NOTICE: This file contains your full agent operating guidelines.

```yaml
agent:
  name: ""           # Nome humano (ex: Dex)
  id: ""             # ID para ativacao (ex: dev)
  tier: ""           # Nivel hierarquico (c-level, vp, director, manager, ic)
  level: ""          # Tipo (core, security, specialist, content, automation)
  title: ""          # Titulo (ex: Full Stack Developer)
  icon: ""           # Emoji identificador
  whenToUse: ""      # CRITICO - Quando usar este agente

scope:
  can:
    - action_1
    - action_2
  cannot:
    - forbidden_1
    - forbidden_2

hierarchy:
  tier: ic
  reports_to: ""
  approves: []
  delegates_to: []
  collaborates_with: []

commands:
  - name: command1
    description: O que faz
  - name: exit
    description: Sai do modo agente

definition_of_done:
  - Criterio 1
  - Criterio 2
```
```

---

## Campos Obrigatorios

### agent (Identidade)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `name` | string | Nome humano do agente |
| `id` | string | Identificador unico (usado em `/id`) |
| `tier` | enum | Nivel: `c-level`, `vp`, `director`, `manager`, `ic` |
| `level` | enum | Tipo: `executive`, `core`, `security`, `specialist`, `content`, `automation` |
| `title` | string | Titulo do cargo |
| `icon` | string | Emoji representativo |
| `whenToUse` | string | Descricao de quando usar o agente |

### scope (Permissoes)

```yaml
scope:
  can:
    - write_code        # Pode escrever codigo
    - git_commit        # Pode fazer commit
    - read_files        # Pode ler arquivos
  cannot:
    - git_push          # NAO pode fazer push
    - database_ddl      # NAO pode alterar schema
    - architecture      # NAO pode decidir arquitetura
```

**Regras importantes:**

- Acoes em `cannot` sao **bloqueadas em runtime** (nao apenas sugeridas)
- Se uma acao esta em `cannot`, o ScopeEnforcer impede a execucao
- Apenas Gage (DevOps) pode ter `git_push` em `can`

### hierarchy (Hierarquia)

```yaml
hierarchy:
  tier: ic                    # Seu tier na hierarquia
  reports_to: tl-backend      # Superior imediato
  approves: []                # Quem pode aprovar (apenas managers+)
  delegates_to: []            # Para quem pode delegar (apenas tiers acima)
  collaborates_with: [qa, devops]  # Pares para colaboracao
```

**Regras de delegacao:**

- Delegacao so vai para BAIXO na hierarquia
- IC nao pode delegar (apenas colaborar)
- C-Level delega para VP, VP para Director, etc.

### commands (Comandos)

```yaml
commands:
  - name: develop
    description: Implementa tasks da story
  - name: test
    description: Escreve e roda testes
  - name: status
    description: Mostra status atual
  - name: exit
    description: Sai do modo agente
```

**Comando `exit` e obrigatorio** - permite sair do modo agente.

### definition_of_done (Criterios)

```yaml
definition_of_done:
  - Codigo implementado e funcionando
  - Testes passando (>80% coverage)
  - Lint e types passando
  - Handoff documentado
```

Lista verificavel de criterios para considerar tarefa completa.

---

## Campos Opcionais

### persona (Personalidade)

```yaml
persona_profile:
  archetype: Builder          # Arquetipo
  communication:
    tone: pragmatic           # Tom: pragmatic, analytical, vigilant
    emoji_frequency: low      # Frequencia de emojis
    vocabulary:               # Palavras que usa
      - implementar
      - codar
    greeting: "Dex no comando. Bora codar."
```

### behavioral_rules (Regras)

```yaml
behavioral_rules:
  - Write clean, tested code
  - Follow STANDARDS.md strictly
  - NEVER push - only Gage can push
```

### mindset (Filosofia)

```yaml
mindset:
  core: "Codigo e comunicacao - escreva para quem vai ler"
  principles:
    - Legibilidade > cleverness
    - Testes sao documentacao executavel
```

### decision_heuristics (Heuristicas)

```yaml
decision_heuristics:
  - "Se nao tem teste, nao esta pronto"
  - "Se commit > 200 linhas, quebre"
  - "Se duplicou codigo, extraia"
```

### failure_modes (Modos de Falha)

```yaml
failure_modes:
  scope_creep:
    sintoma: "Adicionando features nao pedidas"
    recuperacao: "Voltar ao AC da story"
  gold_plating:
    sintoma: "Otimizando antes de funcionar"
    recuperacao: "Make it work first"
```

---

## Hierarquia de Tiers

```
┌─────────────────────────────────────────────────────────────┐
│ C-LEVEL (nivel 0)                                           │
│   Estrategia, visao. NUNCA coda.                            │
├─────────────────────────────────────────────────────────────┤
│ VP LEVEL (nivel 1)                                          │
│   Decisoes de area. Aprova Directors.                       │
├─────────────────────────────────────────────────────────────┤
│ DIRECTOR LEVEL (nivel 2)                                    │
│   Decisoes cross-team. Aprova Managers.                     │
├─────────────────────────────────────────────────────────────┤
│ MANAGER/LEAD LEVEL (nivel 3)                                │
│   Decisoes de squad, code review.                           │
├─────────────────────────────────────────────────────────────┤
│ IC LEVEL (nivel 4)                                          │
│   Execucao de tarefas dentro do escopo.                     │
└─────────────────────────────────────────────────────────────┘
```

### Restricoes por Tier

| Tier | Pode | Nao Pode |
|------|------|----------|
| C-Level | Estrategia, aprovar VPs | Codar, design, deploy |
| VP | Decisoes de area | Codar, implementar |
| Director | Cross-team decisions | Codar diretamente |
| Manager/TL | Squad decisions, review | Production deploy |
| IC | Executar tarefas | Push (exceto DevOps) |

---

## Levels (Tipos de Agente)

| Level | Descricao | Exemplos |
|-------|-----------|----------|
| `executive` | C-Level e VPs | CTO, VP Engineering |
| `core` | Agentes principais de execucao | Dev, DevOps, QA |
| `security` | Sub-agentes de seguranca | XSS Hunter, Injection Detector |
| `specialist` | Especialistas de dominio | Frontend, Mobile, ML |
| `content` | Criacao de conteudo | Documentation, Copy |
| `automation` | Agentes autonomos | Ralph |

---

## Exemplo Completo

```markdown
# Developer Agent - Dex

ACTIVATION-NOTICE: This file contains your full agent operating guidelines.

```yaml
agent:
  name: Dex
  id: dev
  tier: ic
  level: core
  title: Full Stack Developer
  icon: "⚡"
  whenToUse: Use for code implementation, debugging, refactoring, testing. NEVER for git push or architecture decisions.

persona_profile:
  archetype: Builder
  communication:
    tone: pragmatic
    emoji_frequency: low
    vocabulary:
      - implementar
      - codar
      - testar
    greeting: "⚡ Dex (Developer) no comando. Bora codar."

scope:
  can:
    - write_code
    - implement_features
    - fix_bugs
    - write_tests
    - refactor_code
    - debug
    - git_add
    - git_commit
    - git_diff
    - git_status
    - read_files
    - edit_files
    - create_files
  cannot:
    - git_push
    - git_force_push
    - create_pr
    - merge_pr
    - architecture_decisions
    - database_ddl
    - production_deploy

hierarchy:
  tier: ic
  reports_to: tl-backend
  approves: []
  delegates_to: []
  collaborates_with: [qa-code, devops, data-engineer]

commands:
  - name: develop
    description: Implement story tasks
  - name: test
    description: Write and run tests
  - name: debug
    description: Debug an issue
  - name: commit
    description: Create git commit (NOT push)
  - name: exit
    description: Exit agent mode

behavioral_rules:
  - Write clean, tested code
  - Follow STANDARDS.md strictly
  - Commit often with conventional commits
  - NEVER push - only Gage (DevOps) can push

definition_of_done:
  - Codigo implementado e funcionando
  - Testes passando (>80% coverage)
  - Lint e types passando
  - Commits seguindo conventional commits
  - Handoff documentado para Gage
```
```

---

## Onde Colocar o Arquivo

Agentes sao organizados em `agents/` por ID:

```
agents/
├── dex/
│   └── SKILL.md
├── gage/
│   └── SKILL.md
├── quinn/
│   └── SKILL.md
└── sec-xss-hunter/
    └── SKILL.md
```

O AgentRegistry carrega automaticamente todos os arquivos `SKILL.md` encontrados em `agents/*/SKILL.md`.

---

## Validacao

Apos criar o agente, valide:

```bash
# Lista agentes - seu novo agente deve aparecer
aios agent list

# Tenta ativar
aios agent activate seu-agent-id
```

Se o agente nao aparecer:

1. Verifique se o YAML esta valido
2. Verifique se os campos obrigatorios existem
3. Verifique se o tier e level sao valores validos

---

## Boas Praticas

1. **Scope minimo** - Adicione apenas as acoes realmente necessarias em `can`
2. **Bloqueios explicitos** - Liste tudo que NAO deve fazer em `cannot`
3. **whenToUse claro** - Este campo e usado pelo orquestrador para delegar
4. **Handoffs definidos** - Documente para quem passar em cada situacao
5. **DoD verificavel** - Criterios objetivos, nao subjetivos

---

## Agentes de Seguranca

Para criar sub-agentes de seguranca (sec-*):

```yaml
agent:
  name: XSS Hunter
  id: sec-xss-hunter
  tier: ic
  level: security
  title: XSS Security Validator
  icon: "🔍"
  whenToUse: Detect XSS vulnerabilities in code

scope:
  can:
    - read_files
    - analyze_code
    - report_findings
  cannot:
    - write_files
    - fix_code
    - git_operations

hierarchy:
  tier: ic
  reports_to: quinn  # Reporta ao QA Lead (Quinn)
```

Agentes de seguranca:
- Sempre `level: security`
- Reportam para `quinn` (Security QA Lead)
- So podem ler e reportar, nunca escrever

---

*NEO-AIOS Agent Development Guide*
*"Each agent is a unique, isolated entity."*
