"""Custom domain exceptions for PyInspect."""

class PyInspectError(Exception):
    """Base exception for all PyInspect errors."""
    def __init__(self, message: str, details: str | None = None, suggested_action: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details
        self.suggested_action = suggested_action

    def __str__(self) -> str:
        res = self.message
        if self.details:
            res += f"\nReason: {self.details}"
        if self.suggested_action:
            res += f"\nSuggested Action: {self.suggested_action}"
        return res


class ProjectScanError(PyInspectError):
    """Raised when project scanning encounters an unrecoverable failure."""
    pass


class ConfigurationError(PyInspectError):
    """Raised when parsing or applying pyinspect.toml configuration fails."""
    pass


class DatabaseError(PyInspectError):
    """Raised when SQLite storage operations fail."""
    pass


class AnalysisError(PyInspectError):
    """Raised when an analyzer fails during execution."""
    pass


class ReportError(PyInspectError):
    """Raised when report generation or export fails."""
    pass
