# Story 4.3: Bounded Reflexion

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Story 4.2

---

## Objetivo

Implementar sistema de auto-fix com máximo 3 tentativas.

## Tasks

### Task 1: Reflexion Loop

**Arquivo:** `src/aios/autofix/reflexion.py`

Loop que:
1. Tenta fix
2. Valida resultado
3. Se falhou, tenta diferente
4. Máximo 3 tentativas
5. Escala para humano se falhar 3x

### Task 2: Escalation Handler

**Arquivo:** `src/aios/autofix/escalation.py`

Quando fix falha 3x:
- Criar issue
- Notificar humano
- Marcar como "needs-human-review"

### Task 3: Testes

**Arquivo:** `tests/test_autofix/test_reflexion.py`

---

## Bounded Reflexion Flow

```
Finding detected
     ↓
Fix Attempt 1 → Verify → [OK] → Done
     ↓ [FAIL]
Fix Attempt 2 (different approach) → Verify → [OK] → Done
     ↓ [FAIL]
Fix Attempt 3 (last resort) → Verify → [OK] → Done
     ↓ [FAIL]
ESCALATE to human (create issue, notify)
```

## Rules

- **MAX 3 ATTEMPTS** - Never more
- **Each attempt different** - Don't repeat same fix
- **Verify after each** - Run validator again
- **Never loop** - Bounded is key

---

## Validação Final

- [ ] Reflexion loop funcionando
- [ ] Máximo 3 tentativas enforçado
- [ ] Cada tentativa diferente
- [ ] Escalation quando falha
- [ ] Testes com 90%+ coverage

## Notas para Ralph

- CRÍTICO: Nunca loop infinito
- Cada tentativa deve ser substantivamente diferente
- Log todas as tentativas para debugging
- Escalation cria issue no GitHub
