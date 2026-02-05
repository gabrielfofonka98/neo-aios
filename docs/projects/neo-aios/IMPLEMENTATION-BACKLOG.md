# NEO-AIOS Implementation Backlog

**Última Atualização:** 2026-02-05
**Status:** Em Desenvolvimento
**Responsável:** Orion (Master) → Delega para Dex (Dev)

---

## Status Geral

| Epic | Nome | Progresso | Prioridade |
|------|------|-----------|------------|
| Epic 1 | Foundation | 40% | P0 |
| Epic 2 | Security Validators | 0% | P1 |
| Epic 3 | Quality Gates | 0% | P2 |
| Epic 4 | Auto-Fix | 0% | P2 |
| Epic 5 | CLI | 0% | P1 |
| Epic 6 | Polish | 0% | P3 |

---

## ✅ O Que Já Está Feito

### Estrutura Base
- [x] `pyproject.toml` - Configuração do projeto
- [x] `src/aios/__init__.py` - Módulo principal
- [x] `tests/conftest.py` - Fixtures de teste
- [x] `.env` e `.env.example` - Configurações de ambiente
- [x] `config/credentials.yaml` - Credenciais
- [x] `.gitignore` - Git ignore

### Epic 1 - Foundation (Parcial)
- [x] **S1.2 Agent Registry** - `src/aios/agents/registry.py` ✅
- [x] **S1.2 Agent Models** - `src/aios/agents/models.py` ✅
- [x] **S1.3 Session Persistence** - `src/aios/context/session.py` ✅

### Agentes
- [x] 33 agentes definidos em `agents/`
- [x] 18 sub-agentes de segurança (sec-*)
- [x] Estrutura padronizada (Squad Architect validou 33/33 PASS)

---

## ❌ O Que Falta Implementar

### Epic 1: Foundation

#### S1.1 Project Setup (Parcial)
**Status:** 70% completo
**Falta:**
- [ ] `src/aios/cli/main.py` - Entry point CLI
- [ ] `src/aios/models/base.py` - Modelos base
- [ ] `src/aios/agents/dispatcher.py` - Dispatcher de agentes
- [ ] Exports em `__init__.py` dos módulos

**Arquivos a criar:**
```
src/aios/cli/main.py
src/aios/models/base.py
src/aios/agents/dispatcher.py
```

---

#### S1.4 Scope Enforcer
**Status:** 0% - NÃO INICIADO
**Prioridade:** CRÍTICO
**Dependência:** S1.2 (feito)

**Arquivos a criar:**
```
src/aios/scope/enforcer.py      # ScopeEnforcer class
src/aios/scope/actions.py       # ActionMapper class
tests/test_scope/test_enforcer.py
```

**Funcionalidades:**
- [ ] `ScopeEnforcer` - Bloqueia ações fora do escopo
- [ ] `ActionMapper` - Mapeia comandos para ações
- [ ] `EXCLUSIVE_ACTIONS` - git_push só para devops
- [ ] `GLOBALLY_BLOCKED` - Ações proibidas para todos
- [ ] Testes unitários (95%+ coverage)

**Código esperado:** Ver `docs/projects/neo-aios/epics/epic-1-foundation/story-1.4-scope-enforcer.md`

---

#### S1.5 Agent Loader
**Status:** 0% - NÃO INICIADO
**Prioridade:** ALTA
**Dependência:** S1.2 (feito)

**Arquivos a criar:**
```
src/aios/agents/loader.py       # AgentLoader class
tests/test_agents/test_loader.py
```

**Funcionalidades:**
- [ ] `AgentLoader` - Carrega agentes do filesystem
- [ ] Parse de SKILL.md com YAML embarcado
- [ ] Validação de estrutura do agente
- [ ] Cache de agentes carregados
- [ ] Testes unitários

**Código esperado:** Ver `docs/projects/neo-aios/epics/epic-1-foundation/story-1.5-agent-loader.md`

---

#### S1.6 Health Check Engine
**Status:** 0% - NÃO INICIADO
**Prioridade:** MÉDIA
**Dependência:** S1.4, S1.5

