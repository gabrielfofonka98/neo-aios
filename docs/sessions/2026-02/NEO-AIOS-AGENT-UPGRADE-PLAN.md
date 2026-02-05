# NEO-AIOS Agent Upgrade Plan

> **Data:** 2026-02-05
> **Autor:** Squad Architect
> **Status:** ✅ CONCLUÍDO
> **Sessões Paralelas:** SIM - Este documento serve como fonte de verdade para múltiplas sessões
> **Data de Conclusão:** 2026-02-05

---

## 1. CONTEXTO

### O Que Foi Feito

O NEO-AIOS possui **33 agentes** divididos em:
- **15 Core Agents** (aria, codex, dara, dex, gage, morgan, ops, oracle, orion, pixel, quinn, ralph, rune, sage, tess)
- **18 Security Sub-Agents** (todos com prefixo `sec-*`)

**Padronização inicial completada:**
- ✅ Todos os 33 agentes têm `hierarchy` (reports_to, delegates_to, collaborates_with)
- ✅ Todos os 33 agentes têm `handoff_to` no YAML
- ✅ Template lean criado em `docs/AGENT-TEMPLATE.md`

### O Que Falta

Análise identificou gaps críticos nas seções obrigatórias do padrão AIOS:

| Seção | Presença | Gap |
|-------|----------|-----|
| hierarchy | 33/33 (100%) | ✅ Completo |
| handoff_to | 33/33 (100%) | ✅ Completo |
| voice_dna | 33/33 (100%) | ✅ Completo |
| output_examples | 27/33 (82%) | ⚠️ 6 agentes faltando |
| **anti_patterns** | **4/33 (12%)** | 🔴 **29 agentes faltando** |
| **completion_criteria** | **9/33 (27%)** | 🔴 **24 agentes faltando** |

---

## 2. INVENTÁRIO COMPLETO DOS AGENTES

### 2.1 Core Agents (15)

| Agente | Linhas | Tier | anti_patterns | completion_criteria | output_examples | Status |
|--------|--------|------|---------------|---------------------|-----------------|--------|
| aria | 176 | VP | ❌ | ❌ | ✅ | INCOMPLETO |
| codex | 190 | IC | ❌ | ✅ | ✅ | INCOMPLETO |
| dara | 183 | IC | ❌ | ✅ | ✅ | INCOMPLETO |
| dex | 200 | IC | ❌ | ✅ | ✅ | INCOMPLETO |
| gage | 210 | IC | ❌ | ✅ | ✅ | INCOMPLETO |
| morgan | 192 | VP | ❌ | ❌ | ✅ | INCOMPLETO |
| ops | 232 | IC | ❌ | ❌ | ❌ | INCOMPLETO |
| oracle | 292 | VP | ❌ | ❌ | ❌ | INCOMPLETO |
| orion | 220 | Master | ❌ | ❌ | ❌ | INCOMPLETO |
| pixel | 338 | VP | ❌ | ❌ | ❌ | INCOMPLETO |
| quinn | 173 | IC | ❌ | ✅ | ✅ | INCOMPLETO |
| ralph | 248 | IC | ❌ | ❌ | ❌ | INCOMPLETO |
| rune | 231 | IC | ❌ | ✅ | ✅ | INCOMPLETO |
| sage | 195 | IC | ❌ | ✅ | ✅ | INCOMPLETO |
| tess | 291 | IC | ❌ | ❌ | ❌ | INCOMPLETO |

### 2.2 Security Sub-Agents (18)

| Agente | Linhas | anti_patterns | completion_criteria | output_examples | Status |
|--------|--------|---------------|---------------------|-----------------|--------|
| sec-ai-code-reviewer | 129 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-api-access-tester | 143 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-client-exposure-scanner | 118 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-cors-csrf-checker | 111 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-deploy-auditor | 120 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-error-leak-detector | 115 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-framework-scanner | 148 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-header-inspector | 118 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-injection-detector | 112 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-jwt-auditor | 131 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-rate-limit-tester | 120 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-redirect-checker | 106 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-rls-guardian | 135 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-secret-scanner | 141 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-supply-chain-monitor | 118 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-upload-validator | 115 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-validation-enforcer | 120 | ❌ | ❌ | ✅ | INCOMPLETO |
| sec-xss-hunter | 147 | ❌ | ❌ | ✅ | INCOMPLETO |

---

## 3. TAREFAS DE EXECUÇÃO

### TASK 1: Adicionar `anti_patterns` em TODOS os agentes
**Owner:** Squad Architect ou Dex (Dev)
**Prioridade:** 🔴 CRÍTICA
**Estimativa:** 33 agentes x ~10 linhas = ~330 linhas de adição

