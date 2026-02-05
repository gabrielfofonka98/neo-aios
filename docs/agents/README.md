# Catalogo de Agentes

Documentacao completa de todos os agentes do NEO-AIOS.

---

## Visao Geral

O NEO-AIOS organiza agentes em uma hierarquia inspirada em empresas Big Tech:

```
┌─────────────────────────────────────────────────────────────┐
│ C-LEVEL (1)                                                 │
│   CTO (Fofonka) - Estrategia, visao                         │
├─────────────────────────────────────────────────────────────┤
│ VP LEVEL (5)                                                │
│   Aria (Engineering), Morgan (Product), Pixel (Design)      │
│   Oracle (Data), Atlas (Platform)                           │
├─────────────────────────────────────────────────────────────┤
│ DIRECTOR / MANAGER LEVEL                                    │
│   Directors e Tech Leads por area                           │
├─────────────────────────────────────────────────────────────┤
│ IC LEVEL - CORE (8)                                         │
│   Dex (Dev), Gage (DevOps), Dara (DB), Quinn (QA)          │
│   Codex (Code QA), Sage (Doc), Rune (Spec), Ralph (Auto)   │
├─────────────────────────────────────────────────────────────┤
│ IC LEVEL - SECURITY (18)                                    │
│   Sub-agentes especializados em seguranca                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Agentes Core

### Dex (Developer)

| Campo | Valor |
|-------|-------|
| **ID** | `dev` |
| **Tier** | IC |
| **Level** | Core |
| **Ativacao** | `/dev`, `@dev` |

**Escopo:**
- **Pode:** write_code, implement_features, fix_bugs, write_tests, refactor_code, debug, git_commit
- **Nao pode:** git_push, architecture_decisions, database_ddl, production_deploy

**Quando usar:**
Implementacao de codigo, debugging, refatoracao, testes. NUNCA para git push ou decisoes de arquitetura.

**Comandos:**
- `*develop` - Implementa tasks
- `*test` - Escreve e roda testes
- `*debug` - Debug de issues
- `*commit` - Cria commit (NAO push)
- `*exit` - Sai do modo agente

---

### Gage (DevOps)

| Campo | Valor |
|-------|-------|
| **ID** | `devops` |
| **Tier** | IC |
| **Level** | Core |
| **Ativacao** | `/devops`, `@devops` |

**Escopo:**
- **Pode:** git_push, git_force_push, create_pr, merge_pr, deploy, ci_cd_config
- **Nao pode:** write_application_code, architecture_decisions, database_ddl

**Quando usar:**
Git push, criacao de PR, merge, deploy. UNICO agente autorizado a fazer push para remoto.

**Comandos:**
- `*push` - Push para remote
- `*pr` - Cria pull request
- `*deploy` - Deploy para ambiente
- `*exit` - Sai do modo agente

**IMPORTANTE:** Gage e o UNICO agente que pode fazer git push. Todos os outros devem delegar para ele.

---

### Dara (Data Engineer)

| Campo | Valor |
|-------|-------|
| **ID** | `data-engineer` |
| **Tier** | IC |
| **Level** | Core |
| **Ativacao** | `/data-engineer`, `@data-engineer` |

**Escopo:**
- **Pode:** database_ddl, create_tables, alter_tables, write_migrations, sql_optimization
- **Nao pode:** write_application_code, git_push, architecture_decisions

**Quando usar:**
Schema de banco de dados, migrations, otimizacao SQL. Mudancas DDL requerem aprovacao.

**Comandos:**
- `*schema` - Analisa/propoe schema
- `*migration` - Cria migration
- `*query` - Otimiza queries
- `*exit` - Sai do modo agente

---

### Quinn (Security QA)

| Campo | Valor |
|-------|-------|
| **ID** | `qa` |
| **Tier** | IC |
| **Level** | Core |
| **Ativacao** | `/qa`, `@qa` |

**Escopo:**
- **Pode:** security_audit, run_validators, analyze_findings, coordinate_sec_agents
- **Nao pode:** write_code, fix_vulnerabilities, git_push

**Quando usar:**
Auditoria de seguranca, coordenacao dos 18 sub-agentes de seguranca, relatorios.

**Comandos:**
- `*audit` - Roda auditoria completa
- `*scan` - Scan rapido
- `*report` - Gera relatorio
- `*exit` - Sai do modo agente

**Nota:** Quinn orquestra os 18 sub-agentes de seguranca, mas NAO corrige vulnerabilidades (isso e com Dex).

---

### Codex (Code QA)

| Campo | Valor |
|-------|-------|
| **ID** | `qa-code` |
| **Tier** | IC |
| **Level** | Core |
| **Ativacao** | `/qa-code`, `@qa-code` |

**Escopo:**
- **Pode:** code_review, test_strategy, quality_validation, standards_enforcement
- **Nao pode:** write_code, security_audit, git_push

**Quando usar:**
Code review, estrategia de testes, validacao de qualidade. NAO faz auditoria de seguranca (isso e com Quinn).

**Comandos:**
- `*review` - Code review
- `*quality` - Valida quality gates
- `*coverage` - Analisa coverage
- `*exit` - Sai do modo agente

---

### Sage (Documentation)

| Campo | Valor |
|-------|-------|
| **ID** | `doc` |
| **Tier** | IC |
| **Level** | Content |
| **Ativacao** | `/doc`, `@doc` |

**Escopo:**
- **Pode:** write_documentation, create_guides, api_docs, architecture_docs
- **Nao pode:** write_code, git_push, make_decisions

**Quando usar:**
Documentacao tecnica, guias, API docs, documentacao de arquitetura.

**Comandos:**
- `*document` - Cria documentacao
- `*api-docs` - Gera API docs
- `*guide` - Cria guia
- `*exit` - Sai do modo agente

---

### Rune (Spec Architect)

| Campo | Valor |
|-------|-------|
| **ID** | `spec` |
| **Tier** | IC |
| **Level** | Core |
| **Ativacao** | `/spec`, `@spec` |

**Escopo:**
- **Pode:** create_specs, transform_prds, detail_requirements, prepare_for_ralph
- **Nao pode:** write_code, implement, git_push

**Quando usar:**
Transformar PRDs em specs ultra-detalhadas para execucao autonoma (Ralph). Zero ambiguidade.

**Comandos:**
- `*spec` - Cria spec de PRD
- `*detail` - Detalha requirements
- `*validate` - Valida completude
- `*exit` - Sai do modo agente

---

### Ralph (Autonomous Agent)

| Campo | Valor |
|-------|-------|
| **ID** | `ralph` |
| **Tier** | IC |
| **Level** | Automation |
| **Ativacao** | `/ralph`, `@ralph` |

**Escopo:**
- **Pode:** autonomous_execution, follow_specs, iterate_until_done
- **Nao pode:** git_push, make_architecture_decisions, deviate_from_spec

**Quando usar:**
Execucao autonoma de specs preparadas por Rune. Persiste progresso entre iteracoes.

**Comandos:**
- `*start` - Inicia execucao
- `*status` - Mostra progresso
- `*pause` - Pausa execucao
- `*exit` - Sai do modo agente

---

## Agentes VP Level

### Aria (VP Engineering)

| Campo | Valor |
|-------|-------|
| **ID** | `architect` |
| **Tier** | VP |
| **Level** | Executive |
| **Ativacao** | `/architect`, `@architect` |

**Escopo:**
- **Pode:** architecture_decisions, technology_selection, api_design, cross_cutting_concerns
- **Nao pode:** write_code, git_push, deploy

**Quando usar:**
Decisoes de arquitetura, selecao de tecnologia, design de API. NUNCA escreve codigo.

---

### Morgan (VP Product)

| Campo | Valor |
|-------|-------|
| **ID** | `pm` |
| **Tier** | VP |
| **Level** | Executive |
| **Ativacao** | `/pm`, `@pm` |

**Escopo:**
- **Pode:** product_strategy, prd_creation, requirements_management, stakeholder_coordination
- **Nao pode:** write_code, technical_decisions, git_push

**Quando usar:**
Estrategia de produto, criacao de PRD, gestao de requisitos.

---

## Agentes de Seguranca (18)

Quinn (QA) orquestra estes sub-agentes especializados:

### Deteccao de Vulnerabilidades

| ID | Nome | Especialidade |
|----|------|---------------|
| `sec-xss-hunter` | XSS Hunter | Cross-Site Scripting |
| `sec-injection-detector` | Injection Detector | SQL/ORM Injection |
| `sec-secret-scanner` | Secret Scanner | Secrets/Credentials expostos |
| `sec-jwt-auditor` | JWT Auditor | JWT vulnerabilities |
| `sec-redirect-checker` | Redirect Checker | Open redirects |

### Configuracao e Headers

| ID | Nome | Especialidade |
|----|------|---------------|
| `sec-header-inspector` | Header Inspector | CSP e Security Headers |
| `sec-cors-csrf-checker` | CORS/CSRF Checker | CORS e CSRF issues |
| `sec-rls-guardian` | RLS Guardian | Supabase Row Level Security |
| `sec-rate-limit-tester` | Rate Limit Tester | Rate limiting |

### Codigo e Dependencias

| ID | Nome | Especialidade |
|----|------|---------------|
| `sec-ai-code-reviewer` | AI Code Reviewer | Vibecoding patterns |
| `sec-validation-enforcer` | Validation Enforcer | Input validation (Zod) |
| `sec-error-leak-detector` | Error Leak Detector | Info leaks em erros |
| `sec-supply-chain-monitor` | Supply Chain Monitor | npm dependencies |
| `sec-framework-scanner` | Framework Scanner | CVEs em frameworks |

### Acesso e Deploy

| ID | Nome | Especialidade |
|----|------|---------------|
| `sec-api-access-tester` | API Access Tester | BOLA, BFLA, auth |
| `sec-upload-validator` | Upload Validator | File upload security |
| `sec-client-exposure-scanner` | Client Exposure Scanner | Client-side data |
| `sec-deploy-auditor` | Deploy Auditor | Vercel deploy security |

### Escopo Comum (todos sec-*)

```yaml
scope:
  can:
    - read_files
    - analyze_code
    - report_findings
  cannot:
    - write_files
    - fix_code
    - git_operations
```

Todos os agentes de seguranca:
- **Reportam para:** Quinn (qa)
- **Podem:** Ler e analisar codigo, reportar findings
- **Nao podem:** Escrever arquivos ou corrigir codigo

---

## Tabela de Delegacao

| De | Para | Quando |
|----|------|--------|
| Qualquer | Gage | Push, PR, merge |
| Qualquer | Aria | Decisao de arquitetura |
| Qualquer | Dara | Mudanca de schema |
| Qualquer | Quinn | Auditoria de seguranca |
| Dex | Codex | Code review |
| Rune | Ralph | Spec pronta para execucao |
| Quinn | sec-* | Scan especializado |

---

## Regras Importantes

1. **Apenas Gage pode fazer git push** - Todos os outros devem delegar
2. **VP e acima nao codam** - Aria decide, Dex implementa
3. **Quinn orquestra, nao corrige** - Identifica issues, Dex corrige
4. **Isolamento de identidade** - Um agente NUNCA simula outro
5. **Delegacao vai para baixo** - C-Level -> VP -> Director -> Manager -> IC

---

*NEO-AIOS Agent Catalog v0.1.0*
