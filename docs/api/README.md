# API Reference

Referencia completa da API Python do NEO-AIOS.

---

## Modulos Principais

| Modulo | Descricao |
|--------|-----------|
| `aios.agents` | Registry e loader de agentes |
| `aios.context` | Gerenciamento de sessao |
| `aios.core` | Utilidades core (waves, cache, profiling) |
| `aios.intelligence` | Roteamento de tarefas e ecomode |
| `aios.memory` | Sistema de memoria de agentes (gotchas, file evolution, hook bridge) |
| `aios.pipeline` | Pipeline de execucao, steps isolados, cost tracking |
| `aios.security` | Framework de validacao de seguranca |
| `aios.healthcheck` | Motor de health checks |
| `aios.quality` | Quality gates (3 camadas) |
| `aios.scope` | Enforcement de escopo |
| `aios.cli` | Interface de linha de comando |

---

## aios.agents

### AgentRegistry

Registry central de todos os agentes.

```python
from aios.agents import AgentRegistry

# Carregar registry do diretorio .claude/skills/
registry = AgentRegistry.load()

# Ou especificar diretorio
registry = AgentRegistry.load(Path("./custom-agents"))
```

#### Metodos

```python
# Buscar agente por ID
agent = registry.get("dev")  # Retorna AgentDefinition ou None

# Buscar agente (levanta excecao se nao encontrar)
agent = registry.get_or_raise("dev")  # Raises AgentNotFoundError

# Listar todos os agentes
all_agents = registry.all()  # List[AgentDefinition]

# Filtrar por tier
ics = registry.get_by_tier(AgentTier.IC)  # List[AgentDefinition]

# Filtrar por level
security_agents = registry.get_by_level(AgentLevel.SECURITY)

# Verificar se agente existe
if "dev" in registry:
    print("Dex esta registrado")

# Iteracao
for agent in registry:
    print(f"{agent.id}: {agent.name}")

# Quantidade de agentes
total = len(registry)
```

#### Validacao

```python
# Validar se agente pode executar acao
can_push = registry.validate_action("dev", "git_push", raise_on_violation=False)
# Retorna False

# Com excecao
try:
    registry.validate_action("dev", "git_push")  # Raises ScopeViolationError
except ScopeViolationError as e:
    print(f"Agent {e.agent_id} cannot {e.action}")

# Validar delegacao
can_delegate = registry.validate_delegation("vp-eng", "director-backend")
# Retorna True (VP pode delegar para Director)

# Regras especiais
can_push = registry.can_git_push("devops")  # True (apenas Gage)
can_code = registry.can_write_code("c-level")  # False (C-Level nao coda)
```

### AgentLoader

Carrega agentes com isolamento de identidade.

```python
from aios.agents.loader import AgentLoader
from aios.context import Session

registry = AgentRegistry.load()
session = Session.load()
loader = AgentLoader(registry, session)

# Carregar agente
agent = loader.load("dev")
print(agent.name)  # "Dex"

# Tentar carregar outro enquanto ativo
try:
    loader.load("devops")  # Raises AgentIdentityError
except AgentIdentityError as e:
    print(f"Cannot load {e.requested_agent} while {e.current_agent} is active")

# Descarregar agente
loader.unload()

# Agora pode carregar outro
agent = loader.load("devops")  # OK

# Propriedades
current = loader.current_agent  # AgentDefinition ou None
is_active = loader.is_agent_active  # bool

# Recarregar da sessao (apos auto-compact)
agent = loader.reload_from_session()

# Obter prompt do agente
prompt = loader.get_agent_prompt()

# Verificar isolamento de identidade
is_valid = loader.verify_identity_isolation("vou agir como Dex")
# Retorna False (padrao de simulacao detectado)
```

### AgentDefinition

Modelo de dados de um agente.

```python
from aios.agents.models import AgentDefinition, AgentTier, AgentLevel, AgentScope

# Criar agente programaticamente
agent = AgentDefinition(
    name="Dex",
    id="dev",
    tier=AgentTier.IC,
    level=AgentLevel.CORE,
    title="Full Stack Developer",
    icon="⚡",
    scope=AgentScope(
        can=["write_code", "git_commit"],
        cannot=["git_push", "database_ddl"]
    )
)

# Verificar permissoes
can_code = agent.can_do("write_code")  # True
cannot_push = agent.cannot_do("git_push")  # True

# Verificar delegacao
other_agent = registry.get("devops")
can_delegate = agent.can_delegate_to(other_agent)  # False (IC -> IC nao pode)
```

