# webscan

**Task ID:** `webscan`
**Version:** 1.0.0
**Status:** Active
**Persona:** Havoc (QA Destroyer)

---

## Purpose

Scan de segurança em URLs/infraestrutura externa. Verifica vulnerabilidades, arquivos expostos, configurações de API, e analisa claims de terceiros detectando padrões de engenharia social.

**Estratégia:** Scan técnico ativo + análise de claims + relatório estruturado.

---

## Execution Modes

**Choose your execution mode:**

### 1. YOLO Mode - Fast, Autonomous (0-1 prompts)
- Executa scan completo automaticamente
- Gera relatório sem interrupções
- **Best for:** Urgências, alegações claramente suspeitas

### 2. Interactive Mode - Balanced, Educational (5-10 prompts) **[DEFAULT]**
- Confirma escopo antes de cada fase
- Explica findings durante execução
- **Best for:** Primeira análise, situações ambíguas

### 3. Pre-Flight Planning - Comprehensive Upfront Planning
- Lista todos endpoints/URLs a testar
- Apresenta plano de scan para aprovação
- **Best for:** Infraestrutura crítica, compliance

**Parameter:** `mode` (optional, default: `interactive`)

---

## Task Definition (AIOS Task Format V1.0)

```yaml
task: webscan()
responsável: Havoc (QA Destroyer)
responsavel_type: Agente
atomic_layer: Strategy

**Entrada:**
- campo: target_url
  tipo: string
  origem: User Input
  obrigatório: true
  validação: URL base para scan (ex: example.com ou https://example.com)

- campo: threat_context
  tipo: string
  origem: User Input
  obrigatório: false
  validação: Mensagem/claim de terceiro (se houver)

- campo: additional_urls
  tipo: array
  origem: User Input
  obrigatório: false
  validação: URLs adicionais para scan (subdomínios, APIs)

- campo: claimant_info
  tipo: object
  origem: User Input
  obrigatório: false
  validação: Informações sobre quem reportou (nome, contato, plataforma)

- campo: scan_depth
  tipo: string
  origem: config
  obrigatório: false
  padrão: standard
  validação: light | standard | deep

**Saída:**
- campo: threat_report
  tipo: markdown
  destino: File (reports/security/)
  persistido: true

- campo: verdict
  tipo: enum
  destino: Memory
  valores: [LEGITIMATE, SOCIAL_ENGINEERING, PARTIAL, INCONCLUSIVE]

- campo: risk_level
  tipo: enum
  destino: Memory
  valores: [CRITICAL, HIGH, MEDIUM, LOW, INFO]
```

---

## Pre-Conditions

```yaml
pre-conditions:
  - [ ] Threat context provided (message, email, or description)
    tipo: pre-condition
    blocker: true
    error_message: "Forneça o contexto da ameaça (mensagem recebida ou descrição)"
```

---

## Step-by-Step Execution

### Phase 1: Claim Analysis (Engenharia Social Detection)

**Purpose:** Identificar red flags que indicam golpe/scam vs. report legítimo

**Actions:**

1. **Parse Threat Context**
   - Extrair alegações específicas feitas
   - Identificar URLs/sistemas mencionados
   - Catalogar termos técnicos usados

2. **Red Flag Analysis**
   Verificar presença de indicadores de engenharia social:

   | Red Flag | Peso | Descrição |
   |----------|------|-----------|
   | Contato não solicitado | +3 | DM/email sem relação prévia |
   | Urgência fabricada | +3 | "urgente", "sério", "imediato" |
   | Linguagem vaga | +2 | "fortes indícios" sem evidências |
   | Credibilidade artificial | +2 | Cita termos técnicos genéricos |
   | Solicitação de autorização | +3 | Pede permissão para "testar" |
   | Social proof fraco | +1 | Perfil de rede social como credencial |
   | Spear phishing markers | +3 | "Encontrei via LinkedIn/Google" |
   | Monetização implícita | +3 | Oferece "consultoria" ou "relatório" |
   | Evidências ausentes | +2 | Nenhum screenshot/PoC fornecido |

   **Scoring:**
   - 0-4: Possivelmente legítimo
   - 5-9: Suspeito - verificar tecnicamente
   - 10+: Provável golpe/scam

3. **Pattern Matching**
   Comparar com padrões conhecidos:
   - Golpe do "hacker ético"
   - Bug bounty predatório
   - Extorsão disfarçada
   - Venda de relatório falso

