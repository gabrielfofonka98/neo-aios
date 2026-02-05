"""AST-based security analysis module.

This package provides AST-based security validators using tree-sitter
for TypeScript/JavaScript and sqlglot for SQL analysis.

Submodules:
    - parser: Tree-sitter parser wrapper
    - typescript: TypeScript/JavaScript validators
    - sql: SQL injection validators

Validators:
    - XSSValidator: Cross-Site Scripting detection
    - JWTValidator: Insecure JWT handling detection
    - SecretValidator: Hardcoded secrets detection
    - InjectionValidator: SQL/ORM injection detection

Example:
    >>> from aios.security.ast import XSSValidator, InjectionValidator
    >>> from pathlib import Path
    >>>
    >>> xss = XSSValidator()
    >>> result = xss.validate(Path("src/app.tsx"))
    >>> print(f"Found {len(result.findings)} XSS issues")
"""

from aios.security.ast.parser import ASTMatch
from aios.security.ast.parser import ASTParser
from aios.security.ast.parser import NodeLocation
from aios.security.ast.parser import SupportedLanguage
from aios.security.ast.parser import get_parser
from aios.security.ast.sql import InjectionValidator
from aios.security.ast.typescript import JWTValidator
from aios.security.ast.typescript import SecretValidator
from aios.security.ast.typescript import XSSValidator

__all__ = [
    "ASTMatch",
    "ASTParser",
    "InjectionValidator",
    "JWTValidator",
    "NodeLocation",
    "SecretValidator",
    "SupportedLanguage",
    "XSSValidator",
    "get_parser",
]