**O que fazer:**
Adicionar seção `anti_patterns` em cada SKILL.md com formato:

```yaml
anti_patterns:
  never_do:
    - "[Ação proibida 1 específica do agente]"
    - "[Ação proibida 2 específica do agente]"
    - "[Ação proibida 3 específica do agente]"
    - "[Ação proibida 4 específica do agente]"
    - "[Ação proibida 5 específica do agente]"
```

**Critério de conclusão:**
- [ ] Todos os 33 agentes têm `anti_patterns.never_do` com mínimo 5 items
- [ ] Anti-patterns são específicos do domínio do agente (não genéricos)

**Agentes afetados:** TODOS (33)

---

### TASK 2: Adicionar `completion_criteria` nos agentes faltando
**Owner:** Squad Architect ou Rune (Spec)
**Prioridade:** 🔴 ALTA
**Estimativa:** 24 agentes x ~8 linhas = ~192 linhas de adição

**O que fazer:**
Adicionar seção `completion_criteria` em cada SKILL.md com formato:

```yaml
completion_criteria:
  task_complete_when:
    - "[Critério verificável 1]"
    - "[Critério verificável 2]"
    - "[Critério verificável 3]"
    - "[Critério verificável 4]"
```

**Critério de conclusão:**
- [ ] Todos os 24 agentes listados têm `completion_criteria`
- [ ] Critérios são mensuráveis/verificáveis

**Agentes afetados (24):**
- Core: aria, morgan, ops, oracle, orion, pixel, ralph, tess
- Security: TODOS os 18 sec-* agents

---

### TASK 3: Adicionar `output_examples` nos agentes faltando
**Owner:** Squad Architect ou Sage (Doc)
**Prioridade:** ⚠️ MÉDIA
**Estimativa:** 6 agentes x ~30 linhas = ~180 linhas de adição

**O que fazer:**
Adicionar seção `output_examples` em cada SKILL.md com formato:

```yaml
output_examples:
  - input: "[Exemplo de input/pedido]"
    output: |
      [Exemplo de output formatado que o agente produziria]
  - input: "[Outro exemplo]"
    output: |
      [Outro output]
  - input: "[Terceiro exemplo]"
    output: |
      [Terceiro output]
```

**Critério de conclusão:**
- [ ] Todos os 6 agentes têm mínimo 3 `output_examples`
- [ ] Exemplos são realistas e demonstram a capacidade do agente

**Agentes afetados (6):**
- ops
- oracle
- orion
- pixel
- ralph
- tess

---

### TASK 4: Expandir `voice_dna` com vocabulário específico
**Owner:** Squad Architect (clone-mind workflow)
**Prioridade:** ⚠️ MÉDIA
**Estimativa:** Variável por agente

**O que fazer:**
Para agentes que têm `voice_dna` básico, expandir com:

```yaml
voice_dna:
  vocabulary:
    always_use:
      - "[Termo específico do domínio]"
      - "[Jargão técnico apropriado]"
    never_use:
      - "[Termo proibido] - [motivo]"
      - "[Jargão incorreto] - [alternativa correta]"
  sentence_starters:
    - "[Frase típica de início]"
    - "[Outra frase de início]"
  tone: "[descrição do tom]"
```

**Critério de conclusão:**
- [ ] voice_dna tem `vocabulary.always_use` com mínimo 5 termos
- [ ] voice_dna tem `vocabulary.never_use` com mínimo 3 termos
- [ ] voice_dna tem `sentence_starters` com mínimo 3 frases

**Agentes prioritários:** orion, ops, ralph (agentes operacionais críticos)

---

### TASK 5: Criar Definition of Done markdown section
**Owner:** Rune (Spec) ou Sage (Doc)
**Prioridade:** 🟡 BAIXA
**Estimativa:** 15 agentes x ~10 linhas = ~150 linhas

**O que fazer:**
Adicionar seção markdown após o YAML:

```markdown
---

## Definition of Done

- [ ] [Critério 1]
- [ ] [Critério 2]
- [ ] [Critério 3]

---
```

**Agentes afetados:** Core agents que ainda não têm (verificar cada um)

---

## 4. ORDEM DE EXECUÇÃO RECOMENDADA

