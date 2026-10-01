"""PySide6 View Tab for Code Behavior Visualizer & Timeline."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QPushButton,
    QLabel, QSplitter, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from app.analyzers.code_behavior.tracer import CodeTracer
from app.analyzers.code_behavior.behavior_analyzer import BehaviorAnalyzer, BehaviorAnalysisResult


class TraceWorkerThread(QThread):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, script_path: Path):
        super().__init__()
        self.script_path = script_path

    def run(self):
        try:
            tracer = CodeTracer(target_script=self.script_path, timeout_sec=8.0)
            events = tracer.run_and_trace()
            result = BehaviorAnalyzer.analyze_events(events)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class BehaviorView(QWidget):
    """View tab for runtime execution tracing and variable state visualization."""

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.selected_script: Path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Controls Header
        header_box = QGroupBox("Target Python Script Selection")
        header_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        h_layout = QHBoxLayout(header_box)

        self.script_label = QLabel("No script selected (Select a .py file to trace)")
        self.script_label.setStyleSheet("color: #a6adc8; font-style: italic;")

        select_btn = QPushButton("Select Script...")
        select_btn.setObjectName("secondary_btn")
        select_btn.clicked.connect(self.select_script)

        self.trace_btn = QPushButton("Trace Execution")
        self.trace_btn.setObjectName("primary_btn")
        self.trace_btn.setEnabled(False)
        self.trace_btn.clicked.connect(self.run_tracing)

        h_layout.addWidget(self.script_label)
        h_layout.addStretch()
        h_layout.addWidget(select_btn)
        h_layout.addWidget(self.trace_btn)

        layout.addWidget(header_box)

        # Main Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: Call Tree Hierarchy
        tree_box = QGroupBox("Call Stack Hierarchy")
        tree_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        t_layout = QVBoxLayout(tree_box)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Function Call", "Duration (ms)", "Line"])
        t_layout.addWidget(self.tree)

        # Right: Timeline & Variable Viewer
        right_splitter = QSplitter(Qt.Vertical)

        # Timeline Table
        timeline_box = QGroupBox("Execution Timeline")
        timeline_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        tl_layout = QVBoxLayout(timeline_box)

        self.timeline_table = QTableWidget()
        self.timeline_table.setColumnCount(4)
        self.timeline_table.setHorizontalHeaderLabels(["Time (ms)", "Event", "Function", "Line #"])
        self.timeline_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.timeline_table.itemSelectionChanged.connect(self.on_timeline_select)
        tl_layout.addWidget(self.timeline_table)

        # Variables State Table
        vars_box = QGroupBox("Variables State (At Selected Step)")
        vars_box.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #313244; border-radius: 8px; margin-top: 6px; padding: 12px; }")
        v_layout = QVBoxLayout(vars_box)

        self.vars_table = QTableWidget()
        self.vars_table.setColumnCount(4)
        self.vars_table.setHorizontalHeaderLabels(["Variable Name", "Type", "Value", "Mutated?"])
        self.vars_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v_layout.addWidget(self.vars_table)

        right_splitter.addWidget(timeline_box)
        right_splitter.addWidget(vars_box)

        splitter.addWidget(tree_box)
        splitter.addWidget(right_splitter)

        layout.addWidget(splitter)

    def select_script(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Python Script", "", "Python Files (*.py)")
        if file_path:
            self.selected_script = Path(file_path).resolve()
            self.script_label.setText(f"Target: {self.selected_script.name}")
            self.script_label.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self.trace_btn.setEnabled(True)

    def run_tracing(self):
        if not self.selected_script or not self.selected_script.exists():
            return

        reply = QMessageBox.question(
            self,
            "Execution Warning",
            f"PyInspect will execute target script '{self.selected_script.name}' under sys.settrace().\n\nEnsure this script is trusted.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.trace_btn.setEnabled(False)
        self.trace_btn.setText("Tracing...")

        self.worker = TraceWorkerThread(self.selected_script)
        self.worker.finished.connect(self.on_trace_finished)
        self.worker.error.connect(self.on_trace_error)
        self.worker.start()

    def on_trace_finished(self, result: BehaviorAnalysisResult):
        self.trace_btn.setEnabled(True)
        self.trace_btn.setText("Trace Execution")
        self.current_result = result

        # 1. Populate Call Tree
        self.tree.clear()
        self.populate_tree_node(self.tree.invisibleRootItem(), result.call_tree_root)
        self.tree.expandAll()

        # 2. Populate Timeline
        self.timeline_table.setRowCount(len(result.events))
        for row, evt in enumerate(result.events):
            self.timeline_table.setItem(row, 0, QTableWidgetItem(f"{evt.timestamp_ms:.2f}"))
            self.timeline_table.setItem(row, 1, QTableWidgetItem(evt.event_type.upper()))
            self.timeline_table.setItem(row, 2, QTableWidgetItem(evt.func_name))
            self.timeline_table.setItem(row, 3, QTableWidgetItem(str(evt.line_number)))

    def populate_tree_node(self, parent_item, call_node):
        for child in call_node.children:
            item = QTreeWidgetItem(parent_item, [child.func_name, f"{child.duration_ms:.2f} ms", str(child.line_number)])
            self.populate_tree_node(item, child)

    def on_timeline_select(self):
        selected_rows = self.timeline_table.selectedIndexes()
        if not selected_rows or not hasattr(self, 'current_result'):
            return

        row = selected_rows[0].row()
        if row < len(self.current_result.events):
            evt = self.current_result.events[row]
            locals_dict = evt.locals_snapshot

            self.vars_table.setRowCount(len(locals_dict))
            for r, (var_name, snap) in enumerate(locals_dict.items()):
                self.vars_table.setItem(r, 0, QTableWidgetItem(var_name))
                self.vars_table.setItem(r, 1, QTableWidgetItem(snap.type_name))
                self.vars_table.setItem(r, 2, QTableWidgetItem(snap.value_repr))
                mut_str = "YES" if snap.is_modified else "No"
                self.vars_table.setItem(r, 3, QTableWidgetItem(mut_str))

    def on_trace_error(self, err_msg: str):
        self.trace_btn.setEnabled(True)
        self.trace_btn.setText("Trace Execution")
        QMessageBox.critical(self, "Tracing Error", f"Failed tracing target script:\n{err_msg}")
