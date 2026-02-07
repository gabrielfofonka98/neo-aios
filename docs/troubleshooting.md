# Troubleshooting Guide

Guia para resolver problemas comuns no NEO-AIOS.

---

## Problemas de Instalacao

### Comando `aios` nao encontrado

**Sintoma:**
```
zsh: command not found: aios
```

**Causa:** Ambiente virtual nao ativado ou CLI nao instalada.

**Solucao:**
```bash
# Opcao 1: Ative o ambiente
source .venv/bin/activate
aios --help

# Opcao 2: Use via uv
uv run aios --help
```

---

### Erro de versao Python

**Sintoma:**
```
NEO-AIOS requires Python 3.12+. Current version: 3.10.x
```

**Causa:** Python muito antigo.

**Solucao:**
```bash
# Instale Python 3.12+
# macOS
brew install python@3.12

# Recrie ambiente
rm -rf .venv
uv venv --python 3.12
uv sync --extra dev
```

---

### Erro ao instalar dependencias

**Sintoma:**
```
error: No solution found when resolving dependencies
```

**Causa:** Conflito de versoes ou lockfile desatualizado.

**Solucao:**
```bash
# Regenere o lockfile
rm uv.lock
uv sync --extra dev
```

---

## Problemas com Agentes

### Agente nao encontrado

**Sintoma:**
```
Agent 'xxx' not found in registry
```

**Causa:** SKILL.md nao existe ou YAML invalido.

**Solucao:**
```bash
# Verifique se arquivo existe
ls .claude/skills/xxx/SKILL.md

# Valide o YAML (deve ter bloco agent:)
cat .claude/skills/xxx/SKILL.md | grep -A5 "^agent:"
```

---

### Erro de identidade ao trocar agente

**Sintoma:**
```
AgentIdentityError: Cannot load 'devops' while 'dev' is active.
```

**Causa:** Tentando carregar agente sem descarregar o atual.

**Solucao:**
```python
# Descarregue primeiro
loader.unload()

# Ou via Claude Code
*exit  # Sai do agente atual
/devops  # Ativa novo agente
```

---

### Agente nao persiste apos auto-compact

**Sintoma:** Claude Code esquece qual agente estava ativo apos compactar contexto.

**Causa:** Session state nao foi salvo ou arquivo corrompido.

**Solucao:**
```bash
# Verifique o arquivo de sessao
cat .aios/session-state.json

# Se corrompido, limpe e reative
rm .aios/session-state.json
/dev  # Reativa agente
```

---

## Problemas com Security Scan

### Scan demora muito

**Sintoma:** Scan travado ou lento.

**Causa:** Muitos arquivos ou validators sem timeout.

**Solucao:**
```python
# Use quick scan em vez de full
from aios.security.orchestrator import security_orchestrator
report = security_orchestrator.quick_scan(Path("./src"))

# Ou configure timeout menor
from aios.security import ScanConfig
config = ScanConfig(timeout_per_validator=10.0)
```

---

### Validator com erro

**Sintoma:**
```
Validator 'sec-xxx' failed: [error message]
```

**Causa:** Validator encontrou condicao inesperada.

**Solucao:**
```bash
# Rode scan sem o validator problematico
aios scan full --path ./src --validator sec-xss-hunter
# Adicione apenas os validators que funcionam

# Verifique logs para mais detalhes
aios scan full --path ./src -v
```

---

### False positives

**Sintoma:** Scan reporta vulnerabilidade que nao existe.

**Causa:** Padrao detectado em contexto invalido.

**Solucao:**
1. Verifique se e realmente false positive
2. Adicione comentario ignorando (se suportado)
3. Reporte como issue para melhorar validator

---

## Problemas com CLI

### Erro ao rodar comando

**Sintoma:**
```
Error: No such command 'xxx'
```

**Causa:** Comando nao existe ou modulo nao carregado.

**Solucao:**
```bash
# Liste comandos disponiveis
aios --help

# Comandos validos:
# agent, scan, health, gate, version
```

---

### Output truncado ou corrompido

**Sintoma:** Tabelas ou texto mal formatado.

**Causa:** Terminal nao suporta rich output.

**Solucao:**
```bash
# Use modo quiet
aios -q agent list

# Ou verifique suporte a unicode
echo $TERM
# Deve ser xterm-256color ou similar
```

---

## Problemas com Health Check

### Check falhando

**Sintoma:**
```
UNHEALTHY: agents - Registry failed to load
```

**Causa:** Diretorio .claude/skills/ com problema.

**Solucao:**
```bash
# Verifique estrutura
ls -la .claude/skills/

# Cada agente deve ter:
# .claude/skills/{id}/SKILL.md

# Valide YAML de cada SKILL.md
for f in .claude/skills/*/SKILL.md; do
  echo "Checking $f"
  python -c "import yaml; yaml.safe_load(open('$f').read())"
done
```

---

### Session check falhando

**Sintoma:**
```
UNHEALTHY: session - Cannot access session file
```

**Causa:** Diretorio .aios/ nao existe ou sem permissao.

**Solucao:**
```bash
# Crie diretorio
mkdir -p .aios

# Verifique permissoes
ls -la .aios/
chmod 755 .aios/
```

---

## Problemas com Quality Gates

### Pre-commit falhando

**Sintoma:**
```
BLOCKED: CRITICAL findings detected
```

**Causa:** Codigo com vulnerabilidade critica.

**Solucao:**
1. Veja detalhes do finding
2. Corrija a vulnerabilidade
3. Re-rode scan para confirmar

```bash
# Ver detalhes
aios scan full --path ./src -v

# Apos corrigir
aios scan quick --path ./src
```

---

### Mypy falhando

**Sintoma:**
```
error: Function is missing return type annotation
```

**Causa:** Codigo sem type hints (mypy --strict).

**Solucao:**
```python
# Adicione type hints
def my_function(x: int) -> str:  # Antes era: def my_function(x)
    return str(x)
```

---

### Ruff falhando

**Sintoma:**
```
error: E501 line too long
```

**Causa:** Lint violation.

**Solucao:**
```bash
# Auto-fix o que for possivel
uv run ruff check --fix src/

# Verifique novamente
uv run ruff check src/
```

---

## Problemas de Scope

### Acao bloqueada

**Sintoma:**
```
ScopeViolationError: Agent 'dev' cannot perform 'git_push'
```

**Causa:** Agente tentando acao fora do escopo.

**Solucao:**
```
Delegue para o agente correto:
- git_push -> Gage (devops)
- database_ddl -> Dara (data-engineer)
- architecture -> Aria (architect)
```

---

### Delegacao bloqueada

**Sintoma:**
```
DelegationViolationError: Cannot delegate from IC to VP
```

**Causa:** Delegacao vai na direcao errada (so pode delegar para BAIXO).

**Solucao:**
```
Delegacao permitida:
C-Level -> VP -> Director -> Manager -> IC

NAO permitido:
IC -> Manager (escalation, nao delegacao)
IC -> IC (colaboracao, nao delegacao)
```

---

## Logs e Debug

### Habilitar verbose

```bash
aios -v <command>
```

### Ver estado da sessao

```bash
cat .aios/session-state.json | python -m json.tool
```

### Verificar registry

```python
from aios.agents import AgentRegistry
registry = AgentRegistry.load()
for agent in registry:
    print(f"{agent.id}: {agent.name} ({agent.tier.value})")
```

---

## Contato

Se o problema persistir:

1. Verifique se ja existe issue no GitHub
2. Colete logs e estado do sistema
3. Abra issue com reproducao minima

---

*NEO-AIOS Troubleshooting Guide v0.1.0*
