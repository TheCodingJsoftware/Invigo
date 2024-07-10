from enum import Enum, auto
from PyQt6.QtWidgets import QAbstractItemView, QTableWidgetItem

from ui.custom_widgets import CustomTableWidget


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class LaserCutTableColumns(AutoNumber):
    PICTURE = auto()
    PART_NAME = auto()
    FILES = auto()
    MATERIAL = auto()
    THICKNESS = auto()
    UNIT_QUANTITY = auto()
    QUANTITY = auto()
    PART_DIM = auto()
    SHELF_NUMBER = auto()
    PAINTING = auto()
    PAINT_SETTINGS = auto()
    PAINT_COST = auto()
    COST_OF_GOODS = auto()
    BEND_COST = auto()
    LABOR_COST = auto()
    UNIT_PRICE = auto()
    PRICE = auto()
    RECUT = auto()
    ADD_TO_INVENTORY = auto()


class LaserCutPartsQuotingTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_height = 70

        editable_columns = [
            LaserCutTableColumns.UNIT_QUANTITY,
            LaserCutTableColumns.BEND_COST,
            LaserCutTableColumns.LABOR_COST,
            LaserCutTableColumns.SHELF_NUMBER,
        ]

        self.set_editable_column_index([col.value for col in editable_columns])
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        headers = {
            "Picture": LaserCutTableColumns.PICTURE.value,
            "Part name": LaserCutTableColumns.PART_NAME.value,
            "Files": LaserCutTableColumns.FILES.value,
            "Material": LaserCutTableColumns.MATERIAL.value,
            "Thickness": LaserCutTableColumns.THICKNESS.value,
            "Unit Qty": LaserCutTableColumns.UNIT_QUANTITY.value,
            "Qty": LaserCutTableColumns.QUANTITY.value,
            "Part Dim": LaserCutTableColumns.PART_DIM.value,
            "Shelf #": LaserCutTableColumns.SHELF_NUMBER.value,
            "Painting": LaserCutTableColumns.PAINTING.value,
            "Paint Settings": LaserCutTableColumns.PAINT_SETTINGS.value,
            "Paint Cost": LaserCutTableColumns.PAINT_COST.value,
            "Cost of\nGoods": LaserCutTableColumns.COST_OF_GOODS.value,
            "Bend Cost": LaserCutTableColumns.BEND_COST.value,
            "Labor Cost": LaserCutTableColumns.LABOR_COST.value,
            "Unit Price": LaserCutTableColumns.UNIT_PRICE.value,
            "Price": LaserCutTableColumns.PRICE.value,
            "Recut": LaserCutTableColumns.RECUT.value,
            "Add to Inventory": LaserCutTableColumns.ADD_TO_INVENTORY.value,
        }
        self.setColumnCount(len(headers))
        for header, column in headers.items():
            self.setHorizontalHeaderItem(column, QTableWidgetItem(header))

        self.setStyleSheet("border-color: transparent;")
