"""Directory size aggregator and tree size analyzer."""

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict
from app.scanner.file_scanner import FileMetadata


@dataclass
class DirectorySizeInfo:
    directory_path: str
    size_bytes: int
    file_count: int


class DirectoryAnalyzer:
    """Calculates storage footprint across project directory hierarchies."""

    @staticmethod
    def analyze_directories(file_metadatas: List[FileMetadata], top_n: int = 15) -> List[DirectorySizeInfo]:
        dir_sizes: Dict[str, int] = defaultdict(int)
        dir_files: Dict[str, int] = defaultdict(int)

        for meta in file_metadatas:
            parts = meta.relative_path.split("/") if "/" in meta.relative_path else meta.relative_path.split("\\")
            if len(parts) > 1:
                # Top directory
                top_dir = parts[0]
                dir_sizes[top_dir] += meta.size_bytes
                dir_files[top_dir] += 1
                
                # Direct parent directory
                parent_dir = "/".join(parts[:-1])
                if parent_dir != top_dir:
                    dir_sizes[parent_dir] += meta.size_bytes
                    dir_files[parent_dir] += 1
            else:
                dir_sizes["(root)"] += meta.size_bytes
                dir_files["(root)"] += 1

        results = [
            DirectorySizeInfo(
                directory_path=dir_path,
                size_bytes=size,
                file_count=dir_files[dir_path]
            )
            for dir_path, size in dir_sizes.items()
        ]

        return sorted(results, key=lambda d: d.size_bytes, reverse=True)[:top_n]
