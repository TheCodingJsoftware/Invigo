from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QPixmap
from PyQt6.QtWidgets import QAbstractItemView, QApplication

from ui.custom_widgets import CustomTableWidget


class ComponentsQuotingTableWidget(CustomTableWidget):
    imagePasted = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_height = 60

        self.picture_column = 0
        self.part_name_column = 1
        self.part_number_column = 2
        self.shelf_number_column = 3
        self.description_column = 4
        self.quantity_column = 5
        self.unit_price_column = 6
        self.price_column = 7

        self.horizontalHeader().setStretchLastSection(True)
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.set_editable_column_index([1, 2, 3, 4, 5, 6])

        headers: dict[str, int] = {
            "Picture": self.picture_column,
            "Part Name": self.part_name_column,
            "Part #": self.part_number_column,
            "Shelf #": self.shelf_number_column,
            "Description": self.description_column,
            "Qty": self.quantity_column,
            "Unit Price": self.unit_price_column,
            "Price": self.price_column,
        }
        self.setColumnCount(len(list(headers.keys())))
        self.setHorizontalHeaderLabels(headers)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Paste):
            self.pasteImageFromClipboard()
        else:
            super().keyPressEvent(event)

    def copySelectedCells(self):
        # Implement this function to copy selected cells to the clipboard if needed
        pass

    def pasteImageFromClipboard(self):
        app: QApplication = QApplication.instance()
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

            new_height = 60
            new_width = int(original_width * (new_height / original_height))

            pixmap = QPixmap.fromImage(image).scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
            image_path = f'images/{datetime.now().strftime("%Y%m%d%H%M%S%f")}.png'
            pixmap.save(image_path)

            item.setData(Qt.ItemDataRole.DecorationRole, pixmap)

            # Optionally, resize the cell to fit the image
            self.resizeColumnToContents(item.column())
            self.resizeRowToContents(item.row())
            self.imagePasted.emit(image_path, item.row())
