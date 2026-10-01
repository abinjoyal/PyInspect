"""PyInspect Dashboard Tab view."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QPushButton
)
from PySide6.QtCore import Qt
from app.ui.widgets.metric_card import MetricCard
from app.ui.widgets.health_gauge import HealthGauge


class DashboardView(QWidget):
    """Main project summary dashboard displaying metrics cards, health score, and anomaly alerts."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Top Metric Cards Grid
        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_size = MetricCard("Project Size", "0 MB", "Total scanned storage")
        self.card_files = MetricCard("Python Files", "0", "0 total files")
        self.card_deps = MetricCard("Dependencies", "0", "packages declared")
        self.card_memory = MetricCard("Memory Baseline", "0 MB", "tracemalloc baseline")
        self.card_logs = MetricCard("Log Anomalies", "0", "0 critical alerts")
        self.card_complexity = MetricCard("Code Complexity", "Low", "AST static index")

        grid.addWidget(self.card_size, 0, 0)
        grid.addWidget(self.card_files, 0, 1)
        grid.addWidget(self.card_deps, 0, 2)
        grid.addWidget(self.card_memory, 1, 0)
        grid.addWidget(self.card_logs, 1, 1)
        grid.addWidget(self.card_complexity, 1, 2)

        main_layout.addLayout(grid)

        # Health Gauge Section
        health_box = QGroupBox("Project Health")
        health_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 16px; }")
        hb_layout = QVBoxLayout(health_box)
        self.health_gauge = HealthGauge(score=100)
        hb_layout.addWidget(self.health_gauge)

        main_layout.addWidget(health_box)

        # Recent Findings / Anomalies Section
        findings_box = QGroupBox("Recent Diagnostic Findings")
        findings_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 16px; }")
        fb_layout = QVBoxLayout(findings_box)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Severity", "Category", "Location", "Evidence & Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        fb_layout.addWidget(self.table)
        main_layout.addWidget(findings_box)

    def update_data(self, summary_data: dict):
        """Updates metrics and table with new scan results."""
        total_size_mb = summary_data.get("total_size_bytes", 0) / (1024 * 1024)
        self.card_size.set_value(f"{total_size_mb:.1f} MB")
        
        py_files = summary_data.get("python_files", 0)
        tot_files = summary_data.get("total_files", 0)
        self.card_files.set_value(str(py_files), f"out of {tot_files} total files")

        deps_count = summary_data.get("dependency_count", 0)
        self.card_deps.set_value(str(deps_count))

        health_score = summary_data.get("health_score", 100)
        self.health_gauge.set_score(health_score)

        # Populate findings table
        anomalies = summary_data.get("anomalies", [])
        self.table.setRowCount(len(anomalies))
        for row, a in enumerate(anomalies):
            self.table.setItem(row, 0, QTableWidgetItem(getattr(a, 'severity', 'INFO')))
            self.table.setItem(row, 1, QTableWidgetItem(getattr(a, 'category', 'size').upper()))
            self.table.setItem(row, 2, QTableWidgetItem(getattr(a, 'location', 'N/A')))
            self.table.setItem(row, 3, QTableWidgetItem(f"{getattr(a, 'evidence', '')} — {getattr(a, 'suggested_action', '')}"))
