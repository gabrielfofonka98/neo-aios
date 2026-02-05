# Guia de Inicio Rapido

**NEO-AIOS: Agent Intelligence Operating System**

Este guia vai te levar do zero ate usar o sistema de agentes em poucos minutos.

---

## Requisitos

- **Python 3.12+** instalado
- **uv** (package manager moderno do Astral)

### Instalando uv (se necessario)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

---

## Instalacao

### 1. Clone o repositorio

```bash
git clone https://github.com/gabrielfofonka98/neo-aios.git
cd neo-aios
```

### 2. Instale as dependencias

```bash
# Instala todas as dependencias (incluindo dev)
uv sync --extra dev
```

### 3. Verifique a instalacao

```bash
# Deve mostrar versao e ajuda
aios --help
```

Saida esperada:

```
NEO-AIOS - Agent Intelligence Operating System
A multi-agent development environment with Big Tech hierarchy.

Usage: aios [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose  Enable verbose output.
  -q, --quiet    Suppress non-essential output.
  --help         Show this message and exit.

Commands:
  agent    Manage agents (activate, deactivate, list, status).
  gate     Run quality gates.
  health   Run health checks.
  scan     Run security scans (quick, full).
  version  Show version information.
```

---

## Primeiro Uso

### Ver versao do sistema

```bash
aios version
```

### Listar agentes disponiveis

```bash
aios agent list
```

Mostra todos os agentes registrados com seu ID, nome, tier e status.

### Ver status atual

```bash
aios agent status
```

Mostra se ha um agente ativo e informacoes da sessao.

---

## Ativando um Agente

Os agentes sao ativados via Claude Code usando comandos ou mencoes:

### Via Comando

```
/dev          # Ativa Dex (Developer)
/architect    # Ativa Aria (VP Engineering)
/devops       # Ativa Gage (DevOps)
/qa           # Ativa Quinn (Security QA)
/qa-code      # Ativa Codex (Code QA)
/doc          # Ativa Sage (Documentation)
```

### Via Mencao

```
@dev          # Ativa Dex
@architect    # Ativa Aria
```

### Comandos do Agente

Uma vez ativo, cada agente responde a comandos:

```
*help         # Mostra ajuda do agente
*status       # Mostra status atual
*exit         # Sai do modo agente
*task {name}  # Executa uma task especifica
```

### Exemplo Pratico

```
Usuario: /dev
Dex: "Dex (Developer) no comando. Bora codar."

Usuario: *help
Dex: [mostra comandos disponiveis]

Usuario: *exit
Sistema: "Agente desativado. Voltando ao Claude padrao."
```

---

## Rodando Scan de Seguranca

### Quick Scan (pre-commit)

Rapido, valida apenas os validators essenciais:

```bash
aios scan quick --path ./src
```

### Full Scan (auditoria completa)

Roda todos os 18 validators de seguranca:

```bash
aios scan full --path ./src
```

### Validadores especificos

```bash
aios scan full --path ./src --validator sec-xss-hunter --validator sec-injection-detector
```

---

## Health Check

Verifica a saude do sistema:

```bash
# Todos os checks
aios health check

# Check especifico
aios health check --name agents
```

### Checks disponiveis

| Check | O que verifica |
|-------|----------------|
| `agents` | Registry de agentes carregado |
| `session` | Arquivo de sessao acessivel |
| `config` | Configuracoes validas |
| `tools` | Ferramentas (ruff, mypy) disponiveis |
| `git` | Repositorio git configurado |
| `python` | Versao Python compativel |

---

## Quality Gates

Tres camadas de verificacao de qualidade:

### Layer 1: Pre-commit

```bash
aios gate run --layer 1
```

Executa: ruff + mypy + pytest + security quick scan

### Layer 2: PR Automation

```bash
aios gate run --layer 2
```

Executa: Layer 1 + full security audit + code review

### Layer 3: Human Review

Requer aprovacao manual de Tech Lead ou superior.

---

## Estrutura de Diretorios

```
neo-aios/
├── src/aios/           # Codigo Python do framework
├── agents/             # Definicoes SKILL.md dos agentes
├── config/             # Configuracoes YAML
├── tests/              # Suite de testes
├── docs/               # Documentacao
│   ├── guides/         # Guias como este
│   ├── api/            # Referencia da API
│   └── agents/         # Catalogo de agentes
└── .aios/              # Estado de runtime (session, etc)
```

---

## Proximos Passos

1. **[Agent Development](./agent-development.md)** - Aprenda a criar novos agentes
2. **[API Reference](../api/README.md)** - Referencia completa da API Python
3. **[Agent Catalog](../agents/README.md)** - Catalogo de todos os agentes

---

## Troubleshooting

### Comando `aios` nao encontrado

```bash
# Certifique-se de que o ambiente esta ativado
source .venv/bin/activate

# Ou use via uv
uv run aios --help
```

### Erro de versao Python

```
NEO-AIOS requer Python 3.12+. Versao atual: X.X
```

Solucao: Instale Python 3.12+ e recrie o ambiente:

```bash
uv venv --python 3.12
uv sync --extra dev
```

### Agente nao encontrado

```
Agent 'xxx' not found in registry
```

Solucao: Verifique se o SKILL.md do agente existe em `agents/`:

```bash
ls agents/
```

---

*NEO-AIOS: Agent Intelligence Operating System*
*"Never take the lazy path. Do the hard work now."*