**Output:** `social_engineering_score` + `red_flags_list`

---

### Phase 2: Infrastructure Discovery

**Purpose:** Mapear infraestrutura mencionada/relacionada

**Actions:**

1. **URL Extraction**
   - Extrair domínios mencionados no claim
   - Identificar subdomínios relacionados
   - Mapear tecnologias visíveis

2. **Technology Fingerprinting**
   ```bash
   # Headers analysis
   curl -sI {url} | grep -E "^(Server|X-Powered-By|X-)"

   # Technology detection via response
   curl -s {url} | grep -oE "(WordPress|Next.js|React|N8N|Vercel)"
   ```

3. **Subdomain Enumeration** (se autorizado)
   - Verificar padrões comuns: www, api, admin, bkp, staging, n8n, wp

**Output:** `infrastructure_map`

---

### Phase 3: Active Security Scan

**Purpose:** Verificar alegações com testes técnicos reais

**Actions:**

#### 3.1 HTTPS/TLS Check
```bash
# Certificate validation
curl -sI https://{domain} | grep -E "^(Strict-Transport|Content-Security)"

# HSTS check
curl -sI https://{domain} | grep -i "strict-transport-security"
```

#### 3.2 Sensitive Files Exposure
| Arquivo | Descrição | Risco |
|---------|-----------|-------|
| /.env | Environment variables | CRITICAL |
| /wp-config.php | WordPress config | CRITICAL |
| /wp-content/debug.log | Debug logs | HIGH |
| /.git/config | Git repository | HIGH |
| /api/docs | API documentation | MEDIUM |
| /swagger.json | OpenAPI spec | MEDIUM |
| /readme.html | Version disclosure | LOW |
| /license.txt | Version disclosure | LOW |

```bash
# Test each sensitive file
for file in .env wp-config.php .git/config debug.log; do
  status=$(curl -s -o /dev/null -w "%{http_code}" "https://{domain}/$file")
  echo "$file: $status"
done
```

#### 3.3 API Authentication Check
```bash
# Test common API endpoints without auth
curl -s -o /dev/null -w "%{http_code}" "https://{domain}/api/v1/users"
curl -s -o /dev/null -w "%{http_code}" "https://{domain}/rest/workflows"
curl -s -o /dev/null -w "%{http_code}" "https://{domain}/rest/credentials"
```

#### 3.4 WordPress Specific
```bash
# User enumeration
curl -s "https://{domain}/wp-json/wp/v2/users" | jq '.[].slug'

# XML-RPC check
curl -s -X POST "https://{domain}/xmlrpc.php" \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>'
```

#### 3.5 N8N Specific
```bash
# Public settings (normally exposed)
curl -s "https://{domain}/rest/settings" | jq '.data.authCookie'

# Protected endpoints (should return 401)
curl -s -o /dev/null -w "%{http_code}" "https://{domain}/rest/workflows"
curl -s -o /dev/null -w "%{http_code}" "https://{domain}/rest/executions"
curl -s -o /dev/null -w "%{http_code}" "https://{domain}/rest/credentials"
```

#### 3.6 Credential Exposure Search
```bash
# Search for exposed keys in HTML/JS
curl -s "https://{domain}" | grep -oE "(sk-[a-zA-Z0-9]{20,}|AKIA[A-Z0-9]{16}|ghp_[a-zA-Z0-9]{36})"

# Check for .env in robots.txt
curl -s "https://{domain}/robots.txt" | grep -i "disallow"
```

**Output:** `scan_results` with status for each check

---

### Phase 4: Claim Verification

**Purpose:** Cruzar alegações específicas com resultados técnicos

**Actions:**

Para cada alegação do terceiro:
1. Identificar o que foi alegado
2. Mapear para teste técnico específico
3. Executar verificação
4. Registrar resultado: CONFIRMADO | FALSO | PARCIAL | INCONCLUSIVO

**Output Table:**
| Alegação | Verificação | Resultado | Evidência |
|----------|-------------|-----------|-----------|

---

### Phase 5: Report Generation

**Purpose:** Gerar relatório profissional estruturado

**Template:**

