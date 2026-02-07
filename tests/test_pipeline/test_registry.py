"""Tests for StepRegistry."""

from pathlib import Path

import pytest

from aios.pipeline.registry import StepRegistry
from aios.pipeline.registry import StepRegistryError


SAMPLE_YAML = """\
workflows:
  greenfield-fullstack:
    steps:
      - id: setup-project
        agent_id: devops
        model: haiku
        max_turns: 5
        token_budget: 8000
        description: "Initialize project"

      - id: implement-backend
        agent_id: dev
        model: opus
        token_budget: 25000

      - id: run-tests
        agent_id: dev
        model: haiku
        token_budget: 5000

  bugfix:
    steps:
      - id: analyze-bug
        agent_id: dev
        model: sonnet
        token_budget: 12000

      - id: implement-fix
        agent_id: dev
        model: opus
        token_budget: 20000
"""

INVALID_YAML = """\
workflows:
  - this is invalid structure
"""


class TestStepRegistryLoading:
    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        config = tmp_path / "step-registry.yaml"
        config.write_text(SAMPLE_YAML)

        registry = StepRegistry.load(config)

        assert "greenfield-fullstack" in registry.list_workflows()
        assert "bugfix" in registry.list_workflows()

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        config = tmp_path / "nonexistent.yaml"
        registry = StepRegistry.load(config)
        assert registry.list_workflows() == []

    def test_load_invalid_yaml(self, tmp_path: Path) -> None:
        config = tmp_path / "bad.yaml"
        config.write_text("{{{{not yaml")

        with pytest.raises(StepRegistryError):
            StepRegistry.load(config)

    def test_load_empty_yaml(self, tmp_path: Path) -> None:
        config = tmp_path / "empty.yaml"
        config.write_text("")
        registry = StepRegistry.load(config)
        assert registry.list_workflows() == []

    def test_load_yaml_without_workflows(self, tmp_path: Path) -> None:
        config = tmp_path / "no-wf.yaml"
        config.write_text("other_key: value")
        registry = StepRegistry.load(config)
        assert registry.list_workflows() == []


class TestStepRegistryAccess:
    def _load_registry(self, tmp_path: Path) -> StepRegistry:
        config = tmp_path / "step-registry.yaml"
        config.write_text(SAMPLE_YAML)
        return StepRegistry.load(config)

    def test_get_workflow(self, tmp_path: Path) -> None:
        registry = self._load_registry(tmp_path)
        steps = registry.get_workflow("greenfield-fullstack")

        assert len(steps) == 3
        assert steps[0].id == "setup-project"
        assert steps[0].agent_id == "devops"
        assert steps[0].model == "haiku"
        assert steps[0].token_budget == 8000

    def test_get_workflow_not_found(self, tmp_path: Path) -> None:
        registry = self._load_registry(tmp_path)
        steps = registry.get_workflow("nonexistent")
        assert steps == []

    def test_get_step(self, tmp_path: Path) -> None:
        registry = self._load_registry(tmp_path)
        step = registry.get_step("greenfield-fullstack", "implement-backend")

        assert step is not None
        assert step.model == "opus"
        assert step.token_budget == 25000

    def test_get_step_not_found(self, tmp_path: Path) -> None:
        registry = self._load_registry(tmp_path)
        step = registry.get_step("greenfield-fullstack", "nonexistent")
        assert step is None

    def test_list_workflows_sorted(self, tmp_path: Path) -> None:
        registry = self._load_registry(tmp_path)
        workflows = registry.list_workflows()
        assert workflows == ["bugfix", "greenfield-fullstack"]

    def test_step_defaults(self, tmp_path: Path) -> None:
        registry = self._load_registry(tmp_path)
        step = registry.get_step("greenfield-fullstack", "implement-backend")
        assert step is not None
        assert step.max_turns == 10
        assert step.timeout_s == 300.0
