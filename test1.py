import sys
from PyQt5.QtWidgets import QApplication, QColumnView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QItemSelectionModel

def create_item(text, parent=None):
    item = QStandardItem(text)
    if parent is not None:
        parent.appendRow(item)
    return item

if __name__ == '__main__':
    app = QApplication(sys.argv)

    model = QStandardItemModel()

    material_item = create_item("Material", model)
    create_item("Wood", material_item)
    create_item("Metal", material_item)
    create_item("Plastic", material_item)

    thickness_item = create_item("Thickness", model)
    create_item("Thin", thickness_item)
    create_item("Medium", thickness_item)
    create_item("Thick", thickness_item)

    column_view = QColumnView()
    column_view.setModel(model)
    column_view.setSelectionMode(3)

    # Enable multi-selection

    column_view.show()

    sys.exit(app.exec_())
