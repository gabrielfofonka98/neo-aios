"""Tests for CodeRabbit config generator."""

from aios.quality.coderabbit_config import CodeRabbitConfig
from aios.quality.coderabbit_config import CodeRabbitGenerator


class TestCodeRabbitGenerator:
    def setup_method(self) -> None:
        self.generator = CodeRabbitGenerator()

    def test_generate_default(self) -> None:
        yaml = self.generator.generate()
        assert "pt-BR" in yaml
        assert "reviews:" in yaml
        assert "assertive" in yaml

    def test_generate_custom_language(self) -> None:
        config = CodeRabbitConfig(language="en-US")
        yaml = self.generator.generate(config)
        assert "en-US" in yaml

    def test_generate_path_filters(self) -> None:
        yaml = self.generator.generate()
        assert ".aios-core" in yaml
        assert "__pycache__" in yaml

    def test_generate_custom_profile(self) -> None:
        config = CodeRabbitConfig(review_profile="chill")
        yaml = self.generator.generate(config)
        assert "chill" in yaml

    def test_auto_review_disabled(self) -> None:
        config = CodeRabbitConfig(auto_review=False)
        yaml = self.generator.generate(config)
        assert "enabled: false" in yaml
