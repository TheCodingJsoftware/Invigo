import contextlib
import copy
import sys
from datetime import datetime
from functools import partial

import ujson as json
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QMainWindow, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget

from utils.json_file import JsonFile
from utils.settings import Settings

settings_file = Settings()


class TableWidget(QTableWidget):
    def __init__(self, parent, data):
        super(TableWidget, self).__init__(parent)
        self.data = data
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Thickness", "Value"])
        self.setRowCount(0)

        for thickness, value in self.data.items():
            currentRow = self.rowCount()
            self.insertRow(currentRow)
            thicknessItem = QTableWidgetItem(thickness)
            thicknessItem.setFlags(thicknessItem.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.setItem(currentRow, 0, thicknessItem)
            valueItem = QTableWidgetItem(str(value))
            self.setItem(currentRow, 1, valueItem)
        self.resizeColumnsToContents()
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 100)


class SheetEditor(QMainWindow):
    windowClosed = pyqtSignal()

    def __init__(self, parent):
        super(SheetEditor, self).__init__(parent=parent)
        self.setWindowTitle("Sheet Editor")
        self.showMaximized()
        self.show()

        with open("price_of_steel_information.json", "r", encoding="utf-8") as file:
            self.data = json.load(file)

        self.price_of_steel_inventory = JsonFile(file_name=f"data/{settings_file.get_value('inventory_file_name')} - Price of Steel")
        with open("price_of_steel_information.json", "r", encoding="utf-8") as file:
            self.data = json.load(file)

        self.threads = []

        self.materialsList = QListWidget(self)
        self.thicknessesList = QListWidget(self)

        self.materialsList.itemDoubleClicked.connect(self.editMaterialName)
        self.thicknessesList.itemDoubleClicked.connect(self.editThicknessName)

        self.tabWidget = QTabWidget(self)
        self.last_selected_tab = None
        self.last_selected_index = None
        self.tabs: list[QWidget] = []
        self.tabWidget.currentChanged.connect(self.tab_changed)

        self.loadInitialData()

        self.addMaterialButton = QPushButton("Add Material", self)
        self.addMaterialButton.clicked.connect(self.addMaterial)

        self.addThicknessButton = QPushButton("Add Thickness", self)
        self.addThicknessButton.clicked.connect(self.addThickness)

        self.removeMaterialButton = QPushButton("Remove Material", self)
        self.removeMaterialButton.clicked.connect(self.removeMaterial)

        self.removeThicknessButton = QPushButton("Remove Thickness", self)
        self.removeThicknessButton.clicked.connect(self.removeThickness)

        self.saveButton = QPushButton("Close and Apply Changes", self)
        self.saveButton.clicked.connect(self.save)

        layout = QHBoxLayout(self)
        tabLayout = QVBoxLayout()
        listsLayout = QVBoxLayout()

        listsLayout.addWidget(QLabel("Materials:"))
        listsLayout.addWidget(self.materialsList)
        listsLayout.addWidget(self.addMaterialButton)
        listsLayout.addWidget(self.removeMaterialButton)
        listsLayout.addWidget(QLabel("Thicknesses:"))
        listsLayout.addWidget(self.thicknessesList)
        listsLayout.addWidget(self.addThicknessButton)
        listsLayout.addWidget(self.removeThicknessButton)

        tabLayout.addWidget(QLabel("Pounds per square foot:"))
        tabLayout.addWidget(self.tabWidget)
        tabLayout.addWidget(self.saveButton)
        layout.addLayout(listsLayout)
        layout.addLayout(tabLayout)
        layout.setStretch(1, 1)
        layout.setStretch(0, 0)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def loadInitialData(self):
        for material in self.data["materials"]:
            self.materialsList.addItem(material)

        for thickness in self.data["thicknesses"]:
            self.thicknessesList.addItem(thickness)

        self.load_data()

    def editMaterialName(self, item: QListWidgetItem):
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Edit Material", "New material name:", text=item.text())
        if ok and new_name:
            item.setText(new_name)

            self.data["materials"].remove(old_name)
            self.data["materials"].append(new_name)

            data_copy = copy.deepcopy(self.data["pounds_per_square_foot"][old_name])
            del self.data["pounds_per_square_foot"][old_name]
            self.data["pounds_per_square_foot"][new_name] = data_copy

            price_of_steel_data = copy.deepcopy(self.price_of_steel_inventory.get_data())
            copy_data = copy.deepcopy(price_of_steel_data["Price Per Pound"][old_name])
            del price_of_steel_data["Price Per Pound"][old_name]
            price_of_steel_data["Price Per Pound"][new_name] = copy_data
            self.price_of_steel_inventory.save_data(price_of_steel_data)

            self.load_data()

    def editThicknessName(self, item: QListWidgetItem):
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "Edit Thickness", "New thickness value:", text=item.text())
        if ok and new_name:
            item.setText(new_name)

            self.data["thicknesses"].remove(old_name)
            self.data["thicknesses"].append(new_name)

            data_copy = copy.deepcopy(self.data)
            for material, data in data_copy["pounds_per_square_foot"].items():
                for data_thickness in list(data.keys()):
                    if old_name == data_thickness:
                        copy_value = self.data["pounds_per_square_foot"][material][old_name]
                        del self.data["pounds_per_square_foot"][material][old_name]
                        self.data["pounds_per_square_foot"][material][new_name] = copy_value

            self.load_data()

    def addMaterial(self):
        text, ok = QInputDialog.getText(self, "Add Material", "Material name:")
        if ok and text:
            self.materialsList.addItem(text)
            self.data["materials"].append(text)

            self.data["pounds_per_square_foot"][text] = {}
            thicknesses = [self.thicknessesList.item(i).text() for i in range(self.thicknessesList.count())]
            for thickness in thicknesses:
                self.data["pounds_per_square_foot"][text][thickness] = 0
            modified_date: str = f'Created at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
            price_of_steel_data = copy.deepcopy(self.price_of_steel_inventory.get_data())
            price_of_steel_data["Price Per Pound"][text] = {
                "price": 0.0,
                "latest_change_price": modified_date,
            }
            self.price_of_steel_inventory.save_data(price_of_steel_data)

            self.load_data()

    def addThickness(self):
        text, ok = QInputDialog.getText(self, "Add Thickness", "Thickness value:")
        if ok and text:
            self.thicknessesList.addItem(text)
            self.data["thicknesses"].append(text)

            for material, _ in self.data["pounds_per_square_foot"].items():
                self.data["pounds_per_square_foot"][material][text] = 0

            self.load_data()

    def removeMaterial(self):
        materials = [self.materialsList.item(i).text() for i in range(self.materialsList.count())]
        material, ok = QInputDialog.getItem(self, "Remove Material", "Select a material to remove:", materials, 0, False)
        if ok and material:
            if foundItems := self.materialsList.findItems(material, Qt.MatchFlag.MatchExactly):
                item = foundItems[0]
                row = self.materialsList.row(item)
                self.materialsList.takeItem(row)

            self.data["materials"].remove(material)
            del self.data["pounds_per_square_foot"][material]

            price_of_steel_data = copy.deepcopy(self.price_of_steel_inventory.get_data())
            del price_of_steel_data["Price Per Pound"][material]
            self.price_of_steel_inventory.save_data(price_of_steel_data)

            self.load_data()

    def removeThickness(self):
        thicknesses = [self.thicknessesList.item(i).text() for i in range(self.thicknessesList.count())]
        thickness, ok = QInputDialog.getItem(
            self,
            "Remove Thickness",
            "Select a thickness to remove:",
            thicknesses,
            0,
            False,
        )
        if ok and thickness:
            if foundItems := self.thicknessesList.findItems(thickness, Qt.MatchFlag.MatchExactly):
                item = foundItems[0]
                row = self.thicknessesList.row(item)
                self.thicknessesList.takeItem(row)

            self.data["thicknesses"].remove(thickness)

            data_copy = copy.deepcopy(self.data)
            for material, data in data_copy["pounds_per_square_foot"].items():
                for data_thickness in list(data.keys()):
                    if thickness == data_thickness:
                        del self.data["pounds_per_square_foot"][material][thickness]

            self.load_data()

    def tab_changed(self):
        current_tab = self.tabWidget.tabText(self.tabWidget.currentIndex())
        self.last_selected_tab = current_tab
        self.last_selected_index = self.tabWidget.currentIndex()

    def table_cell_changed(self, table: TableWidget, material: str, item: QTableWidgetItem):
        thickness = table.item(item.row(), 0).text()
        print(material, thickness, item.text())
        with contextlib.suppress(Exception):
            self.data["pounds_per_square_foot"][material][thickness] = float(item.text())

    def load_data(self):
        self.tabWidget.blockSignals(True)
        self.tabWidget.clear()
        self.tabs.clear()
        materials = [self.materialsList.item(i).text() for i in range(self.materialsList.count())]
        for material in materials:
            if self.last_selected_tab is None:
                self.last_selected_tab = material
            if self.last_selected_index is None:
                self.last_selected_index = 0
            widget = TableWidget(self.tabWidget, self.data["pounds_per_square_foot"][material])
            widget.itemChanged.connect(partial(self.table_cell_changed, widget, material))
            self.tabs.append(widget)
            self.tabWidget.addTab(widget, material)

        self.tabWidget.setCurrentIndex(self.last_selected_index)
        self.tabWidget.blockSignals(False)

    def save(self):
        with open("price_of_steel_information.json", "w", encoding="utf-8") as file:
            json.dump(self.data, file, sort_keys=True, indent=4)
        self.close()

    def closeEvent(self, event):
        self.windowClosed.emit()
        super(SheetEditor, self).closeEvent(event)
