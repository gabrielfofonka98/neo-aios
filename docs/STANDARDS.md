# NEO-AIOS Technical Standards

**Version:** 1.0.0
**Last Updated:** 2026-02-04

Read this file BEFORE any implementation. These standards are enforced by quality gates.

---

## 1. Code Style

### 1.1 Python

- **Version:** 3.12+
- **Package Manager:** uv
- **Linting:** ruff
- **Type Checking:** mypy --strict
- **Testing:** pytest
- **Coverage:** 80%+ required

### 1.2 Naming Conventions

```python
# Variables and functions: snake_case
agent_name = "dex"
def validate_scope():
    pass

# Classes: PascalCase
class AgentRegistry:
    pass

# Constants: SCREAMING_SNAKE_CASE
MAX_FIX_ATTEMPTS = 3
DEFAULT_TIMEOUT = 30

# Private members: _prefix
_internal_state = {}

# Type aliases: PascalCase
AgentId = str
ScopeList = list[str]
```

### 1.3 File Organization

```
src/aios/
├── __init__.py              # Package exports
├── module/
│   ├── __init__.py          # Module exports
│   ├── models.py            # Pydantic models
│   ├── service.py           # Business logic
│   └── exceptions.py        # Custom exceptions
```

### 1.4 Import Order

```python
# 1. Standard library
from pathlib import Path
from typing import TYPE_CHECKING

# 2. Third-party
import click
from pydantic import BaseModel

# 3. Local (absolute imports)
from aios.agents.registry import AgentRegistry
from aios.config.loader import ConfigLoader
```

---

## 2. Type Safety

### 2.1 All Code Must Be Typed

```python
# GOOD
def get_agent(agent_id: str) -> AgentDefinition | None:
    return self.agents.get(agent_id)

# BAD
def get_agent(agent_id):
    return self.agents.get(agent_id)
```

### 2.2 Use Pydantic v2 for Data Models

```python
from pydantic import BaseModel, Field

class Finding(BaseModel):
    """Security finding from a validator."""

    id: str = Field(..., description="Unique finding ID")
    validator: str = Field(..., description="Validator that found it")
    severity: Severity
    file: Path
    line: int
    description: str

    model_config = {"frozen": True}
```

### 2.3 Avoid `Any` Type

```python
# GOOD
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}

# BAD
def process_items(items: Any) -> Any:
    return {item: len(item) for item in items}
```

---

## 3. Error Handling

### 3.1 Custom Exceptions

```python
# src/aios/exceptions.py

class AIOSError(Exception):
    """Base exception for AIOS."""
    pass

class ScopeViolationError(AIOSError):
    """Agent attempted action outside scope."""

    def __init__(self, agent_id: str, action: str) -> None:
        self.agent_id = agent_id
        self.action = action
        super().__init__(f"Agent '{agent_id}' cannot perform '{action}'")

class AgentNotFoundError(AIOSError):
    """Requested agent does not exist."""
    pass
```

### 3.2 Never Catch Bare Exceptions

```python
# GOOD
try:
    result = validate_agent(agent_id)
except AgentNotFoundError:
    logger.warning(f"Agent {agent_id} not found")
    return None
except ScopeViolationError as e:
    logger.error(f"Scope violation: {e}")
    raise

# BAD
try:
    result = validate_agent(agent_id)
except:
    pass
```

---

## 4. Testing

### 4.1 Test File Naming

```
tests/
├── unit/
│   └── test_agent_registry.py
├── integration/
│   └── test_security_pipeline.py
└── conftest.py
```

### 4.2 Test Structure

```python
# tests/unit/test_agent_registry.py

import pytest
from aios.agents.registry import AgentRegistry

class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_get_existing_agent(self, sample_registry: AgentRegistry) -> None:
        """Should return agent when it exists."""
        agent = sample_registry.get("dev")
        assert agent is not None
        assert agent.name == "Dex"

    def test_get_nonexistent_agent(self, sample_registry: AgentRegistry) -> None:
        """Should return None for unknown agent."""
        agent = sample_registry.get("unknown")
        assert agent is None

    def test_can_delegate_to_lower_tier(self, sample_registry: AgentRegistry) -> None:
        """VP should be able to delegate to Director."""
        can_delegate = sample_registry.can_delegate_to("vp-engineering", "dir-frontend")
        assert can_delegate is True
```

### 4.3 Fixtures

```python
# tests/conftest.py

import pytest
from pathlib import Path
from aios.agents.registry import AgentRegistry

@pytest.fixture
def sample_registry(tmp_path: Path) -> AgentRegistry:
    """Create registry with test agents."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    # ... setup test agents
    return AgentRegistry(agents_dir)
```

---

## 5. Documentation

### 5.1 Docstrings (Google Style)

```python
def validate_scope(
    agent_id: str,
    action: str,
    *,
    strict: bool = True
) -> bool:
    """Validate if agent can perform action.

    Checks the agent's scope rules against the requested action.
    If strict mode is enabled, raises an exception on violation.

    Args:
        agent_id: The agent's unique identifier.
        action: The action to validate.
        strict: If True, raise on violation. Defaults to True.

    Returns:
        True if action is allowed, False otherwise.

    Raises:
        AgentNotFoundError: If agent_id is not registered.
        ScopeViolationError: If strict=True and action is forbidden.

    Example:
        >>> validate_scope("dev", "write_code")
        True
        >>> validate_scope("dev", "git_push")
        False
    """
```

