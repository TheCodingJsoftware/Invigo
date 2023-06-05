import json
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem


class CustomTreeWidgetItem(QTreeWidgetItem):
    itemChanged = pyqtSignal(QTreeWidgetItem, int)

    def setData(self, column, role, value):
        super().setData(column, role, value)
        if role == Qt.EditRole:
            self.itemChanged.emit(self, column)


def load_json_data(data, parent_item):
    for key, value in data.items():
        if isinstance(value, dict):
            child_item = CustomTreeWidgetItem(parent_item)
            child_item.setText(0, str(key))
            load_json_data(value, child_item)
        elif isinstance(value, list):
            for item in value:
                child_item = CustomTreeWidgetItem(parent_item)
                child_item.setText(0, str(item))
        else:
            child_item = CustomTreeWidgetItem(parent_item)
            child_item.setText(0, str(key))
            child_item.setText(1, str(value))
            child_item.setFlags(child_item.flags() | Qt.ItemIsEditable)


# Load JSON data from file
with open("data/workspace.json") as file:
    json_data = json.load(file)

# Create the application
app = QApplication([])

# Create the tree widget
tree_widget = QTreeWidget()
tree_widget.setHeaderLabels(["Key", "Value"])
tree_widget.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.EditKeyPressed)

# Connect the signal to a custom slot
def onItemChanged(item, column):
    print("Item changed:", item.text(column))


tree_widget.itemChanged.connect(onItemChanged)
# Load the JSON data into the tree widget
load_json_data(json_data, tree_widget)

# Show the tree widget
tree_widget.show()

# Run the application
app.exec_()
