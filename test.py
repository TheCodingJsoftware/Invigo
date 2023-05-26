
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QMainWindow,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tableWidget = QTableWidget(4, 4)
        self.setCentralWidget(self.tableWidget)

        # Set table headers
        self.tableWidget.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3", "Column 4"])

        # Create a custom context menu
        self.createContextMenu()

        # Load table data
        self.loadTable()

    def createContextMenu(self):
        # Clear any existing context menu
        if self.tableWidget.contextMenuPolicy() == Qt.CustomContextMenu:
            self.tableWidget.setContextMenuPolicy(Qt.DefaultContextMenu)

        # Create a new custom context menu
        self.contextMenu = QMenu(self)
        action1 = QAction("Action 1", self)
        action2 = QAction("Action 2", self)
        self.contextMenu.addAction(action1)
        self.contextMenu.addAction(action2)

        # Set custom context menu policy
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, pos):
        globalPos = self.tableWidget.mapToGlobal(pos)
        self.contextMenu.exec_(globalPos)

    def loadTable(self):
        # Load table data here
        pass

if __name__ == '__main__':
    app = QApplication([])
    mainWindow = MainWindow()
    mainWindow.show()
    app.exec_()
