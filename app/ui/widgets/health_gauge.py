"""Health score visual progress bar and indicator widget."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt


class HealthGauge(QWidget):
    """Displays project health score with color-coded feedback."""

    def __init__(self, score: int = 100, parent: QWidget = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        self.label = QLabel("Project Health Score")
        self.label.setStyleSheet("font-weight: bold; font-size: 14px; color: #cdd6f4;")
        
        self.score_badge = QLabel(f"{score} / 100")
        self.score_badge.setStyleSheet("font-weight: bold; font-size: 16px; color: #a6e3a1;")

        header_layout.addWidget(self.label)
        header_layout.addStretch()
        header_layout.addWidget(self.score_badge)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(score)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.progress)
        self.set_score(score)

    def set_score(self, score: int):
        self.progress.setValue(score)
        self.score_badge.setText(f"{score} / 100")

        if score >= 80:
            color = "#a6e3a1"  # Soft green
        elif score >= 60:
            color = "#f9e2af"  # Yellow
        else:
            color = "#f38ba8"  # Soft red

        self.score_badge.setStyleSheet(f"font-weight: bold; font-size: 16px; color: {color};")
        self.progress.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 6px; }}"
        )
