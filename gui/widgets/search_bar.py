from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QLineEdit, QLabel, QCheckBox
from config.settings import settings

class SearchBar(QWidget):
    search_requested = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Search Column:"))
        self.column_selector = QComboBox()
        self.column_selector.setFixedWidth(settings.column_width_file_selector)
        self.column_selector.setObjectName("column_selector")
        layout.addWidget(self.column_selector)
        layout.addWidget(QLabel("Search Text:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Enter search text here…")
        self.search_box.setObjectName("search_box")
        layout.addWidget(self.search_box)
        self.fuzzy_checkbox = QCheckBox("Show Fuzzy Results")
        self.fuzzy_checkbox.setObjectName("fuzzy_checkbox")
        layout.addWidget(self.fuzzy_checkbox)

    def _connect_signals(self):
        self.search_box.textChanged.connect(self._on_search_text_changed)
        self.fuzzy_checkbox.stateChanged.connect(self._on_search_text_changed)

    def _on_search_text_changed(self):
        self.search_requested.emit(self.column_selector.currentText(), self.search_box.text().strip())

    def set_columns(self, columns: list):
        self.column_selector.clear()
        self.column_selector.addItems(columns)

    def set_search_text(self, text: str):
        self.search_box.blockSignals(True)
        self.search_box.setText(text)
        self.search_box.blockSignals(False)

    def show_fuzzy_results(self) -> bool:
        return self.fuzzy_checkbox.isChecked()
