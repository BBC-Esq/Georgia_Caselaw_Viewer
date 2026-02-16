import pandas as pd
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from config.settings import EXPECTED_COLUMNS


class PandasModel(QAbstractTableModel):
    def __init__(self, data=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._data = data
        self._display_columns = []
        self._update_display_columns()

    def _update_display_columns(self):
        if self._data.empty:
            self._display_columns = []
        else:
            self._display_columns = [col for col in EXPECTED_COLUMNS if col in self._data.columns]

    def update_data(self, data: pd.DataFrame):
        self.beginResetModel()
        self._data = data
        self._update_display_columns()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._display_columns)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and index.isValid():
            try:
                col_name = self._display_columns[index.column()]
                return str(self._data.iloc[index.row()][col_name])
            except (IndexError, KeyError):
                return None
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._display_columns[section] if section < len(self._display_columns) else ""
        return str(section)

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled