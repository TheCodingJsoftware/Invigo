import os
from datetime import datetime
from enum import Enum, auto

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QPixmap
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QTableWidgetItem

from ui.custom_widgets import CustomTableWidget


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class ComponentsTableColumns(AutoNumber):
    PICTURE = auto()
    PART_NAME = auto()
    PART_NUMBER = auto()
    UNIT_QUANTITY = auto()
    QUANTITY = auto()
    SHELF_NUMBER = auto()
    NOTES = auto()


class ComponentsPlanningTableWidget(CustomTableWidget):
    imagePasted = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_height = 60

        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        editable_columns = [
            ComponentsTableColumns.PART_NAME,
            ComponentsTableColumns.PART_NUMBER,
            ComponentsTableColumns.UNIT_QUANTITY,
            ComponentsTableColumns.NOTES,
            ComponentsTableColumns.SHELF_NUMBER,
        ]
        self.set_editable_column_index([col.value for col in editable_columns])

        headers = {
            "Picture": ComponentsTableColumns.PICTURE.value,
            "Part Name": ComponentsTableColumns.PART_NAME.value,
            "Part Number": ComponentsTableColumns.PART_NUMBER.value,
            "Unit Quantity": ComponentsTableColumns.UNIT_QUANTITY.value,
            "Quantity": ComponentsTableColumns.QUANTITY.value,
            "Shelf #": ComponentsTableColumns.SHELF_NUMBER.value,
            "Notes": ComponentsTableColumns.NOTES.value,
        }
        self.setColumnCount(len(headers))
        for header, column in headers.items():
            self.setHorizontalHeaderItem(column, QTableWidgetItem(header))

        self.setStyleSheet("border-color: transparent;")

    def keyPressEvent(self, event: QKeySequence):
        if event.matches(QKeySequence.StandardKey.Paste):
            self.pasteImageFromClipboard()
        else:
            super().keyPressEvent(event)

    def pasteImageFromClipboard(self):
        app = QApplication.instance()
        clipboard = app.clipboard()
        image = clipboard.image()
        if not image.isNull():
            selected_items = self.selectedItems()
            for selected_item in selected_items:
                if selected_item.column() == ComponentsTableColumns.PICTURE.value:
                    item = selected_item
                    break

            original_width = image.width()
            original_height = image.height()

            new_height = self.row_height
            new_width = int(original_width * (new_height / original_height))

            if not os.path.exists("images"):
                os.makedirs("images")
            # Resize the image to fit the specified height while maintaining aspect ratio
            pixmap = QPixmap.fromImage(image).scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_path = f'images/{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png'
            pixmap.save(image_path)

            item.setData(Qt.ItemDataRole.DecorationRole, pixmap)

            # Optionally, resize the cell to fit the image
            self.resizeColumnToContents(item.column())
            self.resizeRowToContents(item.row())
            self.imagePasted.emit(image_path, item.row())
