from PySide6.QtCore import Signal, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDateEdit,
    QCheckBox,
    QPushButton,
    QFrame,
)
from datetime import date
from typing import Optional, Tuple


class DateFilterBar(QWidget):
    filter_changed = Signal()

    def __init__(self):
        super().__init__()
        self._expanded = False
        self._setup_ui()
        self._connect_signals()
        self._update_visibility()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        toggle_row = QHBoxLayout()
        self.toggle_btn = QPushButton("Date Filters ▸")
        self.toggle_btn.setMaximumWidth(150)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(self._toggle_expanded)
        toggle_row.addWidget(self.toggle_btn)
        toggle_row.addStretch()
        main_layout.addLayout(toggle_row)

        self.filter_panel = QFrame()
        self.filter_panel.setFrameStyle(QFrame.StyledPanel)
        filter_layout = QVBoxLayout(self.filter_panel)
        filter_layout.setSpacing(8)

        from_row = QHBoxLayout()
        from_row.addWidget(QLabel("Beginning From:"))
        
        self.from_enabled = QCheckBox("Enable")
        self.from_enabled.setObjectName("from_date_enabled")
        from_row.addWidget(self.from_enabled)
        
        self.from_date = QDateEdit()
        self.from_date.setObjectName("from_date")
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("MMM d, yyyy")
        self.from_date.setDate(QDate(1700, 1, 1))
        self.from_date.setEnabled(False)
        from_row.addWidget(self.from_date)
        
        from_row.addStretch()
        filter_layout.addLayout(from_row)

        to_row = QHBoxLayout()
        to_row.addWidget(QLabel("Up to and Including:"))
        
        self.to_enabled = QCheckBox("Enable")
        self.to_enabled.setObjectName("to_date_enabled")
        to_row.addWidget(self.to_enabled)
        
        self.to_date = QDateEdit()
        self.to_date.setObjectName("to_date")
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("MMM d, yyyy")
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setEnabled(False)
        to_row.addWidget(self.to_date)
        
        to_row.addStretch()
        filter_layout.addLayout(to_row)

        bottom_row = QHBoxLayout()
        bottom_row.addStretch()
        
        self.apply_btn = QPushButton("Apply Filter")
        self.apply_btn.setObjectName("apply_date_filter")
        self.apply_btn.setMaximumWidth(120)
        self.apply_btn.setProperty("class", "primary")
        bottom_row.addWidget(self.apply_btn)
        
        self.clear_btn = QPushButton("Clear All Filters")
        self.clear_btn.setObjectName("clear_date_filters")
        self.clear_btn.setMaximumWidth(120)
        bottom_row.addWidget(self.clear_btn)
        
        filter_layout.addLayout(bottom_row)
        
        main_layout.addWidget(self.filter_panel)

    def _connect_signals(self):
        self.from_enabled.stateChanged.connect(self._on_from_enabled_changed)
        self.to_enabled.stateChanged.connect(self._on_to_enabled_changed)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        self.clear_btn.clicked.connect(self._clear_all_filters)

    def _toggle_expanded(self):
        self._expanded = not self._expanded
        self._update_visibility()

    def _update_visibility(self):
        self.filter_panel.setVisible(self._expanded)
        self.toggle_btn.setText("Date Filters ▾" if self._expanded else "Date Filters ▸")
        self.toggle_btn.setChecked(self._expanded)

    def _on_from_enabled_changed(self, state):
        enabled = bool(state)
        self.from_date.setEnabled(enabled)

    def _on_to_enabled_changed(self, state):
        enabled = bool(state)
        self.to_date.setEnabled(enabled)

    def _on_apply_clicked(self):
        self.filter_changed.emit()

    def _clear_all_filters(self):
        self.blockSignals(True)
        
        self.from_enabled.setChecked(False)
        self.to_enabled.setChecked(False)
        self.from_date.setDate(QDate(1700, 1, 1))
        self.to_date.setDate(QDate.currentDate())
        
        self.blockSignals(False)
        
        self.filter_changed.emit()

    def get_date_filters(self) -> Tuple[Optional[date], Optional[date]]:
        from_date = None
        if self.from_enabled.isChecked():
            qdate = self.from_date.date()
            from_date = date(qdate.year(), qdate.month(), qdate.day())
        
        to_date = None
        if self.to_enabled.isChecked():
            qdate = self.to_date.date()
            to_date = date(qdate.year(), qdate.month(), qdate.day())
        
        return (from_date, to_date)

    def set_date_filters(self, from_date: Optional[date], to_date: Optional[date]):
        self.blockSignals(True)
        
        if from_date:
            self.from_enabled.setChecked(True)
            self.from_date.setDate(QDate(from_date.year, from_date.month, from_date.day))
        else:
            self.from_enabled.setChecked(False)
        
        if to_date:
            self.to_enabled.setChecked(True)
            self.to_date.setDate(QDate(to_date.year, to_date.month, to_date.day))
        else:
            self.to_enabled.setChecked(False)
        
        self.blockSignals(False)

    def has_active_filters(self) -> bool:
        return self.from_enabled.isChecked() or self.to_enabled.isChecked()

    def is_expanded(self) -> bool:
        return self._expanded