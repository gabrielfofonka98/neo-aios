# Story 2.2: AST Validators

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Story 2.1

---

## Objetivo

Implementar os 9 validators baseados em AST usando tree-sitter.

## AST Validators (9)

1. **sec-xss-hunter** - XSS detection (DOM manipulation, script injection)
2. **sec-injection-detector** - SQL/ORM injection
3. **sec-jwt-auditor** - JWT vulnerabilities
4. **sec-rls-guardian** - Supabase RLS
5. **sec-api-access-tester** - BOLA/BFLA
6. **sec-validation-enforcer** - Input validation
7. **sec-upload-validator** - File upload
8. **sec-redirect-checker** - Open redirect
9. **sec-error-leak-detector** - Info leakage

## Tasks

### Task 1: Setup tree-sitter

**Arquivo:** `src/aios/security/ast/parser.py`

Criar parser AST usando tree-sitter para TypeScript/JavaScript.

### Task 2: XSS Hunter

**Arquivo:** `src/aios/security/validators/xss_hunter.py`

Detectar:
- DOM manipulation inseguro
- Script injection vectors
- href injection com javascript:

### Task 3: Injection Detector

**Arquivo:** `src/aios/security/validators/injection_detector.py`

Detectar:
- Prisma raw queries sem parameterização
- Template strings com SQL
- Supabase queries não sanitizadas

### Task 4: JWT Auditor

**Arquivo:** `src/aios/security/validators/jwt_auditor.py`

Detectar:
- jwt.decode sem verify
- Algorithm confusion
- Token storage inseguro

### Task 5-9: Demais Validators

Seguir mesmo padrão para os validators restantes.

---

## Validação Final

- [ ] tree-sitter funcionando
- [ ] 9 AST validators implementados
- [ ] Registrados no validator_registry
- [ ] Testes com 85%+ coverage

## Notas para Ralph

- Usar tree-sitter para parsing preciso
- AST é mais confiável que regex para código
- Confidence score para reduzir false positives
- Sempre incluir CWE IDs
