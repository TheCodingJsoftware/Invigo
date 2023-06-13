from PyQt6.QtCore import QFile, QFileInfo, Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QApplication, QHeaderView, QTableView, QAbstractItemView


class FreezeTableWidget(QTableView):
    def __init__(self, model):
        super().__init__()
        self.setModel(model)
        self.frozenTableView = QTableView(self)
        self.init()
        self.horizontalHeader().sectionResized.connect(self.updateSectionWidth)
        self.verticalHeader().sectionResized.connect(self.updateSectionHeight)
        self.frozenTableView.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(self.frozenTableView.verticalScrollBar().setValue)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def init(self):
        self.frozenTableView.setModel(self.model())
        self.frozenTableView.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.frozenTableView.verticalHeader().hide()
        self.frozenTableView.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.viewport().stackUnder(self.frozenTableView)

        self.frozenTableView.setStyleSheet(
            """
            QTableView { border: none;
                         background-color: #8EDE21;
                         selection-background-color: #999;
            }"""
        )  # for demo purposes

        self.frozenTableView.setSelectionModel(self.selectionModel())
        for col in range(1, self.model().columnCount()):
            self.frozenTableView.setColumnHidden(col, True)
        self.frozenTableView.setColumnWidth(0, self.columnWidth(0))
        self.frozenTableView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frozenTableView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.frozenTableView.show()
        self.updateFrozenTableGeometry()
        self.setHorizontalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.frozenTableView.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)

    def updateSectionWidth(self, logicalIndex, oldSize, newSize):
        self.frozenTableView.setColumnWidth(0, newSize)
        self.updateFrozenTableGeometry()

    def updateSectionHeight(self, logicalIndex, oldSize, newSize):
        self.frozenTableView.setRowHeight(logicalIndex, newSize)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateFrozenTableGeometry()

    def moveCursor(self, cursorAction, modifiers):
        current = super().moveCursor(cursorAction, modifiers)
        if (
            cursorAction == self.CursorAction.MoveLeft
            and self.current.column() > 0
            and self.visualRect(current).topLeft().x() < self.frozenTableView.columnWidth(0)
        ):
            newValue = self.horizontalScrollBar().value() + self.visualRect(current).topLeft().x() - self.frozenTableView.columnWidth(0)
            self.horizontalScrollBar().setValue(newValue)
        return current

    def scrollTo(self, index, hint):
        if index.column() > 0:
            super().scrollTo(index, hint)

    def updateFrozenTableGeometry(self):
        self.frozenTableView.setGeometry(
            self.verticalHeader().width() + self.frameWidth(),
            self.frameWidth(),
            self.columnWidth(0),
            self.viewport().height() + self.horizontalHeader().height(),
        )

    def setCellWidget(self, row, column, widget):
        index = self.model().index(row, column)
        self.setIndexWidget(index, widget)

    def getRowCount(self):
        return self.model().rowCount()

    def insertRow(self, row, items):
        self.model().insertRow(row, items)

    def removeRow(self, row):
        self.model().removeRow(row - 1)


def main(args):
    def split_and_strip(s, splitter):
        return [s.strip() for s in line.split(splitter)]

    app = QApplication(args)
    model = QStandardItemModel()
    file = QFile(QFileInfo(__file__).absolutePath() + "/grades.txt")
    if file.open(QFile.OpenModeFlag.ReadOnly):
        line = file.readLine(200).decode("utf-8")
        header = split_and_strip(line, ",")
        model.setHorizontalHeaderLabels(header)
        row = 0
        while file.canReadLine():
            line = file.readLine(200).decode("utf-8")
            if not line.startswith("#") and "," in line:
                fields = split_and_strip(line, ",")
                model.insertRow(row)
                for col, field in enumerate(fields):
                    newItem = QStandardItem(field)
                    model.setItem(row, col, newItem)
                row += 1
    file.close()
    tableView = FreezeTableWidget(model)
    tableView.setWindowTitle("Frozen Column Example")
    tableView.resize(560, 680)
    print(tableView.getRowCount())
    tableView.removeRow(tableView.getRowCount())
    tableView.show()
    return app.exec()


if __name__ == "__main__":
    import sys

    main(sys.argv)
