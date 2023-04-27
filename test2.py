from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem

app = QApplication([])
window = QMainWindow()

table = QTableWidget()
table.setRowCount(2)
table.setColumnCount(2)

cell1 = QTableWidgetItem("1")
cell2 = QTableWidgetItem("2")
cell3 = QTableWidgetItem("3")
cell4 = QTableWidgetItem("4")

table.setItem(0, 0, cell1)
table.setItem(0, 1, cell2)
table.setItem(1, 0, cell3)
table.setItem(1, 1, cell4)

# Set style for specific cell
cell1.setBackgroundColor(QColor("green"))

# Set style for all cells
table.setStyleSheet(
    "QTableWidget::item:selected { background-color: blue; }"
    "QTableWidget::item:!selected { background-color: red; }"
)

window.setCentralWidget(table)
window.show()
app.exec_()
