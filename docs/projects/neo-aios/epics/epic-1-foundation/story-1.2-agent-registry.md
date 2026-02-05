# Story 1.2: Agent Registry

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Story 1.1

---

## Objetivo

Criar o sistema de registro de agentes que carrega definições dos SKILL.md e disponibiliza para o sistema.

## Tasks

### Task 1: Criar modelo AgentDefinition

**Arquivo:** `src/aios/models/agent.py`
**Tipo:** create

**O que fazer:**
1. Criar modelo Pydantic para AgentDefinition
2. Incluir todos os campos do SKILL.md
3. Adicionar validações

**Código esperado:**
```python
"""Agent definition models."""

from typing import Optional
from pydantic import BaseModel, Field


class AgentScope(BaseModel):
    """Agent scope definition."""

    can: list[str] = Field(default_factory=list)
    cannot: list[str] = Field(default_factory=list)


class AgentCommand(BaseModel):
    """Agent command definition."""

    name: str
    description: str


class AgentDefinition(BaseModel):
    """Complete agent definition from SKILL.md."""

    # Core fields
    name: str
    id: str = Field(alias="id")
    icon: str = ""
    title: str = ""

    # Optional tier info (for backwards compatibility)
    tier: str = "ic"
    level: str = "core"

    # Scope
    scope: AgentScope = Field(default_factory=AgentScope)

    # Relationships
    reports_to: Optional[str] = None
    collaborates_with: list[str] = Field(default_factory=list)
    delegates_to: list[str] = Field(default_factory=list)

    # Commands
    commands: list[AgentCommand] = Field(default_factory=list)

    # Behavioral
    behavioral_rules: list[str] = Field(default_factory=list)

    # Source file
    skill_path: Optional[str] = None

    class Config:
        populate_by_name = True

    def can_do(self, action: str) -> bool:
        """Check if agent can perform action."""
        if action in self.scope.cannot:
            return False
        return action in self.scope.can or len(self.scope.can) == 0

    def cannot_do(self, action: str) -> bool:
        """Check if action is explicitly forbidden."""
        return action in self.scope.cannot
```

**Acceptance Criteria:**
- [ ] Modelo criado com validação Pydantic
- [ ] Métodos can_do/cannot_do funcionando
- [ ] Type hints completos

**Validação:**
```bash
uv run python -c "from aios.models.agent import AgentDefinition; print('OK')"
```

---

### Task 2: Criar SKILL.md Parser

**Arquivo:** `src/aios/agents/parser.py`
**Tipo:** create

**O que fazer:**
1. Criar parser que lê SKILL.md
2. Extrair bloco YAML do markdown
3. Converter para AgentDefinition

**Código esperado:**
```python
"""SKILL.md parser for agent definitions."""

import re
from pathlib import Path
from typing import Optional

import yaml

from aios.models.agent import AgentDefinition


class SkillParser:
    """Parser for SKILL.md agent definition files."""

    YAML_BLOCK_PATTERN = re.compile(
        r"```ya?ml\n(.*?)```",
        re.DOTALL | re.MULTILINE
    )

    def parse_file(self, file_path: Path) -> Optional[AgentDefinition]:
        """Parse a SKILL.md file and return AgentDefinition."""
        if not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")
        return self.parse_content(content, str(file_path))

    def parse_content(
        self,
        content: str,
        source_path: Optional[str] = None
    ) -> Optional[AgentDefinition]:
        """Parse SKILL.md content and return AgentDefinition."""
        yaml_blocks = self.YAML_BLOCK_PATTERN.findall(content)

        if not yaml_blocks:
            return None

        # First YAML block should contain agent definition
        yaml_content = yaml_blocks[0]

        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            return None

        if not data or "agent" not in data:
            return None

        # Flatten agent data
        agent_data = data.get("agent", {})

        # Add scope if present at root level
        if "scope" in data:
            agent_data["scope"] = data["scope"]

        # Add other root-level fields
        for key in ["commands", "behavioral_rules", "hierarchy"]:
            if key in data:
                agent_data[key] = data[key]

        # Handle hierarchy fields
        if "hierarchy" in data:
            hierarchy = data["hierarchy"]
            agent_data["reports_to"] = hierarchy.get("reports_to")
            agent_data["collaborates_with"] = hierarchy.get("collaborates_with", [])
            agent_data["delegates_to"] = hierarchy.get("delegates_to", [])

        # Add source path
        agent_data["skill_path"] = source_path

        try:
            return AgentDefinition(**agent_data)
        except Exception:
            return None


# Singleton instance
skill_parser = SkillParser()
```

