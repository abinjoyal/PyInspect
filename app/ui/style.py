"""Centralized Qt Style Sheets (QSS) for PyInspect Dark Theme."""

DARK_THEME_QSS = """
/* Global Window & Typography */
QMainWindow, QDialog {
    background-color: #11111b;
    color: #cdd6f4;
    font-family: 'Segoe UI', 'Roboto', 'Inter', sans-serif;
    font-size: 13px;
}

QWidget {
    color: #cdd6f4;
}

/* Sidebar Navigation */
#sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
    min-width: 220px;
    max-width: 220px;
}

#sidebar QLabel#app_title {
    font-size: 18px;
    font-weight: bold;
    color: #89b4fa;
    padding: 16px 12px 4px 12px;
}

#sidebar QLabel#app_subtitle {
    font-size: 11px;
    color: #a6adc8;
    padding: 0px 12px 16px 12px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #a6adc8;
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    margin: 2px 8px;
    font-weight: 500;
}

#sidebar QPushButton:hover {
    background-color: #313244;
    color: #cdd6f4;
}

#sidebar QPushButton:checked {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
}

/* Header Area */
#header {
    background-color: #181825;
    border-bottom: 1px solid #313244;
    padding: 8px 16px;
}

#header QLabel#project_title {
    font-size: 16px;
    font-weight: bold;
    color: #f5e0dc;
}

/* Content Area & Cards */
.MetricCard {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 16px;
}

.MetricCard:hover {
    border: 1px solid #89b4fa;
}

QLabel#metric_title {
    font-size: 12px;
    color: #a6adc8;
    text-transform: uppercase;
}

QLabel#metric_value {
    font-size: 24px;
    font-weight: bold;
    color: #89b4fa;
}

QLabel#metric_subtitle {
    font-size: 11px;
    color: #a6adc8;
}

/* Tables */
QTableWidget, QTreeView {
    background-color: #1e1e2e;
    alternate-background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    gridline-color: #313244;
    color: #cdd6f4;
    selection-background-color: #45475a;
    selection-color: #f5e0dc;
}

QHeaderView::section {
    background-color: #181825;
    color: #89b4fa;
    padding: 6px;
    font-weight: bold;
    border: 1px solid #313244;
}

/* Buttons */
QPushButton#primary_btn {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
    padding: 8px 18px;
    border-radius: 6px;
    border: none;
}

QPushButton#primary_btn:hover {
    background-color: #b4befe;
}

QPushButton#secondary_btn {
    background-color: #313244;
    color: #cdd6f4;
    padding: 8px 18px;
    border-radius: 6px;
    border: 1px solid #45475a;
}

QPushButton#secondary_btn:hover {
    background-color: #45475a;
}

/* Progress Bar */
QProgressBar {
    background-color: #313244;
    border-radius: 6px;
    height: 14px;
    text-align: center;
    color: #11111b;
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #a6e3a1;
    border-radius: 6px;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #181825;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
"""
