# PRD - NEO-AIOS: Agent Intelligence Operating System

**Versao:** 2.0.0
**Data:** 2026-02-04
**Autor:** Morgan (Product Manager Agent) + Orion (Master Orchestrator)
**Status:** Draft
**Arquitetura:** Flat Orchestration (15 Core Agents + 18 Security Sub-agents)

---

## Indice

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Non-Goals](#3-goals--non-goals)
4. [User Personas](#4-user-personas)
5. [User Stories](#5-user-stories)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Technical Architecture](#8-technical-architecture)
9. [Agent Catalog](#9-agent-catalog)
10. [Delegation Matrix](#10-delegation-matrix)
11. [Approval Workflows](#11-approval-workflows)
12. [Operational Workflows](#12-operational-workflows) ← **NEW**
13. [Integration Points](#13-integration-points)
14. [Success Metrics](#14-success-metrics)
15. [Risks & Mitigations](#15-risks--mitigations)
16. [Milestones & Phases](#16-milestones--phases)
17. [Open Questions](#17-open-questions)

---

## 1. Executive Summary

### 1.1 Visao Geral

NEO-AIOS (Next Evolution Operating Intelligence System) e um sistema de agentes inteligentes que simula uma organizacao de tecnologia completa, com hierarquia clara, escopo definido, e governanca automatica. O sistema combina:

1. **SynkraAI/aios-core** - Framework original de orquestracao de agentes
2. **aios-next** - Sistema Python com validators, fixers, quality gates (793 testes, 31 agentes)
3. **Estrutura Big Tech** - Hierarquia organizacional inspirada em Google, Meta, Amazon

### 1.2 Proposta de Valor

| Aspecto | Valor Entregue |
|---------|----------------|
| **Governanca** | Scope enforcement em runtime (nao sugestao, bloqueio) |
| **Qualidade** | 18 validators de seguranca AST-based (zero false positives) |
| **Autonomia** | Auto-fix engine com bounded reflexion (max 3 tentativas) |
| **Persistencia** | Session state sobrevive auto-compact do Claude Code |
| **Orquestracao Flat** | 15 core agents + 18 security sub-agents, coordenados por Orion |
| **Determinismo** | AST-based detection, nao vibes-based |

### 1.3 Principios Fundamentais

```
1. DETERMINISMO    -> AST-based, nao vibes-based
2. ENFORCED        -> Scope violations sao bloqueados, nao sugeridos
3. PERSISTENT      -> Session state sobrevive context resets
4. FLAT ORCHESTRATION -> Orion coordena todos, sem hierarquia complexa
5. BOUNDED         -> Reflexion loops com limite (max 3 tentativas)
6. SECURITY FIRST  -> 18 sub-agents de seguranca sao inegociaveis
```

---

## 2. Problem Statement

### 2.1 Contexto Atual

Sistemas de agentes de IA atuais sofrem de:

| Problema | Impacto | Exemplo |
|----------|---------|---------|
| **Falta de hierarquia** | Agentes atuam como pares, sem delegacao clara | Dev e QA competem pelo mesmo escopo |
| **Scope creep** | Agentes ultrapassam seus limites sem controle | Architect escreve codigo |
| **Vibes-based detection** | Falsos positivos em seguranca | Regex detecta "password" em comentarios |
| **Session loss** | Contexto perdido apos auto-compact | Agente esquece quem e apos 30min |
| **Infinite loops** | Fix tenta indefinidamente | Auto-fix roda 100x sem sucesso |
| **No governance** | Qualquer agente pode fazer qualquer coisa | Dev faz git push sem review |

### 2.2 Gaps Identificados

```
SISTEMAS ATUAIS                    NEO-AIOS
----------------                   --------
Agentes desorganizados         ->  Orion coordena 15 core + 18 security
Scope por convencao            ->  Scope enforced em runtime
Regex-based security           ->  AST-based (tree-sitter + sqlglot)
Context volatil                ->  Session persistence file-based
Loops infinitos                ->  Bounded reflexion (max 3)
Quality gates manuais          ->  3-layer automatizado
Seguranca ad-hoc               ->  18 sub-agents especializados (Quinn)
```

### 2.3 Impacto do Problema

- **Produtividade:** 40% do tempo gasto em retrabalho por scope creep
- **Seguranca:** False positives geram alert fatigue
- **Continuidade:** Session loss forca re-explicar contexto
- **Qualidade:** Sem gates, bugs chegam em producao

---

## 3. Goals & Non-Goals

### 3.1 Goals (In Scope)

| # | Goal | Metric | Target |
|---|------|--------|--------|
| G1 | Hierarquia de agentes funcional | Agentes organizados em 5 niveis | 50+ agentes |
| G2 | Scope enforcement em runtime | Violacoes bloqueadas | 100% |
| G3 | Security validators AST-based | False positive rate | < 1% |
| G4 | Session persistence | Sobrevive auto-compact | 100% |
| G5 | Auto-fix bounded | Max tentativas por issue | 3 |
| G6 | Quality gates | 3 camadas operacionais | pre-commit, PR, human |
| G7 | Health check engine | Dominios monitorados | 5 |
| G8 | CLI completo | Comandos para toda hierarquia | 100% coverage |

### 3.2 Non-Goals (Out of Scope)

| # | Non-Goal | Razao |
|---|----------|-------|
| NG1 | GUI/Dashboard web | MVP e CLI-first |
| NG2 | Multi-tenancy | Foco em single-user/team |
| NG3 | Cloud hosting do sistema | Roda local com Claude Code |
| NG4 | Integracao com outros LLMs | Focado em Claude |
| NG5 | Real-time collaboration | Um operador por vez |
| NG6 | Mobile app | Desktop-first |

### 3.3 Future Scope (v2.0+)

- Dashboard web para visualizacao de metricas
- Multi-agent parallelism real
- Integration com Jira/Linear
- Suporte a outros LLMs

---

## 4. User Personas

### 4.1 Persona Principal: Solo Developer / Small Team Lead

**Nome:** Gabriel (Tech Lead)
**Contexto:** Desenvolvedor full-stack que usa Claude Code diariamente
**Necessidades:**
- Sistema que mantem contexto entre sessoes
- Governanca automatica sem overhead
- Security checks que nao geram noise
- Delegacao clara entre "agentes mentais"

**Pain Points Atuais:**
- Claude esquece contexto apos auto-compact
- Precisa re-explicar arquitetura toda sessao
- Security tools com muitos falsos positivos
- Nao tem estrutura para decisions em times

### 4.2 Persona Secundaria: Startup CTO

**Nome:** Carlos (CTO)
**Contexto:** CTO de startup early-stage com 3-5 devs
**Necessidades:**
- Framework para organizar trabalho de IA
- Quality gates antes de merge
- Visibility sobre o que agentes fizeram
- Padronizacao de workflows

**Pain Points Atuais:**
- Cada dev usa IA de forma diferente
- Sem audit trail de decisoes
- Inconsistencia em code style
- Review manual de todo codigo IA

### 4.3 Persona Terciaria: Enterprise Architect

**Nome:** Marina (Enterprise Architect)
**Contexto:** Arquiteta em grande empresa avaliando AI tooling
**Necessidades:**
- Compliance e governance
- Integracao com toolchain existente
- Metricas de qualidade
- Controle de escopo

**Pain Points Atuais:**
- IA generativa sem guardrails
- Risco de shadow IT com Claude
- Dificuldade de medir ROI
- Preocupacoes de seguranca

---

## 5. User Stories

### 5.1 Gestao de Sessao

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| US-001 | Como usuario, quero que o sistema lembre qual agente estava ativo apos auto-compact | Session state persiste em arquivo JSON |
| US-002 | Como usuario, quero ativar agentes com comandos simples (/dev, /architect) | Todos os agentes tem comando de ativacao |
| US-003 | Como usuario, quero desativar agente e voltar ao Claude padrao | Comando /clear-agent funciona |
| US-004 | Como usuario, quero handoff documentado ao fim de sessao | Documento gerado em docs/sessions/YYYY-MM/ |

### 5.2 Hierarquia e Delegacao

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| US-010 | Como CTO (agente), quero delegar para VPs sem codar | CTO nao pode executar Write em arquivos .py/.ts/.js |
| US-011 | Como VP, quero aprovar/rejeitar decisions de Directors | Approval workflow funciona |
| US-012 | Como Dev, quero receber tasks apenas de meu escopo | Tasks fora de escopo sao recusadas |
| US-013 | Como DevOps, quero ser o UNICO que pode git push | Push bloqueado para outros agentes |

### 5.3 Qualidade e Seguranca

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| US-020 | Como Dev, quero que security scan rode automaticamente | Pre-commit hook executa validators |
| US-021 | Como QA, quero orquestrar 18 sub-agentes de seguranca | Quinn pode dispatch parallel |
| US-022 | Como usuario, quero auto-fix bounded | Max 3 tentativas, depois escala |
| US-023 | Como usuario, quero quality gates em 3 camadas | pre-commit, PR, human review |

### 5.4 Desenvolvimento

| ID | Story | Acceptance Criteria |
|----|-------|---------------------|
| US-030 | Como Dev, quero trabalhar em stories definidas | Story files em docs/projects/{project}/epics/{epic}/ |
| US-031 | Como Dev, quero update apenas sections autorizadas | Outros sections sao read-only |
| US-032 | Como usuario, quero commits convencionais | Conventional commits enforced |
| US-033 | Como usuario, quero staging-first deploy | Merge para staging antes de production |

---

## 6. Functional Requirements

### 6.1 Arquitetura Flat de Agentes

#### 6.1.1 Estrutura de Orquestracao

NEO-AIOS usa **orquestracao flat** em vez de hierarquia complexa. Um unico Master (Orion) coordena todos os 15 core agents.

```
                        ┌─────────────┐
                        │   ORION     │
                        │   (Master)  │
                        └──────┬──────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
    ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐
    │   PRODUTO   │     │ ENGENHARIA  │     │  QUALIDADE  │
    │  (4 agents) │     │  (5 agents) │     │  (3 + 18)   │
    │             │     │             │     │             │
    │ Morgan (PM) │     │ Dex (Dev)   │     │ Quinn (Sec) │
    │ Aria (Arch) │     │ Gage (DevOps│     │ Codex (Code)│
    │ Pixel (UX)  │     │ Ops (SRE)   │     │ Tess (Func) │
    │ Rune (Spec) │     │ Sage (Doc)  │     │             │
    │             │     │ Ralph (Auto)│     │ + 18 sub-ag │
    └─────────────┘     └─────────────┘     └─────────────┘
           │
    ┌──────┴──────┐
    │    DADOS    │
    │  (2 agents) │
    │             │
    │ Dara (DE)   │
    │ Oracle (DA) │
    └─────────────┘
```

#### 6.1.2 Principios da Orquestracao Flat

| Principio | Descricao |
|-----------|-----------|
| **Single Point of Contact** | Usuario fala com Orion, agentes se organizam |
| **Scope Enforcement** | Acoes fora de escopo sao BLOQUEADAS em runtime |
| **Especializacao Clara** | Cada agente tem funcao bem definida |
| **18 Security Agents** | Seguranca e critica, nao negociavel |

#### 6.1.3 Scope Enforcement

```python
# src/aios/agents/scope_enforcer.py

class ScopeEnforcer:
    """Enforce scope rules at runtime for flat orchestration."""

    SCOPE_RULES = {
        "master": {
            "can": ["coordinate", "delegate", "monitor"],
            "cannot": ["execute_tasks_directly"]
        },
        "pm": {
            "can": ["prd", "stories", "prioritize"],
            "cannot": ["code", "architecture", "deploy"]
        },
        "architect": {
            "can": ["architecture", "rfc", "adr", "tech_decisions"],
            "cannot": ["code", "deploy"]
        },
        "dev": {
            "can": ["code", "test", "commit"],
            "cannot": ["push_to_remote", "architecture_decision"]  # CRITICAL
        },
        "devops": {
            "can": ["push_to_remote", "create_pr", "deploy", "ci_cd"],
            "cannot": ["write_feature_code"]
        },
        "qa-sec": {
            "can": ["security_audit", "orchestrate_sub_agents"],
            "cannot": ["code", "code_quality_review"]
        },
        "qa-code": {
            "can": ["code_review", "quality_gates"],
            "cannot": ["security_audit"]
        },
        "qa-func": {
            "can": ["test_plan", "e2e_tests", "bug_reports"],
            "cannot": ["security_audit", "code"]
        }
    }

    def check_permission(self, agent_id: str, action: str) -> bool:
        """Return True if agent can perform action."""
        rules = self.SCOPE_RULES.get(agent_id, {})
        if action in rules.get("cannot", []):
            return False
        return action in rules.get("can", [])
```

### 6.2 Sistema de Agentes

#### 6.2.1 Estrutura de Definicao (SKILL.md)

```yaml
# agents/{tier}/{agent-id}/SKILL.md

agent:
  name: Dex
  id: dev
  tier: ic
  level: core
  title: Full Stack Developer
  icon: "ic"

scope:
  can:
    - implement_stories
    - write_tests
    - debug_code
    - refactor
    - git_add
    - git_commit
    - git_diff
  cannot:
    - git_push           # Only DevOps
    - architecture       # Only Architect
    - database_ddl       # Only Data Engineer
    - approve_merge      # Only Manager+

reports_to: engineering_manager
collaborates_with:
  - qa_code
  - devops
  - data_engineer

commands:
  - name: develop
    description: Implement story tasks
  - name: test
    description: Run tests
  - name: exit
    description: Exit agent mode
```

#### 6.2.2 Registry de Agentes

```python
# src/aios/agents/registry.py

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

@dataclass
class AgentDefinition:
    id: str
    name: str
    tier: str  # c-level, vp, director, manager, ic
    level: str  # core, security, specialist, content
    scope_can: List[str]
    scope_cannot: List[str]
    reports_to: Optional[str]
    skill_path: Path

class AgentRegistry:
    """Central registry of all agents."""

    def __init__(self, agents_dir: Path):
        self.agents: dict[str, AgentDefinition] = {}
        self._load_agents(agents_dir)

    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        return self.agents.get(agent_id)

    def get_by_tier(self, tier: str) -> List[AgentDefinition]:
        return [a for a in self.agents.values() if a.tier == tier]

    def can_delegate_to(self, from_id: str, to_id: str) -> bool:
        """Check if agent can delegate to another."""
        from_agent = self.get(from_id)
        to_agent = self.get(to_id)

        tier_order = ["c-level", "vp", "director", "manager", "ic"]
        from_idx = tier_order.index(from_agent.tier)
        to_idx = tier_order.index(to_agent.tier)

        return to_idx > from_idx  # Can only delegate down
```

### 6.3 Security Validators

#### 6.3.1 Arquitetura de Validators

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SECURITY VALIDATOR PIPELINE                      │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  AST-Based  │    │ Regex-Based │    │  Hybrid     │             │
│  │  (6 validators) │  (10 validators)│  (2 validators) │             │
│  │             │    │             │    │             │             │
│  │ tree-sitter │    │ Pattern     │    │ AST + Regex │             │
│  │ sqlglot     │    │ Matching    │    │ Combined    │             │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘             │
│         │                  │                  │                     │
│         └──────────────────┼──────────────────┘                     │
│                            ▼                                        │
│                    ┌───────────────┐                               │
│                    │   FINDINGS    │                               │
│                    │   COLLECTOR   │                               │
│                    └───────┬───────┘                               │
│                            ▼                                        │
│                    ┌───────────────┐                               │
│                    │   SEVERITY    │                               │
│                    │   CALCULATOR  │                               │
│                    │ (compound     │                               │
│                    │  detection)   │                               │
│                    └───────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

#### 6.3.2 Lista de Validators

| # | Validator ID | Tipo | Dominio | Ferramenta |
|---|--------------|------|---------|------------|
| 01 | sec-rls-guardian | AST | Supabase RLS | sqlglot |
| 02 | sec-framework-scanner | Hybrid | Next.js CVEs | semver + regex |
| 03 | sec-xss-hunter | AST | Cross-Site Scripting | tree-sitter |
| 04 | sec-api-access-tester | AST | BOLA/BFLA | tree-sitter |
| 05 | sec-jwt-auditor | AST | JWT Security | tree-sitter |
| 06 | sec-secret-scanner | Regex | Secrets/Env | entropy + patterns |
| 07 | sec-cors-csrf-checker | Regex | CORS/CSRF | pattern matching |
| 08 | sec-injection-detector | AST | SQL Injection | sqlglot |
| 09 | sec-validation-enforcer | AST | Zod/TypeScript | tree-sitter |
| 10 | sec-supply-chain-monitor | Hybrid | npm deps | npm audit + checks |
| 11 | sec-upload-validator | Regex | File Upload | magic bytes |
| 12 | sec-header-inspector | Regex | CSP Headers | pattern matching |
| 13 | sec-client-exposure-scanner | AST | Client Data | tree-sitter |
| 14 | sec-rate-limit-tester | Regex | Rate Limiting | pattern matching |
| 15 | sec-redirect-checker | AST | Open Redirect | tree-sitter |
| 16 | sec-error-leak-detector | Regex | Error Leaks | pattern matching |
| 17 | sec-deploy-auditor | Hybrid | Vercel Deploy | config analysis |
| 18 | sec-ai-code-reviewer | AST | Vibecoding | tree-sitter |

#### 6.3.3 Compound Vulnerability Detection

```python
# src/aios/validators/compound_detector.py

COMPOUND_RULES = [
    {
        "agents": ["sec-xss-hunter", "sec-header-inspector"],
        "condition": "xss_found AND no_csp",
        "escalation": "CRITICAL",
        "reason": "XSS sem CSP = exploit garantido"
    },
    {
        "agents": ["sec-api-access-tester", "sec-rate-limit-tester"],
        "condition": "missing_auth AND no_rate_limit",
        "escalation": "CRITICAL",
        "reason": "API aberta + sem rate limit = abuso em massa"
    },
    {
        "agents": ["sec-secret-scanner", "sec-client-exposure-scanner"],
        "condition": "secrets_in_code AND source_maps_enabled",
        "escalation": "CRITICAL",
        "reason": "Secrets + source maps = chave na mao do atacante"
    },
    {
        "agents": ["sec-rls-guardian", "sec-secret-scanner"],
        "condition": "service_role_exposed AND rls_disabled",
        "escalation": "CRITICAL",
        "reason": "service_role sem RLS = acesso total ao banco"
    },
    {
        "agents": ["sec-validation-enforcer", "sec-ai-code-reviewer"],
        "condition": "no_zod_validation AND high_any_count",
        "escalation": "HIGH",
        "reason": "Sem validacao runtime + any types = input nao confiavel"
    },
    {
        "agents": ["sec-redirect-checker", "sec-api-access-tester"],
        "condition": "open_redirect AND client_only_auth",
        "escalation": "CRITICAL",
        "reason": "Redirect + auth so no client = phishing completo"
    },
    {
        "agents": ["sec-jwt-auditor", "sec-cors-csrf-checker"],
        "condition": "jwt_in_localstorage AND cors_misconfigured",
        "escalation": "CRITICAL",
        "reason": "Token acessivel via XSS + CORS aberto = session hijack"
    },
    {
        "agents": ["sec-injection-detector", "sec-error-leak-detector"],
        "condition": "raw_queries AND verbose_errors",
        "escalation": "CRITICAL",
        "reason": "SQL injection + erro detalhado = exfiltracao de schema"
    },
    {
        "agents": ["sec-framework-scanner", "sec-deploy-auditor"],
        "condition": "vulnerable_framework AND dangerous_deploy",
        "escalation": "CRITICAL",
        "reason": "Framework vulneravel + deploy forcado = RCE em producao"
    }
]
```

### 6.4 Auto-Fix Engine

#### 6.4.1 Bounded Reflexion

```python
# src/aios/fixers/engine.py

from dataclasses import dataclass
from typing import Optional
from enum import Enum

class FixResult(Enum):
    FIXED = "fixed"
    PARTIAL = "partial"
    FAILED = "failed"
    ESCALATED = "escalated"

@dataclass
class FixAttempt:
    iteration: int
    action: str
    result: FixResult
    error: Optional[str] = None

class AutoFixEngine:
    """Auto-fix engine with bounded reflexion."""

    MAX_ITERATIONS = 3

    def fix(self, finding: Finding) -> FixResult:
        """Attempt to fix a finding with bounded iterations."""
        attempts: List[FixAttempt] = []

        for i in range(self.MAX_ITERATIONS):
            attempt = self._try_fix(finding, i + 1, attempts)
            attempts.append(attempt)

            if attempt.result == FixResult.FIXED:
                return FixResult.FIXED

            if attempt.result == FixResult.FAILED:
                # Different strategy next iteration
                continue

        # Max iterations reached, escalate
        self._escalate(finding, attempts)
        return FixResult.ESCALATED

    def _try_fix(
        self,
        finding: Finding,
        iteration: int,
        previous_attempts: List[FixAttempt]
    ) -> FixAttempt:
        """Single fix attempt with learning from previous."""
        strategy = self._select_strategy(finding, iteration, previous_attempts)

        try:
            result = strategy.execute(finding)
            return FixAttempt(iteration, strategy.name, result)
        except Exception as e:
            return FixAttempt(iteration, strategy.name, FixResult.FAILED, str(e))

    def _escalate(self, finding: Finding, attempts: List[FixAttempt]):
        """Escalate to human after max iterations."""
        # Create escalation record
        # Notify appropriate agent (Manager or above)
        pass
```

### 6.5 Quality Gates

#### 6.5.1 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       QUALITY GATES PIPELINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  LAYER 1: PRE-COMMIT (Local)                                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐               │
│  │  ruff   │  │  mypy   │  │ pytest  │  │ security│               │
│  │ (lint)  │  │ (types) │  │ (test)  │  │ (quick) │               │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘               │
│       │           │            │            │                       │
│       └───────────┴────────────┴────────────┘                       │
│                         │                                           │
│                    [GATE 1]                                         │
│                    Must pass                                        │
│                         │                                           │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  LAYER 2: PR AUTOMATION (CI)                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │ CodeRabbit  │  │  QA Agent   │  │ Security    │                │
│  │   Review    │  │   Review    │  │   Full      │                │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│         │                │                │                         │
│         └────────────────┴────────────────┘                         │
│                         │                                           │
│                    [GATE 2]                                         │
│                    Must pass                                        │
│                         │                                           │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  LAYER 3: HUMAN REVIEW                                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Tech Lead / Manager                       │   │
│  │                       Sign-off                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                         │                                           │
│                    [GATE 3]                                         │
│                    Approval                                         │
│                         │                                           │
│                         ▼                                           │
│                    [MERGE]                                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 6.5.2 Gate Configuration

```yaml
# .aios-core/core/quality-gates/quality-gate-config.yaml

gates:
  layer_1_precommit:
    enabled: true
    blocking: true
    checks:
      - name: ruff
        command: "uv run ruff check src/"
        severity: error
      - name: mypy
        command: "uv run mypy --strict src/"
        severity: error
      - name: pytest
        command: "uv run pytest tests/ -x"
        severity: error
      - name: security_quick
        command: "uv run aios security --quick"
        severity: warning

  layer_2_pr:
    enabled: true
    blocking: true
    checks:
      - name: coderabbit
        type: external_service
        config:
          auto_review: true
          severity_filter: [critical, high]
      - name: qa_agent
        type: agent_dispatch
        agent: qa-code
        command: "*review"
      - name: security_full
        type: agent_dispatch
        agent: qa
        command: "*security-audit"

  layer_3_human:
    enabled: true
    blocking: true
    required_approvers:
      - role: tech_lead
        count: 1
      - role: manager
        count: 1
        conditions:
          - path_pattern: "src/aios/security/*"
          - path_pattern: "config/*"
```

### 6.6 Health Check Engine

#### 6.6.1 Monitored Domains

```python
# src/aios/healthcheck/domains.py

class HealthDomain:
    """Health check domains."""

    DOMAINS = {
        "session": {
            "checks": [
                "session_state_valid",
                "active_agent_exists",
                "session_not_expired"
            ],
            "interval_seconds": 60
        },
        "agents": {
            "checks": [
                "all_agents_registered",
                "scope_rules_loaded",
                "delegation_matrix_valid"
            ],
            "interval_seconds": 300
        },
        "validators": {
            "checks": [
                "tree_sitter_loaded",
                "sqlglot_available",
                "all_validators_operational"
            ],
            "interval_seconds": 300
        },
        "quality": {
            "checks": [
                "ruff_installed",
                "mypy_installed",
                "pytest_installed"
            ],
            "interval_seconds": 600
        },
        "infrastructure": {
            "checks": [
                "git_available",
                "uv_installed",
                "python_version_valid"
            ],
            "interval_seconds": 600
        }
    }
```

#### 6.6.2 Self-Healing Actions

```python
# src/aios/healthcheck/healing.py

HEALING_ACTIONS = {
    "session_state_invalid": {
        "action": "reset_session_state",
        "auto": True,
        "max_attempts": 3
    },
    "agent_not_registered": {
        "action": "reload_agent_registry",
        "auto": True,
        "max_attempts": 2
    },
    "tree_sitter_not_loaded": {
        "action": "reinstall_tree_sitter",
        "auto": False,  # Requires user confirmation
        "escalate_to": "devops"
    },
    "git_not_available": {
        "action": "notify_user",
        "auto": True,
        "message": "Git not found in PATH. Please install Git."
    }
}
```

### 6.7 CLI Commands

#### 6.7.1 Command Structure

```
aios
├── agent
│   ├── activate <agent-id>    # Activate agent
│   ├── deactivate             # Deactivate current agent
│   ├── list                   # List all agents
│   ├── status                 # Current agent status
│   └── hierarchy              # Show hierarchy tree
│
├── security
│   ├── audit                  # Full security audit
│   ├── audit --quick          # Quick scan
│   ├── audit --domain <dom>   # Domain-specific
│   ├── report                 # Generate report
│   └── findings <severity>    # Show findings
│
├── quality
│   ├── check                  # Run all quality checks
│   ├── gate --layer <1|2|3>   # Run specific gate
│   └── report                 # Generate quality report
│
├── fix
│   ├── auto <finding-id>      # Auto-fix specific finding
│   ├── all                    # Auto-fix all fixable
│   └── report                 # Show fix attempts
│
├── session
│   ├── status                 # Current session info
│   ├── save                   # Save session state
│   ├── restore                # Restore from file
│   └── handoff                # Generate handoff doc
│
├── healthcheck
│   ├── run                    # Run all health checks
│   ├── domain <domain>        # Check specific domain
│   └── heal                   # Attempt self-healing
│
└── config
    ├── show                   # Show current config
    ├── validate               # Validate config files
    └── reset                  # Reset to defaults
```

#### 6.7.2 CLI Implementation

```python
# src/aios/cli/main.py

import click
from aios.agents import AgentRegistry
from aios.validators import SecurityPipeline
from aios.quality import QualityGates

@click.group()
@click.version_option()
def cli():
    """NEO-AIOS: Agent Intelligence Operating System."""
    pass

@cli.group()
def agent():
    """Agent management commands."""
    pass

@agent.command()
@click.argument("agent_id")
def activate(agent_id: str):
    """Activate an agent by ID."""
    registry = AgentRegistry()
    agent = registry.get(agent_id)

    if not agent:
        click.echo(f"Agent '{agent_id}' not found.", err=True)
        raise SystemExit(1)

    # Write session state
    session = Session.current()
    session.activate_agent(agent)
    session.save()

    click.echo(f"{agent.icon} {agent.name} ({agent.title}) activated.")

@cli.group()
def security():
    """Security audit commands."""
    pass

@security.command()
@click.option("--quick", is_flag=True, help="Quick scan only")
@click.option("--domain", help="Specific domain to scan")
def audit(quick: bool, domain: str):
    """Run security audit."""
    pipeline = SecurityPipeline()

    if quick:
        results = pipeline.run_quick()
    elif domain:
        results = pipeline.run_domain(domain)
    else:
        results = pipeline.run_full()

    click.echo(results.summary())

if __name__ == "__main__":
    cli()
```

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Metric | Target | Rationale |
|--------|--------|-----------|
| Agent activation | < 500ms | User experience |
| Security quick scan | < 30s | Pre-commit usability |
| Security full audit | < 5min | CI time budget |
| Session restore | < 100ms | Auto-compact recovery |
| CLI command response | < 200ms | Interactive feel |

### 7.2 Scalability

| Dimension | Target | Approach |
|-----------|--------|----------|
| Codebase size | 500K+ LOC | Parallel scanning |
| Agent count | 100+ | Lazy loading |
| Concurrent checks | 18 | Async pipeline |
| History depth | 1 year | Rolling cleanup |

### 7.3 Security

| Requirement | Implementation |
|-------------|----------------|
| Credentials never in code | .env + credentials.yaml (gitignored) |
| Scope enforcement | Runtime blocking, not suggestions |
| Audit trail | All agent actions logged |
| Least privilege | Agents only have required permissions |

### 7.4 Reliability

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| Session persistence | 100% | File-based state |
| Health check | 5 domains | Auto-healing |
| Fix bounded | Max 3 | Escalation after |
| Graceful degradation | Yes | Fallback modes |

### 7.5 Maintainability

| Requirement | Implementation |
|-------------|----------------|
| Test coverage | 80%+ (793 tests baseline) |
| Type safety | mypy --strict |
| Code style | ruff (auto-formatted) |
| Documentation | Inline + docs/ |

---

## 8. Technical Architecture

### 8.1 Folder Structure

```
neo-aios/
├── src/aios/                    # Python source
│   ├── __init__.py
│   ├── agents/                  # Agent system
│   │   ├── __init__.py
│   │   ├── registry.py          # Agent registry
│   │   ├── loader.py            # SKILL.md loader
│   │   └── dispatcher.py        # Agent dispatch
│   │
│   ├── hierarchy/               # NEW: Big Tech hierarchy
│   │   ├── __init__.py
│   │   ├── levels.py            # Tier definitions
│   │   ├── scope_enforcer.py    # Permission checks
│   │   └── delegation.py        # Delegation rules
│   │
│   ├── governance/              # NEW: Approval chains
│   │   ├── __init__.py
│   │   ├── approvals.py         # Approval workflows
│   │   └── audit_log.py         # Action logging
│   │
│   ├── validators/              # Security validators
│   │   ├── __init__.py
│   │   ├── base.py              # Base validator
│   │   ├── ast_validators/      # AST-based (6)
│   │   │   ├── xss_hunter.py
│   │   │   ├── rls_guardian.py
│   │   │   └── ...
│   │   ├── regex_validators/    # Regex-based (10)
│   │   │   ├── secret_scanner.py
│   │   │   └── ...
│   │   ├── compound_detector.py # Compound vulns
│   │   └── pipeline.py          # Orchestration
│   │
│   ├── fixers/                  # Auto-fix engine
│   │   ├── __init__.py
│   │   ├── engine.py            # Bounded reflexion
│   │   ├── strategies/          # Fix strategies
│   │   └── escalation.py        # Escalation logic
│   │
│   ├── quality/                 # Quality gates
│   │   ├── __init__.py
│   │   ├── gates.py             # 3-layer gates
│   │   ├── checks/              # Individual checks
│   │   └── reports.py           # Report generation
│   │
│   ├── healthcheck/             # Health monitoring
│   │   ├── __init__.py
│   │   ├── domains.py           # 5 domains
│   │   ├── checks.py            # Individual checks
│   │   └── healing.py           # Self-healing
│   │
│   ├── context/                 # Session management
│   │   ├── __init__.py
│   │   ├── session.py           # Session state
│   │   └── persistence.py       # File-based persistence
│   │
│   ├── cli/                     # Click CLI
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point
│   │   ├── agent_commands.py
│   │   ├── security_commands.py
│   │   └── ...
│   │
│   ├── orchestration/           # Workflow engine
│   ├── api/                     # Internal API
│   ├── config/                  # Config loading
│   ├── development/             # Dev utilities
│   ├── elicitation/             # User interaction
│   ├── findings/                # Finding models
│   ├── hooks/                   # Pre-commit hooks
│   ├── infrastructure/          # Infra utilities
│   ├── manifest/                # Manifest handling
│   ├── mcp/                     # MCP integration
│   ├── pipeline/                # Pipeline utilities
│   ├── registry/                # General registry
│   ├── sandbox/                 # Docker sandbox
│   ├── security/                # Security utilities
│   ├── staging/                 # Staging utilities
│   └── templates/               # Template engine
│
├── agents/                      # Agent definitions (SKILL.md) - FLAT STRUCTURE
│   ├── orion/                   # Master Orchestrator
│   │   └── SKILL.md
│   ├── morgan/                  # PM
│   │   └── SKILL.md
│   ├── aria/                    # Architect
│   │   └── SKILL.md
│   ├── pixel/                   # Design
│   │   └── SKILL.md
│   ├── rune/                    # Spec
│   │   └── SKILL.md
│   ├── dex/                     # Dev
│   │   └── SKILL.md
│   ├── gage/                    # DevOps (ONLY PUSH)
│   │   └── SKILL.md
│   ├── ops/                     # SRE
│   │   └── SKILL.md
│   ├── sage/                    # Documentation
│   │   └── SKILL.md
│   ├── ralph/                   # Autonomous
│   │   └── SKILL.md
│   ├── dara/                    # Data Engineer
│   │   └── SKILL.md
│   ├── oracle/                  # Data Analyst
│   │   └── SKILL.md
│   ├── quinn/                   # Security QA (orchestrates 18)
│   │   └── SKILL.md
│   ├── codex/                   # Code QA
│   │   └── SKILL.md
│   ├── tess/                    # Functional QA
│   │   └── SKILL.md
│   └── security/                # 18 Security Sub-agents
│       ├── sec-rls-guardian/
│       ├── sec-xss-hunter/
│       ├── sec-api-access-tester/
│       └── ... (18 sub-agents)
│
├── .aios-core/                  # Framework (read-only)
│   ├── core/
│   │   ├── quality-gates/
│   │   └── ...
│   └── development/
│       ├── tasks/
│       ├── templates/
│       └── checklists/
│
├── .aios-custom/                # Project overlay (editable)
│   ├── config/
│   │   ├── core-config.yaml
│   │   ├── deployment-strategy.yaml
│   │   └── credentials.yaml
│   ├── STANDARDS.md
│   ├── workflows/
│   └── scripts/
│
├── .claude/                     # Claude Code integration
│   ├── skills/                  # Skill definitions
│   ├── hooks/                   # Governance hooks
│   └── rules/                   # Restriction rules
│
├── .aios/                       # Runtime state
│   └── session-state.json
│
├── config/                      # YAML configs
├── tests/                       # Test suite
├── docs/                        # Documentation
│   ├── PRD.md                   # This document
│   ├── architecture/
│   ├── projects/
│   │   └── {project}/
│   │       ├── prd.md
│   │       └── epics/
│   ├── sessions/
│   │   └── YYYY-MM/
│   └── security/
│
├── bin/                         # Scripts
├── scripts/                     # Utility scripts
├── pyproject.toml               # Project config
├── ANALYSIS.md                  # Analysis document
└── README.md
```

### 8.2 Module Dependencies

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MODULE DEPENDENCY GRAPH                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                           ┌─────────┐                               │
│                           │   CLI   │                               │
│                           └────┬────┘                               │
│                                │                                     │
│         ┌──────────────────────┼──────────────────────┐             │
│         │                      │                      │             │
│         ▼                      ▼                      ▼             │
│   ┌───────────┐         ┌───────────┐         ┌───────────┐        │
│   │  Agents   │         │ Security  │         │  Quality  │        │
│   └─────┬─────┘         └─────┬─────┘         └─────┬─────┘        │
│         │                     │                     │               │
│         ├─────────────────────┼─────────────────────┤               │
│         │                     │                     │               │
│         ▼                     ▼                     ▼               │
│   ┌───────────┐         ┌───────────┐         ┌───────────┐        │
│   │ Hierarchy │         │Validators │         │   Gates   │        │
│   └─────┬─────┘         └─────┬─────┘         └─────┬─────┘        │
│         │                     │                     │               │
│         └──────────┬──────────┴──────────┬──────────┘               │
│                    │                     │                          │
│                    ▼                     ▼                          │
│             ┌───────────┐         ┌───────────┐                    │
│             │  Context  │         │   Fixers  │                    │
│             └─────┬─────┘         └─────┬─────┘                    │
│                   │                     │                          │
│                   └──────────┬──────────┘                          │
│                              │                                      │
│                              ▼                                      │
│                       ┌───────────┐                                │
│                       │  Config   │                                │
│                       └───────────┘                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

DEPENDENCIES:
- CLI depends on: Agents, Security, Quality
- Agents depends on: Hierarchy, Context
- Security depends on: Validators, Fixers
- Quality depends on: Gates, Checks
- Hierarchy depends on: Config
- Validators depends on: tree-sitter, sqlglot
- All depend on: Config, Context
```

### 8.3 Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  USER INPUT                                                          │
│      │                                                               │
│      ▼                                                               │
│  ┌─────────┐                                                        │
│  │   CLI   │ ─────────────────────────────────────┐                │
│  └────┬────┘                                      │                │
│       │                                           │                │
│       ▼                                           ▼                │
│  ┌─────────────┐                          ┌─────────────┐         │
│  │   Command   │                          │   Session   │         │
│  │   Parser    │                          │    State    │         │
│  └──────┬──────┘                          │   (.json)   │         │
│         │                                  └──────┬──────┘         │
│         ▼                                         │                │
│  ┌─────────────┐                                 │                │
│  │   Router    │◄────────────────────────────────┘                │
│  └──────┬──────┘                                                   │
│         │                                                          │
│    ┌────┴────┬────────┬────────┬────────┐                         │
│    ▼         ▼        ▼        ▼        ▼                         │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                     │
│ │Agent │ │Secur │ │Qual  │ │Health│ │Config│                     │
│ │System│ │ity   │ │ity   │ │Check │ │      │                     │
│ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──────┘                     │
│    │        │        │        │                                    │
│    │        ▼        │        │                                    │
│    │   ┌─────────┐   │        │                                    │
│    │   │Pipeline │   │        │                                    │
│    │   │ (18     │   │        │                                    │
│    │   │agents)  │   │        │                                    │
│    │   └────┬────┘   │        │                                    │
│    │        │        │        │                                    │
│    │        ▼        │        │                                    │
│    │   ┌─────────┐   │        │                                    │
│    │   │Findings │   │        │                                    │
│    │   └────┬────┘   │        │                                    │
│    │        │        │        │                                    │
│    │        ▼        │        │                                    │
│    │   ┌─────────┐   │        │                                    │
│    │   │Compound │   │        │                                    │
│    │   │Detector │   │        │                                    │
│    │   └────┬────┘   │        │                                    │
│    │        │        │        │                                    │
│    └────────┴────────┴────────┘                                    │
│             │                                                       │
│             ▼                                                       │
│      ┌───────────┐                                                 │
│      │  Report   │                                                 │
│      │ Generator │                                                 │
│      └─────┬─────┘                                                 │
│            │                                                        │
│            ▼                                                        │
│       OUTPUT                                                        │
│  (terminal / file)                                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Agent Catalog

> **Arquitetura:** Flat Orchestration com 15 Core Agents + 18 Security Sub-agents

### 9.1 Visao Geral

```
                        ┌─────────────┐
                        │   ORION     │
                        │   (Master)  │
                        └──────┬──────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
    ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐
    │   PRODUTO   │     │ ENGENHARIA  │     │  QUALIDADE  │
    │  (4 agents) │     │  (5 agents) │     │  (3 + 18)   │
    └─────────────┘     └─────────────┘     └─────────────┘
           │                                       │
    ┌──────┴──────┐                         ┌──────┴──────┐
    │    DADOS    │                         │   SECURITY  │
    │  (2 agents) │                         │ (18 sub-ag) │
    └─────────────┘                         └─────────────┘
```

### 9.2 Os 15 Core Agents

| Categoria | Nome | ID | Icon | Funcao | Tipo |
|-----------|------|-----|------|--------|------|
| **CORE** | Orion | `master` | 🌟 | Orquestra tudo, ponto unico de contato | Orchestrator |
| **PRODUTO** | Morgan | `pm` | 📊 | PRDs, stories, priorizacao | Generalista |
| | Aria | `architect` | 🏛️ | Arquitetura, RFCs, decisoes tecnicas | Especialista |
| | Pixel | `design` | 🎨 | UX/UI, design system, prototipos | Generalista |
| | Rune | `spec` | ⚔️ | Specs ultra-detalhados pro Ralph | Generalista |
| **ENGENHARIA** | Dex | `dev` | ⚡ | Codigo, testes, commits | Especialista |
| | Gage | `devops` | 🔥 | Push, PR, deploy, CI/CD (**UNICO push**) | Especialista |
| | Ops | `sre` | 📡 | Monitoring, alertas, incidentes, SLO | Especialista |
| | Sage | `doc` | 📚 | Documentacao tecnica | Generalista |
| | Ralph | `ralph` | 🤖 | Execucao autonoma ate completar | Especialista |
| **DADOS** | Dara | `data-eng` | 🔷 | Schema, migrations, pipelines, SQL | Especialista |
| | Oracle | `analyst` | 📈 | Analises, dashboards, metricas | Generalista |
| **QUALIDADE** | Quinn | `qa-sec` | 🛡️ | Security audit, orquestra 18 sub-agents | Especialista |
| | Codex | `qa-code` | 📝 | Code review, quality gates | Especialista |
| | Tess | `qa-func` | 🧪 | Testes funcionais, E2E, test plans | Especialista |

### 9.3 18 Security Sub-Agents (Orquestrados por Quinn)

#### AST-Based (6 agentes)

| # | ID | Dominio | Ferramenta |
|---|-----|---------|------------|
| 01 | sec-rls-guardian | Supabase RLS | sqlglot |
| 02 | sec-xss-hunter | Cross-Site Scripting | tree-sitter |
| 03 | sec-api-access-tester | BOLA/BFLA | tree-sitter |
| 04 | sec-jwt-auditor | JWT Security | tree-sitter |
| 05 | sec-injection-detector | SQL/ORM Injection | sqlglot |
| 06 | sec-validation-enforcer | Zod/TypeScript | tree-sitter |

#### Regex-Based (12 agentes)

| # | ID | Dominio |
|---|-----|---------|
| 07 | sec-secret-scanner | Secrets & Env Vars |
| 08 | sec-cors-csrf-checker | CORS & CSRF |
| 09 | sec-header-inspector | CSP & Headers |
| 10 | sec-client-exposure-scanner | Client-Side Exposure |
| 11 | sec-rate-limit-tester | Rate Limiting & DoS |
| 12 | sec-redirect-checker | Open Redirect |
| 13 | sec-error-leak-detector | Error & Info Leak |
| 14 | sec-deploy-auditor | Vercel Deployment |
| 15 | sec-upload-validator | File Upload |
| 16 | sec-supply-chain-monitor | npm Supply Chain |
| 17 | sec-framework-scanner | Next.js/React CVEs |
| 18 | sec-ai-code-reviewer | AI/Vibecoding Code |

### 9.4 Scope Rules

| Agente | Pode | Nao Pode |
|--------|------|----------|
| **Orion** | Coordenar, delegar, monitorar | Executar tarefas direto |
| **Morgan** | PRD, stories, priorizacao | Codigo, arquitetura |
| **Aria** | Arquitetura, RFC, ADR | Codigo, deploy |
| **Pixel** | Design, prototipos, handoff | Codigo |
| **Rune** | Specs detalhados | Codigo, deploy |
| **Dex** | Codigo, testes, commit | **Git push** |
| **Gage** | **Git push, PR, deploy** (UNICO) | Escrever codigo de feature |
| **Ops** | SLOs, runbooks, postmortems | Codigo |
| **Sage** | Documentacao | Codigo, deploy |
| **Ralph** | Execucao autonoma | Push, decisoes de arquitetura |
| **Dara** | Schema, migrations, SQL | Push |
| **Oracle** | Analises, dashboards | Codigo, deploy |
| **Quinn** | Security audit | Code quality |
| **Codex** | Code review, quality gates | Security |
| **Tess** | Testes funcionais, E2E | Security |

### 9.5 Regra de Ouro: Git Push

**APENAS Gage pode fazer `git push`.**

Esta regra e enforced em runtime pelo ScopeEnforcer. Qualquer outro agente que tentar push tera a acao BLOQUEADA.

---

## 10. Collaboration Matrix

### 10.1 Orquestracao Flat

Na arquitetura flat, Orion coordena todos os agentes. Nao ha hierarquia rigida de delegacao - ha especializacao.

```
                     ┌─────────┐
                     │  ORION  │
                     │ (coord) │
                     └────┬────┘
                          │
    ┌─────────┬───────┬───┴───┬───────┬─────────┐
    ▼         ▼       ▼       ▼       ▼         ▼
 PRODUTO  ENGENHARIA DADOS QUALIDADE SPEC    AUTO
 Morgan   Dex        Dara  Quinn     Rune    Ralph
 Aria     Gage       Oracle Codex
 Pixel    Ops              Tess
          Sage
```

### 10.2 Colaboracao entre Agentes

| Scenario | Primary | Colabora Com |
|----------|---------|--------------|
| Feature development | Dex (Dev) | Codex, Gage, Dara |
| Security audit | Quinn (Sec) | 18 security sub-agents |
| Database migration | Dara (DE) | Dex, Gage |
| Production deploy | Gage (DevOps) | Quinn, Codex, Tess |
| Architecture decision | Aria (Arch) | Morgan, Dex |
| Spec creation | Rune (Spec) | Morgan, Aria |
| Test plan | Tess (Func QA) | Codex, Dex |
| Autonomous execution | Ralph | Rune (spec source) |
| Incident response | Ops (SRE) | Gage, Dex |
| Data analysis | Oracle (Analyst) | Dara, Morgan |

### 10.3 Fluxo de Trabalho Tipico

```
[Usuario] → [Orion] → [Classifica demanda]
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   [Produto]         [Engenharia]       [Qualidade]
   Morgan define     Dex implementa     Quinn + Codex
   Aria arquiteta    Gage deploya       revisam
   Pixel desenha     Ops monitora       Tess testa
   Rune especifica   Ralph executa
```

---

## 11. Approval Workflows

### 11.1 Code Change Approval (3-Layer Quality Gates)

```
┌───────────────────────────────────────────────────────────────────┐
│                    CODE CHANGE APPROVAL FLOW                       │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Dex (Dev) cria codigo                                             │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐                                                  │
│  │ Pre-commit  │ Layer 1: ruff + mypy + pytest                    │
│  │   Hooks     │                                                  │
│  └──────┬──────┘                                                  │
│         │                                                          │
│    [PASS?]                                                        │
│    │    │                                                          │
│   YES   NO ──► FIX and retry                                      │
│    │                                                               │
│    ▼                                                               │
│  Dex commits locally                                               │
│         │                                                          │
│         ▼                                                          │
│  Gage (DevOps) creates PR ← UNICO que pode push                   │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────┐                                                  │
│  │ PR Checks   │ Layer 2: CodeRabbit + Codex + Quinn              │
│  └──────┬──────┘                                                  │
│         │                                                          │
│    [PASS?]                                                        │
│    │    │                                                          │
│   YES   NO ──► FIX and re-push (Gage)                             │
│    │                                                               │
│    ▼                                                               │
│  ┌─────────────┐                                                  │
│  │   Human     │ Layer 3: Sign-off required                       │
│  │   Review    │                                                  │
│  └──────┬──────┘                                                  │
│         │                                                          │
│   [APPROVED?]                                                     │
│    │    │                                                          │
│   YES   NO ──► REQUEST CHANGES                                    │
│    │                                                               │
│    ▼                                                               │
│  MERGE to staging (Gage)                                           │
│         │                                                          │
│         ▼                                                          │
│  Tess (Functional QA) validates                                    │
│         │                                                          │
│   [PASS?]                                                         │
│    │    │                                                          │
│   YES   NO ──► ROLLBACK (Gage)                                    │
│    │                                                               │
│    ▼                                                               │
│  MERGE to main + Deploy (Gage)                                     │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### 11.2 Architecture Decision Approval

```
┌───────────────────────────────────────────────────────────────────┐
│                ARCHITECTURE DECISION FLOW                          │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Aria (Architect) proposes change                                  │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────────────────────────────────┐                      │
│  │ Architecture Decision Record (ADR)       │                      │
│  │ - Context                                │                      │
│  │ - Decision                               │                      │
│  │ - Consequences                           │                      │
│  │ - Alternatives considered                │                      │
│  └────────────────┬────────────────────────┘                      │
│                   │                                                │
│                   ▼                                                │
│        Morgan (PM) reviews impact                                  │
│                   │                                                │
│                   ▼                                                │
│         Orion coordena aprovacao                                   │
│                   │                                                │
│           [APPROVED?]                                              │
│            │      │                                                │
│           YES    NO ──► Aria revisa                               │
│            │                                                       │
│            ▼                                                       │
│     Dex implementa                                                 │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### 11.3 Database Schema Approval

```
┌───────────────────────────────────────────────────────────────────┐
│                DATABASE SCHEMA CHANGE FLOW                         │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  Dara (Data Engineer) proposes schema change                       │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────────────────────────────────┐                      │
│  │ SQL Proposal Document                    │                      │
│  │ - CREATE/ALTER/DROP statements           │                      │
│  │ - Impact analysis                        │                      │
│  │ - Rollback plan                          │                      │
│  │ - Migration script                       │                      │
│  └────────────────┬────────────────────────┘                      │
│                   │                                                │
│                   ▼                                                │
│  ┌─────────────────────────────────────────┐                      │
│  │ SQL Governance Hook                      │                      │
│  │ (BLOCKS until approval)                  │                      │
│  └────────────────┬────────────────────────┘                      │
│                   │                                                │
│                   ▼                                                │
│  Aria (Architect) reviews schema design                            │
│         │                                                          │
│   [APPROVED?]                                                     │
│    │    │                                                          │
│   YES   NO ──► Dara revisa                                        │
│    │                                                               │
│    ▼                                                               │
│  Execute on STAGING first (Gage)                                   │
│         │                                                          │
│         ▼                                                          │
│  Tess validates                                                    │
│         │                                                          │
│   [PASS?]                                                         │
│    │    │                                                          │
│   YES   NO ──► ROLLBACK (Gage)                                    │
│    │                                                               │
│    ▼                                                               │
│  Execute on PRODUCTION (Gage)                                      │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

---

## 12. Operational Workflows

> **Documento Detalhado:** Ver [docs/WORKFLOWS.md](./WORKFLOWS.md) para workflows completos com templates e artefatos.

### 12.1 Visao Geral do Fluxo End-to-End

```
Ideia → Discovery → Design → Planning → Development → QA → Deploy → Monitor → Learn
         (PM)      (Design)   (PM+Eng)    (Devs)      (QA)  (DevOps)  (SRE)   (Data)
```

### 12.2 Mapeamento de Workflows por Agente

| Agente | Workflow | Artefatos Produzidos |
|--------|----------|---------------------|
| **Morgan (PM)** | Discovery → Define → Prioritize → Spec → Grooming → Planning → Acompanha → Learn | PRD, User Stories, Priorizacao |
| **Pixel (Design)** | Entender → Divergir → Convergir → Prototipar → Handoff → Teste → Iterate | Design Spec, Wireframes, Prototipos, Handoff |
| **Aria (Tech Lead)** | Entender → Design Tecnico → Quebrar → Delegar → Acompanhar → Deploy Review → Retro | RFC, ADR, Task Breakdown |
| **Dex (Dev)** | Pegar Task → Entender → Codar → Testes → PR → Code Review → Merge → Monitor | Codigo, PRs, Testes |
| **Quinn (Security QA)** | Analisar → Orquestrar 18 sub-agents → Coletar → Validar → Reportar | Security Findings, Audit Report |
| **Codex (Code QA)** | Analisar → Criar Casos → Executar → Reportar → Track → Validar → Regress → Sign-off | Test Plan, Test Cases, Bug Reports |
| **Gage (DevOps)** | CI Setup → CD Setup → IaC → Monitor → Deploy → Incident → Postmortem | CI/CD Pipeline, Terraform, Runbooks, Postmortems |
| **Dara (Data Eng)** | Entender → Modelar → Implement DDL → Pipeline → Deploy → Monitor → Optimize | Schema, Migrations, Pipelines |
| **Oracle (Analyst)** | Receber → Explorar → Analisar → Apresentar → A/B Test → Recomendar → Iterar | Analises SQL, A/B Reports, Dashboards |

### 12.3 Input/Output Matrix

| Agente | Input Principal | Output Principal | Decisoes que Toma |
|--------|-----------------|------------------|-------------------|
| **Morgan** | Dados, pesquisa, estrategia | PRD, Stories, Priorizacao | O que construir, por que |
| **Pixel** | PRD, pesquisa | Designs, Prototipos, Specs | Como se parece, fluxos |
| **Aria** | PRD, Design | RFC, Task breakdown, Arquitetura | Como construir |
| **Dex** | Tasks, RFC | Codigo, PRs, APIs, UI | Implementacao |
| **Quinn** | Codigo | Security audit, findings | Vulnerabilidades |
| **Codex** | PRD, Design, Codigo | Test cases, Bug reports | Qualidade de codigo |
| **Gage** | Codigo aprovado | CI/CD, Infra, Deploy | Como entregar |
| **Dara** | Requisitos de dados | Schema, Migrations, Pipelines | Estrutura de dados |
| **Oracle** | Perguntas de negocio | Analises, Dashboards | Insights de dados |

### 12.4 Handoff Protocols

#### PM → Tech Lead

```
Entrega do PM:
- [ ] PRD completo e aprovado
- [ ] User stories com criterios de aceite
- [ ] Priorizacao definida
- [ ] Metricas de sucesso definidas

Aceite do Tech Lead:
- [ ] PRD revisado tecnicamente
- [ ] Viabilidade confirmada
- [ ] RFC iniciado (se necessario)
```

#### Tech Lead → Devs

```
Entrega do Tech Lead:
- [ ] RFC aprovado (se houver)
- [ ] Tasks quebradas e estimadas
- [ ] Dependencias mapeadas
- [ ] Arquitetura documentada

Aceite do Dev:
- [ ] Tasks entendidas
- [ ] Ambiente configurado
- [ ] Branch criado
```

#### Dev → QA

```
Entrega do Dev:
- [ ] Codigo completo
- [ ] Testes unitarios passando
- [ ] PR criado com descricao
- [ ] Deploy em staging

Aceite do QA:
- [ ] PR revisado
- [ ] Casos de teste prontos
- [ ] Timeline acordado
```

#### QA → DevOps

```
Entrega do QA:
- [ ] Todos os testes passando
- [ ] Bugs P0/P1 resolvidos
- [ ] Sign-off documentado
- [ ] Aprovacao para deploy

Aceite do DevOps:
- [ ] PR aprovado
- [ ] Pipeline verde
- [ ] Rollback plan confirmado
```

### 12.5 Artefatos Padrao por Papel

#### PRD Template (PM)

```markdown
# Feature: [Nome]

## Problema
[Descricao com dados]

## Hipotese
Se [acao], entao [resultado].

## Metricas de Sucesso
- Primaria: [Metrica] ([Target])
- Secundaria: [Metrica] ([Target])

## Escopo
### In Scope
- [Item]

### Out of Scope
- [Item] (v2)

## User Stories
[Lista]

## Riscos e Dependencias
- [Lista]

## Timeline
- Design: X semanas
- Dev: Y semanas
- QA: Z semana
```

#### RFC Template (Tech Lead)

```markdown
# RFC: [Titulo]

## Status: [Draft | Em Review | Aceito]
## Autor: @[autor]

## Contexto
[Descricao]. PRD: [link]

## Decisao
[Decisao tecnica]

## Alternativas Consideradas
### Opcao A (escolhida)
- Pros/Cons

### Opcao B
- Pros/Cons

## Design Tecnico
[Arquitetura, Schema, Endpoints]

## Riscos e Mitigacoes
[Tabela]

## Rollout Plan
[Fases]
```

#### PR Template (Dev)

```markdown
## Descricao
[O que foi implementado]

## Ticket
[JIRA-XXXX]

## Tipo de mudanca
- [ ] Nova feature
- [ ] Bugfix
- [ ] Refactor

## Como testar
[Passos]

## Checklist
- [ ] Testes passando
- [ ] Sem secrets hardcoded
- [ ] Documentacao atualizada
```

#### Bug Report Template (QA)

```markdown
## BUG-XXX: [Titulo]

**Severidade**: [P0 | P1 | P2 | P3]
**Ambiente**: [Staging | Prod]

### Steps to Reproduce
1. [Passo]

### Resultado Atual
[Comportamento]

### Resultado Esperado
[Comportamento]

### Impacto
[% usuarios afetados]
```

### 12.6 Cerimônias

| Cerimonia | Frequencia | Participantes | Objetivo |
|-----------|------------|---------------|----------|
| Sprint Planning | Bi-semanal | PM, TL, Devs, QA | Definir sprint backlog |
| Daily | Diaria | Squad | Sincronizacao |
| Refinement | Semanal | PM, TL, Devs | Detalhar stories |
| Sprint Review | Bi-semanal | Squad + Stakeholders | Demo + feedback |
| Retro | Bi-semanal | Squad | Melhoria continua |
| Design Review | Por feature | Design, TL, Dev | Validar designs |
| Architecture Review | Por RFC | Aria + Directors | Validar arquitetura |

---

## 13. Integration Points

### 13.1 External Tools

| Tool | Integration | Purpose |
|------|-------------|---------|
| Claude Code | Primary runtime | Agent execution environment |
| Git | Version control | Code versioning |
| GitHub | Repository | Code hosting, PRs |
| Vercel | Deployment | Hosting, preview deploys |
| Supabase | Database | PostgreSQL, Auth, Storage |
| CodeRabbit | Code review | Automated PR review |

### 13.2 Internal Integrations

| From | To | Protocol |
|------|-----|----------|
| CLI | Agents | Python API |
| Agents | Validators | Function calls |
| Validators | Findings | Pydantic models |
| Quality Gates | CI/CD | Exit codes |
| Health Check | Healing | Event-driven |

### 13.3 MCP Integration Points

```yaml
# .claude/skills/ integration via MCP

mcp_servers:
  - name: git
    purpose: Version control operations
    allowed_for: [devops]

  - name: supabase
    purpose: Database operations
    allowed_for: [data-engineer, dev]

  - name: browser
    purpose: Web testing
    allowed_for: [dev, qa]

  - name: coderabbit
    purpose: Code review
    allowed_for: [qa-code]
```

---

## 14. Success Metrics

### 14.1 KPIs Primarios

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Session persistence rate | 0% | 100% | Sessions recovered after auto-compact |
| Scope violation rate | N/A | 0% | Violations blocked at runtime |
| Security false positive rate | ~20% | < 1% | FP / Total findings |
| Auto-fix success rate | N/A | > 60% | Fixed / Total attempted |
| Quality gate pass rate | N/A | > 90% | Passes / Total runs |

### 14.2 KPIs Secundarios

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent activation time | < 500ms | Avg time to activate |
| Security scan time (quick) | < 30s | Avg quick scan duration |
| Security scan time (full) | < 5min | Avg full audit duration |
| Test coverage | > 80% | Lines covered / Total lines |
| Documentation coverage | 100% | Docs / Total agents |

### 14.3 Health Metrics

| Domain | Metric | Target |
|--------|--------|--------|
| Session | State valid | 100% |
| Agents | All registered | 100% |
| Validators | All operational | 100% |
| Quality | Tools installed | 100% |
| Infrastructure | Dependencies met | 100% |

---

## 15. Risks & Mitigations

### 15.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| tree-sitter incompatibility | Medium | High | Fallback to regex validators |
| Claude Code API changes | Low | High | Abstraction layer for API |
| Performance degradation | Medium | Medium | Lazy loading, caching |
| Session state corruption | Low | High | Automatic backup, recovery |

### 15.2 Product Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| User adoption resistance | Medium | High | Gradual rollout, documentation |
| Learning curve steep | Medium | Medium | Tutorials, examples |
| Over-engineering | High | Medium | MVP-first, iterate |
| Scope creep | High | Medium | Strict PRD adherence |

### 15.3 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Single point of failure | Medium | High | Graceful degradation |
| Configuration complexity | High | Medium | Sensible defaults |
| Debugging difficulty | Medium | Medium | Comprehensive logging |
| Upgrade path unclear | Low | Medium | Version management plan |

---

## 16. Milestones & Phases

### 16.1 Phase 1: Foundation (4 semanas)

**Objetivo:** Core infrastructure funcionando

| Week | Deliverables |
|------|--------------|
| 1 | Project setup (uv, ruff, mypy, pytest) |
| 1 | Folder structure criada |
| 1 | Base classes definidas |
| 2 | Session persistence implementada |
| 2 | Agent registry funcionando |
| 2 | Basic CLI (agent activate/deactivate) |
| 3 | Hierarchy levels definidos |
| 3 | Scope enforcer implementado |
| 3 | 4 core agents (Dex, Gage, Dara, Quinn) |
| 4 | Health check engine (5 domains) |
| 4 | Integration tests |
| 4 | Documentation |

**Exit Criteria:**
- [ ] Ativar agente via CLI funciona
- [ ] Session persiste apos restart
- [ ] Scope enforcement bloqueia violacoes
- [ ] Health check reporta status

### 16.2 Phase 2: Security (4 semanas)

**Objetivo:** 18 validators operacionais

| Week | Deliverables |
|------|--------------|
| 5 | tree-sitter setup |
| 5 | 3 AST validators (XSS, RLS, Injection) |
| 6 | sqlglot setup |
| 6 | 3 AST validators (JWT, API, Client) |
| 7 | 6 regex validators |
| 7 | Compound detector |
| 8 | 4 regex validators |
| 8 | Security pipeline integration |
| 8 | Quinn orchestration |

**Exit Criteria:**
- [ ] 18 validators funcionando
- [ ] Compound detection operacional
- [ ] False positive rate < 5%
- [ ] Full audit < 5 min

### 16.3 Phase 3: Quality (3 semanas)

**Objetivo:** 3-layer quality gates

| Week | Deliverables |
|------|--------------|
| 9 | Pre-commit hooks (ruff, mypy, pytest) |
| 9 | Layer 1 gate funcionando |
| 10 | CodeRabbit integration |
| 10 | QA agent review integration |
| 10 | Layer 2 gate funcionando |
| 11 | Human review workflow |
| 11 | Layer 3 gate funcionando |
| 11 | Quality reports |

**Exit Criteria:**
- [ ] Pre-commit bloqueia codigo ruim
- [ ] PR automation funciona
- [ ] Human approval required
- [ ] Quality reports gerados

### 16.4 Phase 4: Auto-Fix (2 semanas)

**Objetivo:** Bounded reflexion engine

| Week | Deliverables |
|------|--------------|
| 12 | Fix strategies implementadas |
| 12 | Bounded loop (max 3) |
| 13 | Escalation logic |
| 13 | Fix reports |
| 13 | Integration with validators |

**Exit Criteria:**
- [ ] Auto-fix tenta max 3x
- [ ] Escalation funciona
- [ ] Success rate > 50%

### 16.5 Phase 5: Full Hierarchy (3 semanas)

**Objetivo:** 50+ agentes organizados

| Week | Deliverables |
|------|--------------|
| 14 | VP level (5 agents) |
| 14 | Director level (8 agents) |
| 15 | Manager/Lead level (12 agents) |
| 15 | Specialist ICs (10+ agents) |
| 16 | Delegation matrix enforced |
| 16 | Approval workflows |
| 16 | Documentation |

**Exit Criteria:**
- [ ] 50+ agentes registrados
- [ ] Delegation funciona
- [ ] Approval workflows operacionais

### 16.6 Phase 6: Polish & Launch (2 semanas)

**Objetivo:** Production ready

| Week | Deliverables |
|------|--------------|
| 17 | Performance optimization |
| 17 | Bug fixes |
| 17 | Documentation completa |
| 18 | Final testing |
| 18 | Release preparation |
| 18 | Launch |

**Exit Criteria:**
- [ ] All tests pass (80%+ coverage)
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Ready for production use

### 16.7 Timeline Overview

```
        Week 1-4          Week 5-8          Week 9-11
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │  PHASE 1    │   │  PHASE 2    │   │  PHASE 3    │
    │ Foundation  │──►│  Security   │──►│  Quality    │
    │  (4 weeks)  │   │  (4 weeks)  │   │  (3 weeks)  │
    └─────────────┘   └─────────────┘   └─────────────┘
                                               │
                                               ▼
       Week 14-16         Week 12-13      Week 17-18
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │  PHASE 5    │◄──│  PHASE 4    │   │  PHASE 6    │
    │  Hierarchy  │   │  Auto-Fix   │──►│   Polish    │
    │  (3 weeks)  │   │  (2 weeks)  │   │  (2 weeks)  │
    └─────────────┘   └─────────────┘   └─────────────┘
          │                                    │
          └────────────────────────────────────┘
                           │
                           ▼
                      LAUNCH v1.0
                    (18 semanas total)
```

---

## 17. Open Questions

### 17.1 Decisoes Pendentes

| # | Questao | Opcoes | Responsavel | Prazo |
|---|---------|--------|-------------|-------|
| Q1 | Como lidar com agentes que nao existem no registry? | A) Criar dinamicamente B) Error e sugerir C) Fallback para Claude | Architect | Phase 1 |
| Q2 | Qual o limite de profundidade de delegacao? | A) 5 niveis B) Ilimitado C) Configurable | CTO | Phase 1 |
| Q3 | Como sincronizar estado entre multiplas instancias de Claude Code? | A) File lock B) Single instance C) Distributed state | Architect | Phase 2 |
| Q4 | Qual o formato de report de security? | A) Markdown B) JSON C) Ambos | QA Lead | Phase 2 |
| Q5 | Como integrar com IDEs alem do Claude Code? | A) VS Code extension B) LSP C) Out of scope v1 | Architect | Future |

