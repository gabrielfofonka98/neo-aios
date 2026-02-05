# NEO-AIOS - Agent Structure & Naming

**Versao:** 2.0.0
**Data:** 2026-02-04
**Estrutura:** 15 Core + 18 Security = 33 Agentes

---

## Arquitetura Final

```
┌─────────────────────────────────────────────────────────────────┐
│                           GABRIEL                               │
│                              │                                  │
│                         ORION (Master)                          │
│                    Ponto Unico de Contato                       │
│                              │                                  │
├──────────────────────────────┼──────────────────────────────────┤
│                              │                                  │
│  PRODUTO         ENGENHARIA           DADOS        QUALIDADE    │
│  ───────         ──────────           ─────        ─────────    │
│                                                                 │
│  Morgan (PM)     Dex (Dev)            Dara (Eng)   Quinn (Sec)  │
│  Aria (Arch)     Gage (DevOps)        Oracle (Ana) Codex (Code) │
│  Pixel (Design)  Ops (SRE)                         Tess (Func)  │
│  Rune (Spec)     Sage (Doc)                                     │
│                  Ralph (Auto)                                   │
│                                                                 │
│                              + 18 Security Sub-Agents           │
│                                (sob Quinn)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Os 15 Core Agents

### CORE (1)

| Nome | ID | Icon | Funcao | Tipo |
|------|-----|------|--------|------|
| **Orion** | `master` | 🌟 | Orquestra tudo, ponto unico de contato | Orchestrator |

### PRODUTO (4)

| Nome | ID | Icon | Funcao | Tipo |
|------|-----|------|--------|------|
| **Morgan** | `pm` | 📊 | PRDs, stories, priorizacao, metricas de produto | Generalista |
| **Aria** | `architect` | 🏛️ | Arquitetura, RFCs, decisoes tecnicas | Especialista |
| **Pixel** | `design` | 🎨 | UX/UI, design system, prototipos | Generalista |
| **Rune** | `spec` | ⚔️ | Specs ultra-detalhados pro Ralph | Generalista |

### ENGENHARIA (5)

| Nome | ID | Icon | Funcao | Tipo |
|------|-----|------|--------|------|
| **Dex** | `dev` | ⚡ | Codigo, testes, commits | Especialista |
| **Gage** | `devops` | 🔥 | Push, PR, deploy, CI/CD (**UNICO push**) | Especialista |
| **Ops** | `sre` | 📡 | Monitoring, alertas, incidentes, SLO | Especialista |
| **Sage** | `doc` | 📚 | Documentacao tecnica | Generalista |
| **Ralph** | `ralph` | 🤖 | Execucao autonoma ate completar | Especialista |

### DADOS (2)

| Nome | ID | Icon | Funcao | Tipo |
|------|-----|------|--------|------|
| **Dara** | `data-eng` | 🔷 | Schema, migrations, pipelines, SQL | Especialista |
| **Oracle** | `analyst` | 📈 | Analises, dashboards, metricas, insights | Generalista |

### QUALIDADE (3)

| Nome | ID | Icon | Funcao | Tipo |
|------|-----|------|--------|------|
| **Quinn** | `qa-sec` | 🛡️ | Security audit, orquestra 18 sub-agents | Especialista |
| **Codex** | `qa-code` | 📝 | Code review, quality gates, standards | Especialista |
| **Tess** | `qa-func` | 🧪 | Testes funcionais, E2E, test plans, bugs | Especialista |

---

## Os 18 Security Sub-Agents

Todos sob orquestracao do **Quinn**.

### AST-Based (6) - Analise de Codigo

| Nome | ID | Focus | Detecta |
|------|-----|-------|---------|
| **Needle** | `sec-sql` | SQL Injection | Prisma raw queries, operator injection |
| **Weave** | `sec-xss` | XSS | Unsafe innerHTML, href injection |
| **Bound** | `sec-cors` | CORS | Origin reflection, wildcard credentials |
| **Gate** | `sec-auth` | Auth Bypass | Missing verification, decode misuse |
| **Vault** | `sec-rls` | RLS | Supabase RLS policy violations |
| **Cast** | `sec-type` | Type Coercion | TypeScript any abuse, type unsafety |

### Regex-Based (12) - Pattern Matching

| Nome | ID | Focus | Detecta |
|------|-----|-------|---------|
| **Cipher** | `sec-secrets` | Secrets | Hardcoded keys, env var abuse |
| **Chain** | `sec-deps` | Dependencies | Vulnerable packages, npm audit |
| **Mist** | `sec-error` | Error Leak | Stack traces expostos |
| **Crown** | `sec-headers` | Headers | CSP, HSTS, X-Frame-Options |
| **Token** | `sec-csrf` | CSRF | SameSite cookies, token validation |
| **Throttle** | `sec-rate` | Rate Limit | Missing rate limiting |
| **Filter** | `sec-input` | Input Validation | Zod enforcement, sanitization |
| **Upload** | `sec-upload` | File Upload | Magic bytes, unsafe filenames |
| **Portal** | `sec-api` | API Access | BOLA, BFLA, excessive exposure |
| **Sigil** | `sec-jwt` | JWT | Algorithm none, verification bypass |
| **Arrow** | `sec-redirect` | Redirect | Open redirect vulnerabilities |
| **Link** | `sec-supply` | Supply Chain | Unpinned versions, lockfile issues |

---

## Comandos de Ativacao

```bash
# Core
/master, /orion          # Orquestrador

