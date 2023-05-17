import os
import sys

from PyQt5.QtCore import QDir, QModelIndex, QSortFilterProxyModel, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView


class PdfFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sort_order = Qt.DescendingOrder

    def filterAcceptsRow(self, row, parent):
        """
        This function filters rows based on whether they contain a file with a .pdf extension.

        Args:
          row: The row number of the item being filtered in the view.
          parent: The parent index of the current index being filtered. It represents the parent item in
        the model hierarchy.

        Returns:
          a boolean value indicating whether the row should be included in the filtered view or not.
        """
        index = self.sourceModel().index(row, 0, parent)
        if not index.isValid():
            return False
        if self.sourceModel().isDir(index):
            return any(
                file.lower().endswith('.pdf')
                for file in os.listdir(self.sourceModel().filePath(index))
            )
        filename = self.sourceModel().fileName(index)
        return filename.lower().endswith('.pdf')

    def lessThan(self, left_index, right_index):
        """
        This function overrides the lessThan method to sort a specific column in a QAbstractTableModel
        based on the sort order.

        Args:
          left_index: The QModelIndex object representing the left item being compared in the sorting
        operation.
          right_index: The index of the item on the right side of the comparison being made in the
        model. In other words, it is the index of the item that is being compared to the item at the
        left_index.

        Returns:
          The method `lessThan` is returning a boolean value indicating whether the data at the
        `left_index` is less than the data at the `right_index`. If the columns of the indices are not
        2, it calls the `lessThan` method of the parent class. If the sort order is descending, it
        returns `left_data > right_data`, otherwise it returns `left_data < right
        """
        if left_index.column() != 2 or right_index.column() != 2:
            return super().lessThan(left_index, right_index)
        left_data = self.sourceModel().data(left_index, Qt.UserRole)
        right_data = self.sourceModel().data(right_index, Qt.UserRole)
        return left_data > right_data if self.sort_order == Qt.DescendingOrder else left_data < right_data

    def sort(self, column, order):
        """
        This function sorts a table by a specified column and order, and updates the sort order
        attribute if the column is the second column.

        Args:
          column: The column number that the data should be sorted by.
          order: The order parameter specifies the sorting order, which can be either Qt.AscendingOrder
        or Qt.DescendingOrder. Qt.AscendingOrder sorts the items in ascending order, while
        Qt.DescendingOrder sorts the items in descending order.
        """
        if column == 2:
            self.sort_order = order
        super().sort(column, order)


class PdfTreeView(QTreeView):
    def __init__(self, path: str):
        super().__init__()
        self.model = QFileSystemModel()
        self.model.setRootPath('')
        self.setModel(self.model)
        self.filterModel = PdfFilterProxyModel()
        self.filterModel.setSourceModel(self.model)
        self.setModel(self.filterModel)
        self.filterModel.setFilterRegExp('')
        self.filterModel.setFilterKeyColumn(0)
        self.setRootIndex(
            self.filterModel.mapFromSource(self.model.index(path)))
        self.header().resizeSection(0, 300)
        self.header().hideSection(1)
        self.header().hideSection(2)
        self.expandAll()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tree_view = PdfTreeView(r'F:\Code\Python-Projects\Laser-Quote-Generator')
    # Change this to the directory you want to show
    tree_view.show()
    sys.exit(app.exec_())
