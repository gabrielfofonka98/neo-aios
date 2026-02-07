# QA Security — Extended Knowledge Base

Loaded on demand via `*kb` command. Not part of activation context.

---

## Full Command Reference

### Core Security
| Command | Description |
|---------|-------------|
| `*help` | Show all commands |
| `*security-audit [--repo=PATH]` | Full 18-agent audit with cross-validation |
| `*security-audit-quick` | Critical checks only (faster) |
| `*security-audit-domain {domain}` | Targeted: rls, framework, xss, api, jwt, secrets, cors, injection, validation, supply-chain, upload, headers, client-exposure, rate-limit, redirect, error-leak, deploy, ai-code |

### Results & Reports
| Command | Description |
|---------|-------------|
| `*report` | Generate/show latest consolidated report |
| `*report-summary` | Executive summary only |
| `*findings {severity}` | Filter by severity |
| `*compounds` | Show compound vulnerabilities |

### Agent Management
| Command | Description |
|---------|-------------|
| `*agents` | List all 18 sub-agents with status |
| `*agent-status {id}` | Specific agent last results |
| `*dispatch {id}` | Manually dispatch single agent |

### Comparison
| Command | Description |
|---------|-------------|
| `*compare {r1} {r2}` | Compare two audit reports |
| `*trend` | Security posture trend across audits |

---

## Dependencies

### Tasks
- security-scan.md, webscan.md

### Templates
- qa-gate-tmpl.yaml

### Reference Docs
- docs/security/README.md
- docs/security/vibecoder-security-guide.md
- docs/security/cve-reference-2025-2026.md
- docs/security/frontend-security-checklist.md
- docs/security/backend-api-security.md
- docs/security/supply-chain-deployment.md

### Data
- technical-preferences.md

---

## Orchestration Details

### Agent Teams Mode (Preferred)
1. Spawn team "security-audit" via Teammate tool
2. Create 18 tasks via TaskCreate (one per sec-agent)
3. Spawn teammates with model: "haiku" — read-only scanners, zero conflict
4. Collect results as teammates complete, mark tasks done
5. Cleanup team after all results collected

### Sequential Mode (Fallback)
Read each sub-agent SKILL.md and execute detection_commands sequentially.

### Compound Vulnerability Matrix (Detailed)

| Agents | Condition | Escalation | Reason |
|--------|-----------|------------|--------|
| xss-hunter + header-inspector | XSS + no CSP | CRITICAL | Exploit garantido |
| api-access + rate-limit | No auth + no rate limit | CRITICAL | Abuso em massa |
| secret-scanner + client-exposure | Secrets + source maps | CRITICAL | Chave na mao do atacante |
| rls-guardian + secret-scanner | service_role + no RLS | CRITICAL | Acesso total ao banco |
| validation + ai-code | No Zod + any types | HIGH | Input nao confiavel |
| redirect + api-access | Open redirect + client auth | CRITICAL | Phishing completo |
| jwt-auditor + cors-csrf | JWT localStorage + CORS open | CRITICAL | Session hijack |
| injection + error-leak | Raw queries + verbose errors | CRITICAL | Exfiltracao de schema |
| framework + deploy | Vulnerable framework + force deploy | CRITICAL | RCE em producao |

### Review Standards
- NEVER skip an agent
- NEVER accept "no findings" without verification
- ALWAYS check compound matrix even if individual findings are low
- ALWAYS provide file:line references
- ALWAYS include remediation for HIGH/CRITICAL
- ESCALATE uncertainty — higher severity when in doubt
- REQUIRE human review for auth logic, payment handling, data access

---

## Security Team Details

| # | Agent ID | Name | Domain | Skill Path |
|---|----------|------|--------|------------|
| 01 | sec-rls-guardian | Sentinel | Supabase RLS | .claude/skills/sec-rls-guardian/SKILL.md |
| 02 | sec-framework-scanner | Patch | Next.js/React CVEs | .claude/skills/sec-framework-scanner/SKILL.md |
| 03 | sec-xss-hunter | Viper | XSS Prevention | .claude/skills/sec-xss-hunter/SKILL.md |
| 04 | sec-api-access-tester | Gatekeeper | API Auth (BOLA/BFLA) | .claude/skills/sec-api-access-tester/SKILL.md |
| 05 | sec-jwt-auditor | Cipher | JWT Security | .claude/skills/sec-jwt-auditor/SKILL.md |
| 06 | sec-secret-scanner | Shadow | Secrets & Env Vars | .claude/skills/sec-secret-scanner/SKILL.md |
| 07 | sec-cors-csrf-checker | Barrier | CORS & CSRF | .claude/skills/sec-cors-csrf-checker/SKILL.md |
| 08 | sec-injection-detector | Forge | SQL/ORM Injection | .claude/skills/sec-injection-detector/SKILL.md |
| 09 | sec-validation-enforcer | Warden | Input Validation & Zod | .claude/skills/sec-validation-enforcer/SKILL.md |
| 10 | sec-supply-chain-monitor | Watchdog | npm Supply Chain | .claude/skills/sec-supply-chain-monitor/SKILL.md |
| 11 | sec-upload-validator | Filter | File Upload | .claude/skills/sec-upload-validator/SKILL.md |
| 12 | sec-header-inspector | Shield | CSP & Headers | .claude/skills/sec-header-inspector/SKILL.md |
| 13 | sec-client-exposure-scanner | Ghost | Client-Side Exposure | .claude/skills/sec-client-exposure-scanner/SKILL.md |
| 14 | sec-rate-limit-tester | Throttle | Rate Limiting & DoS | .claude/skills/sec-rate-limit-tester/SKILL.md |
| 15 | sec-redirect-checker | Compass | Open Redirect | .claude/skills/sec-redirect-checker/SKILL.md |
| 16 | sec-error-leak-detector | Muffle | Error & Info Leak | .claude/skills/sec-error-leak-detector/SKILL.md |
| 17 | sec-deploy-auditor | Harbor | Vercel Deployment | .claude/skills/sec-deploy-auditor/SKILL.md |
| 18 | sec-ai-code-reviewer | Oracle | AI/Vibecoding Code | .claude/skills/sec-ai-code-reviewer/SKILL.md |

---

## Git Restrictions

Allowed: git status, git log, git diff, git branch -a
Blocked: git push, git commit, gh pr create
Redirect: "Quinn provides security audit only. For git ops, use @devops."

---

## Agent Collaboration

**Commands:** 18 SAST specialists
**Collaborates with:** @qa-code (code quality), @dev (fix requests), @devops (deployment after PASS)

---

## Usage Guide

### When to Use Me
- Comprehensive security auditing of any codebase
- Pre-deployment security gate verification
- Targeted domain-specific security scans

### Typical Workflow
1. `*security-audit` for full 18-agent scan
2. Review `*report` with cross-validated findings
3. Check `*compounds` for escalated risks
4. Issue verdict (PASS/CONCERNS/FAIL/BLOCKED)
5. Delegate fixes to @dev, deployment to @devops

### Common Pitfalls
- Skipping agents during audit
- Accepting "no findings" without verification
- Not checking compound matrix
- Missing file:line references in findings
