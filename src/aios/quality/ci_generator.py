"""GitHub Actions CI/CD YAML generator."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field


@dataclass
class CIConfig:
    """Configuration for CI generation."""

    python_version: str = "3.12"
    package_manager: str = "uv"
    run_ruff: bool = True
    run_mypy: bool = True
    run_pytest: bool = True
    run_security: bool = True
    coverage_threshold: int = 80
    branches: list[str] = field(default_factory=lambda: ["main", "staging"])


class CIGenerator:
    """Generates GitHub Actions workflow YAML."""

    def generate_pr_check(self, config: CIConfig | None = None) -> str:
        """Generate .github/workflows/pr-check.yml content."""
        cfg = config or CIConfig()

        steps: list[str] = []

        # Checkout
        steps.append(self._step_checkout())

        # Python setup
        steps.append(self._step_python(cfg.python_version))

        # UV install
        if cfg.package_manager == "uv":
            steps.append(self._step_uv_install())

        # Linting
        if cfg.run_ruff:
            steps.append(self._step_ruff())

        # Type checking
        if cfg.run_mypy:
            steps.append(self._step_mypy())

        # Tests
        if cfg.run_pytest:
            steps.append(self._step_pytest(cfg.coverage_threshold))

        # Security
        if cfg.run_security:
            steps.append(self._step_security())

        branches_str = str(cfg.branches).replace("'", '"')

        yaml_parts = [
            "name: PR Check",
            "",
            "on:",
            "  pull_request:",
            f"    branches: {branches_str}",
            "",
            "permissions:",
            "  contents: read",
            "",
            "jobs:",
            "  quality-check:",
            '    runs-on: ubuntu-latest',
            "    steps:",
        ]

        for step in steps:
            yaml_parts.append(step)

        return "\n".join(yaml_parts) + "\n"

    def _step_checkout(self) -> str:
        return (
            "      - name: Checkout\n"
            "        uses: actions/checkout@v4"
        )

    def _step_python(self, version: str) -> str:
        return (
            f"      - name: Setup Python {version}\n"
            "        uses: actions/setup-python@v5\n"
            "        with:\n"
            f'          python-version: "{version}"'
        )

    def _step_uv_install(self) -> str:
        return (
            "      - name: Install uv\n"
            "        uses: astral-sh/setup-uv@v4\n"
            "      - name: Install dependencies\n"
            '        run: uv sync --dev'
        )

    def _step_ruff(self) -> str:
        return (
            "      - name: Lint (ruff)\n"
            "        run: uv run ruff check src/"
        )

    def _step_mypy(self) -> str:
        return (
            "      - name: Type check (mypy)\n"
            "        run: uv run mypy --strict src/aios/"
        )

    def _step_pytest(self, coverage: int) -> str:
        return (
            "      - name: Tests (pytest)\n"
            f"        run: uv run pytest tests/ -v --cov=src/aios --cov-report=term --cov-fail-under={coverage}"
        )

    def _step_security(self) -> str:
        return (
            "      - name: Security scan\n"
            "        run: uv run aios scan run --path src/ || true"
        )