**Acceptance Criteria:**
- [ ] Parser extrai YAML do markdown
- [ ] Converte para AgentDefinition
- [ ] Handles errors gracefully

**Validação:**
```bash
uv run pytest tests/test_agents/test_parser.py -v
```

---

### Task 3: Criar Agent Registry

**Arquivo:** `src/aios/agents/registry.py`
**Tipo:** create

**O que fazer:**
1. Criar registro central de agentes
2. Carregar agentes de diretório
3. Métodos de busca (by id, by category)

**Código esperado:**
```python
"""Central registry for all agents."""

from pathlib import Path
from typing import Optional

from aios.models.agent import AgentDefinition
from aios.agents.parser import skill_parser


class AgentRegistry:
    """Central registry of all available agents."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinition] = {}
        self._loaded = False

    def load_from_directory(self, agents_dir: Path) -> int:
        """Load all agents from a directory. Returns count loaded."""
        if not agents_dir.exists():
            return 0

        count = 0
        for agent_path in agents_dir.iterdir():
            if not agent_path.is_dir():
                continue

            skill_file = agent_path / "SKILL.md"
            if not skill_file.exists():
                continue

            agent = skill_parser.parse_file(skill_file)
            if agent:
                self._agents[agent.id] = agent
                count += 1

        self._loaded = True
        return count

    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_all(self) -> list[AgentDefinition]:
        """Get all registered agents."""
        return list(self._agents.values())

    def get_by_category(self, category: str) -> list[AgentDefinition]:
        """Get agents by category (tier or level)."""
        return [
            a for a in self._agents.values()
            if a.tier == category or a.level == category
        ]

    def exists(self, agent_id: str) -> bool:
        """Check if agent exists."""
        return agent_id in self._agents

    @property
    def count(self) -> int:
        """Number of registered agents."""
        return len(self._agents)

    @property
    def is_loaded(self) -> bool:
        """Check if registry has been loaded."""
        return self._loaded

    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
        self._loaded = False


# Global registry instance
agent_registry = AgentRegistry()
```

**Acceptance Criteria:**
- [ ] Carrega agentes de diretório
- [ ] Busca por ID funciona
- [ ] Busca por categoria funciona
- [ ] Singleton pattern

**Validação:**
```bash
uv run pytest tests/test_agents/test_registry.py -v
```

---

### Task 4: Criar testes

**Arquivo:** `tests/test_agents/test_parser.py`
**Tipo:** create

**Código esperado:**
```python
"""Tests for SKILL.md parser."""

import pytest
from pathlib import Path

from aios.agents.parser import SkillParser


@pytest.fixture
def parser() -> SkillParser:
    return SkillParser()


def test_parse_valid_skill_md(parser: SkillParser, tmp_path: Path) -> None:
    """Test parsing a valid SKILL.md file."""
    skill_content = '''
# Test Agent

```yaml
agent:
  name: TestAgent
  id: test-agent
  icon: "🧪"
  title: Test Agent

scope:
  can:
    - test_action
    - another_action
  cannot:
    - forbidden_action
