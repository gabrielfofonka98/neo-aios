# Story 1.1: Project Setup

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média

---

## Objetivo

Configurar o projeto Python com uv, ruff, mypy, pytest e estrutura de pastas.

## Tasks

### Task 1: Criar pyproject.toml

**Arquivo:** `pyproject.toml`
**Tipo:** create

**O que fazer:**
1. Criar pyproject.toml com configuração completa
2. Definir dependências principais
3. Configurar ruff, mypy, pytest

**Código esperado:**
```toml
[project]
name = "neo-aios"
version = "0.1.0"
description = "Agent Intelligence Operating System"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "click>=8.1.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.23.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",
]
security = [
    "tree-sitter>=0.21.0",
    "tree-sitter-typescript>=0.21.0",
    "tree-sitter-javascript>=0.21.0",
    "sqlglot>=20.0.0",
]

[project.scripts]
aios = "aios.cli.main:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
target-version = "py312"
line-length = 100
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]

[tool.ruff.isort]
known-first-party = ["aios"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --cov=src/aios --cov-report=term-missing"

[tool.coverage.run]
source = ["src/aios"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

**Acceptance Criteria:**
- [ ] pyproject.toml criado
- [ ] `uv sync` funciona sem erros
- [ ] `uv run ruff check .` funciona
- [ ] `uv run mypy .` funciona

**Validação:**
```bash
uv sync && uv run ruff check . && uv run mypy src/
```

---

### Task 2: Criar estrutura de pastas

**Tipo:** create (múltiplos arquivos)

**O que fazer:**
1. Criar estrutura src/aios/
2. Criar __init__.py em todas as pastas
3. Criar pasta tests/

**Estrutura esperada:**
```
src/
└── aios/
    ├── __init__.py
    ├── agents/
    │   ├── __init__.py
    │   ├── registry.py
    │   ├── loader.py
    │   └── dispatcher.py
    ├── context/
    │   ├── __init__.py
    │   ├── session.py
    │   └── persistence.py
    ├── scope/
    │   ├── __init__.py
    │   └── enforcer.py
    ├── healthcheck/
    │   ├── __init__.py
    │   ├── domains.py
    │   └── checks.py
    ├── cli/
    │   ├── __init__.py
    │   └── main.py
    └── models/
        ├── __init__.py
        └── base.py

tests/
├── __init__.py
├── conftest.py
├── test_agents/
│   └── __init__.py
├── test_context/
│   └── __init__.py
└── test_scope/
    └── __init__.py
```

**Acceptance Criteria:**
- [ ] Todas as pastas criadas
- [ ] Todos os __init__.py criados
- [ ] Import `from aios.agents import registry` funciona

**Validação:**
```bash
python -c "from aios.agents import registry; print('OK')"
```

---

### Task 3: Criar src/aios/__init__.py

**Arquivo:** `src/aios/__init__.py`
**Tipo:** create

**Código esperado:**
```python
"""NEO-AIOS: Agent Intelligence Operating System."""

__version__ = "0.1.0"
__all__ = ["__version__"]
```

---

### Task 4: Criar tests/conftest.py

**Arquivo:** `tests/conftest.py`
**Tipo:** create

**Código esperado:**
```python
"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def tmp_agents_dir(tmp_path: Path) -> Path:
    """Create a temporary agents directory for testing."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    return agents_dir


@pytest.fixture
def tmp_session_file(tmp_path: Path) -> Path:
    """Create a temporary session state file path."""
    return tmp_path / ".aios" / "session-state.json"


@pytest.fixture
def sample_agent_skill(tmp_agents_dir: Path) -> Path:
    """Create a sample agent SKILL.md for testing."""
    agent_dir = tmp_agents_dir / "test-agent"
    agent_dir.mkdir()

    skill_content = '''
agent:
  name: TestAgent
  id: test-agent
  icon: "🧪"

scope:
  can:
    - test_action
  cannot:
    - forbidden_action
'''
    skill_file = agent_dir / "SKILL.md"
    skill_file.write_text(skill_content)
    return skill_file
```

**Acceptance Criteria:**
- [ ] conftest.py criado
- [ ] Fixtures funcionando

**Validação:**
```bash
uv run pytest tests/ -v --collect-only
```

---

## Validação Final

- [ ] `uv sync` sem erros
- [ ] `uv run ruff check src/` sem erros
- [ ] `uv run mypy src/` sem erros
- [ ] `uv run pytest tests/ --collect-only` funciona

## Notas para Ralph

- Use `uv` para gerenciamento de pacotes, não pip
- Crie todos os __init__.py mesmo que vazios (para imports)
- Siga type hints em todo código (mypy --strict)
