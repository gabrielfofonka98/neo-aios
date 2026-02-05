# Epic 2: Security Validators

**Status:** Ready for Execution
**Prioridade:** P0 (Crítico)
**Dependências:** Epic 1

---

## Objetivo

Implementar os 18 security validators AST-based e regex-based com zero false positives.

## REGRA CRÍTICA

```
🚨 AGENT IDENTITY ISOLATION 🚨
Quinn (QA Security) orquestra os 18 sub-agents.
Cada sub-agent é uma entidade ÚNICA - não pode simular outro.
```

## Stories

| Story | Nome | Complexidade | Status |
|-------|------|--------------|--------|
| S2.1 | Validator Framework | Alta | [ ] Pending |
| S2.2 | AST Validators (9) | Alta | [ ] Pending |
| S2.3 | Regex Validators (9) | Média | [ ] Pending |
| S2.4 | Validator Orchestration | Alta | [ ] Pending |
| S2.5 | Security Report Engine | Média | [ ] Pending |

## 18 Security Sub-Agents

### AST-Based (tree-sitter)
1. **sec-xss-hunter** - XSS detection
2. **sec-injection-detector** - SQL/ORM injection
3. **sec-jwt-auditor** - JWT vulnerabilities
4. **sec-rls-guardian** - Supabase RLS
5. **sec-api-access-tester** - BOLA/BFLA
6. **sec-validation-enforcer** - Input validation
7. **sec-upload-validator** - File upload
8. **sec-redirect-checker** - Open redirect
9. **sec-error-leak-detector** - Info leakage

### Regex/Pattern-Based
10. **sec-secret-scanner** - Hardcoded secrets
11. **sec-cors-csrf-checker** - CORS/CSRF
12. **sec-header-inspector** - Security headers
13. **sec-rate-limit-tester** - Rate limiting
14. **sec-framework-scanner** - CVE detection
15. **sec-supply-chain-monitor** - npm audit
16. **sec-deploy-auditor** - Vercel security
17. **sec-client-exposure-scanner** - Client-side exposure
18. **sec-ai-code-reviewer** - AI-generated code review

## Ordem de Execução

```
S2.1 (Framework) → S2.2 (AST) → S2.3 (Regex) → S2.4 (Orchestration) → S2.5 (Reports)
```

## Definition of Done

- [ ] 18 validators implementados
- [ ] < 1% false positives
- [ ] Quinn pode orquestrar todos
- [ ] Relatórios consolidados
- [ ] Testes com 85%+ coverage
