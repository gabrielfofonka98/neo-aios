"""Tests for CI Generator."""

from aios.quality.ci_generator import CIConfig
from aios.quality.ci_generator import CIGenerator


class TestCIGenerator:
    def setup_method(self) -> None:
        self.generator = CIGenerator()

    def test_generate_default(self) -> None:
        yaml = self.generator.generate_pr_check()
        assert "name: PR Check" in yaml
        assert "ruff" in yaml
        assert "mypy" in yaml
        assert "pytest" in yaml

    def test_generate_custom_python(self) -> None:
        config = CIConfig(python_version="3.13")
        yaml = self.generator.generate_pr_check(config)
        assert "3.13" in yaml

    def test_generate_no_security(self) -> None:
        config = CIConfig(run_security=False)
        yaml = self.generator.generate_pr_check(config)
        assert "Security scan" not in yaml

    def test_generate_custom_coverage(self) -> None:
        config = CIConfig(coverage_threshold=90)
        yaml = self.generator.generate_pr_check(config)
        assert "90" in yaml

    def test_generate_custom_branches(self) -> None:
        config = CIConfig(branches=["main", "develop"])
        yaml = self.generator.generate_pr_check(config)
        assert "develop" in yaml

    def test_generate_no_ruff(self) -> None:
        config = CIConfig(run_ruff=False)
        yaml = self.generator.generate_pr_check(config)
        assert "ruff" not in yaml
