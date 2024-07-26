from enum import Enum, auto

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QTableWidgetItem

from ui.custom_widgets import CustomTableWidget


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class WorkspaceAssemblyTableColumns(AutoNumber):
    PICTURE = auto()
    ASSEMBLY_NAME = auto()
    ASSEMBLY_FILES = auto()
    PAINT = auto()
    PROCESS_CONTROLS = auto()


class WorkspaceAssemblyTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_height = 70

        editable_columns = []

        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.set_editable_column_index([col.value for col in editable_columns])

        headers = {
            "Picture": WorkspaceAssemblyTableColumns.PICTURE.value,
            "Assembly Name": WorkspaceAssemblyTableColumns.ASSEMBLY_NAME.value,
            "Assembly Files": WorkspaceAssemblyTableColumns.ASSEMBLY_FILES.value,
            "Paint": WorkspaceAssemblyTableColumns.PAINT.value,
            "Process Controls": WorkspaceAssemblyTableColumns.PROCESS_CONTROLS.value,
        }

        self.setColumnCount(len(headers))
        for header, column in headers.items():
            self.setHorizontalHeaderItem(column, QTableWidgetItem(header))

        self.setStyleSheet("border-color: transparent;")
