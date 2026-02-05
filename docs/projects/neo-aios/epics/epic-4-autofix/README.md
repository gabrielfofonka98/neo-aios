# Epic 4: Auto-Fix Engine

**Status:** Ready for Execution
**Prioridade:** P1
**Dependências:** Epic 2

---

## Objetivo

Implementar o Bounded Reflexion auto-fix engine com máximo 3 tentativas.

## Stories

| Story | Nome | Complexidade | Status |
|-------|------|--------------|--------|
| S4.1 | Auto-Fix Framework | Alta | [ ] Pending |
| S4.2 | Fix Generators | Alta | [ ] Pending |
| S4.3 | Bounded Reflexion | Alta | [ ] Pending |

## Bounded Reflexion

```
Erro Detectado
     ↓
Fix Attempt 1 → Verificar → [OK] → Done
     ↓ [FAIL]
Fix Attempt 2 → Verificar → [OK] → Done
     ↓ [FAIL]
Fix Attempt 3 → Verificar → [OK] → Done
     ↓ [FAIL]
ESCALATE (não auto-fix)
```

### Regras
- Máximo 3 tentativas
- Cada tentativa deve ser diferente
- Se falhar 3x → escalate para humano
- Nunca loop infinito

## Auto-Fixers por Categoria

### Security Fixes
- XSS escaping
- SQL parameterization
- Input validation injection

### Code Quality Fixes
- Import sorting
- Type annotation addition
- Unused variable removal

### Style Fixes
- Formatting (via ruff)
- Naming conventions
- Docstring generation

## Ordem de Execução

```
S4.1 (Framework) → S4.2 (Generators) → S4.3 (Bounded Reflexion)
```

## Definition of Done

- [ ] Auto-fix para issues comuns
- [ ] Bounded reflexion funcionando
- [ ] Máximo 3 tentativas enforçado
- [ ] Escalation para humano
- [ ] Testes com 85%+ coverage