### Enums

```python
from aios.agents.models import AgentTier, AgentLevel

# Tiers (hierarquia)
AgentTier.C_LEVEL   # "c-level" - nivel 0
AgentTier.VP        # "vp" - nivel 1
AgentTier.DIRECTOR  # "director" - nivel 2
AgentTier.MANAGER   # "manager" - nivel 3
AgentTier.IC        # "ic" - nivel 4

# Verificar nivel
tier = AgentTier.VP
level = tier.level  # 1
can_delegate = tier.can_delegate_to(AgentTier.DIRECTOR)  # True

# Levels (tipo de agente)
AgentLevel.EXECUTIVE   # Executivos (C-Level, VP)
AgentLevel.CORE        # Agentes principais (Dev, DevOps, QA)
AgentLevel.SECURITY    # Sub-agentes de seguranca
AgentLevel.SPECIALIST  # Especialistas de dominio
AgentLevel.CONTENT     # Criacao de conteudo
AgentLevel.AUTOMATION  # Agentes autonomos
```

---

## aios.security

### SecurityOrchestrator

Orquestra validadores de seguranca.

```python
from pathlib import Path
from aios.security import SecurityOrchestrator, ScanConfig
from aios.security.validators import validator_registry

# Usar instancia global
from aios.security.orchestrator import security_orchestrator

# Ou criar com configuracao customizada
config = ScanConfig(
    timeout_per_validator=30.0,  # Timeout por validator
    max_workers=4,               # Validators paralelos
    fail_fast=False,             # Parar no primeiro CRITICAL?
    quick_scan_validators=[      # Validators para quick scan
        "sec-secret-scanner",
        "sec-xss-hunter",
        "sec-injection-detector"
    ]
)
orchestrator = SecurityOrchestrator(validator_registry, config)

# Scan sincrono
report = orchestrator.scan(Path("./src"))

# Scan assincrono
import asyncio
report = asyncio.run(orchestrator.scan_async(Path("./src")))

# Quick scan (pre-commit)
report = orchestrator.quick_scan(Path("./src"))

# Full audit (PR review)
report = orchestrator.full_audit(Path("./src"))

# Validators especificos
report = orchestrator.scan(
    Path("./src"),
    validators=["sec-xss-hunter", "sec-injection-detector"]
)

# Com callback de progresso
def on_progress(validator_id: str, current: int, total: int, status: str):
    print(f"[{current}/{total}] {validator_id}: {status}")

report = orchestrator.scan(Path("./src"), progress_callback=on_progress)
```

### SecurityReport

Relatorio de scan de seguranca.

```python
from aios.security.models import SecurityReport, Severity, FindingCategory

# Propriedades do relatorio
print(f"Total: {report.total_findings}")
print(f"Critical: {report.critical_findings}")
print(f"High: {report.high_findings}")
print(f"Medium: {report.medium_findings}")
print(f"Low: {report.low_findings}")
print(f"Info: {report.info_findings}")

print(f"Files scanned: {report.files_scanned}")
print(f"Duration: {report.total_duration_ms}ms")
print(f"Has blockers: {report.has_blockers}")  # CRITICAL ou HIGH
print(f"Has errors: {report.has_errors}")

# Filtrar findings
critical_findings = report.get_findings_by_severity(Severity.CRITICAL)
xss_findings = report.get_findings_by_category(FindingCategory.XSS)

# Verificar se deve bloquear
should_block_commit = orchestrator.should_block_commit(report)  # CRITICAL
should_block_merge = orchestrator.should_block_merge(report)    # CRITICAL ou HIGH

# Sumario
summary = orchestrator.get_scan_summary(report)
# {
#     "total_findings": 5,
#     "critical": 0,
#     "high": 2,
#     "medium": 3,
#     "files_scanned": 42,
#     "validators_run": 18,
#     "should_block_commit": False,
#     "should_block_merge": True,
#     "duration_ms": 1234
# }

# Findings ordenados por severidade
sorted_findings = orchestrator.get_all_findings_sorted(report)
```

### SecurityFinding

Um finding individual de seguranca.

