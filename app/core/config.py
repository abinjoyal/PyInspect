"""Configuration manager for PyInspect."""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from app.core.constants import DEFAULT_EXCLUDES, DEFAULT_MAX_FILE_SIZE
from app.core.exceptions import ConfigurationError
from app.core.logger import get_logger

logger = get_logger("config")


@dataclass
class ScannerConfig:
    exclude: Set[str] = field(default_factory=lambda: set(DEFAULT_EXCLUDES))
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE
    calculate_hashes: bool = True


@dataclass
class MemoryConfig:
    snapshot_interval: int = 2
    max_snapshots: int = 50


@dataclass
class LogsConfig:
    max_file_size_bytes: int = 100_000_000
    log_patterns: List[str] = field(default_factory=list)


@dataclass
class ReportsConfig:
    output_directory: str = "reports"
    default_format: str = "html"


@dataclass
class PyInspectConfig:
    project_name: str = "PyInspect"
    scanner: ScannerConfig = field(default_factory=ScannerConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    logs: LogsConfig = field(default_factory=LogsConfig)
    reports: ReportsConfig = field(default_factory=ReportsConfig)

    @classmethod
    def load_from_file(cls, config_path: Path | str) -> "PyInspectConfig":
        path = Path(config_path)
        if not path.is_file():
            logger.debug(f"Configuration file {path} not found. Using defaults.")
            return cls()

        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            
            proj_data = data.get("project", {})
            scan_data = data.get("scanner", {})
            mem_data = data.get("memory", {})
            log_data = data.get("logs", {})
            rep_data = data.get("reports", {})

            scanner_cfg = ScannerConfig(
                exclude=set(scan_data.get("exclude", DEFAULT_EXCLUDES)),
                max_file_size_bytes=scan_data.get("max_file_size_mb", 100) * 1024 * 1024,
                calculate_hashes=scan_data.get("calculate_hashes", True)
            )

            memory_cfg = MemoryConfig(
                snapshot_interval=mem_data.get("snapshot_interval", 2),
                max_snapshots=mem_data.get("max_snapshots", 50)
            )

            logs_cfg = LogsConfig(
                max_file_size_bytes=log_data.get("max_file_size_bytes", 100_000_000),
                log_patterns=log_data.get("log_patterns", [])
            )

            reports_cfg = ReportsConfig(
                output_directory=rep_data.get("output_directory", "reports"),
                default_format=rep_data.get("default_format", "html")
            )

            return cls(
                project_name=proj_data.get("name", "PyInspect"),
                scanner=scanner_cfg,
                memory=memory_cfg,
                logs=logs_cfg,
                reports=reports_cfg
            )
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to parse config file: {path}",
                details=str(e),
                suggested_action="Ensure pyinspect.toml contains valid TOML formatting."
            ) from e
