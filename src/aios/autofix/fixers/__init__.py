"""Security fixers for auto-fix framework.

This package provides specialized fixers for different categories of
security vulnerabilities. Each fixer implements the BaseFixer interface
and handles specific vulnerability patterns.

Available Fixers:
    - XSSFixer: Cross-Site Scripting vulnerabilities
    - InjectionFixer: SQL/NoSQL injection vulnerabilities
    - SecretsFixer: Hardcoded secrets and credential exposure

Example:
    >>> from aios.autofix.fixers import XSSFixer, InjectionFixer, SecretsFixer
    >>> from aios.autofix.framework import AutoFixFramework
    >>>
    >>> # Create framework and register fixers
    >>> framework = AutoFixFramework()
    >>> framework.register_fixer(XSSFixer())
    >>> framework.register_fixer(InjectionFixer())
    >>> framework.register_fixer(SecretsFixer())
    >>>
    >>> # Fix a finding
    >>> result = framework.fix_finding(finding, dry_run=True)
"""

from aios.autofix.fixers.injection import InjectionFixer
from aios.autofix.fixers.secrets import SecretsFixer
from aios.autofix.fixers.xss import XSSFixer

__all__ = [
    "InjectionFixer",
    "SecretsFixer",
    "XSSFixer",
]
