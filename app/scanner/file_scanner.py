"""Individual file metadata scanner and hash generator."""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from app.core.logger import get_logger

logger = get_logger("file_scanner")


@dataclass
class FileMetadata:
    path: Path
    relative_path: str
    extension: str
    size_bytes: int
    is_python: bool
    hash_sha256: Optional[str] = None
    line_count: Optional[int] = None
    error: Optional[str] = None


class FileScanner:
    """Scans individual file metadata safely without loading entire large files into memory."""

    @staticmethod
    def scan_file(
        file_path: Path,
        root_path: Path,
        calculate_hash: bool = True,
        max_hash_size_bytes: int = 50 * 1024 * 1024
    ) -> FileMetadata:
        try:
            stat = file_path.stat()
            size = stat.st_size
            extension = file_path.suffix.lower()
            is_python = extension == ".py"
            
            try:
                rel_path = str(file_path.relative_to(root_path))
            except ValueError:
                rel_path = str(file_path)

            sha256_hash = None
            if calculate_hash and size <= max_hash_size_bytes and size > 0:
                sha256_hash = FileScanner.calculate_sha256(file_path)

            line_count = None
            if is_python and size > 0 and size <= 10 * 1024 * 1024:
                line_count = FileScanner.count_lines(file_path)

            return FileMetadata(
                path=file_path,
                relative_path=rel_path,
                extension=extension,
                size_bytes=size,
                is_python=is_python,
                hash_sha256=sha256_hash,
                line_count=line_count
            )

        except PermissionError:
            logger.warning(f"Permission denied accessing file: {file_path}")
            return FileMetadata(
                path=file_path,
                relative_path=str(file_path.name),
                extension=file_path.suffix.lower(),
                size_bytes=0,
                is_python=file_path.suffix.lower() == ".py",
                error="Permission denied"
            )
        except FileNotFoundError:
            logger.warning(f"File disappeared during scan: {file_path}")
            return FileMetadata(
                path=file_path,
                relative_path=str(file_path.name),
                extension=file_path.suffix.lower(),
                size_bytes=0,
                is_python=file_path.suffix.lower() == ".py",
                error="File not found"
            )
        except Exception as e:
            logger.warning(f"Unexpected error scanning file {file_path}: {e}")
            return FileMetadata(
                path=file_path,
                relative_path=str(file_path.name),
                extension=file_path.suffix.lower(),
                size_bytes=0,
                is_python=file_path.suffix.lower() == ".py",
                error=str(e)
            )

    @staticmethod
    def calculate_sha256(file_path: Path) -> Optional[str]:
        """Calculates SHA256 in 64KB chunks to maintain low memory usage."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None

    @staticmethod
    def count_lines(file_path: Path) -> Optional[int]:
        """Counts text lines safely handling encoding errors."""
        try:
            count = 0
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for _ in f:
                    count += 1
            return count
        except Exception:
            return None
