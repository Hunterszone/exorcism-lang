from __future__ import annotations

from dataclasses import dataclass

from enum import Enum

from typing import Optional


class DiagnosticSeverity(Enum):
    """Severity levels for compiler diagnostics."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class SourceLocation:
    """
    Location of a diagnostic in the source file.

    Lines and columns are 1-based.
    """

    line: int
    column: int
    length: int = 1


@dataclass
class Diagnostic:
    """
    Represents a single compiler diagnostic.
    """

    message: str
    location: SourceLocation
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    code: Optional[str] = None

    def to_dict(self):
        """
        Convert the diagnostic to a JSON-compatible dictionary.
        """

        result = {
            "severity": self.severity.value,
            "message": self.message,
            "line": self.location.line,
            "column": self.location.column,
            "length": self.location.length,
        }

        if self.code is not None:
            result["code"] = self.code

        return result


class DiagnosticBag:
    """
    Collection of compiler diagnostics.

    Allows the compiler to collect multiple errors instead of
    immediately aborting on the first one.
    """

    def __init__(self):
        self._diagnostics: list[Diagnostic] = []

    def add(
        self,
        message: str,
        line: int,
        column: int,
        length: int = 1,
        severity: DiagnosticSeverity = DiagnosticSeverity.ERROR,
        code: Optional[str] = None,
    ):
        """Add a diagnostic to the bag."""
        diagnostic = Diagnostic(
            message=message,
            location=SourceLocation(
                line=line,
                column=column,
                length=length,
            ),
            severity=severity,
            code=code,
        )

        self._diagnostics.append(diagnostic)

    def error(
        self,
        message: str,
        line: int,
        column: int,
        length: int = 1,
        code: Optional[str] = None,
    ):
        """Add an error diagnostic to the bag."""
        self.add(
            message=message,
            line=line,
            column=column,
            length=length,
            severity=DiagnosticSeverity.ERROR,
            code=code,
        )

    def warning(
        self,
        message: str,
        line: int,
        column: int,
        length: int = 1,
        code: Optional[str] = None,
    ):
        """Add a warning diagnostic to the bag."""
        self.add(
            message=message,
            line=line,
            column=column,
            length=length,
            severity=DiagnosticSeverity.WARNING,
            code=code,
        )

    def info(
        self,
        message: str,
        line: int,
        column: int,
        length: int = 1,
        code: Optional[str] = None,
    ):
        """Add an informational diagnostic to the bag."""
        self.add(
            message=message,
            line=line,
            column=column,
            length=length,
            severity=DiagnosticSeverity.INFO,
            code=code,
        )

    @property
    def diagnostics(self) -> list[Diagnostic]:
        return self._diagnostics

    @property
    def has_errors(self) -> bool:
        return any(
            diagnostic.severity == DiagnosticSeverity.ERROR
            for diagnostic in self._diagnostics
        )

    @property
    def has_warnings(self) -> bool:
        """Return whether the diagnostic bag contains any warnings."""
        return any(
            diagnostic.severity == DiagnosticSeverity.WARNING
            for diagnostic in self._diagnostics
        )

    @property
    def is_empty(self) -> bool:
        """Return whether the diagnostic bag contains no diagnostics."""
        return len(self._diagnostics) == 0

    def clear(self):
        """Remove all diagnostics from the bag."""
        self._diagnostics.clear()

    def to_list(self):
        """Convert all diagnostics to JSON-compatible dictionaries."""
        return [
            diagnostic.to_dict()
            for diagnostic in self._diagnostics
        ]

    def to_json(self):
        """Convert all diagnostics to a formatted JSON string."""
        import json

        return json.dumps(
            self.to_list(),
            indent=2,
        )