```
FASE 1 - CRÍTICO (Sessão 1)
├── TASK 1: anti_patterns em 33 agentes
│   ├── Batch 1: 15 Core agents
│   └── Batch 2: 18 Security agents
│
FASE 2 - ALTO (Sessão 2)
├── TASK 2: completion_criteria em 24 agentes
│   ├── Batch 1: 8 Core agents (aria, morgan, ops, oracle, orion, pixel, ralph, tess)
│   └── Batch 2: 18 Security agents
│
FASE 3 - MÉDIO (Sessão 3)
├── TASK 3: output_examples em 6 agentes
└── TASK 4: voice_dna expansion em 3 agentes prioritários
```

---

## 5. TEMPLATES PARA EXECUÇÃO

### 5.1 Template anti_patterns por tipo de agente

**Para Core Agents (VP/IC):**
```yaml
anti_patterns:
  never_do:
    - "Executar ações fora do meu escopo definido"
    - "Fazer push/deploy (apenas Gage pode)"
    - "Pular etapas do workflow sem aprovação"
    - "Assumir contexto sem verificar"
    - "Ignorar hierarquia de delegação"
```

**Para Security Agents:**
```yaml
anti_patterns:
  never_do:
    - "Reportar falsos positivos sem validação"
    - "Ignorar findings CRITICAL"
    - "Executar scans sem escopo definido"
    - "Modificar código (apenas reportar)"
    - "Aprovar código com vulnerabilidades conhecidas"
```

### 5.2 Template completion_criteria por tipo

**Para Core Agents:**
```yaml
completion_criteria:
  task_complete_when:
    - "Artefato principal entregue"
    - "Validação de qualidade passou"
    - "Handoff documentado para próximo agente"
    - "Nenhum blocker pendente"
```

**Para Security Agents:**
```yaml
completion_criteria:
  scan_complete_when:
    - "Todos os arquivos no escopo foram analisados"
    - "Findings classificados por severidade"
    - "Report gerado em docs/qa/security/"
    - "Handoff para Quinn com resumo executivo"
```

---

## 6. COMO USAR ESTE DOCUMENTO

### Para abrir sessão paralela:

1. Ative o agente apropriado:
   - `/squad-architect` para Tasks 1, 3, 4
   - `/spec` (Rune) para Task 2, 5
   - `/dev` (Dex) para implementação bulk

2. Informe a task:
   ```
   Estou executando o NEO-AIOS Agent Upgrade Plan.
   Leia: docs/sessions/2026-02/NEO-AIOS-AGENT-UPGRADE-PLAN.md
   Execute: TASK [número]
   ```

3. O agente terá todo o contexto necessário.

### Para verificar progresso:

Atualize as checkboxes neste documento conforme tasks forem concluídas:
- [x] TASK 1 completa (2026-02-05)
- [x] TASK 2 completa (2026-02-05)
- [x] TASK 3 completa (2026-02-05)
- [x] TASK 4 completa (2026-02-05)
- [x] TASK 5 completa (2026-02-05)

---

## 7. ARQUIVOS RELACIONADOS

| Arquivo | Propósito |
|---------|-----------|
| `docs/AGENT-TEMPLATE.md` | Template lean para novos agentes |
| `agents/*/SKILL.md` | Arquivos dos agentes (33 total) |
| `.aios/session-state.json` | Estado da sessão atual |
| `docs/sessions/2026-02/` | Logs de sessão |

---

## 8. CRITÉRIO DE SUCESSO FINAL

O upgrade está completo quando:

- [x] **33/33 agentes** têm `anti_patterns` com 5+ items ✅
- [x] **33/33 agentes** têm `completion_criteria` com 4+ items ✅
- [x] **33/33 agentes** têm `output_examples` com 3+ exemplos ✅
- [x] **33/33 agentes** têm `voice_dna.vocabulary` expandido ✅
- [ ] Validação `*validate-squad` passa em todos (PENDENTE)

**Meta de qualidade:** Todos os agentes com score >= 7/10 no quality gate.

---

## 9. EXECUÇÃO CONCLUÍDA

**Data de conclusão:** 2026-02-05
**Executor:** Squad Architect
**Método:** Execução paralela com 3 agentes simultâneos (batches de ~11 arquivos cada)

### Resumo da Execução

| Fase | Tasks | Agentes Editados | Status |
|------|-------|------------------|--------|
| 1 | anti_patterns + completion_criteria | 33 | ✅ |
| 2 | output_examples + voice_dna.vocabulary | 6 | ✅ |
| 3 | Definition of Done markdown | 15 | ✅ |

**Próximo passo sugerido:** Rodar `*validate-squad` para verificar score de qualidade.

---

*Documento gerado por Squad Architect em 2026-02-05*
*Última atualização: 2026-02-05*
