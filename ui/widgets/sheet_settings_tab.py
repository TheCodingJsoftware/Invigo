import contextlib
import os
from typing import TYPE_CHECKING
from datetime import datetime

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QFont, QIcon
from PyQt6.QtWidgets import QApplication, QAbstractItemView, QComboBox, QDialog, QDoubleSpinBox, QInputDialog, QLineEdit, QListWidget, QMenu, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget

from ui.custom_widgets import CustomTableWidget, CustomTabWidget
from utils.settings import Settings
from utils.sheet_settings.pounds_per_square_foot import Pound
from utils.sheet_settings.price_per_pound import Price
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.sheet_settings.thickness import Thickness

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow

settings_file = Settings()


class PricePerPoundTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(True)
        self.setRowCount(0)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.set_editable_column_index([1])
        headers: list[str] = ["Material", "Price Per Pound", "Modified Date"]
        self.horizontalHeader().setStretchLastSection(True)
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)


class PoundsPerSquareFootTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setShowGrid(True)
        self.setRowCount(0)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.set_editable_column_index([1])
        headers: list[str] = ["Thickness", "Pounds Per Square Foot", "Modified Date"]
        self.horizontalHeader().setStretchLastSection(True)
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)


class PoundsPerSquareFootTab(CustomTabWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)


class PopoutWidget(QWidget):
    def __init__(self, layout_to_popout: QVBoxLayout, parent=None):
        super().__init__(parent)
        self.parent: MainWindow = parent
        self.original_layout = layout_to_popout
        self.original_layout_parent: "SheetSettingsTab" = self.original_layout.parentWidget()
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Sheet Settings")
        self.setWindowIcon(QIcon.fromTheme("document-properties"))
        self.setLayout(self.original_layout)

    def closeEvent(self, event):
        if self.original_layout_parent:
            self.original_layout_parent.setLayout(self.original_layout)
            self.original_layout_parent.pushButton_popout.setIcon(QIcon("icons/open_in_new.png"))
            self.original_layout_parent.pushButton_popout.clicked.disconnect()
            self.original_layout_parent.pushButton_popout.clicked.connect(self.original_layout_parent.popout)
        super().closeEvent(event)


class SheetSettingsTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        uic.loadUi("ui/widgets/sheet_settings_tab.ui", self)
        self.parent: MainWindow = parent
        self.sheet_settings = self.parent.sheet_settings

        self.price_per_pound_table: PricePerPoundTableWidget = None
        self.price_per_pound_table_items: dict[Price, QTableWidgetItem] = {}

        self.pounds_per_square_foot_tab: PoundsPerSquareFootTab = None
        self.pounds_per_square_foot_tables: dict[int, PoundsPerSquareFootTableWidget] = {}
        self.pounds_per_square_foot_table_items: dict[Pound, QTableWidgetItem] = {}

        self.last_selected_index: int = 0
        self.load_ui()

    def load_ui(self):
        self.sheet_settings.load_data()
        self.tables_font = QFont()
        self.tables_font.setFamily(settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(settings_file.get_value("tables_font")["italic"])

        self.nitrogen_cost_spinbox = self.findChild(QDoubleSpinBox, "nitrogen_cost_spinbox")
        self.nitrogen_cost_spinbox.setValue(self.sheet_settings.cost_for_laser["Nitrogen"])
        self.nitrogen_cost_spinbox.editingFinished.connect(self.nitrogen_spin_box_changed)
        self.co2_cost_spinbox = self.findChild(QDoubleSpinBox, "co2_cost_spinbox")
        self.co2_cost_spinbox.setValue(self.sheet_settings.cost_for_laser["CO2"])
        self.co2_cost_spinbox.editingFinished.connect(self.co2_spin_box_changed)

        self.tabWidget = self.findChild(QTabWidget, "tabWidget")

        self.price_per_pound_layout = self.findChild(QVBoxLayout, "price_per_pound_layout")

        self.pounds_per_square_foot_layout = self.findChild(QVBoxLayout, "pounds_per_square_foot_layout")

        self.materials_list = self.findChild(QListWidget, "materials_list")
        self.materials_list.doubleClicked.connect(self.rename_material)
        self.materials_list.itemSelectionChanged.connect(self.material_list_clicked)

        self.pushButton_add_material = self.findChild(QPushButton, "pushButton_add_material")
        self.pushButton_add_material.clicked.connect(self.add_material)
        self.pushButton_add_material.setIcon(QIcon("icons/list_add.png"))

        self.pushButton_remove_material = self.findChild(QPushButton, "pushButton_remove_material")
        self.pushButton_remove_material.clicked.connect(self.remove_material)
        self.pushButton_remove_material.setIcon(QIcon("icons/list_remove.png"))

        self.thicknesses_list = self.findChild(QListWidget, "thicknesses_list")
        self.thicknesses_list.doubleClicked.connect(self.rename_thickness)
        self.thicknesses_list.itemSelectionChanged.connect(self.thickness_list_clicked)

        self.pushButton_add_thickness = self.findChild(QPushButton, "pushButton_add_thickness")
        self.pushButton_add_thickness.clicked.connect(self.add_thickness)
        self.pushButton_add_thickness.setIcon(QIcon("icons/list_add.png"))

        self.pushButton_remove_thickness = self.findChild(QPushButton, "pushButton_remove_thickness")
        self.pushButton_remove_thickness.clicked.connect(self.remove_thickness)
        self.pushButton_remove_thickness.setIcon(QIcon("icons/list_remove.png"))

        self.tableWidget_thickness_id = self.findChild(QTableWidget, "tableWidget_thickness_id")

        self.load_thickness_ids()

        self.lineEdit_SS_name = self.findChild(QLineEdit, "lineEdit_SS_name")
        self.comboBox_SS_cut = self.findChild(QComboBox, "comboBox_SS_cut")

        self.lineEdit_ST_name = self.findChild(QLineEdit, "lineEdit_ST_name")
        self.comboBox_ST_cut = self.findChild(QComboBox, "comboBox_ST_cut")

        self.lineEdit_AL_name = self.findChild(QLineEdit, "lineEdit_AL_name")
        self.comboBox_AL_cut = self.findChild(QComboBox, "comboBox_AL_cut")

        self.lineEdit_GALV_name = self.findChild(QLineEdit, "lineEdit_GALV_name")
        self.comboBox_GALV_cut = self.findChild(QComboBox, "comboBox_GALV_cut")

        self.lineEdit_GALN_name = self.findChild(QLineEdit, "lineEdit_GALN_name")
        self.comboBox_GALN_cut = self.findChild(QComboBox, "comboBox_GALN_cut")

        self.load_material_cutting_methods()

        self.lineEdit_SS_name.editingFinished.connect(self.material_cutting_changes)
        self.comboBox_SS_cut.currentTextChanged.connect(self.material_cutting_changes)
        self.lineEdit_ST_name.editingFinished.connect(self.material_cutting_changes)
        self.comboBox_ST_cut.currentTextChanged.connect(self.material_cutting_changes)
        self.lineEdit_AL_name.editingFinished.connect(self.material_cutting_changes)
        self.comboBox_AL_cut.currentTextChanged.connect(self.material_cutting_changes)
        self.lineEdit_GALV_name.editingFinished.connect(self.material_cutting_changes)
        self.comboBox_GALV_cut.currentTextChanged.connect(self.material_cutting_changes)
        self.lineEdit_GALN_name.editingFinished.connect(self.material_cutting_changes)
        self.comboBox_GALN_cut.currentTextChanged.connect(self.material_cutting_changes)

        self.pushButton_popout = self.findChild(QPushButton, "pushButton_popout")
        self.pushButton_popout.setStyleSheet("background-color: transparent; border: none;")
        self.pushButton_popout.clicked.connect(self.popout)

        self.load_tabs()

    def load_tabs(self):
        self.materials_list.blockSignals(True)
        self.materials_list.clear()
        self.materials_list.addItems(self.sheet_settings.get_materials())
        self.materials_list.blockSignals(False)
        self.thicknesses_list.blockSignals(True)
        self.thicknesses_list.clear()
        self.thicknesses_list.addItems(self.sheet_settings.get_thicknesses())
        self.thicknesses_list.blockSignals(False)

        self.clear_layout(self.pounds_per_square_foot_layout)
        self.pounds_per_square_foot_tab = PoundsPerSquareFootTab(self)
        self.pounds_per_square_foot_tab.currentChanged.connect(self.pounds_per_square_foot_tab_changed)
        self.pounds_per_square_foot_layout.addWidget(self.pounds_per_square_foot_tab)
        self.load_pounds_per_square_foot()

        self.price_per_pound_table = PricePerPoundTableWidget(self)
        self.clear_layout(self.price_per_pound_layout)
        self.price_per_pound_layout.addWidget(self.price_per_pound_table)
        self.load_price_per_pound_table()
        self.price_per_pound_table.cellChanged.connect(self.price_per_pound_table_changed)

    def load_material_cutting_methods(self):
        self.lineEdit_SS_name.setText(self.sheet_settings.material_id["cutting_methods"]["SS"]["name"])
        self.comboBox_SS_cut.setCurrentText(self.sheet_settings.material_id["cutting_methods"]["SS"]["cut"])
        self.lineEdit_ST_name.setText(self.sheet_settings.material_id["cutting_methods"]["ST"]["name"])
        self.comboBox_ST_cut.setCurrentText(self.sheet_settings.material_id["cutting_methods"]["ST"]["cut"])
        self.lineEdit_AL_name.setText(self.sheet_settings.material_id["cutting_methods"]["AL"]["name"])
        self.comboBox_AL_cut.setCurrentText(self.sheet_settings.material_id["cutting_methods"]["AL"]["cut"])
        self.lineEdit_GALV_name.setText(self.sheet_settings.material_id["cutting_methods"]["GALV"]["name"])
        self.comboBox_GALV_cut.setCurrentText(self.sheet_settings.material_id["cutting_methods"]["GALV"]["cut"])
        self.lineEdit_GALN_name.setText(self.sheet_settings.material_id["cutting_methods"]["GALN"]["name"])
        self.comboBox_GALN_cut.setCurrentText(self.sheet_settings.material_id["cutting_methods"]["GALN"]["cut"])

    def load_thickness_ids(self):
        for row, (thickness_id, thickness) in enumerate(self.sheet_settings.material_id["thickness_ids"].items()):
            self.tableWidget_thickness_id.insertRow(row)
            thickness_id_item = QTableWidgetItem(thickness_id)
            thickness_id_item.setFont(self.tables_font)

            self.tableWidget_thickness_id.setItem(row, 0, thickness_id_item)
            thickness_item = QTableWidgetItem(thickness)
            thickness_item.setFont(self.tables_font)
            self.tableWidget_thickness_id.setItem(row, 1, thickness_item)
        self.tableWidget_thickness_id.cellChanged.connect(self.thickness_id_table_changes)

    def thickness_id_table_changes(self):
        self.tableWidget_thickness_id.blockSignals(True)
        for row in range(self.tableWidget_thickness_id.rowCount()):
            thickness_id = self.tableWidget_thickness_id.item(row, 0)
            thickness = self.tableWidget_thickness_id.item(row, 1)
            self.sheet_settings.material_id["thickness_ids"].update({thickness_id.text(): thickness.text()})
        self.tableWidget_thickness_id.blockSignals(False)

        self.sheet_settings.save_data()
        self.sync_changes()

    def material_cutting_changes(self):
        self.sheet_settings.material_id["cutting_methods"]["SS"]["name"] = self.lineEdit_SS_name.text()
        self.sheet_settings.material_id["cutting_methods"]["SS"]["cut"] = self.comboBox_SS_cut.currentText()

        self.sheet_settings.material_id["cutting_methods"]["ST"]["name"] = self.lineEdit_ST_name.text()
        self.sheet_settings.material_id["cutting_methods"]["ST"]["cut"] = self.comboBox_ST_cut.currentText()

        self.sheet_settings.material_id["cutting_methods"]["AL"]["name"] = self.lineEdit_AL_name.text()
        self.sheet_settings.material_id["cutting_methods"]["AL"]["cut"] = self.comboBox_AL_cut.currentText()

        self.sheet_settings.material_id["cutting_methods"]["GALV"]["name"] = self.lineEdit_GALV_name.text()
        self.sheet_settings.material_id["cutting_methods"]["GALV"]["cut"] = self.comboBox_GALV_cut.currentText()

        self.sheet_settings.material_id["cutting_methods"]["GALN"]["name"] = self.lineEdit_GALN_name.text()
        self.sheet_settings.material_id["cutting_methods"]["GALN"]["cut"] = self.comboBox_GALN_cut.currentText()

        self.sheet_settings.save_data()
        self.sync_changes()

    def load_price_per_pound_table(self):
        self.price_per_pound_table_items.clear()
        self.price_per_pound_table.clearContents()
        self.price_per_pound_table.setRowCount(0)
        self.price_per_pound_table.blockSignals(True)
        for row, (material, price_per_pound) in enumerate(self.sheet_settings.price_per_pound):
            self.price_per_pound_table.insertRow(row)
            table_item_material = QTableWidgetItem(material.name)
            table_item_material.setFont(self.tables_font)
            self.price_per_pound_table.setItem(row, 0, table_item_material)

            table_item_price = QTableWidgetItem(f"${price_per_pound.price_per_pound:,.2f}")
            table_item_price.setFont(self.tables_font)
            self.price_per_pound_table.setItem(row, 1, table_item_price)
            self.price_per_pound_table_items[price_per_pound] = table_item_price

            table_item_latest_change = QTableWidgetItem(price_per_pound.latest_change)
            table_item_latest_change.setFont(self.tables_font)
            self.price_per_pound_table.setItem(row, 2, table_item_latest_change)
        self.price_per_pound_table.blockSignals(False)

    def price_per_pound_table_changed(self):
        for price, table_item_price in self.price_per_pound_table_items.items():
            new_price = float(table_item_price.text().strip().replace("$", "").replace(",", ""))
            old_price = price.price_per_pound
            if new_price != old_price:
                modified_date: str = f'{os.getlogin().title()} - Modified from ${old_price:,.2f} to ${new_price:,.2f} at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
                price.price_per_pound = new_price
                price.latest_change = modified_date
        self.sheet_settings.save_data()
        self.sync_changes()
        self.load_price_per_pound_table()

    def load_pounds_per_square_foot(self):
        self.pounds_per_square_foot_table_items.clear()
        self.pounds_per_square_foot_tables.clear()
        self.pounds_per_square_foot_tab.blockSignals(True)
        self.pounds_per_square_foot_tab.clear()
        for i, (material, thickness_data) in enumerate(self.sheet_settings.pounds_per_square_foot):
            material_pounds_per_square_foot_table = PoundsPerSquareFootTableWidget(self)
            self.pounds_per_square_foot_tables.update({i: material_pounds_per_square_foot_table})
            self.load_material_pounds_per_square_foot_table(thickness_data, material_pounds_per_square_foot_table)
            material_pounds_per_square_foot_table.resizeColumnsToContents()
            self.pounds_per_square_foot_tab.addTab(material_pounds_per_square_foot_table, material.name)
        self.pounds_per_square_foot_tab.blockSignals(False)
        self.pounds_per_square_foot_tab.setCurrentIndex(self.last_selected_index)

    def load_material_pounds_per_square_foot_table(self, data: dict[Thickness, Pound], table: PoundsPerSquareFootTableWidget):
        for row, (thickness, pound) in enumerate(data.items()):
            table.insertRow(row)
            table_item_thickness = QTableWidgetItem(thickness.name)
            table_item_thickness.setFont(self.tables_font)
            table.setItem(row, 0, table_item_thickness)

            table_item_pounds = QTableWidgetItem(f"{pound.pounds_per_square_foot:,.4f}")
            table_item_pounds.setFont(self.tables_font)
            table.setItem(row, 1, table_item_pounds)
            self.pounds_per_square_foot_table_items[pound] = table_item_pounds

            table_item_latest_change = QTableWidgetItem(pound.latest_change)
            table_item_latest_change.setFont(self.tables_font)
            table.setItem(row, 2, table_item_latest_change)
        table.cellChanged.connect(self.pounds_per_square_foot_table_changed)

    def pounds_per_square_foot_table_changed(self):
        for pound, table_item_pounds in self.pounds_per_square_foot_table_items.items():
            new_value = float(table_item_pounds.text().replace(",", "").strip())
            old_value = pound.pounds_per_square_foot
            if new_value != old_value:
                modified_date: str = f'{os.getlogin().title()} - Modified from {old_value:,.4f} to {new_value:,.4f} at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
                pound.pounds_per_square_foot = new_value
                pound.latest_change = modified_date
        self.sheet_settings.save_data()
        self.sync_changes()
        self.load_pounds_per_square_foot()

    def pounds_per_square_foot_tab_changed(self):
        self.last_selected_index = self.pounds_per_square_foot_tab.currentIndex()

    def nitrogen_spin_box_changed(self):
        self.sheet_settings.cost_for_laser["Nitrogen"] = self.nitrogen_cost_spinbox.value()
        self.sheet_settings.save_data()
        self.sync_changes()

    def co2_spin_box_changed(self):
        self.sheet_settings.cost_for_laser["CO2"] = self.co2_cost_spinbox.value()
        self.sheet_settings.save_data()
        self.sync_changes()

    def material_list_clicked(self):
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Price Per Pound":
            for row in range(self.price_per_pound_table.rowCount()):
                if self.price_per_pound_table.item(row, 0).text() == self.materials_list.selectedItems()[0].text():
                    self.price_per_pound_table.selectRow(row)
                    return
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Pounds Per Square Foot":
            self.pounds_per_square_foot_tab.setCurrentIndex(self.sheet_settings.get_materials().index(self.materials_list.selectedItems()[0].text()))

    def thickness_list_clicked(self):
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Pounds Per Square Foot":
            current_table = self.pounds_per_square_foot_tables[self.pounds_per_square_foot_tab.currentIndex()]
            for row in range(current_table.rowCount()):
                if current_table.item(row, 0).text() == self.thicknesses_list.selectedItems()[0].text():
                    current_table.selectRow(row)
                    return

    def add_material(self):
        new_material_name, ok = QInputDialog.getText(self, "Add material", "Enter a material name:")
        if new_material_name and ok:
            self.sheet_settings.add_material(new_material_name)
            self.sheet_settings.save_data()
            self.sync_changes()
            self.load_tabs()

    def remove_material(self):
        try:
            selected_row = self.sheet_settings.get_materials().index(self.materials_list.selectedItems()[0].text())
        except IndexError:
            selected_row = 0
        material_to_remove, ok = QInputDialog.getItem(
            self,
            "Remove material",
            "Select a material to remove",
            self.sheet_settings.get_materials(),
            selected_row,
            False,
        )
        if material_to_remove and ok:
            self.sheet_settings.remove_material(material_to_remove)
            self.sheet_settings.save_data()
            self.sync_changes()
            self.load_tabs()

    def rename_material(self):
        selected_material = self.sheet_settings.materials.get(self.materials_list.selectedItems()[0].text())
        text, ok = QInputDialog.getText(self, "Rename material", "Enter a new name:", text=selected_material.name)
        if text and ok:
            selected_material.name = text
            self.sheet_settings.save_data()
            self.sync_changes()
            self.load_tabs()

    def add_thickness(self):
        new_thickness_name, ok = QInputDialog.getText(self, "Add thickness", "Enter a thickness name:")
        if new_thickness_name and ok:
            self.sheet_settings.add_thickness(new_thickness_name)
            self.sheet_settings.save_data()
            self.sync_changes()
            self.load_tabs()

    def remove_thickness(self):
        try:
            selected_row = self.sheet_settings.get_thicknesses().index(self.thicknesses_list.selectedItems()[0].text())
        except IndexError:
            selected_row = 0
        thickness_to_remove, ok = QInputDialog.getItem(
            self,
            "Remove thickness",
            "Select a thickness to remove",
            self.sheet_settings.get_thicknesses(),
            selected_row,
            False,
        )
        if thickness_to_remove and ok:
            self.sheet_settings.remove_thickness(thickness_to_remove)
            self.sheet_settings.save_data()
            self.sync_changes()
            self.load_tabs()

    def rename_thickness(self):
        selected_thickness = self.sheet_settings.thicknesses.get(self.thicknesses_list.selectedItems()[0].text())
        text, ok = QInputDialog.getText(self, "Rename material", "Enter a new name:", text=selected_thickness.name)
        if text and ok:
            selected_thickness.name = text
            self.sheet_settings.save_data()
            self.sync_changes()
            self.load_tabs()

    def popout(self):
        self.pushButton_popout.setIcon(QIcon("icons/dock_window.png"))
        self.pushButton_popout.clicked.disconnect()
        self.popout_widget = PopoutWidget(self.layout(), self.parent)
        self.popout_widget.show()
        self.pushButton_popout.clicked.connect(self.popout_widget.close)

    def open_group_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def sync_changes(self):
        self.parent.sync_changes("sheet_settings_tab")

    def clear_layout(self, layout: QVBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
