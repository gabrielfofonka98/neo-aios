# Story 2.5: Security Report Engine

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Story 2.4

---

## Objetivo

Criar sistema de geração de relatórios de segurança em múltiplos formatos.

## Tasks

### Task 1: Report Formatters

**Arquivo:** `src/aios/security/reports/formatter.py`

Formatos:
- **JSON** - Programmatic access
- **Markdown** - Documentation
- **Console** - Terminal output
- **SARIF** - IDE integration

### Task 2: Report Generator

**Arquivo:** `src/aios/security/reports/generator.py`

- Gerar em múltiplos formatos
- Salvar em arquivo
- Inferir formato da extensão

### Task 3: Testes

**Arquivo:** `tests/test_security/test_reports.py`

---

## Output Formats

### JSON
```json
{
  "scan_id": "...",
  "findings": [...]
}
```

### Markdown
```markdown
# Security Scan Report
- Total: X findings
- Critical: Y
```

### Console
```
═══════════════════════════
  SECURITY SCAN REPORT
═══════════════════════════
  [CRITICAL] XSS found...
```

### SARIF
Standard format for IDE integration (VS Code, etc.)

---

## Validação Final

- [ ] 4 formatters funcionando
- [ ] Report generator com múltiplos formatos
- [ ] SARIF para IDE integration
- [ ] Testes com 90%+ coverage

## Notas para Ralph

- SARIF é padrão para IDE integration
- Console output deve ser visual/legível
- JSON para programmatic access
