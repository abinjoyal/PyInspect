"""Unit tests for ProjectScanner and FileScanner."""

import tempfile
from pathlib import Path
import pytest

from app.scanner.project_scanner import ProjectScanner
from app.scanner.file_scanner import FileScanner


def test_project_scanner_basic(tmp_path):
    # Create test directory structure
    (tmp_path / "main.py").write_text("print('hello world')\n", encoding="utf-8")
    (tmp_path / "utils.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "data.txt").write_text("sample text content", encoding="utf-8")
    
    ignore_dir = tmp_path / "venv"
    ignore_dir.mkdir()
    (ignore_dir / "ignored.py").write_text("raise Exception()", encoding="utf-8")

    scanner = ProjectScanner(exclude_patterns={"venv"})
    result = scanner.scan(tmp_path)

    assert result.total_files == 3
    assert result.python_files == 2
    assert result.total_size_bytes > 0
    assert result.directory_count >= 1


def test_file_scanner_sha256_and_lines(tmp_path):
    sample_file = tmp_path / "test.py"
    sample_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")

    meta = FileScanner.scan_file(file_path=sample_file, root_path=tmp_path)

    assert meta.is_python is True
    assert meta.line_count == 3
    assert meta.hash_sha256 is not None
    assert len(meta.hash_sha256) == 64
