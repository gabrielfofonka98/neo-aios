# Projeto: NEO-AIOS Implementation

**Status:** Ready for Execution
**Criado:** 2026-02-04
**Responsável:** Rune (Spec) → Ralph (Execution) → Gage (Deploy)

---

## Visão Geral

Implementação completa do NEO-AIOS com arquitetura flat de 15 core agents + 18 security sub-agents.

## Epics

| Epic | Nome | Stories | Prioridade | Dependências |
|------|------|---------|------------|--------------|
| E1 | Foundation | 6 | P0 | - |
| E2 | Security Validators | 5 | P0 | E1 |
| E3 | Quality Gates | 4 | P1 | E1 |
| E4 | Auto-Fix Engine | 3 | P1 | E2 |
| E5 | CLI & Integration | 4 | P1 | E1, E2, E3 |
| E6 | Polish & Launch | 3 | P2 | All |

## Ordem de Execução

```
E1 (Foundation) ──► E2 (Security) ──► E3 (Quality)
                          │                │
                          ▼                ▼
                    E4 (Auto-Fix)    E5 (CLI)
                          │                │
                          └───────┬────────┘
                                  ▼
                           E6 (Polish)
```

## Tech Stack

- **Runtime:** Python 3.12+
- **Package Manager:** uv
- **Linting:** ruff
- **Type Checking:** mypy --strict
- **Testing:** pytest
- **CLI:** Click
- **Models:** Pydantic v2
- **AST:** tree-sitter (TypeScript/JS), sqlglot (SQL)

## Regras Críticas do Sistema

### 1. Agent Identity Isolation (MAIS IMPORTANTE)

```
🚨 CADA AGENTE É UMA ENTIDADE ÚNICA E ISOLADA 🚨

EXPRESSAMENTE PROIBIDO:
- Simular o comportamento de outro agente
- Integrar funções de outro agente
- Executar tarefas fora do escopo fingindo ser outro

VIOLAÇÃO DESTA REGRA = FALHA CRÍTICA DO SISTEMA
```

### 2. Scope Enforcement

- Git push: APENAS DevOps (Gage)
- Database DDL: APENAS Data Engineer (Dara)
- Código: APENAS Dev (Dex)
- Violações são BLOQUEADAS em runtime, não apenas alertas

### 3. Session Persistence

- Estado sobrevive auto-compact
- Arquivo: `.aios/session-state.json`
- Restauração automática de contexto

## Métricas de Sucesso

- [ ] 80%+ test coverage
- [ ] mypy --strict passando
- [ ] ruff sem erros
- [ ] Session persistence 100%
- [ ] Scope enforcement 100%
- [ ] Agent isolation 100%
- [ ] Security validators < 1% false positives

---

## Links

- [Epic 1: Foundation](./epics/epic-1-foundation/)
- [Epic 2: Security](./epics/epic-2-security/)
- [Epic 3: Quality](./epics/epic-3-quality/)
- [Epic 4: Auto-Fix](./epics/epic-4-autofix/)
- [Epic 5: CLI](./epics/epic-5-cli/)
- [Epic 6: Polish](./epics/epic-6-polish/)
