"""PySide6 View Tab for Log Anomaly Detection."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QPushButton, QLabel, QComboBox, QSplitter, QFileDialog
)
from PySide6.QtCore import Qt

from app.analyzers.logs.log_parser import LogParser, LogEntry
from app.analyzers.logs.anomaly_detector import LogAnomalyDetector, LogAnalysisSummary
from app.ui.widgets.metric_card import MetricCard


class LogView(QWidget):
    """View tab for inspecting log events, filtering error levels, and detecting pattern anomalies."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.entries: list[LogEntry] = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # File Selector Header
        header_box = QGroupBox("Log File Selection & Filter")
        header_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        h_layout = QHBoxLayout(header_box)

        self.file_label = QLabel("No log file loaded (Select .log, .txt, or .json file)")
        self.file_label.setStyleSheet("color: #a6adc8; font-style: italic;")

        select_btn = QPushButton("Select Log File...")
        select_btn.setObjectName("secondary_btn")
        select_btn.clicked.connect(self.select_log_file)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["ALL LEVELS", "ERROR / CRITICAL", "WARNING", "INFO"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)

        h_layout.addWidget(self.file_label)
        h_layout.addStretch()
        h_layout.addWidget(QLabel("Filter:"))
        h_layout.addWidget(self.filter_combo)
        h_layout.addWidget(select_btn)

        layout.addWidget(header_box)

        # Metric Cards
        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_total = MetricCard("Total Log Events", "0", "Parsed log records")
        self.card_errors = MetricCard("Errors & Criticals", "0", "0% error rate")
        self.card_patterns = MetricCard("Pattern Anomalies", "0", "Matches detected")

        grid.addWidget(self.card_total, 0, 0)
        grid.addWidget(self.card_errors, 0, 1)
        grid.addWidget(self.card_patterns, 0, 2)

        layout.addLayout(grid)

        # Main Table Area
        splitter = QSplitter(Qt.Vertical)

        events_box = QGroupBox("Log Events Stream")
        events_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        e_layout = QVBoxLayout(events_box)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["Line #", "Timestamp", "Level", "Message Payload"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.verticalHeader().setVisible(False)

        e_layout.addWidget(self.log_table)
        splitter.addWidget(events_box)

        layout.addWidget(splitter)

    def select_log_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Log File", "", "Log Files (*.log *.txt *.json *.jsonl);;All Files (*.*)")
        if file_path:
            path = Path(file_path).resolve()
            self.file_label.setText(f"Loaded: {path.name}")
            self.file_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self.entries = LogParser.parse_file(path)
            self.filter_combo.setCurrentIndex(0)  # Reset filter to ALL LEVELS
            self.analyze_and_display()

    def analyze_and_display(self):
        summary = LogAnomalyDetector.analyze_logs(self.entries)
        
        self.card_total.set_value(str(summary.total_events))
        errors_count = summary.level_counts.get("ERROR", 0) + summary.level_counts.get("CRITICAL", 0)
        err_pct = (errors_count / summary.total_events * 100) if summary.total_events > 0 else 0
        self.card_errors.set_value(str(errors_count), f"{err_pct:.1f}% error rate")
        self.card_patterns.set_value(str(len(summary.pattern_matches)))

        self.apply_filter()

    def apply_filter(self):
        filter_text = self.filter_combo.currentText()
        filtered = self.entries

        if filter_text == "ERROR / CRITICAL":
            filtered = [e for e in self.entries if e.level in ["ERROR", "CRITICAL"]]
        elif filter_text == "WARNING":
            filtered = [e for e in self.entries if e.level in ["WARNING", "WARN"]]
        elif filter_text == "INFO":
            filtered = [e for e in self.entries if e.level == "INFO"]

        self.log_table.setRowCount(len(filtered))
        for row, entry in enumerate(filtered):
            self.log_table.setItem(row, 0, QTableWidgetItem(str(entry.line_number)))
            self.log_table.setItem(row, 1, QTableWidgetItem(entry.timestamp_str or "N/A"))
            self.log_table.setItem(row, 2, QTableWidgetItem(entry.level))
            self.log_table.setItem(row, 3, QTableWidgetItem(entry.message))
