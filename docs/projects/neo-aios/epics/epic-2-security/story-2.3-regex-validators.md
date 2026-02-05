# Story 2.3: Regex Validators

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Story 2.1

---

## Objetivo

Implementar os 9 validators baseados em regex/pattern matching.

## Regex Validators (9)

10. **sec-secret-scanner** - Hardcoded secrets, API keys, tokens
11. **sec-cors-csrf-checker** - CORS misconfiguration, CSRF issues
12. **sec-header-inspector** - CSP, security headers validation
13. **sec-rate-limit-tester** - Missing rate limiting
14. **sec-framework-scanner** - CVE detection in dependencies
15. **sec-supply-chain-monitor** - npm audit, dependency vulnerabilities
16. **sec-deploy-auditor** - Vercel/deployment security
17. **sec-client-exposure-scanner** - Client-side data exposure
18. **sec-ai-code-reviewer** - AI-generated code security review

## Tasks

### Task 1: Secret Scanner

**Arquivo:** `src/aios/security/validators/secret_scanner.py`

Detectar:
- API keys hardcoded
- AWS credentials
- Database connection strings
- NEXT_PUBLIC_ misuse

### Task 2: Header Inspector

**Arquivo:** `src/aios/security/validators/header_inspector.py`

Validar:
- Content-Security-Policy
- X-Frame-Options
- HSTS
- Outras security headers

### Task 3-9: Demais Validators

Seguir mesmo padrão para os validators restantes.

---

## Validação Final

- [ ] 9 regex validators implementados
- [ ] Secrets são REDACTADOS nos reports
- [ ] Exemplos não são flaggeados (reduce false positives)
- [ ] Testes com 85%+ coverage

## Notas para Ralph

- Regex deve ser case-insensitive onde faz sentido
- SEMPRE redactar secrets nos reports
- Ignorar exemplos óbvios (your_api_key, example, test)
