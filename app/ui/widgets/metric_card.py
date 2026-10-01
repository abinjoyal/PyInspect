"""Reusable metric display card widget."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class MetricCard(QWidget):
    """Custom card widget for displaying key performance and diagnostic metrics."""

    def __init__(self, title: str, value: str = "—", subtitle: str = "", parent: QWidget = None):
        super().__init__(parent)
        self.setProperty("class", "MetricCard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_label = QLabel(title.upper())
        self.title_label.setObjectName("metric_title")

        self.value_label = QLabel(value)
        self.value_label.setObjectName("metric_value")

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("metric_subtitle")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)

    def set_value(self, value: str, subtitle: str = None):
        self.value_label.setText(value)
        if subtitle is not None:
            self.subtitle_label.setText(subtitle)
