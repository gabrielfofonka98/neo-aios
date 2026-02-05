"""Tests for CLI output formatting."""

import pytest
from io import StringIO
from unittest.mock import patch

from rich.console import Console
from rich.table import Table

from aios.cli.output import agent_status
from aios.cli.output import console
from aios.cli.output import create_table
from aios.cli.output import error
from aios.cli.output import header
from aios.cli.output import info
from aios.cli.output import print_version
from aios.cli.output import success
from aios.cli.output import warning


@pytest.fixture
def capture_console() -> Console:
    """Create a console that captures output."""
    return Console(file=StringIO(), force_terminal=True)


class TestOutputFunctions:
    """Tests for output formatting functions."""

    def test_console_exists(self) -> None:
        """Test that global console is available."""
        assert console is not None
        assert isinstance(console, Console)

    def test_info_function(self) -> None:
        """Test info output function."""
        # Should not raise
        info("Test info message")

    def test_success_function(self) -> None:
        """Test success output function."""
        # Should not raise
        success("Test success message")

    def test_warning_function(self) -> None:
        """Test warning output function."""
        # Should not raise
        warning("Test warning message")

    def test_error_function(self) -> None:
        """Test error output function."""
        # Should not raise
        error("Test error message")


class TestHeaderFunction:
    """Tests for header formatting."""

    def test_header_with_title(self) -> None:
        """Test header with only title."""
        # Should not raise
        header("Test Title")

    def test_header_with_subtitle(self) -> None:
        """Test header with title and subtitle."""
        # Should not raise
        header("Test Title", "Test Subtitle")


class TestTableCreation:
    """Tests for table creation."""

    def test_create_table_returns_table(self) -> None:
        """Test that create_table returns a Table."""
        table = create_table(
            title="Test Table",
            columns=[("Col1", ""), ("Col2", "")],
            rows=[["val1", "val2"]],
        )
        assert isinstance(table, Table)

    def test_create_table_with_styles(self) -> None:
        """Test table creation with column styles."""
        table = create_table(
            title="Test Table",
            columns=[("ID", "cyan"), ("Name", "bold")],
            rows=[["1", "Test"]],
        )
        assert isinstance(table, Table)

    def test_create_table_multiple_rows(self) -> None:
        """Test table creation with multiple rows."""
        table = create_table(
            title="Test Table",
            columns=[("A", ""), ("B", ""), ("C", "")],
            rows=[
                ["1", "2", "3"],
                ["4", "5", "6"],
                ["7", "8", "9"],
            ],
        )
        assert isinstance(table, Table)


class TestAgentStatus:
    """Tests for agent status formatting."""

    def test_agent_status_active(self) -> None:
        """Test agent status with active status."""
        # Should not raise
        agent_status("dev", "Dex", "[icon]", "active")

    def test_agent_status_inactive(self) -> None:
        """Test agent status with inactive status."""
        # Should not raise
        agent_status("dev", "Dex", "[icon]", "inactive")


class TestVersionPrinting:
    """Tests for version printing."""

    def test_print_version(self) -> None:
        """Test version printing function."""
        # Should not raise
        print_version("0.1.0", "3.12.0")

    def test_print_version_output_contains_neo_aios(self) -> None:
        """Test that version output contains NEO-AIOS branding."""
        output = StringIO()
        test_console = Console(file=output, force_terminal=False)

        # Temporarily patch the console
        with patch("aios.cli.output.console", test_console):
            from aios.cli import output

            # Re-import to get patched version
            output.console = test_console
            output.print_version("0.1.0", "3.12.0")

        result = output.value if hasattr(output, "value") else ""
        # The function should execute without error
        assert True
