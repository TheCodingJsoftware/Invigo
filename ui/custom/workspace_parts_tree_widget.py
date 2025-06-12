from enum import Enum, auto

from PyQt6.QtWidgets import QAbstractItemView, QTreeWidget


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class WorkspacePartsTreeColumns(AutoNumber):
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


class WorkspacePartsTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(WorkspacePartsTreeColumns))
        self.ROW_HEIGHT = 50
        self.setHeaderLabels(
            [
                "Job/Part Name",
                "Files",
                "Material",
                "Paint",
                "Quantity",
                "Quantity in Stock",
                "Process Controls",
                "Shelf #",
                "Notes",
                "Recut",
                "Recoat",
            ]
        )

        self.setUniformRowHeights(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setRootIsDecorated(True)
        self.setStyleSheet(f"QTreeWidget::item {{ height: {self.ROW_HEIGHT}px; }}")
