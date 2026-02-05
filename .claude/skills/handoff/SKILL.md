---
description: "Cria documento de handoff no fim da sessão. Salva em docs/sessions/YYYY-MM/"
user_invocable: true
---

# /handoff - Documento de Fim de Sessão

Documento que resume a sessão para continuidade futura. Salva contexto importante para a próxima sessão.

## Fluxo

### 1. COLETAR INFO
```bash
date +%Y-%m-%d
git branch --show-current
git log --since="2 hours ago" --oneline
git diff --name-only HEAD~5 2>/dev/null || git diff --name-only
```

### 2. CRIAR DIRETÓRIO
```bash
mkdir -p docs/sessions/$(date +%Y-%m)
```

### 3. GERAR DOCUMENTO

Arquivo: `docs/sessions/YYYY-MM/YYYY-MM-DD-handoff.md`

Conteúdo:
```markdown
# Handoff - [Data]

## Contexto
- **Projeto:** [nome do projeto]
- **Branch:** [branch atual]
- **Sessão:** [duração aproximada]

## O que foi feito
- Item 1
- Item 2

## Arquivos modificados
- `path/to/file1` - descrição
- `path/to/file2` - descrição

## Commits
- abc1234 - feat: ...

## Pendente
- [ ] Item pendente 1
- [ ] Item pendente 2

## Contexto para próxima sessão
[Informações importantes que a próxima sessão precisa saber]

## Decisões tomadas
| Decisão | Motivo |
|---------|--------|
| Usar X em vez de Y | Porque Z |

---
*Gerado automaticamente por /handoff*
```

### 4. CONFIRMAR
Mostrar preview e perguntar se quer adicionar algo.

### 5. SALVAR + COMMIT
```bash
git add docs/sessions/
git commit -m "docs: add session handoff $(date +%Y-%m-%d)"
```

## Regras
- SEMPRE salvar em docs/sessions/YYYY-MM/
- SEMPRE incluir pendências
- SEMPRE commitar o handoff
- NUNCA inventar - usar dados reais da sessão
