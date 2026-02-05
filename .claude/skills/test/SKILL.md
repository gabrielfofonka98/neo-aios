---
description: "Roda testes do projeto. Detecta framework automaticamente."
user_invocable: true
---

# /test - Rodar Testes

## Fluxo

### 1. DETECTAR FRAMEWORK
Verificar arquivos no projeto:

| Arquivo | Framework | Comando |
|---------|-----------|---------|
| pyproject.toml (pytest) | Python/Pytest | `uv run pytest` ou `pytest` |
| package.json (scripts.test) | Node/Jest/Vitest | `npm test` |
| Cargo.toml | Rust | `cargo test` |
| go.mod | Go | `go test ./...` |

### 2. EXECUTAR
```bash
# Python (preferido)
uv run pytest

# Ou Node
npm test
```

### 3. ANALISAR RESULTADO
Se falhar:
- Mostrar quais testes falharam
- Mostrar erro específico
- Sugerir correção se possível

Se passar:
- Mostrar resumo (X passed, Y skipped)
- Coverage se disponível

## Opções
- `/test` - Roda todos
- `/test watch` - Modo watch
- `/test coverage` - Com relatório de coverage
- `/test [arquivo]` - Testa arquivo específico

## Regras
- SEMPRE detectar framework antes de rodar
- SEMPRE mostrar resumo claro do resultado
- Se falhar, sugerir correção