### 5.2 Module Documentation

```python
"""Agent Registry Module.

This module provides the central registry for all NEO-AIOS agents.
It handles agent loading, scope validation, and delegation rules.

Key Classes:
    AgentRegistry: Central agent management.
    AgentDefinition: Agent metadata model.

Example:
    >>> from aios.agents import AgentRegistry
    >>> registry = AgentRegistry.load()
    >>> dev = registry.get("dev")
    >>> dev.name
    'Dex'
"""
```

---

## 6. Configuration

### 6.1 YAML Structure

```yaml
# .aios-custom/config/core-config.yaml

version: "1.0.0"

agents:
  registry_path: "agents/"
  default_tier: "ic"

hierarchy:
  levels:
    - c-level
    - vp
    - director
    - manager
    - ic

  delegation:
    max_depth: 5
    require_approval:
      - database_ddl
      - production_deploy

quality:
  gates:
    layer_1:
      enabled: true
      blocking: true
    layer_2:
      enabled: true
      blocking: true
    layer_3:
      enabled: true
      blocking: true
```

### 6.2 Environment Variables

```bash
# .env.example

# Required
AIOS_CONFIG_PATH=.aios-custom/config

# Optional
AIOS_LOG_LEVEL=INFO
AIOS_CACHE_TTL=300
AIOS_MAX_FIX_ATTEMPTS=3
```

---

## 7. CLI Patterns

### 7.1 Command Structure

```python
import click
from rich.console import Console

console = Console()

@click.group()
@click.version_option()
def cli() -> None:
    """NEO-AIOS: Agent Intelligence Operating System."""
    pass

@cli.group()
def agent() -> None:
    """Agent management commands."""
    pass

@agent.command()
@click.argument("agent_id")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def activate(agent_id: str, verbose: bool) -> None:
    """Activate an agent by ID."""
    try:
        # ... activation logic
        console.print(f"[green]Agent {agent_id} activated.[/green]")
    except AgentNotFoundError:
        console.print(f"[red]Error: Agent '{agent_id}' not found.[/red]")
        raise SystemExit(1)
```

### 7.2 Output Formatting

```python
from rich.table import Table
from rich.console import Console

console = Console()

def print_agents_table(agents: list[AgentDefinition]) -> None:
    """Print agents in a formatted table."""
    table = Table(title="Registered Agents")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Tier", style="yellow")
    table.add_column("Level", style="blue")

    for agent in agents:
        table.add_row(
            agent.id,
            agent.name,
            agent.tier,
            agent.level
        )

    console.print(table)
```

---

## 8. Security

### 8.1 No Secrets in Code

```python
# GOOD - Use environment variables
import os
api_key = os.environ.get("SUPABASE_KEY")

# BAD - Hardcoded secrets
api_key = "sb-xxxxxxx"
```

### 8.2 Input Validation

```python
from pydantic import BaseModel, Field, field_validator

class AgentActivation(BaseModel):
    """Agent activation request."""

    agent_id: str = Field(..., min_length=1, max_length=50)

    @field_validator("agent_id")
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Ensure agent_id is safe."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("agent_id must be alphanumeric with - or _")
        return v.lower()
```

### 8.3 Path Safety

```python
from pathlib import Path

def safe_path(base: Path, user_input: str) -> Path:
    """Resolve path safely, preventing traversal."""
    resolved = (base / user_input).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ValueError("Path traversal detected")
    return resolved
```

---

## 9. Performance

### 9.1 Lazy Loading

```python
from functools import cached_property

class AgentRegistry:
    def __init__(self, agents_dir: Path) -> None:
        self._agents_dir = agents_dir
        self._agents: dict[str, AgentDefinition] | None = None

    @cached_property
    def agents(self) -> dict[str, AgentDefinition]:
        """Load agents on first access."""
        if self._agents is None:
            self._agents = self._load_agents()
        return self._agents
```

### 9.2 Caching with TTL

```python
from datetime import datetime, timedelta
from typing import Generic, TypeVar

T = TypeVar("T")

class CachedValue(Generic[T]):
    """Value with TTL caching."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._value: T | None = None
        self._expires_at: datetime | None = None
        self._ttl = timedelta(seconds=ttl_seconds)

    def get(self, loader: Callable[[], T]) -> T:
        """Get value, reloading if expired."""
        now = datetime.now()
        if self._value is None or (self._expires_at and now > self._expires_at):
            self._value = loader()
            self._expires_at = now + self._ttl
        return self._value
```

---

## 10. Git Workflow

### 10.1 Conventional Commits

```
feat: add agent activation command
fix: correct scope enforcement for DevOps
docs: update PRD with hierarchy details
refactor: simplify delegation matrix
test: add unit tests for registry
chore: update dependencies
```

### 10.2 Branch Naming

```
feature/agent-hierarchy
fix/scope-enforcement-bug
docs/prd-update
refactor/validator-pipeline
```

### 10.3 Staging-First

```
feature/xxx → PR to staging → preview deploy
staging validated → merge to main → production
```

---

*NEO-AIOS Technical Standards v1.0.0*
*"Never take the lazy path. Do the hard work now."*
