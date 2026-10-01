"""Unit tests for SizeAnalyzer, FileSizeAnalyzer, and DirectoryAnalyzer."""

import pytest
from app.scanner.file_scanner import FileMetadata
from app.analyzers.size.file_analyzer import FileSizeAnalyzer
from app.analyzers.size.size_analyzer import SizeAnalyzer
from app.scanner.project_scanner import ScanResult
from pathlib import Path


def test_duplicate_file_detection():
    hash_val = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    files = [
        FileMetadata(
            path=Path("/tmp/a.bin"),
            relative_path="data/a.bin",
            extension=".bin",
            size_bytes=2 * 1024 * 1024,
            is_python=False,
            hash_sha256=hash_val
        ),
        FileMetadata(
            path=Path("/tmp/b.bin"),
            relative_path="backup/b.bin",
            extension=".bin",
            size_bytes=2 * 1024 * 1024,
            is_python=False,
            hash_sha256=hash_val
        )
    ]

    analyzer = FileSizeAnalyzer()
    res = analyzer.analyze(files)

    assert len(res.duplicate_groups) == 1
    assert res.duplicate_groups[0].sha256_hash == hash_val
    assert len(res.duplicate_groups[0].files) == 2


def test_large_file_anomaly():
    files = [
        FileMetadata(
            path=Path("/tmp/model.pt"),
            relative_path="weights/model.pt",
            extension=".pt",
            size_bytes=100 * 1024 * 1024,  # 100MB
            is_python=False,
            hash_sha256="abc1234"
        )
    ]

    analyzer = FileSizeAnalyzer(large_file_threshold_mb=50)
    res = analyzer.analyze(files)

    assert len(res.anomalies) == 1
    assert res.anomalies[0].category == "size"
    assert "model.pt" in res.anomalies[0].location
