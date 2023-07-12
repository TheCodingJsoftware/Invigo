from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


def _create_item(text, is_folder):
    item = QStandardItem(text)
    item.setData(is_folder, Qt.UserRole)
    return item


def _folder_row(name, date):
    return [_create_item(text, True) for text in (name, date)]


def _file_row(name, date):
    return [_create_item(text, False) for text in (name, date)]


class _SortProxyModel(QSortFilterProxyModel):
    """Sorting proxy model that always places folders on top."""

    def __init__(self, model):
        super().__init__()
        self.setSourceModel(model)

    def lessThan(self, left, right):
        """Perform sorting comparison.

        Since we know the sort order, we can ensure that folders always come first.
        """
        left_is_folder = left.data(Qt.UserRole)
        left_data = left.data(Qt.DisplayRole)
        right_is_folder = right.data(Qt.UserRole)
        right_data = right.data(Qt.DisplayRole)
        sort_order = self.sortOrder()

        if left_is_folder and not right_is_folder:
            result = sort_order == Qt.AscendingOrder
        elif not left_is_folder and right_is_folder:
            result = sort_order != Qt.AscendingOrder
        else:
            result = left_data < right_data
        return result


class _Window(QMainWindow):
    def __init__(self):
        super().__init__()

        widget = QWidget()
        self.__view = QTreeView()
        layout = QVBoxLayout(widget)
        layout.addWidget(self.__view)
        self.setCentralWidget(widget)

        model = QStandardItemModel()
        model.appendRow(_file_row("File #1", "01.09.2014"))
        model.appendRow(_folder_row("Folder #1", "01.09.2014"))
        model.appendRow(_folder_row("Folder #2", "02.09.2014"))
        model.appendRow(_file_row("File #2", "03.09.2014"))
        model.setHorizontalHeaderLabels(["Name", "Date"])
        proxy_model = _SortProxyModel(model)
        self.__view.setModel(proxy_model)
        self.__view.setSortingEnabled(True)


app = QApplication([])
w = _Window()
w.show()
app.exec_()
