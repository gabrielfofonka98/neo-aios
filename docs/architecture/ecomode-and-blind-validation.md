# Ecomode & Blind Validation

**Author:** Dex (Dev Agent)
**Date:** 2026-02-06
**Status:** Active
**Type:** Architecture Decision Record

---

## Overview

Este documento descreve dois patterns de otimização implementados no NEO-AIOS:

1. **Ecomode** — Modo econômico para redução de 30-50% no consumo de tokens
2. **Blind Validation** — Validação de código sem viés de confirmação

Ambos são inspirados em projetos open-source de referência:
- Ecomode ← `oh-my-claudecode` (roteamento agressivo para Haiku)
- Blind Validation ← `zeroshot` (validação sem contexto do desenvolvedor)

---

## 1. Ecomode (Economic Mode)

### 1.1 Problema

Usar Opus 4.6 para TODAS as tarefas é caro e desnecessário. Tasks simples (clear-agent, handoff, test runner) não precisam de deep reasoning, mas pagamos preço premium.

### 1.2 Solução

Roteamento agressivo baseado em complexidade:
- **Haiku** → Tasks determinísticas, leitura-only, sem reasoning
- **Sonnet** → Tasks text-heavy, documentação, specs simples
- **Opus** → APENAS quando deep reasoning é crítico

### 1.3 Decisões de Design

| Aspecto | Decisão | Rationale |
|---------|---------|-----------|
| **Quality gates** | Mantidos em TODOS os níveis | Economia NUNCA compromete qualidade |
| **Security** | 18 sec-agents sempre Haiku | São scanners read-only, já otimizados |
| **Architect** | SEMPRE Opus | Arquitetura = zero-compromisso |
| **Dev (Dex)** | Opus para critical, Sonnet para simple | Contextual downgrade |
| **PM/Doc** | Sonnet | Text-heavy, não reasoning-heavy |

### 1.4 Ativação

**Config:** `.aios-custom/config/ecomode.yaml`

```yaml
ecomode:
  enabled: false  # Toggle global
```

**Keywords mid-session:**
- Ativar: `@eco`, `ecomode`, `modo econômico`
- Desativar: `@full`, `fullmode`, `modo completo`

### 1.5 Savings Esperados

```
Cenário: Sprint típico (40 tasks)
  Normal: 15 Opus + 10 Sonnet + 15 Haiku
  Ecomode: 8 Opus + 17 Sonnet + 15 Haiku

  Redução: ~35% de custos (mantendo qualidade)
```

### 1.6 Trade-offs

| Benefício | Custo |
|-----------|-------|
| 30-50% redução de custos | Precisa configurar model routing |
| Mesma qualidade final | Output pode ser mais terse |
| Mantém todos os quality gates | Requires explicit activation |

---

## 2. Blind Validation

### 2.1 Problema

**Confirmation bias em code review:**

```
Developer: "Eu escolhi X porque Y faz sentido no contexto Z."
Reviewer: *lê explicação* "Faz sentido mesmo!" → APPROVE

Problema: Código pode estar ERRADO mas a explicação convence.
```

### 2.2 Solução

Validator recebe:
- ✅ Source code
- ✅ Requirements (story/task)
- ✅ Quality standards (STANDARDS.md)
- ❌ Developer's conversation history
- ❌ Developer's reasoning/decisions
- ❌ Implementation notes

Resultado: Validação OBJETIVA contra requirements, não contra explicações.

### 2.3 Workflow

```
1. Developer (Dex) implementa feature
   ↓ (conversation context = 100K tokens)

2. Code committed → Layer 1 quality gate
   ↓ (ruff, mypy, pytest)

3. PR created → Blind Validation triggered
   ↓

4. Validator (Codex/Quinn/Tess) recebe:
   - Code diff
   - Story requirements
   - STANDARDS.md
   - Test results (pass/fail only)

   NÃO recebe:
   - Chat history com Dex
   - "Eu escolhi X porque..."
   - Tentativas anteriores

5. Validator valida OBJETIVAMENTE:
   ✓ Code atende acceptance criteria?
   ✓ Code segue STANDARDS.md?
   ✓ Code passa quality gates?

6. Validator responde:
   - APPROVE | REQUEST_CHANGES | REJECT
   - Findings (structured, objective)
```

### 2.4 Validators por Categoria

| Categoria | Validator | Model | Valida |
|-----------|-----------|-------|--------|
| Code Quality | Codex (qa-code) | Opus | Style, types, errors, maintainability |
| Security | Quinn (qa) | Opus | Vulnerabilities, auth, secrets, input validation |
| Functional | Tess (qa-functional) | Sonnet | Acceptance criteria, edge cases, integration |
| Architecture | Aria (architect) | Opus | ADR adherence, patterns, coupling, consistency |

