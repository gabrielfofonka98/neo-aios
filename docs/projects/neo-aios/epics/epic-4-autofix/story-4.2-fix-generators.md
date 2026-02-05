# Story 4.2: Fix Generators

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Story 4.1

---

## Objetivo

Implementar fixers específicos para cada tipo de vulnerability.

## Tasks

### Task 1: XSS Fixers

**Arquivo:** `src/aios/autofix/fixers/xss.py`

- Escape HTML output
- Sanitize with DOMPurify
- Replace dangerous patterns

### Task 2: Injection Fixers

**Arquivo:** `src/aios/autofix/fixers/injection.py`

- Parameterize SQL queries
- Add Prisma.sql`` wrapper

### Task 3: Input Validation Fixers

**Arquivo:** `src/aios/autofix/fixers/validation.py`

- Add Zod schemas
- Inject runtime validation

### Task 4: Testes

**Arquivo:** `tests/test_autofix/test_fixers.py`

---

## Fixer Categories

1. **Security Fixes** - XSS, injection, auth
2. **Code Quality** - Imports, types, unused vars
3. **Style Fixes** - Formatting via ruff

---

## Validação Final

- [ ] XSS fixers
- [ ] Injection fixers
- [ ] Validation fixers
- [ ] Testes com 85%+ coverage
