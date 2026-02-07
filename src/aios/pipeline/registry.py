"""Step registry — loads step definitions from YAML config."""

from __future__ import annotations

from pathlib import Path

import yaml

from aios.pipeline.step_models import StepDefinition


class StepRegistryError(Exception):
    """Raised when step registry loading fails."""


class StepRegistry:
    """Registry of step definitions loaded from YAML.

    Example:
        >>> registry = StepRegistry.load()
        >>> steps = registry.get_workflow("greenfield-fullstack")
    """

    DEFAULT_CONFIG_FILE = Path(".aios-custom/config/step-registry.yaml")

    def __init__(self, workflows: dict[str, list[StepDefinition]]) -> None:
        self._workflows = workflows

    @classmethod
    def load(cls, config_file: Path | None = None) -> StepRegistry:
        """Load step registry from YAML file.

        Args:
            config_file: Path to YAML config. Defaults to .aios-custom/config/step-registry.yaml.

        Returns:
            StepRegistry with loaded workflows.

        Raises:
            StepRegistryError: If config file cannot be loaded or parsed.
        """
        path = config_file or cls.DEFAULT_CONFIG_FILE

        if not path.exists():
            return cls(workflows={})

        try:
            data = yaml.safe_load(path.read_text())
        except yaml.YAMLError as e:
            msg = f"Failed to parse step registry: {e}"
            raise StepRegistryError(msg) from e

        if not isinstance(data, dict) or "workflows" not in data:
            return cls(workflows={})

        workflows: dict[str, list[StepDefinition]] = {}
        raw_workflows = data.get("workflows", {})

        for wf_name, wf_data in raw_workflows.items():
            steps_raw = wf_data.get("steps", []) if isinstance(wf_data, dict) else []
            steps: list[StepDefinition] = []

            for step_raw in steps_raw:
                if not isinstance(step_raw, dict):
                    continue
                normalized = {
                    "id": step_raw.get("id", ""),
                    "agentId": step_raw.get("agent_id", "dev"),
                    "model": step_raw.get("model", "sonnet"),
                    "maxTurns": step_raw.get("max_turns", 10),
                    "tokenBudget": step_raw.get("token_budget", 15000),
                    "timeoutS": step_raw.get("timeout_s", 300.0),
                    "description": step_raw.get("description", ""),
                }
                steps.append(StepDefinition(**normalized))

            workflows[wf_name] = steps

        return cls(workflows=workflows)

    def get_workflow(self, workflow_name: str) -> list[StepDefinition]:
        """Get step definitions for a workflow.

        Args:
            workflow_name: Name of the workflow.

        Returns:
            List of StepDefinitions, empty if workflow not found.
        """
        return list(self._workflows.get(workflow_name, []))

    def list_workflows(self) -> list[str]:
        """List all available workflow names."""
        return sorted(self._workflows.keys())

    def get_step(self, workflow_name: str, step_id: str) -> StepDefinition | None:
        """Get a specific step definition.

        Args:
            workflow_name: Name of the workflow.
            step_id: ID of the step.

        Returns:
            StepDefinition if found, None otherwise.
        """
        for step in self._workflows.get(workflow_name, []):
            if step.id == step_id:
                return step
        return None