```python
from aios.security.models import SecurityFinding, Severity, FindingCategory, CodeLocation

finding = SecurityFinding(
    id="xss-001",
    validator_id="sec-xss-hunter",
    severity=Severity.HIGH,
    category=FindingCategory.XSS,
    title="XSS vulnerability in user input",
    description="User input passed directly to unsafe render method without sanitization",
    location=CodeLocation(
        file_path="src/components/Comment.tsx",
        line_start=42,
        line_end=42,
        column_start=10,
        column_end=50,
        snippet='<div {...unsafeRenderProps} />'
    ),
    recommendation="Sanitize input with DOMPurify before rendering",
    auto_fixable=True,
    confidence=0.95,
    cwe_id="CWE-79",
    owasp_id="A03:2021"
)

# Propriedades
print(finding.severity.value)  # "high"
print(finding.category.value)  # "xss"
print(finding.location.file_path)  # "src/components/Comment.tsx"
```

### Severity e Category

```python
from aios.security.models import Severity, FindingCategory

# Severidades (maior para menor)
Severity.CRITICAL  # Risco imediato, bloqueia commit
Severity.HIGH      # Risco significativo, bloqueia PR
Severity.MEDIUM    # Preocupacao, deve corrigir
Severity.LOW       # Menor, pode agendar
Severity.INFO      # Informativo, best practice

# Categorias (mapeiam para OWASP/CWE)
FindingCategory.XSS              # Cross-Site Scripting
FindingCategory.INJECTION        # SQL/Command Injection
FindingCategory.AUTH             # Authentication issues
FindingCategory.CRYPTO           # Cryptography issues
FindingCategory.CONFIG           # Configuration issues
FindingCategory.DATA_EXPOSURE    # Data exposure
FindingCategory.INPUT_VALIDATION # Input validation
FindingCategory.ACCESS_CONTROL   # Access control
```

---

## aios.healthcheck

### HealthCheckEngine

Motor de health checks.

```python
from aios.healthcheck import HealthCheckEngine, health_engine, HealthStatus

# Usar instancia global
health = health_engine.run_all()

# Ou criar engine customizada
engine = HealthCheckEngine()

# Rodar todos os checks
health = engine.run_all()

# Rodar check especifico
health = engine.run_check("agents")

# Rodar multiplos checks
health = engine.run_checks(["agents", "session", "config"])

# Propriedades da engine
names = engine.check_names  # Lista de nomes
count = engine.check_count  # Quantidade

# Verificar resultado
print(health.status)  # HealthStatus.HEALTHY, DEGRADED, ou UNHEALTHY
print(health.healthy_count)
print(health.unhealthy_count)
print(health.is_healthy)  # bool
```

### SystemHealth

Resultado dos health checks.

```python
from aios.healthcheck.models import SystemHealth, HealthStatus, CheckResult

# Propriedades
print(health.status)          # Status geral
print(health.is_healthy)      # True se HEALTHY
print(health.healthy_count)   # Quantidade de checks OK
print(health.unhealthy_count) # Quantidade de checks falhando
print(health.degraded_count)  # Quantidade de checks degradados
print(health.unknown_count)   # Quantidade de checks desconhecidos

# Acessar checks individuais
for check in health.checks:
    print(f"{check.name}: {check.status} - {check.message}")

# Obter check especifico
agent_check = health.get_check("agents")
if agent_check:
    print(agent_check.status)
```

### HealthStatus

```python
from aios.healthcheck.models import HealthStatus

HealthStatus.HEALTHY    # Tudo funcionando
HealthStatus.DEGRADED   # Funcionando com problemas
HealthStatus.UNHEALTHY  # Falha
HealthStatus.UNKNOWN    # Nao verificado
```

---

## aios.context

### Session

Gerenciamento de sessao (persiste apos auto-compact).

```python
from aios.context import Session

# Carregar sessao existente ou criar nova
session = Session.load()

# Ou especificar arquivo
session = Session.load(Path(".aios/session-state.json"))

# Ativar agente
session.activate_agent("dev", ".claude/skills/dev/SKILL.md")

# Desativar agente
session.deactivate_agent()

# Atualizar atividade
session.update_activity()

# Definir tarefa atual
session.set_current_task("Implementing login feature")

# Definir contexto de projeto
session.set_project_context(
    project="neo-aios",
    epic="epic-1",
    story="story-1.1"
)

# Salvar estado
session.save()

# Acessar estado
state = session.state
print(state.active_agent)     # "dev" ou None
print(state.agent_file)       # Path do SKILL.md
print(state.activated_at)     # datetime
print(state.last_activity)    # datetime
print(state.current_task)     # str ou None
print(state.project_context)  # dict
```

---

## aios.scope

### ScopeEnforcer

