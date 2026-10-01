"""Project Size & File Explorer View Tab."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QLabel
)
from PySide6.QtCore import Qt


class ProjectSizeView(QWidget):
    """View tab for inspecting project directory sizes, bulk files, and duplicate file groups."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        splitter = QSplitter(Qt.Vertical)

        # Top Section: Largest Directories Table
        dir_box = QGroupBox("Top Directory Footprint")
        dir_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        dir_layout = QVBoxLayout(dir_box)

        self.dir_table = QTableWidget()
        self.dir_table.setColumnCount(3)
        self.dir_table.setHorizontalHeaderLabels(["Directory Path", "Storage Size", "File Count"])
        self.dir_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dir_table.verticalHeader().setVisible(False)
        dir_layout.addWidget(self.dir_table)

        # Bottom Section: Largest Files Table
        files_box = QGroupBox("Largest Files")
        files_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        files_layout = QVBoxLayout(files_box)

        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["Relative Path", "Extension", "Size", "SHA256 Hash"])
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.files_table.verticalHeader().setVisible(False)
        files_layout.addWidget(self.files_table)

        splitter.addWidget(dir_box)
        splitter.addWidget(files_box)
        layout.addWidget(splitter)

    def update_data(self, size_summary):
        """Updates directory and file tables from SizeAnalysisSummary."""
        # Update Directories
        top_dirs = getattr(size_summary, 'top_directories', [])
        self.dir_table.setRowCount(len(top_dirs))
        for row, d in enumerate(top_dirs):
            size_mb = d.size_bytes / (1024 * 1024)
            self.dir_table.setItem(row, 0, QTableWidgetItem(d.directory_path))
            self.dir_table.setItem(row, 1, QTableWidgetItem(f"{size_mb:.2f} MB"))
            self.dir_table.setItem(row, 2, QTableWidgetItem(str(d.file_count)))

        # Update Files
        file_analysis = getattr(size_summary, 'file_analysis', None)
        if file_analysis:
            largest = getattr(file_analysis, 'largest_files', [])
            self.files_table.setRowCount(len(largest))
            for row, f in enumerate(largest):
                size_mb = f.size_bytes / (1024 * 1024)
                self.files_table.setItem(row, 0, QTableWidgetItem(f.relative_path))
                self.files_table.setItem(row, 1, QTableWidgetItem(f.extension))
                self.files_table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.2f} MB"))
                self.files_table.setItem(row, 3, QTableWidgetItem(f.hash_sha256 or "N/A"))