```markdown
# Security Threat Assessment Report

**Data:** {YYYY-MM-DD}
**Analista:** Havoc (QA Destroyer)
**Escopo:** {escopo_definido}

---

## 1. CONTEXTO

{Descrição do contexto: quem reportou, como, quando, alegações}

---

## 2. ANÁLISE DA ABORDAGEM

### Red Flags Identificados

| Indicador | Descrição | Risco |
|-----------|-----------|-------|
{lista de red flags encontrados}

### Padrão Identificado

{Descrição do padrão de golpe/report identificado}

### Social Engineering Score: {score}/20

---

## 3. SCAN TÉCNICO

### Infraestrutura Identificada

| Componente | URL | Tecnologia |
|------------|-----|------------|
{lista de componentes descobertos}

### Testes Executados

{Detalhes de cada categoria de teste}

---

## 4. RESULTADOS

### Passou (Seguro)

| Item | Descrição |
|------|-----------|
{itens que passaram nos testes}

### Atenção (Hardening Recomendado)

| Severidade | Tipo | Descrição | Recomendação |
|------------|------|-----------|--------------|
{vulnerabilidades de baixa/média severidade}

### Crítico (Ação Imediata)

| Severidade | Tipo | Descrição | Recomendação |
|------------|------|-----------|--------------|
{vulnerabilidades críticas, se houver}

### Verificação de Alegações

| Alegação | Verificação | Resultado |
|----------|-------------|-----------|
{cada alegação vs. resultado técnico}

---

## 5. VEREDICTO

### Site/Infraestrutura: {APROVADO | REPROVADO | ATENÇÃO}

{Justificativa técnica}

### Mensagem/Claim: {LEGÍTIMO | GOLPE/SOCIAL_ENGINEERING | PARCIAL | INCONCLUSIVO}

{Justificativa com base nos red flags e verificações}

---

## 6. RECOMENDAÇÕES

### Imediato (Sem Custo)

- [ ] {ações imediatas}

### Hardening Opcional

{código/comandos para melhorias}

---

## 7. EVIDÊNCIAS

{Logs, responses, screenshots relevantes}

---

**Relatório gerado por Havoc QA Destroyer**
**Classificação: CONFIDENCIAL**
```

---

## Post-Conditions

```yaml
post-conditions:
  - [ ] Report generated and saved to reports/security/
    tipo: post-condition
    blocker: true

  - [ ] All claims verified with technical evidence
    tipo: post-condition
    blocker: false

  - [ ] Verdict provided with justification
    tipo: post-condition
    blocker: true
```

---

## Error Handling

**Strategy:** graceful-degradation

**Common Errors:**

1. **Error:** URL Unreachable
   - **Cause:** Target offline or blocking requests
   - **Resolution:** Try with different user-agent, document as "unable to verify"
   - **Recovery:** Mark specific tests as INCONCLUSIVE

2. **Error:** Rate Limited
   - **Cause:** Too many requests to target
   - **Resolution:** Slow down requests, use delays
   - **Recovery:** Complete partial scan, note limitation

3. **Error:** SSL/TLS Error
   - **Cause:** Invalid certificate or TLS configuration
   - **Resolution:** Document as security finding
   - **Recovery:** Continue with other tests

---

## Tools

```yaml
tools:
  - WebFetch:
      purpose: HTTP requests to external URLs

  - Bash (curl):
      purpose: Direct HTTP testing with headers

  - Grep:
      purpose: Pattern matching in responses

  - jq (optional):
      purpose: JSON parsing of API responses
```

---

## Usage Examples

### Example 1: Suspicious Third-Party Message

```
*threat-assessment

Context: Received WhatsApp from "Daniel" claiming:
- "Your N8N workflows are exposed"
- "API keys leaking"
- "Need authorization to test"

Target: academialendaria.ai
```

### Example 2: Bug Bounty Report

```
*threat-assessment --mode=deep

Context: HackerOne report #12345 claiming XSS in /profile endpoint

Target: app.example.com/profile
```

### Example 3: Quick Verification

```
*threat-assessment --mode=yolo

Context: Email claiming our .env is public
Target: api.oursite.com
```

---

## Integration

This task can be called from:
- `@qa` agent via `*threat-assessment`
- Review workflows when security claims arise
- Incident response procedures

---

## Metadata

```yaml
story: N/A
version: 1.0.0
created_by: Quinn (QA Agent)
created_at: 2026-01-23
dependencies:
  - WebFetch tool
  - Bash tool
  - curl (system)
tags:
  - security
  - threat-assessment
  - social-engineering
  - external-audit
```

---

## Command Alias

Add to QA agent commands:

```yaml
commands:
  - threat-assessment {context}: |
      Execute security-threat-assessment task.
      Analyzes third-party security claims + active infrastructure scan.
      Produces: Professional report in reports/security/
```