Enforcement de escopo em runtime.

```python
from aios.scope import ScopeEnforcer, ActionType

enforcer = ScopeEnforcer(registry)

# Verificar acao
result = enforcer.check_action("dev", ActionType.GIT_PUSH)
# result.allowed = False
# result.reason = "Action git_push is in agent's cannot list"

# Verificar com bloqueio
try:
    enforcer.enforce("dev", ActionType.GIT_PUSH)
except ScopeViolationError:
    print("Blocked!")

# Verificar path de arquivo
result = enforcer.check_file_write("dev", Path("src/main.py"))
# Verifica se agente pode escrever neste path
```

### ActionType

```python
from aios.scope import ActionType

ActionType.WRITE_CODE
ActionType.GIT_COMMIT
ActionType.GIT_PUSH
ActionType.GIT_FORCE_PUSH
ActionType.CREATE_PR
ActionType.MERGE_PR
ActionType.DATABASE_DDL
ActionType.PRODUCTION_DEPLOY
ActionType.ARCHITECTURE_DECISION
```

---

## aios.pipeline

### PipelineManager

Gerencia estado de pipeline com dependency graph e file-based locking.

```python
from aios.pipeline import PipelineManager, PipelineStory, StoryStatus

# Carregar estado (cria arquivo se nao existe)
manager = PipelineManager()
manager.load()

# Adicionar stories com dependencias
manager.add_story(PipelineStory(id="auth", name="Authentication"))
manager.add_story(PipelineStory(id="dashboard", name="Dashboard", dependencies=["auth"]))

# Obter stories prontas (wave 1 do dependency graph)
ready = manager.get_ready_stories()  # Retorna ["auth"]

# Atualizar status (propaga dependencias automaticamente)
manager.update_story_status("auth", StoryStatus.DONE)
ready = manager.get_ready_stories()  # Agora retorna ["dashboard"]

# Detectar ciclos
has_cycles = manager.detect_cycles()

# Analise completa de dependencias (via WaveAnalyzer)
analysis = manager.analyze_dependencies()
print(f"Waves: {analysis.wave_count}, Speedup: {analysis.parallelism_speedup:.1f}x")

# File-based locking para sessoes paralelas
manager.acquire_lock("session-1")
manager.save()
manager.release_lock("session-1")
```

### StepExecutor

Orquestra execucao sequencial de steps isolados com checkpoint.

```python
from aios.pipeline import StepExecutor, StepRegistry

# Carregar step definitions de YAML
registry = StepRegistry.load()
steps = registry.get_workflow("greenfield-fullstack")

# Executar story step-by-step
executor = StepExecutor(manager, runner, fail_fast=True)
results = executor.execute_story("auth", steps, story_path="docs/stories/auth.md")

# Retomar de onde parou (apos crash/timeout)
results = executor.resume_story("auth", steps)
```

### StoryCostReport

Tracking de custo por model tier com calculo de economia.

```python
from aios.pipeline import StoryCostReport

# Construir report a partir de resultados
steps = [("haiku", 8000), ("sonnet", 12000), ("opus", 25000)]
report = StoryCostReport.from_step_results("auth", steps)

print(f"Custo total: ${report.total_cost_usd:.4f}")
print(f"Se fosse tudo opus: ${report.all_opus_cost_usd:.4f}")
print(f"Economia: ${report.savings_vs_all_opus_usd:.4f} ({report.savings_percentage:.0f}%)")
```

### TaskRouter.classify_by_step

Roteamento de modelo por step com cadeia de prioridade.

```python
from aios.intelligence.router import TaskRouter

router = TaskRouter()

# Prioridade 1: model explicito do step-registry
result = router.classify_by_step("run-tests", step_model="haiku")
# -> model="haiku", confidence=1.0

# Prioridade 2: fallback para agent
result = router.classify_by_step("step-1", agent_id="qa")
# -> model="opus" (qa = MAX effort)

# Prioridade 3: default
result = router.classify_by_step("unknown")
# -> model="opus", confidence=0.5
```

---

## aios.memory

### GotchasMemory

Rastreia problemas recorrentes e auto-promove a regras.

