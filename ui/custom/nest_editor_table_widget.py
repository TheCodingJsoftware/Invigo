from enum import Enum, auto

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QTableWidgetItem, QTreeWidget

from ui.custom_widgets import CustomTableWidget


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class NestEditorPartsTableColumns(AutoNumber):
    PICTURE = auto()
    PART_NAME = auto()
    MATERIAL = auto()
    THICKNESS = auto()
    QUANTITY_ON_SHEET = auto()
    TOTAL_QUANTITY = auto()
    PART_DIMENSION = auto()
    RECUT = auto()


class NestEditorPartsTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_height = 70

        editable_columns: list[NestEditorPartsTableColumns] = [
            NestEditorPartsTableColumns.QUANTITY_ON_SHEET,
        ]

        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.set_editable_column_index([col.value for col in editable_columns])

        headers = {
            "Picture": NestEditorPartsTableColumns.PICTURE.value,
            "Part name": NestEditorPartsTableColumns.PART_NAME.value,
            "Material": NestEditorPartsTableColumns.MATERIAL.value,
            "Thickness": NestEditorPartsTableColumns.THICKNESS.value,
            "Quantity\non Sheet": NestEditorPartsTableColumns.QUANTITY_ON_SHEET.value,
            "Total\nQuantity": NestEditorPartsTableColumns.TOTAL_QUANTITY.value,
            "Part Dim": NestEditorPartsTableColumns.PART_DIMENSION.value,
            "Recut": NestEditorPartsTableColumns.RECUT.value,
        }

        self.setColumnCount(len(headers))
        for header, column in headers.items():
            self.setHorizontalHeaderItem(column, QTableWidgetItem(header))
