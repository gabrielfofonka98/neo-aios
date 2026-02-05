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
    skill_file = agent_dir / "SKILL.md"
    skill_file.write_text(skill_content)
    return skill_file


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent
