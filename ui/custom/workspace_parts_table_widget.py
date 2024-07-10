from enum import Enum, auto
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QTableWidgetItem

from ui.custom_widgets import CustomTableWidget


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class WorkspacePartsTableColumns(AutoNumber):
    PICTURE = auto()
    PART_NAME = auto()
    BENDING_FILES = auto()
    WELDING_FILES = auto()
    CNC_MILLING_FILES = auto()
    MATERIAL = auto()
    THICKNESS = auto()
    PAINT = auto()
    QUANTITY = auto()
    PROCESS_CONTROLS = auto()
    TIMERS = auto()
    NOTES = auto()
    SHELF_NUMBER = auto()


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
            "Picture": WorkspacePartsTableColumns.PICTURE.value,
            "Part Name": WorkspacePartsTableColumns.PART_NAME.value,
            "Bending Files": WorkspacePartsTableColumns.BENDING_FILES.value,
            "Welding Files": WorkspacePartsTableColumns.WELDING_FILES.value,
            "CNC/Milling Files": WorkspacePartsTableColumns.CNC_MILLING_FILES.value,
            "Material": WorkspacePartsTableColumns.MATERIAL.value,
            "Thickness": WorkspacePartsTableColumns.THICKNESS.value,
            "Paint": WorkspacePartsTableColumns.PAINT.value,
            "Quantity": WorkspacePartsTableColumns.QUANTITY.value,
            "Process Controls": WorkspacePartsTableColumns.PROCESS_CONTROLS.value,
            "Timers": WorkspacePartsTableColumns.TIMERS.value,
            "Shelf #": WorkspacePartsTableColumns.SHELF_NUMBER.value,
            "Notes": WorkspacePartsTableColumns.NOTES.value,
        }

        self.setColumnCount(len(headers))
        for header, column in headers.items():
            self.setHorizontalHeaderItem(column, QTableWidgetItem(header))

        self.setStyleSheet("border-color: transparent;")
