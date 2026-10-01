# PyInspect — Python Project Intelligence & Diagnostics Platform

> Analyze code execution, trace runtime behavior, detect memory leaks, identify log anomalies, and evaluate project health.

---

## Overview

**PyInspect** is an enterprise-grade developer diagnostics and project intelligence platform built with Python 3.11+, PySide6, and modern static and dynamic analysis engines.

### Key Features
- **Project & Storage Size Analyzer**: Traverses project workspace, computes file distributions, detects bulk files and duplicate content via SHA256 hashes.
- **Code Behavior Visualizer**: Dynamic execution tracer capturing call trees, line step execution, function durations, and variable state mutations.
- **Memory Leak Profiler**: Tracks process RSS memory and heap allocations via `tracemalloc`, compares differential snapshots, and flags suspicious memory growth.
- **Log Anomaly Detector**: Multi-format streaming parser for raw and JSON logs, clustering recurring error signatures (HTTP 500s, DB timeouts, exceptions).
- **Unified Health Score Engine**: Objectively evaluates project health (0–100) and stores historical runs in SQLite for comparison.
- **Standalone Reports & Desktop GUI**: Features a modern PySide6 dark theme desktop dashboard and exports HTML, JSON, and CSV reports.

---

## Quick Start

### 1. Installation

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Launch Desktop GUI Application

```bash
python -m app.main
```

### 3. CLI Command Reference

| Command | Description |
| :--- | :--- |
| `python -m app.main scan .` | Scan current directory and display storage summary |
| `python -m app.main scan . --save` | Scan workspace and persist results to SQLite database |
| `python -m app.main report .` | Generate standalone HTML, JSON, and CSV diagnostic reports |
| `python -m app.main logs app.log` | Analyze log file for pattern anomalies and error spikes |
| `pytest` | Execute full unit test suite |

---

## Configuration (`pyinspect.toml`)

```toml
[project]
name = "MyProject"

[scanner]
exclude = [
    ".git",
    "venv",
    "__pycache__",
    "node_modules"
]

[reports]
output_directory = "reports"
default_format = "html"
```

---

## Security & Execution Boundaries

PyInspect includes safety controls for dynamic analysis:
- **Tracing Warning**: Prompts confirmation before executing scripts under `sys.settrace()`.
- **Secret Redaction**: Redacts sensitive API keys and database credentials during scanning and reporting.