### 2.5 Quando Aplicar

**SEMPRE blind:**
- PR review (padrão)
- Security audit
- Layer 2 quality gate
- Architecture review

**NUNCA blind:**
- Hotfix (urgência > processo)
- Documentation-only (sem código)
- Config changes (contexto ajuda)

### 2.6 Exemplo Real

**Scenario:** Validation de input antes de SQL query

**Traditional (context-aware):**
```
Dev: "Estou usando parameterized queries, então não precisa validar input."
Reviewer: *vê explicação* "Parameterized queries previnem SQL injection, APPROVE."
```

**Blind (context-free):**
```
Requirement: "Validate user input before database query"
Code: No validation presente
Validator: "No input validation found. REJECT per STANDARDS.md section 8.2"
```

Resultado: Blind validation FORÇA conformidade objetiva, independent de "explicações".

### 2.7 Trade-offs

| Benefício | Custo |
|-----------|-------|
| Elimina confirmation bias | Pode parecer "frio" (sem empatia com dev) |
| Validação objetiva | Overhead de setup (extract clean context) |
| Catch mais issues | Pode gerar false positives (sem contexto) |
| Melhora quality over time | Requires disciplina do processo |

---

## 3. Integração dos Dois Patterns

**Ecomode + Blind Validation trabalham juntos:**

```
1. Ecomode reduz custos no DESENVOLVIMENTO
   (Dev usando Sonnet para tasks simples)

2. Blind Validation garante QUALIDADE no REVIEW
   (Validator usando Opus para reasoning crítico)

Resultado: Economia onde possível + Rigor onde necessário
```

**Config files:**
- `.aios-custom/config/ecomode.yaml`
- `.aios-custom/config/blind-validation.yaml`

**Quality gates:**
- Ecomode: Mantém TODOS os gates
- Blind Validation: É PARTE do Layer 2 gate

---

## 4. Métricas de Sucesso

### 4.1 Ecomode

```json
{
  "metric": "token_savings",
  "target": "30-50% reduction",
  "baseline": "all-opus sprint",
  "ecomode": "smart-routing sprint",
  "tracks": [
    "token_count_by_model",
    "cost_per_sprint",
    "quality_gate_pass_rate"
  ]
}
```

### 4.2 Blind Validation

```json
{
  "metric": "validation_effectiveness",
  "target": "reduce false-negatives by 40%",
  "baseline": "traditional context-aware review",
  "blind": "context-free review",
  "tracks": [
    "issues_caught_by_blind",
    "false_positive_rate",
    "rework_rate",
    "time_to_validation"
  ]
}
```

---

## 5. Decisões Arquiteturais

### ADR-001: Ecomode não bypassa quality gates

**Decisão:** Ecomode otimiza EXECUTION, não VALIDATION.

**Rationale:**
- Security não pode ser comprometida por economia
- Quality gates são firewall, não opcionais
- Economia vem de routing inteligente, não de cortar cantos

### ADR-002: Blind Validation é padrão para PR review

**Decisão:** Todas as PRs passam por blind validation (Layer 2).

**Rationale:**
- Confirmation bias é problema real em code review
- Validação objetiva melhora qualidade over time
- Overhead é justificável (catch 40% mais issues)

### ADR-003: Validators sempre usam effort adequado

**Decisão:** Blind validation NUNCA downgrades validator model.

**Rationale:**
- Quinn (security) = SEMPRE Opus (reasoning crítico)
- Codex (code quality) = SEMPRE Opus (deep analysis)
- Tess (functional) = Sonnet OK (checklist-based)
- Aria (architecture) = SEMPRE Opus (design decisions)

---

## 6. Futuro

### 6.1 Ecomode v2 (Roadmap)

- [ ] Adaptive routing baseado em task complexity (auto-detect)
- [ ] A/B testing de routing strategies
- [ ] Integration com context limits (prevent bloat)
- [ ] Real-time cost dashboard

### 6.2 Blind Validation v2 (Roadmap)

- [ ] Post-validation learning (track false positives/negatives)
- [ ] Custom validation rules per project
- [ ] Integration com external static analysis tools
- [ ] Automated rework suggestions (não só findings)

---

## 7. Referências

- **oh-my-claudecode:** Ecomode pattern, aggressive haiku routing
- **zeroshot:** Blind validation, context-free review
- **NEO-AIOS effort-levels:** `.claude/rules/effort-levels.md`
- **Quality gates:** `.aios-custom/config/quality-gates.yaml`

---

## 8. Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-06 | Initial implementation | Dex (Dev) |

---

*"Never take the lazy path. Do the hard work now. The shortcut is forbidden."*

**Ecomode** = Smart routing, não shortcuts
**Blind Validation** = Objective review, não confirmação
