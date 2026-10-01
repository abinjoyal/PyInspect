"""Main PySide6 Window container for PyInspect Desktop Application."""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QPushButton, QLabel, QFileDialog, QMessageBox, QFrame, QProgressDialog
)
from PySide6.QtCore import Qt, QThread, Signal

from app.ui.style import DARK_THEME_QSS
from app.ui.dashboard import DashboardView
from app.ui.project_view import ProjectSizeView
from app.ui.behavior_view import BehaviorView
from app.ui.memory_view import MemoryView
from app.ui.log_view import LogView
from app.ui.reports_view import ReportsView
from app.core.config import PyInspectConfig
from app.scanner.project_scanner import ProjectScanner
from app.scanner.dependency_scanner import DependencyScanner
from app.analyzers.size.size_analyzer import SizeAnalyzer


class ScanWorkerThread(QThread):
    """Background worker thread to keep the UI responsive while scanning large projects."""
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, target_path: Path):
        super().__init__()
        self.target_path = target_path

    def run(self):
        try:
            config_file = self.target_path / "pyinspect.toml"
            config = PyInspectConfig.load_from_file(config_file)

            scanner = ProjectScanner(
                exclude_patterns=config.scanner.exclude,
                calculate_hashes=config.scanner.calculate_hashes
            )
            scan_result = scanner.scan(self.target_path)
            deps = DependencyScanner.scan_dependencies(self.target_path)

            size_analyzer = SizeAnalyzer()
            summary = size_analyzer.analyze_scan(scan_result)

            data = {
                "target_path": str(self.target_path),
                "total_size_bytes": summary.total_size_bytes,
                "total_files": summary.total_files,
                "python_files": summary.python_files,
                "directory_count": summary.directory_count,
                "dependency_count": len(deps),
                "health_score": summary.storage_health_score,
                "anomalies": summary.anomalies,
                "size_summary": summary
            }
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))


class PyInspectMainWindow(QMainWindow):
    """Main window with sidebar navigation, top header, and tabbed view container."""

    def __init__(self, target_dir: str = "."):
        super().__init__()
        self.target_dir = Path(target_dir).resolve()
        self.setWindowTitle("PyInspect — Python Project Intelligence & Diagnostics Platform")
        self.resize(1200, 750)
        self.setStyleSheet(DARK_THEME_QSS)

        self.init_ui()
        if self.target_dir.exists():
            self.start_scan(self.target_dir)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Sidebar Navigation
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(4)

        app_title = QLabel("PyInspect")
        app_title.setObjectName("app_title")
        app_subtitle = QLabel("Project Intelligence")
        app_subtitle.setObjectName("app_subtitle")

        sidebar_layout.addWidget(app_title)
        sidebar_layout.addWidget(app_subtitle)

        # Sidebar Buttons
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0))

        self.btn_project_size = QPushButton("Project Size")
        self.btn_project_size.setCheckable(True)
        self.btn_project_size.clicked.connect(lambda: self.switch_page(1))

        self.btn_code_behavior = QPushButton("Code Behavior")
        self.btn_code_behavior.setCheckable(True)
        self.btn_code_behavior.clicked.connect(lambda: self.switch_page(2))

        self.btn_memory = QPushButton("Memory Leak")
        self.btn_memory.setCheckable(True)
        self.btn_memory.clicked.connect(lambda: self.switch_page(3))

        self.btn_logs = QPushButton("Log Anomalies")
        self.btn_logs.setCheckable(True)
        self.btn_logs.clicked.connect(lambda: self.switch_page(4))

        self.btn_reports = QPushButton("Reports & Export")
        self.btn_reports.setCheckable(True)
        self.btn_reports.clicked.connect(lambda: self.switch_page(5))

        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_project_size)
        sidebar_layout.addWidget(self.btn_code_behavior)
        sidebar_layout.addWidget(self.btn_memory)
        sidebar_layout.addWidget(self.btn_logs)
        sidebar_layout.addWidget(self.btn_reports)
        sidebar_layout.addStretch()

        root_layout.addWidget(sidebar)

        # 2. Main Content Container
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header Toolbar
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        self.project_label = QLabel(f"Project: {self.target_dir.name}")
        self.project_label.setObjectName("project_title")

        open_btn = QPushButton("Open Project...")
        open_btn.setObjectName("primary_btn")
        open_btn.clicked.connect(self.open_project_dialog)

        scan_btn = QPushButton("Re-Scan")
        scan_btn.setObjectName("secondary_btn")
        scan_btn.clicked.connect(lambda: self.start_scan(self.target_dir))

        header_layout.addWidget(self.project_label)
        header_layout.addStretch()
        header_layout.addWidget(scan_btn)
        header_layout.addWidget(open_btn)

        content_layout.addWidget(header)

        # Stacked Pages
        self.pages = QStackedWidget()
        self.dashboard_view = DashboardView()
        self.project_size_view = ProjectSizeView()
        self.behavior_view = BehaviorView()
        self.memory_view = MemoryView()
        self.log_view = LogView()
        self.reports_view = ReportsView()

        self.pages.addWidget(self.dashboard_view)
        self.pages.addWidget(self.project_size_view)
        self.pages.addWidget(self.behavior_view)
        self.pages.addWidget(self.memory_view)
        self.pages.addWidget(self.log_view)
        self.pages.addWidget(self.reports_view)

        content_layout.addWidget(self.pages)
        root_layout.addWidget(content_container)

    def switch_page(self, index: int):
        self.pages.setCurrentIndex(index)
        self.btn_dashboard.setChecked(index == 0)
        self.btn_project_size.setChecked(index == 1)
        self.btn_code_behavior.setChecked(index == 2)
        self.btn_memory.setChecked(index == 3)
        self.btn_logs.setChecked(index == 4)
        self.btn_reports.setChecked(index == 5)

    def open_project_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Python Project Directory", str(self.target_dir))
        if folder:
            self.target_dir = Path(folder).resolve()
            self.project_label.setText(f"Project: {self.target_dir.name}")
            self.start_scan(self.target_dir)

    def start_scan(self, path: Path):
        self.progress_dialog = QProgressDialog("Scanning project files...", None, 0, 0, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()

        self.worker = ScanWorkerThread(path)
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.error.connect(self.on_scan_error)
        self.worker.start()

    def on_scan_finished(self, data: dict):
        self.progress_dialog.close()
        self.dashboard_view.update_data(data)
        self.reports_view.update_data(data)
        if "size_summary" in data:
            self.project_size_view.update_data(data["size_summary"])

    def on_scan_error(self, err_msg: str):
        self.progress_dialog.close()
        QMessageBox.critical(self, "Scan Error", f"Failed to analyze project:\n{err_msg}")