```python
from pathlib import Path
from aios.memory.gotchas import GotchasMemory

# Criar instancia com diretorio de storage
memory = GotchasMemory(storage_dir=Path(".aios/memory"))

# Registrar um problema
memory.record_issue(
    category="macOS",
    description="grep -P not supported on macOS",
    context=["agent:dev", "file:hooks/pre-prompt-context.sh"]
)

# Apos 3 ocorrencias (threshold padrao), auto-promove a gotcha
gotchas = memory.get_gotchas()
for g in gotchas:
    print(f"[{g.category}] {g.description} (count: {g.occurrence_count})")

# Gerar texto para injecao em prompt
prompt_text = memory.format_for_prompt(agent_id="dev")
```

### FileEvolutionTracker

Detecta conflitos quando multiplos agentes modificam os mesmos arquivos.

```python
from pathlib import Path
from aios.memory.file_evolution import FileEvolutionTracker

tracker = FileEvolutionTracker(storage_dir=Path(".aios/memory/evolution"))

# Registrar modificacao
tracker.record_modification(
    file_path="src/main.py",
    agent_id="dev",
    task_id="implement-auth"
)

# Verificar conflitos
conflicts = tracker.check_conflicts(agent_id="dev")
for c in conflicts:
    print(f"{c.file_path}: {c.severity} — {len(c.agents)} agents")

# Detectar drift (mudancas divergentes)
drift = tracker.detect_drift(file_path="src/main.py")
print(f"Agents: {drift.agents}, Severity: {drift.severity}")

# Limpar entradas antigas
tracker.cleanup(days=7)
```

### Hook Bridge CLI

Ponte entre hooks bash e modulos Python.

```bash
# Registrar mudanca de arquivo
uv run python -m aios.memory.hook_bridge record-file-change \
  --agent dev --file src/main.py --action modify

# Verificar conflitos
uv run python -m aios.memory.hook_bridge check-conflicts --agent dev

# Registrar gotcha
uv run python -m aios.memory.hook_bridge record-gotcha \
  --agent dev --category "macOS" --description "grep -P not supported"

# Obter gotchas para prompt
uv run python -m aios.memory.hook_bridge get-gotchas --agent dev --format text
```

---

## aios.cli

### Comandos Programaticos

```python
from click.testing import CliRunner
from aios.cli import cli

runner = CliRunner()

# Rodar comando
result = runner.invoke(cli, ["agent", "list"])
print(result.output)
print(result.exit_code)

# Comandos de memoria
result = runner.invoke(cli, ["memory", "list-agents"])
result = runner.invoke(cli, ["memory", "show", "dev"])
result = runner.invoke(cli, ["gotchas", "list", "--agent", "dev"])
result = runner.invoke(cli, ["gotchas", "stats"])
result = runner.invoke(cli, ["conflicts", "check"])
result = runner.invoke(cli, ["conflicts", "history", "--days", "7"])
```

---

## Exemplos de Uso

### Scan de Seguranca Completo

```python
from pathlib import Path
from aios.security.orchestrator import security_orchestrator
from aios.security.models import Severity

# Rodar scan
report = security_orchestrator.full_audit(Path("./src"))

# Verificar resultado
if report.has_blockers:
    print("BLOCKED: Critical or High findings detected")
    for finding in report.get_findings_by_severity(Severity.CRITICAL):
        print(f"  CRITICAL: {finding.title}")
        print(f"    File: {finding.location.file_path}:{finding.location.line_start}")
    for finding in report.get_findings_by_severity(Severity.HIGH):
        print(f"  HIGH: {finding.title}")
        print(f"    File: {finding.location.file_path}:{finding.location.line_start}")
else:
    print("PASSED: No blockers found")
```

### Ativacao de Agente com Validacao

```python
from aios.agents import AgentRegistry
from aios.agents.loader import AgentLoader
from aios.context import Session

registry = AgentRegistry.load()
session = Session.load()
loader = AgentLoader(registry, session)

# Verificar se agente existe
if "dev" not in registry:
    raise ValueError("Agent not found")

# Carregar com isolamento
agent = loader.load("dev")

# Verificar scope antes de acao
if not registry.can_git_push(agent.id):
    print(f"{agent.name} cannot push. Delegate to Gage.")

# Cleanup
loader.unload()
```

### Health Check com Alertas

```python
from aios.healthcheck import health_engine
from aios.healthcheck.models import HealthStatus

health = health_engine.run_all()

if not health.is_healthy:
    unhealthy_checks = [c for c in health.checks if c.status == HealthStatus.UNHEALTHY]
    for check in unhealthy_checks:
        print(f"ALERT: {check.name} is unhealthy: {check.message}")
```

---

*NEO-AIOS API Reference v0.2.0 (Unreleased)*