# Produto
/pm, /morgan             # Product Manager
/architect, /aria        # Arquiteto
/design, /pixel          # Designer
/spec, /rune             # Spec Writer

# Engenharia
/dev, /dex               # Developer
/devops, /gage           # DevOps (UNICO push)
/sre, /ops               # SRE
/doc, /sage              # Documentation
/ralph                   # Autonomous

# Dados
/data-eng, /dara         # Data Engineer
/analyst, /oracle        # Data Analyst

# Qualidade
/qa-sec, /quinn          # Security QA
/qa-code, /codex         # Code QA
/qa-func, /tess          # Functional QA
```

---

## Scope Rules

### Quem faz o que

| Tarefa | Quem FAZ | Quem NAO FAZ |
|--------|----------|--------------|
| Orquestrar | Orion | Todos outros |
| PRDs, stories | Morgan | Engenharia, QA |
| Arquitetura | Aria | Dev, QA |
| Design/UX | Pixel | Dev, Data |
| Specs detalhados | Rune | Dev, QA |
| Codigo | Dex | PM, Design |
| **Git push/PR** | **Gage** | **TODOS OUTROS** |
| Monitoring | Ops | Dev, PM |
| Documentacao | Sage | PM, QA |
| Execucao autonoma | Ralph | - |
| Schema/SQL | Dara | Dev, PM |
| Analise dados | Oracle | Dara, Dev |
| Security audit | Quinn | Codex, Tess |
| Code review | Codex | Quinn, Tess |
| Testes funcionais | Tess | Quinn, Codex |

### Regra de Ouro

```
So Gage faz push. Isso e BLOQUEADO em runtime pra outros agentes.
```

---

## Fluxo de Trabalho

```
Voce: "Preciso de feature X"
         │
         ▼
    ┌─────────┐
    │  Orion  │ ← Entende, planeja, delega
    └────┬────┘
         │
    ┌────┴────┬────────┬────────┬────────┐
    ▼         ▼        ▼        ▼        ▼
 Morgan    Aria     Dex      Quinn    Gage
 (PRD)    (Arch)   (Code)   (Sec)    (Push)
    │         │        │        │        │
    └────┬────┴────────┴────────┴────────┘
         │
         ▼
    Voce: "PR #42 criada"
```

---

## Especialista vs Generalista

| Tipo | Agentes | Por que |
|------|---------|---------|
| **Especialista** | Aria, Dex, Gage, Ops, Ralph, Dara, Quinn, Codex, Tess | Areas criticas, nao pode errar |
| **Generalista** | Morgan, Pixel, Rune, Sage, Oracle | Escopo mais flexivel |
| **Orchestrator** | Orion | Coordena todos |

---

## Totais

| Categoria | Quantidade |
|-----------|------------|
| Core Agents | 15 |
| Security Sub-Agents | 18 |
| **Total** | **33** |

---

## Pronuncia

| Nome | Pronuncia |
|------|-----------|
| Orion | o-RI-on |
| Morgan | MOR-gan |
| Aria | A-ri-a |
| Pixel | PI-kel |
| Rune | RU-ne |
| Dex | DEKS |
| Gage | GEIDJ |
| Ops | OPS |
| Sage | SEIDJ |
| Ralph | RALF |
| Dara | DA-ra |
| Oracle | O-ra-kel |
| Quinn | KUIN |
| Codex | KO-deks |
| Tess | TES |

---

*NEO-AIOS Agent Structure v2.0*
*"Estrutura completa, sem burocracia"*
