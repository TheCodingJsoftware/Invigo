from PyQt5.QtWidgets import QTableWidgetItem, QTableWidget, QApplication, QWidget, QVBoxLayout
from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QDialog


# Create the table
app = QApplication([])
window = QWidget()
layout = QVBoxLayout()
table = QTableWidget()
table.setColumnCount(2)
table.setRowCount(6)
layout.addWidget(table)
window.setLayout(layout)

# Insert data into cells
table.setItem(0, 0, QTableWidgetItem("Group 1"))
table.setItem(0, 1, QTableWidgetItem("Data 1"))
table.setItem(1, 0, QTableWidgetItem("Data 2"))
table.setItem(2, 0, QTableWidgetItem("Data 3"))
table.setItem(3, 0, QTableWidgetItem("Group 2"))
table.setItem(3, 1, QTableWidgetItem("Data 4"))
table.setItem(4, 0, QTableWidgetItem("Data 5"))
table.setItem(5, 0, QTableWidgetItem("Data 6"))

# Group rows by merging cells
table.setSpan(0, 0, 1, 2)  # Merge cells for Group 1
table.setSpan(3, 0, 1, 2)  # Merge cells for Group 2

# Apply style to the grouped cells
group_background_color = "lightgray"
group_font_weight = "bold"
for row in range(table.rowCount()):
    item = table.item(row, 0)
    if item and item.text().startswith("Group"):
        item.setBackground(QColor(group_background_color))

window.show()
app.exec_()