```
'''
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(skill_content)

    agent = parser.parse_file(skill_file)

    assert agent is not None
    assert agent.name == "TestAgent"
    assert agent.id == "test-agent"
    assert agent.icon == "🧪"
    assert "test_action" in agent.scope.can
    assert "forbidden_action" in agent.scope.cannot


def test_parse_missing_file(parser: SkillParser, tmp_path: Path) -> None:
    """Test parsing a non-existent file."""
    result = parser.parse_file(tmp_path / "nonexistent.md")
    assert result is None


def test_parse_invalid_yaml(parser: SkillParser, tmp_path: Path) -> None:
    """Test parsing invalid YAML."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("```yaml\ninvalid: yaml: content:\n```")

    result = parser.parse_file(skill_file)
    assert result is None


def test_can_do_method(parser: SkillParser, tmp_path: Path) -> None:
    """Test AgentDefinition.can_do method."""
    skill_content = '''
```yaml
agent:
  name: Test
  id: test

scope:
  can:
    - allowed_action
  cannot:
    - forbidden_action
```
'''
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(skill_content)

    agent = parser.parse_file(skill_file)
    assert agent is not None
    assert agent.can_do("allowed_action") is True
    assert agent.can_do("forbidden_action") is False
    assert agent.cannot_do("forbidden_action") is True
```

**Arquivo:** `tests/test_agents/test_registry.py`
**Tipo:** create

**Código esperado:**
```python
"""Tests for agent registry."""

import pytest
from pathlib import Path

from aios.agents.registry import AgentRegistry


@pytest.fixture
def registry() -> AgentRegistry:
    return AgentRegistry()


@pytest.fixture
def agents_dir(tmp_path: Path) -> Path:
    """Create a temporary agents directory with sample agents."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # Create test agent 1
    agent1_dir = agents_dir / "agent-one"
    agent1_dir.mkdir()
    (agent1_dir / "SKILL.md").write_text('''
```yaml
agent:
  name: AgentOne
  id: agent-one
  tier: ic
  level: core

scope:
  can:
    - action_one
```
''')

    # Create test agent 2
    agent2_dir = agents_dir / "agent-two"
    agent2_dir.mkdir()
    (agent2_dir / "SKILL.md").write_text('''
```yaml
agent:
  name: AgentTwo
  id: agent-two
  tier: ic
  level: security

scope:
  can:
    - action_two
```
''')

    return agents_dir


def test_load_from_directory(registry: AgentRegistry, agents_dir: Path) -> None:
    """Test loading agents from directory."""
    count = registry.load_from_directory(agents_dir)

    assert count == 2
    assert registry.is_loaded is True
    assert registry.count == 2


def test_get_agent(registry: AgentRegistry, agents_dir: Path) -> None:
    """Test getting agent by ID."""
    registry.load_from_directory(agents_dir)

    agent = registry.get("agent-one")
    assert agent is not None
    assert agent.name == "AgentOne"


def test_get_nonexistent_agent(registry: AgentRegistry, agents_dir: Path) -> None:
    """Test getting non-existent agent."""
    registry.load_from_directory(agents_dir)

    agent = registry.get("nonexistent")
    assert agent is None


def test_get_by_category(registry: AgentRegistry, agents_dir: Path) -> None:
    """Test getting agents by category."""
    registry.load_from_directory(agents_dir)

    core_agents = registry.get_by_category("core")
    assert len(core_agents) == 1
    assert core_agents[0].id == "agent-one"

    security_agents = registry.get_by_category("security")
    assert len(security_agents) == 1
    assert security_agents[0].id == "agent-two"


def test_clear_registry(registry: AgentRegistry, agents_dir: Path) -> None:
    """Test clearing the registry."""
    registry.load_from_directory(agents_dir)
    assert registry.count == 2

    registry.clear()
    assert registry.count == 0
    assert registry.is_loaded is False
```

---

## Validação Final

- [ ] Parser funciona com SKILL.md reais
- [ ] Registry carrega todos os 15 agentes
- [ ] Testes passando com 90%+ coverage
- [ ] mypy --strict sem erros

## Notas para Ralph

- O parser deve ser tolerante a variações no formato YAML
- Usar yaml.safe_load (nunca yaml.load)
- Manter agentes em dict para O(1) lookup
- Testar com os SKILL.md reais em agents/
