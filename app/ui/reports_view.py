"""PySide6 View Tab for Reports & Export and Historical Analysis Comparison."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt

from app.reports.report_generator import ReportGenerator
from app.database.database import Database
from app.database.repository import Repository


class ReportsView(QWidget):
    """View tab for generating reports and comparing historical runs."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.current_data: dict = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 1. Export Section Box
        export_box = QGroupBox("Generate & Export Reports")
        export_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 16px; }")
        e_layout = QHBoxLayout(export_box)

        lbl = QLabel("Export full diagnostic findings into standalone formats:")
        lbl.setStyleSheet("color: #a6adc8;")

        html_btn = QPushButton("Export HTML Report")
        html_btn.setObjectName("primary_btn")
        html_btn.clicked.connect(lambda: self.export_format("html"))

        json_btn = QPushButton("Export JSON")
        json_btn.setObjectName("secondary_btn")
        json_btn.clicked.connect(lambda: self.export_format("json"))

        csv_btn = QPushButton("Export CSV")
        csv_btn.setObjectName("secondary_btn")
        csv_btn.clicked.connect(lambda: self.export_format("csv"))

        e_layout.addWidget(lbl)
        e_layout.addStretch()
        e_layout.addWidget(html_btn)
        e_layout.addWidget(json_btn)
        e_layout.addWidget(csv_btn)

        layout.addWidget(export_box)

        # 2. Historical Run Comparison Box
        hist_box = QGroupBox("Historical Analysis Comparison (SQLite Engine)")
        hist_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 16px; }")
        h_layout = QVBoxLayout(hist_box)

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Select Run #1 (Before):"))
        self.combo_before = QComboBox()
        combo_layout.addWidget(self.combo_before)

        combo_layout.addWidget(QLabel("Select Run #2 (After):"))
        self.combo_after = QComboBox()
        combo_layout.addWidget(self.combo_after)

        compare_btn = QPushButton("Compare Runs")
        compare_btn.setObjectName("primary_btn")
        compare_btn.clicked.connect(self.run_comparison)
        combo_layout.addWidget(compare_btn)

        h_layout.addLayout(combo_layout)

        # Delta Comparison Table
        self.delta_table = QTableWidget()
        self.delta_table.setColumnCount(4)
        self.delta_table.setHorizontalHeaderLabels(["Metric", "Run #1 Value", "Run #2 Value", "Net Delta Change"])
        self.delta_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.delta_table.verticalHeader().setVisible(False)

        h_layout.addWidget(self.delta_table)
        layout.addWidget(hist_box)

    def update_data(self, data: dict):
        self.current_data = data
        # Populate history dropdowns from database if available
        try:
            target_path = data.get("target_path", ".")
            db = Database(Path(target_path) / "pyinspect.db")
            db.initialize()
            repo = Repository(db)
            proj = repo.get_or_create_project("Current", target_path)
            runs = repo.get_latest_analyses(proj.id, limit=10)

            self.combo_before.clear()
            self.combo_after.clear()
            for r in runs:
                item_text = f"Analysis #{r.id} ({r.timestamp}) - Score: {r.health_score}"
                self.combo_before.addItem(item_text, userData=r.id)
                self.combo_after.addItem(item_text, userData=r.id)
        except Exception:
            pass

    def export_format(self, fmt: str):
        if not self.current_data:
            QMessageBox.warning(self, "Export Warning", "Please run a project scan before exporting reports.")
            return

        folder = QFileDialog.getExistingDirectory(self, "Select Export Directory", ".")
        if folder:
            out_dir = Path(folder)
            res = ReportGenerator.generate_all_reports(self.current_data, out_dir)
            target = res.get(fmt)
            QMessageBox.information(self, "Export Complete", f"Successfully exported {fmt.upper()} report to:\n{target}")

    def run_comparison(self):
        id1 = self.combo_before.currentData()
        id2 = self.combo_after.currentData()
        if not id1 or not id2:
            return

        try:
            target_path = self.current_data.get("target_path", ".")
            db = Database(Path(target_path) / "pyinspect.db")
            repo = Repository(db)
            cmp = repo.compare_analyses(id1, id2)

            if "error" in cmp:
                QMessageBox.warning(self, "Comparison Error", cmp["error"])
                return

            self.delta_table.setRowCount(3)
            # Size
            s1 = cmp["before"]["total_size_bytes"] / (1024 * 1024)
            s2 = cmp["after"]["total_size_bytes"] / (1024 * 1024)
            ds = cmp["delta"]["size_bytes"] / (1024 * 1024)
            self.delta_table.setItem(0, 0, QTableWidgetItem("Total Storage Size"))
            self.delta_table.setItem(0, 1, QTableWidgetItem(f"{s1:.2f} MB"))
            self.delta_table.setItem(0, 2, QTableWidgetItem(f"{s2:.2f} MB"))
            self.delta_table.setItem(0, 3, QTableWidgetItem(f"{ds:+.2f} MB"))

            # Files
            f1 = cmp["before"]["total_files"]
            f2 = cmp["after"]["total_files"]
            df = cmp["delta"]["total_files"]
            self.delta_table.setItem(1, 0, QTableWidgetItem("Total Files"))
            self.delta_table.setItem(1, 1, QTableWidgetItem(str(f1)))
            self.delta_table.setItem(1, 2, QTableWidgetItem(str(f2)))
            self.delta_table.setItem(1, 3, QTableWidgetItem(f"{df:+d}"))

            # Health
            h1 = cmp["before"]["health_score"]
            h2 = cmp["after"]["health_score"]
            dh = cmp["delta"]["health_score"]
            self.delta_table.setItem(2, 0, QTableWidgetItem("Health Score"))
            self.delta_table.setItem(2, 1, QTableWidgetItem(f"{h1} / 100"))
            self.delta_table.setItem(2, 2, QTableWidgetItem(f"{h2} / 100"))
            self.delta_table.setItem(2, 3, QTableWidgetItem(f"{dh:+d} pts"))
        except Exception as e:
            QMessageBox.critical(self, "Comparison Failure", f"Failed comparing analysis runs: {e}")
