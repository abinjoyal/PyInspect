"""PySide6 View Tab for Memory Profiling and Leak Detection."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QPushButton, QLabel, QSplitter
)
from PySide6.QtCore import Qt, QTimer

from app.analyzers.memory.memory_profiler import MemoryProfiler
from app.analyzers.memory.leak_detector import MemoryLeakDetector
from app.ui.widgets.metric_card import MetricCard


class MemoryView(QWidget):
    """View tab for live memory profiling, heap snapshots, and leak detection."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.profiler = MemoryProfiler()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_tick)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header & Controls
        header_box = QGroupBox("Memory Profiling Controls")
        header_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        h_layout = QHBoxLayout(header_box)

        self.status_label = QLabel("Profiling Status: Stopped")
        self.status_label.setStyleSheet("color: #a6adc8; font-weight: bold;")

        self.start_btn = QPushButton("Start Profiling")
        self.start_btn.setObjectName("primary_btn")
        self.start_btn.clicked.connect(self.start_profiling)

        self.stop_btn = QPushButton("Stop & Analyze")
        self.stop_btn.setObjectName("secondary_btn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_profiling)

        h_layout.addWidget(self.status_label)
        h_layout.addStretch()
        h_layout.addWidget(self.start_btn)
        h_layout.addWidget(self.stop_btn)

        layout.addWidget(header_box)

        # Metrics Cards
        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_initial = MetricCard("Initial RSS", "0 MB", "Baseline before profile")
        self.card_peak = MetricCard("Peak RSS", "0 MB", "Maximum observed heap")
        self.card_growth = MetricCard("Net Growth", "+0 MB", "Classification: Normal")

        grid.addWidget(self.card_initial, 0, 0)
        grid.addWidget(self.card_peak, 0, 1)
        grid.addWidget(self.card_growth, 0, 2)

        layout.addLayout(grid)

        # Tables Section
        splitter = QSplitter(Qt.Vertical)

        # Top Allocations / Differential Table
        diff_box = QGroupBox("Top Memory Accumulating Lines (Tracemalloc Diff)")
        diff_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        d_layout = QVBoxLayout(diff_box)

        self.diff_table = QTableWidget()
        self.diff_table.setColumnCount(4)
        self.diff_table.setHorizontalHeaderLabels(["Filename", "Line #", "Net Size Diff", "Object Count Diff"])
        self.diff_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.diff_table.verticalHeader().setVisible(False)

        d_layout.addWidget(self.diff_table)
        splitter.addWidget(diff_box)

        layout.addWidget(splitter)

    def start_profiling(self):
        self.profiler.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Profiling Status: ACTIVE")
        self.status_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        self.timer.start(1000)  # Take snapshot every second

    def on_timer_tick(self):
        self.profiler.take_snapshot()

    def stop_profiling(self):
        self.timer.stop()
        result = self.profiler.stop()
        MemoryLeakDetector.detect_leaks(result)

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Profiling Status: Stopped")
        self.status_label.setStyleSheet("color: #a6adc8; font-weight: bold;")

        init_mb = result.initial_rss_bytes / (1024 * 1024)
        peak_mb = result.peak_rss_bytes / (1024 * 1024)
        growth_mb = result.total_growth_bytes / (1024 * 1024)

        self.card_initial.set_value(f"{init_mb:.1f} MB")
        self.card_peak.set_value(f"{peak_mb:.1f} MB")
        self.card_growth.set_value(f"+{growth_mb:.1f} MB", f"Status: {result.leak_classification}")

        # Update diff table
        self.diff_table.setRowCount(len(result.top_diffs))
        for row, diff in enumerate(result.top_diffs):
            self.diff_table.setItem(row, 0, QTableWidgetItem(diff.filename))
            self.diff_table.setItem(row, 1, QTableWidgetItem(str(diff.line_number)))
            self.diff_table.setItem(row, 2, QTableWidgetItem(diff.formatted_diff))
            self.diff_table.setItem(row, 3, QTableWidgetItem(f"{diff.count_diff:+d}"))
