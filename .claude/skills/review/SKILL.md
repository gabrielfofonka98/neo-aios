---
description: "Code review com 12 lentes mentais. Análise profunda antes de PR."
user_invocable: true
---

# /review - Code Review Multi-Lens

**Agente:** Codex (Code Quality)

## O que é

Review de código usando 12 modelos mentais para encontrar problemas que review normal não pega.

## Fluxo

### 1. IDENTIFICAR ESCOPO
```bash
git diff --stat
git diff --name-only
```

Perguntar:
```
O que você quer revisar?

1. Todas as mudanças (git diff)
2. Arquivo específico
3. PR existente (informar número)
```

### 2. ANÁLISE 12-LENSES

Aplicar cada lente ao código:

| Lente | Pergunta | Busca |
|-------|----------|-------|
| First Principles | É necessário? | Código desnecessário |
| Steel Man | Qual a melhor versão disso? | Melhorias |
| Inversion | O que pode dar errado? | Edge cases |
| Via Negativa | O que remover? | Dead code |
| Pre-Mortem | Se falhar, por quê? | Pontos de falha |
| Second-Order | Consequências? | Side effects |
| Goodhart | Vira métrica ruim? | Incentivos errados |
| Skin in the Game | Quem tem risco? | Responsabilidade |
| Circle of Competence | Domínio correto? | Fora da expertise |
| Lindy Effect | Dura no tempo? | Soluções frágeis |
| Antifragility | Melhora com stress? | Resiliência |
| Interdisciplinary | Outros campos? | Soluções de outras áreas |

### 3. RELATÓRIO

Para cada achado:
- Severidade: CRITICAL / HIGH / MEDIUM / LOW
- Lente que identificou
- Localização (arquivo:linha)
- Problema
- Sugestão de fix

## Opções
- `/review` - Todas 12 lentes (padrão)
- `/review quick` - Só 3 lentes principais (First Principles, Pre-Mortem, Inversion)
