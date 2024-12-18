from enum import Enum, auto

from PyQt6.QtWidgets import QAbstractItemView, QTreeWidget


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class WorkspaceAssemblyTreeColumns(AutoNumber):
    PICTURE = auto()
    ASSEMBLY_NAME = auto()
    QUANTITY = auto()
    ASSEMBLY_PARTS_BUTTON = auto()
    ASSEMBLY_FILES = auto()
    PAINT = auto()
    PROCESS_CONTROLS = auto()


class WorkspaceAssemblyTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ROW_HEIGHT = 70

        self.setColumnCount(len(WorkspaceAssemblyTreeColumns))
        self.setHeaderLabels(
            [
                "Picture",
                "Assembly Name",
                "Quantity",
                "View Parts",
                "Assembly Files",
                "Paint",
                "Process Controls",
            ]
        )

        self.setUniformRowHeights(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setRootIsDecorated(True)
        self.setStyleSheet(f"QTreeWidget::item {{ height: {self.ROW_HEIGHT}px; }}")
