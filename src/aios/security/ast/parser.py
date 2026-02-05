"""Tree-sitter AST parser for TypeScript/JavaScript.

This module provides a unified interface for parsing TypeScript and JavaScript
source code using tree-sitter, enabling precise AST-based security analysis.

Example:
    >>> from aios.security.ast.parser import ASTParser
    >>> parser = ASTParser()
    >>> tree = parser.parse("const x = 1;", language="typescript")
    >>> print(tree.root_node.type)
    'program'
"""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts
from tree_sitter import Language
from tree_sitter import Node
from tree_sitter import Parser
from tree_sitter import Tree

if TYPE_CHECKING:
    from collections.abc import Iterator


class SupportedLanguage(Enum):
    """Supported programming languages for AST parsing."""

    TYPESCRIPT = "typescript"
    TSX = "tsx"
    JAVASCRIPT = "javascript"


@dataclass(frozen=True)
class NodeLocation:
    """Location information for an AST node.

    Attributes:
        line_start: Starting line number (1-indexed).
        line_end: Ending line number (1-indexed).
        column_start: Starting column (0-indexed).
        column_end: Ending column (0-indexed).
    """

    line_start: int
    line_end: int
    column_start: int
    column_end: int

    @classmethod
    def from_node(cls, node: Node) -> "NodeLocation":
        """Create NodeLocation from a tree-sitter Node.

        Args:
            node: The tree-sitter node.

        Returns:
            NodeLocation with 1-indexed line numbers.
        """
        return cls(
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            column_start=node.start_point[1],
            column_end=node.end_point[1],
        )


@dataclass(frozen=True)
class ASTMatch:
    """A match found during AST traversal.

    Attributes:
        node_type: The type of the matched node.
        text: The source text of the matched node.
        location: The location of the match in the source.
        node: The underlying tree-sitter node.
    """

    node_type: str
    text: str
    location: NodeLocation
    node: Node


