"""Application-wide constants."""

from pathlib import Path

APP_NAME = "PyInspect"
APP_TAGLINE = "Python Project Intelligence & Diagnostics Platform"
APP_VERSION = "0.1.0"

DEFAULT_EXCLUDES = {
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    "node_modules",
    ".env",
    "build",
    "dist",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "*.pyc",
    "*.pyo"
}

# Maximum file size to scan deep (bytes) — 100MB
DEFAULT_MAX_FILE_SIZE = 100 * 1024 * 1024

# Severity levels for diagnostics
class Severity:
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

DEFAULT_DB_FILENAME = "pyinspect.db"
