"""File size analyzer for detecting largest files, extension distributions, and duplicates."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Set
from app.scanner.file_scanner import FileMetadata
from app.database.models import AnomalyRecord
from app.core.constants import Severity


@dataclass
class DuplicateGroup:
    sha256_hash: str
    size_bytes: int
    files: List[str]


@dataclass
class FileSizeAnalysisResult:
    largest_files: List[FileMetadata]
    extension_distribution: Dict[str, int]  # ext -> size in bytes
    extension_counts: Dict[str, int]        # ext -> file count
    duplicate_groups: List[DuplicateGroup]
    anomalies: List[AnomalyRecord] = field(default_factory=list)


class FileSizeAnalyzer:
    """Analyzes file distributions, finds largest files, and detects duplicate files."""

    def __init__(self, large_file_threshold_mb: int = 50):
        self.large_file_threshold_mb = large_file_threshold_mb
        self.large_file_threshold_bytes = large_file_threshold_mb * 1024 * 1024

    def analyze(self, file_metadatas: List[FileMetadata]) -> FileSizeAnalysisResult:
        largest_files = sorted(file_metadatas, key=lambda f: f.size_bytes, reverse=True)[:15]

        extension_distribution: Dict[str, int] = defaultdict(int)
        extension_counts: Dict[str, int] = defaultdict(int)
        hashes_map: Dict[str, List[FileMetadata]] = defaultdict(list)
        anomalies: List[AnomalyRecord] = []

        for meta in file_metadatas:
            ext = meta.extension if meta.extension else "(no ext)"
            extension_distribution[ext] += meta.size_bytes
            extension_counts[ext] += 1

            if meta.hash_sha256:
                hashes_map[meta.hash_sha256].append(meta)

            # Detect large files anomaly
            if meta.size_bytes >= self.large_file_threshold_bytes:
                size_mb = meta.size_bytes / (1024 * 1024)
                anomalies.append(
                    AnomalyRecord(
                        id=None,
                        analysis_id=0,
                        category="size",
                        severity=Severity.MEDIUM if size_mb < 200 else Severity.HIGH,
                        location=meta.relative_path,
                        evidence=f"File size: {size_mb:.2f} MB",
                        explanation=f"File '{meta.relative_path}' exceeds the large file threshold ({self.large_file_threshold_mb} MB).",
                        suggested_action="Consider Git LFS, compression, or external storage for large files."
                    )
                )

        # Detect duplicates
        duplicate_groups: List[DuplicateGroup] = []
        for sha256_hash, files in hashes_map.items():
            if len(files) > 1 and files[0].size_bytes > 1024 * 1024:  # Only report duplicates > 1MB
                paths = [f.relative_path for f in files]
                duplicate_groups.append(
                    DuplicateGroup(
                        sha256_hash=sha256_hash,
                        size_bytes=files[0].size_bytes,
                        files=paths
                    )
                )
                wasted_bytes = files[0].size_bytes * (len(files) - 1)
                wasted_mb = wasted_bytes / (1024 * 1024)
                anomalies.append(
                    AnomalyRecord(
                        id=None,
                        analysis_id=0,
                        category="size",
                        severity=Severity.LOW if wasted_mb < 50 else Severity.MEDIUM,
                        location=", ".join(paths[:2]),
                        evidence=f"{len(files)} duplicate files found ({wasted_mb:.2f} MB wasted)",
                        explanation="Identical content stored in multiple file locations.",
                        suggested_action="Consolidate duplicate files or use symlinks/shared imports."
                    )
                )

        return FileSizeAnalysisResult(
            largest_files=largest_files,
            extension_distribution=dict(extension_distribution),
            extension_counts=dict(extension_counts),
            duplicate_groups=duplicate_groups,
            anomalies=anomalies
        )