class ASTParser:
    """Tree-sitter based AST parser for TypeScript/JavaScript.

    This parser provides methods for parsing source code and traversing
    the resulting AST to find patterns of interest.

    Attributes:
        _parsers: Dictionary of language-specific parsers.
        _languages: Dictionary of language objects.
    """

    def __init__(self) -> None:
        """Initialize the AST parser with TypeScript and JavaScript support."""
        self._languages: dict[SupportedLanguage, Language] = {
            SupportedLanguage.TYPESCRIPT: Language(tsts.language_typescript()),
            SupportedLanguage.TSX: Language(tsts.language_tsx()),
            SupportedLanguage.JAVASCRIPT: Language(tsjs.language()),
        }
        self._parsers: dict[SupportedLanguage, Parser] = {}

        # Initialize parsers for each language
        for lang, language_obj in self._languages.items():
            parser = Parser(language_obj)
            self._parsers[lang] = parser

    def parse(
        self,
        source: str,
        language: SupportedLanguage | str = SupportedLanguage.TYPESCRIPT,
    ) -> Tree:
        """Parse source code into an AST.

        Args:
            source: The source code to parse.
            language: The language to use for parsing.

        Returns:
            The parsed tree.

        Raises:
            ValueError: If the language is not supported.
        """
        if isinstance(language, str):
            try:
                language = SupportedLanguage(language)
            except ValueError:
                msg = f"Unsupported language: {language}"
                raise ValueError(msg) from None

        parser = self._parsers.get(language)
        if parser is None:
            msg = f"Parser not available for language: {language}"
            raise ValueError(msg)

        return parser.parse(source.encode("utf-8"))

    def detect_language(self, file_path: str) -> SupportedLanguage:
        """Detect the language based on file extension.

        Args:
            file_path: Path to the file.

        Returns:
            The detected language.

        Raises:
            ValueError: If the file extension is not supported.
        """
        ext_map: dict[str, SupportedLanguage] = {
            ".ts": SupportedLanguage.TYPESCRIPT,
            ".tsx": SupportedLanguage.TSX,
            ".js": SupportedLanguage.JAVASCRIPT,
            ".jsx": SupportedLanguage.TSX,  # JSX uses TSX grammar
            ".mjs": SupportedLanguage.JAVASCRIPT,
            ".cjs": SupportedLanguage.JAVASCRIPT,
        }

        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang

        msg = f"Cannot detect language for file: {file_path}"
        raise ValueError(msg)

    def parse_file_content(self, content: str, file_path: str) -> Tree:
        """Parse file content with auto-detected language.

        Args:
            content: The file content.
            file_path: Path to the file (used for language detection).

        Returns:
            The parsed tree.
        """
        language = self.detect_language(file_path)
        return self.parse(content, language)

    def find_nodes(
        self,
        tree: Tree,
        node_types: list[str],
    ) -> "Iterator[ASTMatch]":
        """Find all nodes of specified types in the tree.

        Args:
            tree: The parsed tree.
            node_types: List of node type names to find.

        Yields:
            ASTMatch for each matching node.
        """
        node_type_set = set(node_types)

        def traverse(node: Node) -> "Iterator[ASTMatch]":
            if node.type in node_type_set:
                yield ASTMatch(
                    node_type=node.type,
                    text=node.text.decode("utf-8") if node.text else "",
                    location=NodeLocation.from_node(node),
                    node=node,
                )

            for child in node.children:
                yield from traverse(child)

        yield from traverse(tree.root_node)

    def find_call_expressions(
        self,
        tree: Tree,
        function_names: list[str] | None = None,
        method_names: list[str] | None = None,
    ) -> "Iterator[ASTMatch]":
        """Find call expressions matching specified names.

        Args:
            tree: The parsed tree.
            function_names: Function names to match (e.g., ["setTimeout"]).
            method_names: Method names to match (e.g., ["write", "decode"]).

        Yields:
            ASTMatch for each matching call expression.
        """
        function_set = set(function_names) if function_names else set()
        method_set = set(method_names) if method_names else set()

        def traverse(node: Node) -> "Iterator[ASTMatch]":
            if node.type == "call_expression":
                func_node = node.child_by_field_name("function")
                if func_node is not None:
                    # Check for simple function call: func(...)
                    if func_node.type == "identifier" and function_set:
                        func_name = func_node.text.decode("utf-8") if func_node.text else ""
                        if func_name in function_set:
                            yield ASTMatch(
                                node_type="call_expression",
                                text=node.text.decode("utf-8") if node.text else "",
                                location=NodeLocation.from_node(node),
                                node=node,
                            )

                    # Check for method call: obj.method(...)
                    elif func_node.type == "member_expression" and method_set:
                        property_node = func_node.child_by_field_name("property")
                        if property_node is not None:
                            method_name = (
                                property_node.text.decode("utf-8") if property_node.text else ""
                            )
                            if method_name in method_set:
                                yield ASTMatch(
                                    node_type="call_expression",
                                    text=node.text.decode("utf-8") if node.text else "",
                                    location=NodeLocation.from_node(node),
                                    node=node,
                                )

            for child in node.children:
                yield from traverse(child)

        yield from traverse(tree.root_node)

    def find_property_assignments(
        self,
        tree: Tree,
        property_names: list[str],
    ) -> "Iterator[ASTMatch]":
        """Find property assignments matching specified names.

        Detects patterns like:
        - element.property = value

        Args:
            tree: The parsed tree.
            property_names: Property names to match.

        Yields:
            ASTMatch for each matching assignment.
        """
        property_set = set(property_names)

        def traverse(node: Node) -> "Iterator[ASTMatch]":
            # Check assignment_expression
            if node.type == "assignment_expression":
                left = node.child_by_field_name("left")
                if left is not None and left.type == "member_expression":
                    prop_node = left.child_by_field_name("property")
                    if prop_node is not None:
                        prop_name = prop_node.text.decode("utf-8") if prop_node.text else ""
                        if prop_name in property_set:
                            yield ASTMatch(
                                node_type="property_assignment",
                                text=node.text.decode("utf-8") if node.text else "",
                                location=NodeLocation.from_node(node),
                                node=node,
                            )

            for child in node.children:
                yield from traverse(child)

        yield from traverse(tree.root_node)

    def find_jsx_attributes(
        self,
        tree: Tree,
        attribute_names: list[str],
    ) -> "Iterator[ASTMatch]":
        """Find JSX attributes matching specified names.

        Detects patterns like:
        - <div someAttribute={...} />
        - <a href={...} />

        Args:
            tree: The parsed tree.
            attribute_names: Attribute names to match.

        Yields:
            ASTMatch for each matching attribute.
        """
        attr_set = set(attribute_names)

        def traverse(node: Node) -> "Iterator[ASTMatch]":
            if node.type == "jsx_attribute":
                # Get the attribute name
                for child in node.children:
                    if child.type == "property_identifier":
                        attr_name = child.text.decode("utf-8") if child.text else ""
                        if attr_name in attr_set:
                            yield ASTMatch(
                                node_type="jsx_attribute",
                                text=node.text.decode("utf-8") if node.text else "",
                                location=NodeLocation.from_node(node),
                                node=node,
                            )
                        break

            for child in node.children:
                yield from traverse(child)

        yield from traverse(tree.root_node)

    def find_string_literals(
        self,
        tree: Tree,
        patterns: list[str] | None = None,
    ) -> "Iterator[ASTMatch]":
        """Find string literals, optionally matching patterns.

        Args:
            tree: The parsed tree.
            patterns: Optional list of substrings to match.

        Yields:
            ASTMatch for each matching string literal.
        """

        def traverse(node: Node) -> "Iterator[ASTMatch]":
            if node.type in ("string", "template_string", "string_fragment"):
                text = node.text.decode("utf-8") if node.text else ""

                if patterns is None:
                    yield ASTMatch(
                        node_type=node.type,
                        text=text,
                        location=NodeLocation.from_node(node),
                        node=node,
                    )
                else:
                    for pattern in patterns:
                        if pattern in text:
                            yield ASTMatch(
                                node_type=node.type,
                                text=text,
                                location=NodeLocation.from_node(node),
                                node=node,
                            )
                            break

            for child in node.children:
                yield from traverse(child)

        yield from traverse(tree.root_node)

    def get_node_text(self, node: Node, source: str) -> str:
        """Get the source text for a node.

        Args:
            node: The AST node.
            source: The original source code.

        Returns:
            The text content of the node.
        """
        return source[node.start_byte : node.end_byte]

    def walk_tree(self, tree: Tree) -> "Iterator[Node]":
        """Walk all nodes in the tree.

        Args:
            tree: The parsed tree.

        Yields:
            Each node in the tree in pre-order.
        """

        def walk(node: Node) -> "Iterator[Node]":
            yield node
            for child in node.children:
                yield from walk(child)

        yield from walk(tree.root_node)


# Global parser instance for convenience
_parser: ASTParser | None = None


def get_parser() -> ASTParser:
    """Get the global AST parser instance.

    Returns:
        The global ASTParser instance.
    """
    global _parser  # noqa: PLW0603
    if _parser is None:
        _parser = ASTParser()
    return _parser
