from enum import Enum, auto

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QTableWidgetItem

from ui.custom_widgets import CustomTableWidget


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class WorkspacePartsTableColumns(AutoNumber):
    PART_NAME = auto()
    FILES = auto()
    MATERIAL = auto()
    PAINT = auto()
    QUANTITY = auto()
    QUANTITY_IN_STOCK = auto()
    PROCESS_CONTROLS = auto()
    NOTES = auto()
    SHELF_NUMBER = auto()
    RECUT = auto()
    RECOAT = auto()


class WorkspacePartsTableWidget(CustomTableWidget):
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
            "Part Name": WorkspacePartsTableColumns.PART_NAME.value,
            "Files": WorkspacePartsTableColumns.FILES.value,
            "Material": WorkspacePartsTableColumns.MATERIAL.value,
            "Paint": WorkspacePartsTableColumns.PAINT.value,
            "Quantity": WorkspacePartsTableColumns.QUANTITY.value,
            "Quantity in Stock": WorkspacePartsTableColumns.QUANTITY_IN_STOCK.value,
            "Process Controls": WorkspacePartsTableColumns.PROCESS_CONTROLS.value,
            "Shelf #": WorkspacePartsTableColumns.SHELF_NUMBER.value,
            "Notes": WorkspacePartsTableColumns.NOTES.value,
            "Recut": WorkspacePartsTableColumns.RECUT.value,
            "Recoat": WorkspacePartsTableColumns.RECOAT.value,
        }

        self.setColumnCount(len(headers))
        for header, column in headers.items():
            self.setHorizontalHeaderItem(column, QTableWidgetItem(header))
