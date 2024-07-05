import os
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QPixmap
from PyQt6.QtWidgets import QAbstractItemView, QApplication

from ui.custom_widgets import CustomTableWidget


class ComponentsPlanningTableWidget(CustomTableWidget):
    imagePasted = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_height = 60

        self.picture_column = 0
        self.part_name_column = 1
        self.part_number_column = 2
        self.quantity_column = 3
        self.notes_column = 4
        self.shelf_number_column = 5

        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.set_editable_column_index(
            [
                self.part_name_column,
                self.part_number_column,
                self.quantity_column,
                self.notes_column,
                self.shelf_number_column,
            ]
        )

        headers: dict[str, int] = {
            "Picture": self.picture_column,
            "Part Name": self.part_name_column,
            "Part Number": self.part_number_column,
            "Quantity": self.quantity_column,
            "Notes": self.notes_column,
            "Shelf #": self.shelf_number_column,
        }
        self.setColumnCount(len(list(headers.keys())))
        self.setHorizontalHeaderLabels(headers)
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
                if selected_item.column() == 0:
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
