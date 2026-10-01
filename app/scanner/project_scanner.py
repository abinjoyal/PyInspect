"""Project directory tree scanner with progress tracking and robust exclusion rules."""

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Callable, Optional
from app.scanner.file_scanner import FileScanner, FileMetadata
from app.core.exceptions import ProjectScanError
from app.core.logger import get_logger

logger = get_logger("project_scanner")


@dataclass
class ScanProgress:
    scanned_files: int
    scanned_directories: int
    total_bytes: int
    current_path: str


@dataclass
class ScanResult:
    root_path: Path
    file_metadatas: List[FileMetadata] = field(default_factory=list)
    total_size_bytes: int = 0
    total_files: int = 0
    python_files: int = 0
    directory_count: int = 0
    skipped_paths: List[str] = field(default_factory=list)


class ProjectScanner:
    """Traverses a target project directory recursively, respecting ignore rules."""

    def __init__(
        self,
        exclude_patterns: Optional[Set[str]] = None,
        calculate_hashes: bool = True
    ):
        self.exclude_patterns = exclude_patterns or set()
        self.calculate_hashes = calculate_hashes

    def is_excluded(self, path: Path, root_path: Path) -> bool:
        """Determines if a given path matches any exclude pattern."""
        name = path.name
        if name in self.exclude_patterns:
            return True

        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            try:
                rel = str(path.relative_to(root_path))
                if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(f"*/{name}", pattern):
                    return True
            except ValueError:
                pass
        return False

    def scan(
        self,
        project_dir: Path | str,
        progress_callback: Optional[Callable[[ScanProgress], None]] = None
    ) -> ScanResult:
        root_path = Path(project_dir).resolve()
        if not root_path.exists():
            raise ProjectScanError(
                message=f"Project directory does not exist: {root_path}",
                suggested_action="Verify the directory path and try again."
            )
        if not root_path.is_dir():
            raise ProjectScanError(
                message=f"Specified path is not a directory: {root_path}",
                suggested_action="Select a valid folder path."
            )

        result = ScanResult(root_path=root_path)
        stack = [root_path]
        scanned_files = 0
        scanned_dirs = 0

        while stack:
            current_dir = stack.pop()
            scanned_dirs += 1

            try:
                children = list(current_dir.iterdir())
            except PermissionError:
                logger.warning(f"Permission denied accessing directory: {current_dir}")
                result.skipped_paths.append(str(current_dir))
                continue
            except Exception as e:
                logger.warning(f"Error accessing directory {current_dir}: {e}")
                result.skipped_paths.append(str(current_dir))
                continue

            for child in children:
                if self.is_excluded(child, root_path):
                    continue

                if child.is_dir():
                    stack.append(child)
                elif child.is_file():
                    meta = FileScanner.scan_file(
                        file_path=child,
                        root_path=root_path,
                        calculate_hash=self.calculate_hashes
                    )
                    result.file_metadatas.append(meta)
                    result.total_size_bytes += meta.size_bytes
                    scanned_files += 1
                    if meta.is_python:
                        result.python_files += 1

                    if progress_callback and scanned_files % 50 == 0:
                        progress_callback(
                            ScanProgress(
                                scanned_files=scanned_files,
                                scanned_directories=scanned_dirs,
                                total_bytes=result.total_size_bytes,
                                current_path=meta.relative_path
                            )
                        )

        result.total_files = scanned_files
        result.directory_count = scanned_dirs

        if progress_callback:
            progress_callback(
                ScanProgress(
                    scanned_files=scanned_files,
                    scanned_directories=scanned_dirs,
                    total_bytes=result.total_size_bytes,
                    current_path="Complete"
                )
            )

        return result