### 17.2 Assuncoes

| # | Assuncao | Risco se Invalida |
|---|----------|-------------------|
| A1 | Claude Code suporta session-state.json indefinidamente | High - redesign necessario |
| A2 | tree-sitter tem bindings Python estaveis | Medium - fallback para regex |
| A3 | Usuarios aceitam hierarquia rigida | Medium - flexibilizar |
| A4 | Performance e aceitavel com 18 validators | Medium - otimizar |
| A5 | Compound detection e util | Low - pode desabilitar |

### 17.3 Dependencies Externas

| Dependency | Status | Risco |
|------------|--------|-------|
| tree-sitter-python | Stable | Low |
| tree-sitter-typescript | Stable | Low |
| sqlglot | Stable | Low |
| Claude Code API | Active development | Medium |
| CodeRabbit API | Stable | Low |
| Vercel API | Stable | Low |

---

## Appendix A: Glossary

| Termo | Definicao |
|-------|-----------|
| Agent | Persona de IA com escopo definido |
| AST | Abstract Syntax Tree - representacao estruturada de codigo |
| Bounded Reflexion | Loop de correcao com limite de tentativas |
| Compound Vulnerability | Vulnerabilidade resultante de multiplos findings |
| Delegation | Passagem de task para nivel inferior |
| Escalation | Passagem de issue para nivel superior |
| Finding | Resultado de security scan |
| Gate | Checkpoint de qualidade |
| IC | Individual Contributor - executor |
| Scope | Conjunto de permissoes de um agente |
| Session | Estado atual de interacao com o sistema |
| Tier | Nivel hierarquico de agente |
| Validator | Componente que detecta vulnerabilidades |

---

## Appendix B: References

- [SynkraAI/aios-core](https://github.com/SynkraAI/aios-core) - Framework original
- [tree-sitter](https://tree-sitter.github.io/tree-sitter/) - Parser generator
- [sqlglot](https://github.com/tobymao/sqlglot) - SQL parser
- [Click](https://click.palletsprojects.com/) - Python CLI framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation

---

## Appendix C: Change Log

| Versao | Data | Autor | Mudancas |
|--------|------|-------|----------|
| 1.0.0 | 2026-02-04 | Morgan | Documento inicial |
| 1.1.0 | 2026-02-04 | Orion | Adicionada Secao 12: Operational Workflows |
| 2.0.0 | 2026-02-04 | Orion | **MAJOR**: Simplificacao para Flat Orchestration (15 core + 18 security sub-agents). Removida hierarquia 5-tier com 50+ agentes. Atualizado Agent Catalog, Folder Structure, Scope Enforcement. |

---

*Documento gerado por Morgan (Product Manager Agent) + Orion (Master Orchestrator)*
*NEO-AIOS: Agent Intelligence Operating System*
*Arquitetura: Flat Orchestration (15 Core + 18 Security)*
*"Never take the lazy path. Do the hard work now."*
