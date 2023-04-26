from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem

app = QApplication([])

# Create a QTableWidget with 2 rows and 3 columns
table_widget = QTableWidget(2, 3)

# Set the flags to show only horizontal grid lines
table_widget.setShowGrid(True)
table_widget.setGridStyle(6)
table_widget.setVerticalScrollBarPolicy(1)

# Add some dummy data to the table
table_widget.setItem(0, 0, QTableWidgetItem("Row 1, Column 1"))
table_widget.setItem(0, 1, QTableWidgetItem("Row 1, Column 2"))
table_widget.setItem(0, 2, QTableWidgetItem("Row 1, Column 3"))
table_widget.setItem(1, 0, QTableWidgetItem("Row 2, Column 1"))
table_widget.setItem(1, 1, QTableWidgetItem("Row 2, Column 2"))
table_widget.setItem(1, 2, QTableWidgetItem("Row 2, Column 3"))

# Show the table
table_widget.show()

app.exec_()