**Arquivos a criar:**
```
src/aios/healthcheck/engine.py      # HealthCheckEngine
src/aios/healthcheck/checks.py      # Individual checks
src/aios/healthcheck/domains.py     # Domain definitions
tests/test_healthcheck/test_engine.py
```

**Funcionalidades:**
- [ ] `HealthCheckEngine` - Executa verificações
- [ ] Domínios: agents, session, scope, security
- [ ] Status: OK, WARNING, ERROR, CRITICAL
- [ ] Report consolidado
- [ ] Testes unitários

**Código esperado:** Ver `docs/projects/neo-aios/epics/epic-1-foundation/story-1.6-health-check.md`

---

### Epic 2: Security Validators

#### S2.1 Validator Framework
**Status:** 0% - NÃO INICIADO
**Prioridade:** ALTA

**Arquivos a criar:**
```
src/aios/security/validators/base.py        # BaseValidator
src/aios/security/validators/registry.py    # ValidatorRegistry
src/aios/security/validators/result.py      # ValidationResult
tests/test_security/test_validators.py
```

**Funcionalidades:**
- [ ] `BaseValidator` - Classe base para validadores
- [ ] `ValidatorRegistry` - Registro central
- [ ] `ValidationResult` - Resultado padronizado
- [ ] `Severity` enum (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- [ ] `Finding` dataclass

---

#### S2.2 AST Validators
**Status:** 0% - NÃO INICIADO
**Dependência:** S2.1

**Arquivos a criar:**
```
src/aios/security/ast/parser.py           # Tree-sitter wrapper
src/aios/security/ast/typescript.py       # TS/JS validators
src/aios/security/ast/sql.py              # SQL validators (sqlglot)
```

**Validadores AST:**
- [ ] XSS Hunter (innerHTML patterns, eval)
- [ ] Injection Detector (SQL, ORM)
- [ ] JWT Auditor (decode vs verify)
- [ ] Secret Scanner (hardcoded secrets)

---

#### S2.3 Regex Validators
**Status:** 0% - NÃO INICIADO
**Dependência:** S2.1

**Arquivos a criar:**
```
src/aios/security/validators/regex/base.py
src/aios/security/validators/regex/patterns.py
```

**Validadores Regex:**
- [ ] CORS Checker
- [ ] Rate Limit Tester
- [ ] Header Inspector
- [ ] Error Leak Detector

---

#### S2.4 Orchestration
**Status:** 0% - NÃO INICIADO
**Dependência:** S2.2, S2.3

**Arquivos a criar:**
```
src/aios/security/orchestrator.py     # SecurityOrchestrator
```

**Funcionalidades:**
- [ ] Execução paralela de validadores
- [ ] Agregação de resultados
- [ ] Priorização por severidade

---

#### S2.5 Security Reports
**Status:** 0% - NÃO INICIADO
**Dependência:** S2.4

**Arquivos a criar:**
```
src/aios/security/reports/generator.py    # ReportGenerator
src/aios/security/reports/formats.py      # Output formats
```

**Funcionalidades:**
- [ ] Relatório consolidado
- [ ] Formatos: JSON, Markdown, HTML
- [ ] Sumário executivo

---

### Epic 3: Quality Gates

#### S3.1 Pre-Commit Layer
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/quality/precommit.py       # PreCommitGate
.pre-commit-config.yaml             # Hook config
```

---

#### S3.2 PR Automation Layer
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/quality/pr_automation.py   # PRAutomationGate
```

---

#### S3.3 Human Review Layer
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/quality/human_review.py    # HumanReviewGate
```

---

#### S3.4 Gate Configuration
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/quality/config.py          # GateConfig
config/quality-gates.yaml           # Configuration file
```

---

### Epic 4: Auto-Fix

#### S4.1 Auto-Fix Framework
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/autofix/framework.py       # AutoFixFramework
src/aios/autofix/base.py            # BaseFixer
```

---

#### S4.2 Fix Generators
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/autofix/fixers/xss.py
src/aios/autofix/fixers/injection.py
src/aios/autofix/fixers/secrets.py
```

---

#### S4.3 Bounded Reflexion
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/autofix/reflexion.py       # BoundedReflexion
```

---

### Epic 5: CLI

#### S5.1 CLI Base
**Status:** 0% - NÃO INICIADO
**Prioridade:** ALTA

**Arquivos a criar:**
```
src/aios/cli/main.py                # Main CLI entry point
src/aios/cli/app.py                 # Click application
```

**Comandos:**
- [ ] `aios` - Entry point
- [ ] `aios version` - Versão
- [ ] `aios help` - Ajuda

---

#### S5.2 Agent Commands
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/cli/commands/agent.py      # Agent commands
```

**Comandos:**
- [ ] `aios agent list` - Listar agentes
- [ ] `aios agent info <id>` - Info do agente
- [ ] `aios agent activate <id>` - Ativar agente

---

#### S5.3 Health Status
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/cli/commands/health.py     # Health commands
```

**Comandos:**
- [ ] `aios health` - Status geral
- [ ] `aios health --domain <domain>` - Status por domínio

---

#### S5.4 Claude Integration
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
src/aios/cli/commands/claude.py     # Claude integration
```

**Funcionalidades:**
- [ ] Skill generation para Claude Code
- [ ] Hook generation

---

### Epic 6: Polish

#### S6.1 Documentation
**Status:** 0% - NÃO INICIADO

**Arquivos a criar:**
```
docs/api/README.md
docs/guides/getting-started.md
docs/guides/agent-development.md
```

---

#### S6.2 Performance
**Status:** 0% - NÃO INICIADO

**Tarefas:**
- [ ] Profiling
- [ ] Otimização de imports
- [ ] Cache strategy

---

#### S6.3 Launch Checklist
**Status:** 0% - NÃO INICIADO

**Tarefas:**
- [ ] Checklist de lançamento
- [ ] CI/CD pipeline
- [ ] Release notes

---

## Ordem de Execução Recomendada

### Fase 1: Foundation Completa (P0)
```
1. S1.4 Scope Enforcer      ← CRÍTICO, primeiro a fazer
2. S1.5 Agent Loader        ← Necessário para carregar agentes
3. S1.6 Health Check        ← Diagnóstico do sistema
4. S1.1 CLI Base (parcial)  ← Entry point básico
```

### Fase 2: CLI Funcional (P1)
```
5. S5.1 CLI Base (completo)
6. S5.2 Agent Commands
7. S5.3 Health Status
```

### Fase 3: Security (P1)
```
8. S2.1 Validator Framework
9. S2.2 AST Validators
10. S2.3 Regex Validators
11. S2.4 Orchestration
12. S2.5 Security Reports
```

### Fase 4: Quality & Polish (P2-P3)
```
13. Epic 3 - Quality Gates
14. Epic 4 - Auto-Fix
15. S5.4 Claude Integration
16. Epic 6 - Polish
```

---

## Critérios de Validação

### Para Cada Story
- [ ] Código implementado conforme spec
- [ ] `uv run ruff check src/` sem erros
- [ ] `uv run mypy src/ --strict` sem erros
- [ ] `uv run pytest tests/` passando
- [ ] Coverage mínimo 80%
- [ ] Documentação inline

### Para Epic Completo
- [ ] Todas as stories implementadas
- [ ] Integration tests passando
- [ ] Health check verde
- [ ] Documentação atualizada

---

## Comandos de Validação

```bash
# Lint
uv run ruff check src/

# Type check
uv run mypy src/ --strict

# Tests
uv run pytest tests/ -v --cov=src/aios

# All
uv sync && uv run ruff check src/ && uv run mypy src/ --strict && uv run pytest tests/ -v
```

---

## Notas Importantes

1. **Agent Identity Isolation** - Cada agente é único, NUNCA simular outro
2. **Scope Enforcement** - git_push APENAS para Gage (devops)
3. **Determinismo** - AST > Regex > LLM
4. **Stack** - Python 3.12+, uv, ruff, mypy --strict, pytest, Click, Pydantic v2

---

*Documento gerado por Orion (Master Orchestrator)*
*Referência: docs/projects/neo-aios/epics/*
