"""Main entry point for PyInspect CLI and Desktop Application."""

import argparse
import sys
from pathlib import Path

from app.core.config import PyInspectConfig
from app.core.constants import APP_NAME, APP_TAGLINE, APP_VERSION
from app.core.logger import get_logger
from app.database.database import Database
from app.database.repository import Repository
from app.database.models import FileStatRecord
from app.scanner.project_scanner import ProjectScanner
from app.scanner.dependency_scanner import DependencyScanner
from app.analyzers.size.size_analyzer import SizeAnalyzer
from app.analyzers.logs.log_parser import LogParser
from app.analyzers.logs.anomaly_detector import LogAnomalyDetector
from app.reports.report_generator import ReportGenerator

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

logger = get_logger("main")


def format_bytes(size: int) -> str:
    """Formats bytes into human-readable units."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size) < 1024.0:
            return f"{size:3.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def handle_scan_command(args):
    target_path = Path(args.path).resolve()
    print(f"\nScanning Project: {target_path}...")

    config_file = target_path / "pyinspect.toml"
    config = PyInspectConfig.load_from_file(config_file)

    db_path = target_path / "pyinspect.db" if getattr(args, 'save', False) else "pyinspect.db"
    db = Database(db_path)
    db.initialize()
    repo = Repository(db)

    scanner = ProjectScanner(
        exclude_patterns=config.scanner.exclude,
        calculate_hashes=config.scanner.calculate_hashes
    )
    scan_result = scanner.scan(target_path)
    deps = DependencyScanner.scan_dependencies(target_path)

    size_analyzer = SizeAnalyzer()
    summary = size_analyzer.analyze_scan(scan_result)

    if getattr(args, 'save', False):
        project_rec = repo.get_or_create_project(
            name=target_path.name,
            path=str(target_path)
        )
        file_stats = [
            FileStatRecord(
                id=None,
                analysis_id=0,
                relative_path=m.relative_path,
                extension=m.extension,
                size_bytes=m.size_bytes,
                is_python=m.is_python,
                hash_sha256=m.hash_sha256,
                line_count=m.line_count
            )
            for m in scan_result.file_metadatas
        ]
        analysis_id = repo.save_analysis(
            project_id=project_rec.id,
            total_size_bytes=summary.total_size_bytes,
            total_files=summary.total_files,
            python_files=summary.python_files,
            health_score=summary.storage_health_score,
            summary={"dependency_count": len(deps)},
            file_stats=file_stats,
            anomalies=summary.anomalies
        )
        print(f"Saved analysis record #{analysis_id} to database.")

    if HAS_RICH:
        console = Console()
        console.print(
            Panel.fit(
                f"[bold cyan]{APP_NAME}[/bold cyan] v{APP_VERSION} — [dim]{APP_TAGLINE}[/dim]\n"
                f"Target: [yellow]{target_path}[/yellow]",
                title="Project Scan Results"
            )
        )

        table = Table(title="Project Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold green")

        table.add_row("Total Size", format_bytes(summary.total_size_bytes))
        table.add_row("Total Files", str(summary.total_files))
        table.add_row("Python Files", str(summary.python_files))
        table.add_row("Directories", str(summary.directory_count))
        table.add_row("Dependencies Detected", str(len(deps)))
        table.add_row("Storage Health Score", f"{summary.storage_health_score} / 100")

        console.print(table)
    else:
        print("=" * 60)
        print(f"{APP_NAME} v{APP_VERSION} - Scan Results")
        print("=" * 60)
        print(f"Total Size:     {format_bytes(summary.total_size_bytes)}")
        print(f"Total Files:    {summary.total_files}")
        print(f"Python Files:   {summary.python_files}")
        print(f"Health Score:   {summary.storage_health_score} / 100")
        print(f"Dependencies:   {len(deps)}")
        print("=" * 60)

    return summary, deps


def handle_report_command(args):
    target_path = Path(args.path).resolve()
    summary, deps = handle_scan_command(args)

    data = {
        "project_name": target_path.name,
        "target_path": str(target_path),
        "total_size_bytes": summary.total_size_bytes,
        "total_files": summary.total_files,
        "python_files": summary.python_files,
        "health_score": summary.storage_health_score,
        "anomalies": summary.anomalies
    }

    out_dir = target_path / "reports"
    res = ReportGenerator.generate_all_reports(data, out_dir)
    print(f"\nSuccessfully generated reports in '{out_dir}':")
    print(f" - HTML: {res['html']}")
    print(f" - JSON: {res['json']}")
    print(f" - CSV:  {res['csv']}")


def handle_logs_command(args):
    log_path = Path(args.path).resolve()
    print(f"\nAnalyzing Log File: {log_path}...")
    entries = LogParser.parse_file(log_path)
    summary = LogAnomalyDetector.analyze_logs(entries)

    print(f"Total Events:      {summary.total_events}")
    print(f"Log Health Score:  {summary.log_health_score} / 100")
    print(f"Level Counts:      {summary.level_counts}")
    print(f"Pattern Anomalies: {len(summary.pattern_matches)}")


def launch_gui(target_dir: str = "."):
    try:
        from PySide6.QtWidgets import QApplication
        from app.ui.main_window import PyInspectMainWindow
        
        app = QApplication(sys.argv)
        window = PyInspectMainWindow(target_dir=target_dir)
        window.show()
        sys.exit(app.exec())
    except ImportError as e:
        print(f"Error launching PySide6 GUI: {e}")
        print("Please ensure PySide6 is installed (`pip install pyside6`).")
        sys.exit(1)


def cli_entrypoint():
    parser = argparse.ArgumentParser(
        prog="pyinspect",
        description=f"{APP_NAME} — {APP_TAGLINE}"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    parser.add_argument("--gui", action="store_true", help="Force launch PySide6 Desktop Interface")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Scan & Analyze command
    scan_parser = subparsers.add_parser("scan", help="Scan a Python project workspace")
    scan_parser.add_argument("path", nargs="?", default=".", help="Target project directory path")
    scan_parser.add_argument("--save", action="store_true", help="Save scan results to SQLite database")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze project health & storage")
    analyze_parser.add_argument("path", nargs="?", default=".", help="Target project directory path")
    analyze_parser.add_argument("--save", action="store_true", help="Save scan results to SQLite database")

    size_parser = subparsers.add_parser("size", help="Analyze project storage size")
    size_parser.add_argument("path", nargs="?", default=".", help="Target project directory path")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate HTML/JSON/CSV diagnostic reports")
    report_parser.add_argument("path", nargs="?", default=".", help="Target project directory path")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Analyze log file for anomalies")
    logs_parser.add_argument("path", help="Path to log file")

    args = parser.parse_args()

    if args.command in ["scan", "analyze", "size"]:
        handle_scan_command(args)
    elif args.command == "report":
        handle_report_command(args)
    elif args.command == "logs":
        handle_logs_command(args)
    else:
        if args.gui:
            launch_gui()
        else:
            launch_gui()


if __name__ == "__main__":
    cli_entrypoint()
