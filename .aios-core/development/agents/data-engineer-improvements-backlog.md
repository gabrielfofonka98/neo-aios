# Data Engineer Improvements Backlog

Melhorias identificadas na análise comparativa com db-sage (2025-12-29).

## Status

- **Implementado:** KISS Gate, Structured Questions, *load-schema, *validate-kiss, *squad-check
- **Pendente:** Items abaixo

---

## 🔴 Alta Prioridade

### 1. Criar Activation Protocol File

**Arquivo:** `.aios-core/development/agents/data-engineer-activation-protocol.md`

**Conteúdo necessário:**
- SQL queries completas para schema loading (PostgreSQL, MySQL, SQLite, MongoDB)
- Session context storage pattern
- Multi-database detection logic

**Referência:** `squads/super-agentes/agents/db-sage-activation-protocol.md`

---

### 2. Adicionar Exemplo Concreto (Worked Example)

Mostrar KISS Gate em ação com caso real no arquivo principal ou em doc separado.

**Exemplo sugerido:**
```
Usuário: "Adicionar mind_id a contents"

✅ STEP 1: Tabela 'contents' existe?
   → SIM (30 colunas, 0 linhas)

✅ STEP 2: Campo 'mind_id' já existe?
   → NÃO direto, mas...

✅ STEP 3: Existe relação contents ↔ minds?
   → SIM! Tabela 'content_minds' (N:M, role-based)

✅ RESULTADO:
   ❌ NÃO adicionar mind_id a contents
   ✅ USAR content_minds com JOIN
```

---

### 3. Adicionar Seção RESTRICTIONS

**Adicionar ao data-engineer.md:**

```yaml
restrictions: |
  DATA-ENGINEER NUNCA PODE:
  - ❌ Propor ALTER sem executar *validate-kiss primeiro
  - ❌ Confiar em documentação estática (sempre *load-schema)
  - ❌ Executar migration sem snapshot + rollback plan
  - ❌ Salvar nada em .aios-core/ (é framework, read-only)
  - ❌ Propor 3+ tabelas sem usuário solicitar explicitamente
  - ❌ Assumir necessidade de analytics sem evidência
  - ❌ Fazer perguntas se já tem schema context carregado
```

---

## 🟡 Média Prioridade

### 4. Proposal Format Template

Adicionar template estruturado para output de propostas:

```sql
-- ANÁLISE:
✓ Tabela 'X' não tem campo 'Y'
✓ Não existe tabela N:M para isso
✓ Dados: [status]
✓ Frequência de acesso: [analysis]

-- SOLUÇÃO RECOMENDADA:
[Opção A] - [Tradeoffs]
[Opção B] - [Tradeoffs]

-- IMPACTO:
- Migration: [simples|complexa]
- RLS: [impacto]
- Performance: [impacto]
- Rollback: [viável em X horas]

-- PRÓXIMOS PASSOS:
1. Criar snapshot (backup)
2. Executar migration
3. Validar constraints
4. Run smoke tests

Qual opção? [1|2|3]
```

---

### 5. Workflow Commands (Orchestrators)

Adicionar comandos de alto nível que orquestram múltiplas tasks:

| Comando | Descrição | Tasks Orquestradas |
|---------|-----------|-------------------|
| `*migrate` | Safe schema migration workflow | snapshot → dry-run → apply-migration → smoke-test |
| `*backup` | Backup/restore workflow | snapshot → validate → store metadata |
| `*tune` | Performance tuning workflow | load-schema → analyze-hotpaths → explain → optimize |

---

## 🟢 Baixa Prioridade

### 6. Visual Checkbox Questions

Converter perguntas estruturadas de prosa para formato visual:

```
1. **Escopo:** Isso é para [mind | content | fragment]?
   ☐ Uma mente específica
   ☐ Todas as mentes
   ☐ Sem relação com mente

2. **Dados Existentes:** Já tem dados aí?
   ☐ Sim (□ quantos registros?) → CUIDADO: migration complexa
   ☐ Não → Proceder normalmente
```

---

## Referências

- **data-engineer atual:** `.aios-core/development/agents/data-engineer.md`
- **db-sage (inspiração):** `squads/super-agentes/agents/db-sage.md`
- **db-sage activation protocol:** `squads/super-agentes/agents/db-sage-activation-protocol.md`

---

## Decisão de Merge

**Pergunta em aberto:** db-sage e data-engineer têm ~70% de sobreposição. Considerar se devem ser unificados:

| Opção | Prós | Contras |
|-------|------|---------|
| **Manter separados** | Flexibilidade, contextos diferentes | Duplicação de manutenção |
| **Unificar** | Uma fonte de verdade | Pode ficar muito complexo |
| **db-sage como alias** | db-sage aponta para data-engineer | Perda de features específicas |

**Recomendação:** Manter separados por enquanto. db-sage é específico para MMOS/squads, data-engineer é core AIOS.

---

*Documento criado em: 2025-12-29*
*Última atualização: 2025-12-29*
