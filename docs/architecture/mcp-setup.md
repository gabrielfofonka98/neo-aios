# MCP Server Setup - NEO-AIOS

Configuração de Model Context Protocol (MCP) servers para o projeto NEO-AIOS.

---

## Servidores Configurados

### 1. Serena (19.8k ⭐)
**Navegação Semântica via LSP**

Serena é um toolkit de coding agent que fornece análise semântica de código e capacidades de edição ao estilo IDE para LLMs através do MCP. Opera em **símbolos** (funções, classes, métodos) em vez de arquivos inteiros, resultando em uso extremamente eficiente de tokens.

**GitHub:** [oraios/serena](https://github.com/oraios/serena)

**Funcionalidades:**
- Semantic code search (find-in-project baseado em símbolos)
- Jump-to-definition
- Find references
- Code structure navigation
- Análise de dependências entre símbolos

**Ideal Para:**
- **Dex (Dev)** - Navegação em grandes codebases, refactoring preciso
- **Quinn (QA Security)** - Auditoria de símbolos específicos, trace de chamadas
- **Codex (QA Code)** - Code review focado em símbolos relacionados
- **Aria (Architect)** - Mapeamento de dependências arquiteturais

### 2. ccusage (10.4k ⭐)
**Tracking de Custos e Tokens**

Ferramenta CLI para análise de uso do Claude Code/Codex a partir de arquivos JSONL locais. Fornece dashboards detalhados de custos, consumo de tokens e métricas de sessão.

**GitHub:** [ryoppippi/ccusage](https://github.com/ryoppippi/ccusage)

**Funcionalidades:**
- Daily/monthly/session cost analysis
- Token usage tracking
- Session blocks analysis
- Cost projections
- Aggregação multi-diretório

**Ideal Para:**
- **Oracle (Analyst)** - Análise de métricas de uso, otimização de custos
- **Orion (Master)** - Monitoramento de performance do sistema, budgeting
- **Morgan (PM)** - Cost tracking por projeto/epic/story
- **Gage (DevOps)** - Otimização de pipelines CI/CD

---

## Instalação

### Pré-requisitos

**Serena:**
```bash
# Requer uvx (parte do uv toolchain)
# Se ainda não tiver instalado:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**ccusage:**
```bash
# Requer Node.js 18+ e npm
# Nenhuma instalação permanente necessária (usa npx)
```

### Verificação

Após adicionar `.mcp.json` ao projeto:

```bash
# Verificar se Claude Code reconhece os servers
# (Claude Code detecta automaticamente .mcp.json no root do projeto)

# Teste manual do Serena
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --help

# Teste manual do ccusage
npx @ccusage/mcp@latest --help
```

---

## Configuração

O arquivo `.mcp.json` está localizado no root do projeto:

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "claude-code",
        "--project",
        "/Users/gabrielfofonka/aios-evo/neo-aios"
      ],
      "env": {}
    },
    "ccusage": {
      "command": "npx",
      "args": [
        "@ccusage/mcp@latest"
      ],
      "env": {
        "CLAUDE_CONFIG_DIR": "/Users/gabrielfofonka/.config/claude"
      }
    }
  }
}
```

### Parâmetros Serena

- `--context claude-code` - Otimizado para Claude Code
- `--project <path>` - Path absoluto do projeto (sempre ativado ao iniciar)

**Alternativas:**
- `--project-from-cwd` - Usa o diretório atual (modo user-level)
- `--context ide` - Contexto genérico de IDE

### Parâmetros ccusage

- `CLAUDE_CONFIG_DIR` - Path para dados do Claude Code (default: `~/.config/claude`)
- Múltiplos diretórios: separar por vírgula

**Opções adicionais (args):**
- `--mode calculate` - Força cálculo de custos
- `--type http --port 8080` - Modo HTTP (default: stdio)

---

## Uso com Agentes NEO-AIOS

### Serena - Navegação Semântica

**Dex (Dev):**
```
*task code-refactor

# Usa Serena automaticamente para:
- Encontrar todas as referências de uma função
- Jump to definition de dependências
- Mapear símbolos relacionados antes de refatorar
```

**Quinn (QA Security):**
```
*security-audit

# Usa Serena para:
- Trace de chamadas de funções sensíveis (auth, payment)
- Auditoria de símbolos específicos
- Find all usages de APIs críticas
```

**Codex (QA Code):**
```
*code-review

# Usa Serena para:
- Análise de símbolos modificados em PR
- Encontrar testes relacionados a símbolos alterados
- Verificar impacto de mudanças via references
```

### ccusage - Tracking de Custos

**Oracle (Analyst):**
```
# Gerar relatório de custos do último mês
@oracle analyze token usage trends

# ccusage fornece via MCP:
- Custos diários/mensais
- Breakdown por tipo de request
- Projeções de budget
```

**Orion (Master):**
```
# Dashboard de performance do sistema
@master system metrics

# ccusage fornece:
- Session blocks (segmentação automática de sessões)
- Token usage por agente
- Cost optimization insights
```

**Morgan (PM):**
```
# Cost tracking por projeto
@pm budget analysis

# ccusage permite:
- Tracking de custos por epic/story (via session tags)
- Comparação de custos entre sprints
- Budget forecasting
```

---

## Troubleshooting

### Serena

**Erro: "uvx: command not found"**
```bash
# Instalar uv toolchain
curl -LsSf https://astral.sh/uv/install.sh | sh

# Adicionar ao PATH (se necessário)
export PATH="$HOME/.local/bin:$PATH"
```

**Erro: "Failed to clone repository"**
```bash
# Verificar conectividade com GitHub
git ls-remote https://github.com/oraios/serena.git

# Se firewall/proxy bloqueia:
# Configurar git proxy ou usar Docker
docker run --rm -i --network host \
  -v /Users/gabrielfofonka/aios-evo/neo-aios:/workspaces/neo-aios \
  ghcr.io/oraios/serena:latest \
  serena start-mcp-server --transport stdio
```

**Serena não encontra símbolos:**
```bash
# Verificar se LSP está ativo no projeto
# Serena requer language servers instalados (pyright, typescript-language-server, etc.)

# Para Python:
pip install pyright

# Para TypeScript:
npm install -g typescript-language-server
```

### ccusage

**Erro: "npx: command not found"**
```bash
# Instalar Node.js 18+
# macOS (Homebrew):
brew install node

# Verificar instalação:
node --version
npm --version
```

**Erro: "No Claude data found"**
```bash
# Verificar localização dos dados do Claude Code
ls -la ~/.config/claude/

# Se não existir, verificar localização antiga:
ls -la ~/.claude/

# Atualizar CLAUDE_CONFIG_DIR no .mcp.json se necessário
```

**Dados incompletos:**
```bash
# ccusage lê arquivos JSONL em:
# ~/.config/claude/logs/*.jsonl

# Verificar se logs existem:
ls -la ~/.config/claude/logs/

# Se vazio, Claude Code ainda não gerou logs suficientes
# (aguardar algumas sessões de uso)
```

**Múltiplas instalações do Claude Code:**
```bash
# Se você tem Claude Code em diferentes locais:
# Atualizar CLAUDE_CONFIG_DIR com múltiplos paths:
{
  "env": {
    "CLAUDE_CONFIG_DIR": "/path/1/.config/claude,/path/2/.config/claude"
  }
}
```

---

## Limitações Conhecidas

### Serena
- Requer language servers instalados (pyright, typescript-language-server, etc.)
- Performance pode degradar em projetos muito grandes (>100k arquivos)
- Suporte limitado a linguagens sem LSP maduro

### ccusage
- Apenas analisa dados locais (não acessa API da Anthropic)
- Requer que Claude Code tenha gerado logs JSONL
- Cálculos de custo baseados em pricing público (pode divergir de billing real)

---

## Recursos

**Serena:**
- [GitHub Repository](https://github.com/oraios/serena)
- [Official Documentation](https://oraios.github.io/serena/)
- [MCP Registry](https://mcp.so/server/serena/oraios)
- [Configuration Guide](https://oraios.github.io/serena/02-usage/050_configuration.html)

**ccusage:**
- [GitHub Repository](https://github.com/ryoppippi/ccusage)
- [Official Documentation](https://ccusage.com/)
- [MCP Server Guide](https://ccusage.com/guide/mcp-server)
- [Environment Variables](https://ccusage.com/guide/environment-variables)

---

*Última Atualização: 2026-02-06*
*Configurado por: Gage (DevOps)*
