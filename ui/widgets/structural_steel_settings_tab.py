import contextlib
import os
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QInputDialog,
    QMenu,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.custom_widgets import CustomTableWidget, CustomTabWidget
from ui.icons import Icons
from ui.widgets.structural_steel_settings_tab_UI import Ui_Form
from utils.settings import Settings
from utils.structural_steel_settings.material_densities import Density
from utils.structural_steel_settings.material_price_per_pounds import Price
from utils.structural_steel_settings.structural_steel_settings import StructuralSteelSettings

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


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


class PoundsPerCubicFootTableWidget(CustomTableWidget):
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
        headers: list[str] = ["Material", "Pounds Per Cubic Foot", "Modified Date"]
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
        self.original_layout_parent: "StructuralSteelSettingsTab" = (
            self.original_layout.parentWidget()
        )
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("Sheet Settings")
        self.setLayout(self.original_layout)
        self.setObjectName("popout_widget")

    def closeEvent(self, event):
        if self.original_layout_parent:
            self.original_layout_parent.setLayout(self.original_layout)
            self.original_layout_parent.pushButton_popout.setIcon(Icons.dock_icon)
            self.original_layout_parent.pushButton_popout.clicked.disconnect()
            self.original_layout_parent.pushButton_popout.clicked.connect(
                self.original_layout_parent.popout
            )
        super().closeEvent(event)


class StructuralSteelSettingsTab(QWidget, Ui_Form):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.parent: MainWindow = parent
        self.structural_steel_settings: StructuralSteelSettings = self.parent.structural_steel_settings

        self.settings_file = Settings()

        self.price_per_pound_table: PricePerPoundTableWidget = None
        self.price_per_pound_table_items: dict[Price, QTableWidgetItem] = {}

        self.pounds_per_cubic_foot_table: PoundsPerCubicFootTableWidget = None
        self.pounds_per_cubic_foot_table_items: dict[Density, QTableWidgetItem] = {}

        self.last_selected_index: int = 0
        self.load_ui()

    def load_ui(self):
        self.settings_file.load_data()
        self.tables_font = QFont()
        self.tables_font.setFamily(
            self.settings_file.get_value("tables_font")["family"]
        )
        self.tables_font.setPointSize(
            self.settings_file.get_value("tables_font")["pointSize"]
        )
        self.tables_font.setWeight(
            self.settings_file.get_value("tables_font")["weight"]
        )
        self.tables_font.setItalic(
            self.settings_file.get_value("tables_font")["italic"]
        )

        self.pushButton_add_material.clicked.connect(self.add_material)
        self.pushButton_remove_material.clicked.connect(self.remove_material)
        self.materials_list.itemSelectionChanged.connect(self.material_list_clicked)
        self.materials_list.doubleClicked.connect(self.rename_material)

        self.load_tabs()

    def load_tabs(self):
        self.materials_list.blockSignals(True)
        self.materials_list.clear()
        self.materials_list.addItems(self.structural_steel_settings.get_materials())
        self.materials_list.blockSignals(False)

        self.price_per_pound_table = PricePerPoundTableWidget(self)
        self.clear_layout(self.price_per_pound_layout)
        self.price_per_pound_layout.addWidget(self.price_per_pound_table)
        self.load_price_per_pound_table()
        self.price_per_pound_table.cellChanged.connect(
            self.price_per_pound_table_changed
        )

        self.pounds_per_cubic_foot_table = PoundsPerCubicFootTableWidget(self)
        self.clear_layout(self.pounds_per_cubic_foot_layout)
        self.pounds_per_cubic_foot_layout.addWidget(self.pounds_per_cubic_foot_table)
        self.load_pounds_per_cubic_foot_table()
        self.pounds_per_cubic_foot_table.cellChanged.connect(
            self.pounds_per_cubic_foot_table_changed
        )

    def load_price_per_pound_table(self):
        self.price_per_pound_table_items.clear()
        self.price_per_pound_table.clearContents()
        self.price_per_pound_table.setRowCount(0)
        self.price_per_pound_table.blockSignals(True)
        for row, (material, price_per_pound) in enumerate(
            self.structural_steel_settings.material_price_per_pounds
        ):
            self.price_per_pound_table.insertRow(row)
            table_item_material = QTableWidgetItem(material.name)
            table_item_material.setFont(self.tables_font)
            self.price_per_pound_table.setItem(row, 0, table_item_material)

            table_item_price = QTableWidgetItem(
                f"${price_per_pound.price_per_pound:,.2f}"
            )
            table_item_price.setFont(self.tables_font)
            self.price_per_pound_table.setItem(row, 1, table_item_price)
            self.price_per_pound_table_items[price_per_pound] = table_item_price

            table_item_latest_change = QTableWidgetItem(price_per_pound.latest_change)
            table_item_latest_change.setFont(self.tables_font)
            self.price_per_pound_table.setItem(row, 2, table_item_latest_change)
        self.price_per_pound_table.blockSignals(False)

    def load_pounds_per_cubic_foot_table(self):
        self.pounds_per_cubic_foot_table_items.clear()
        self.pounds_per_cubic_foot_table.clearContents()
        self.pounds_per_cubic_foot_table.setRowCount(0)
        self.pounds_per_cubic_foot_table.blockSignals(True)
        for row, (material, pounds_per_cubic_foot) in enumerate(
            self.structural_steel_settings.material_densities
        ):
            self.pounds_per_cubic_foot_table.insertRow(row)
            table_item_material = QTableWidgetItem(material.name)
            table_item_material.setFont(self.tables_font)
            self.pounds_per_cubic_foot_table.setItem(row, 0, table_item_material)

            table_item_pounds_per_cubic_foot = QTableWidgetItem(
                f"{pounds_per_cubic_foot.density:,.3f}"
            )
            table_item_pounds_per_cubic_foot.setFont(self.tables_font)
            self.pounds_per_cubic_foot_table.setItem(
                row, 1, table_item_pounds_per_cubic_foot
            )
            self.pounds_per_cubic_foot_table_items[pounds_per_cubic_foot] = table_item_pounds_per_cubic_foot

            table_item_latest_change = QTableWidgetItem(pounds_per_cubic_foot.latest_change)
            table_item_latest_change.setFont(self.tables_font)
            self.pounds_per_cubic_foot_table.setItem(
                row, 2, table_item_latest_change
            )
        self.pounds_per_cubic_foot_table.blockSignals(False)

    def price_per_pound_table_changed(self):
        for price, table_item_price in self.price_per_pound_table_items.items():
            new_price = float(
                table_item_price.text().strip().replace("$", "").replace(",", "")
            )
            old_price = price.price_per_pound
            if new_price != old_price:
                modified_date: str = f'{os.getlogin().title()} - Modified from ${old_price:,.2f} to ${new_price:,.2f} at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
                price.price_per_pound = new_price
                price.latest_change = modified_date
        self.structural_steel_settings.save_data()
        self.sync_changes()
        self.load_price_per_pound_table()

    def pounds_per_cubic_foot_table_changed(self):
        for pounds_per_cubic_foot, table_item_pound in self.pounds_per_cubic_foot_table_items.items():
            new_value = float(
                table_item_pound.text().strip().replace(",", "")
            )
            old_value = pounds_per_cubic_foot.density
            if new_value != old_value:
                modified_date: str = f'{os.getlogin().title()} - Modified from {old_value:,.3f} to {new_value:,.3f} at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
                pounds_per_cubic_foot.density = new_value
                pounds_per_cubic_foot.latest_change = modified_date
        self.structural_steel_settings.save_data()
        self.sync_changes()
        self.load_pounds_per_cubic_foot_table()

    def material_list_clicked(self):
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Price Per Pound":
            for row in range(self.price_per_pound_table.rowCount()):
                if (
                    self.price_per_pound_table.item(row, 0).text()
                    == self.materials_list.selectedItems()[0].text()
                ):
                    self.price_per_pound_table.selectRow(row)
                    return
        elif (
            self.tabWidget.tabText(self.tabWidget.currentIndex())
            == "Pounds Per Cubic Foot"
        ):
            for row in range(self.pounds_per_cubic_foot_table.rowCount()):
                if (
                    self.pounds_per_cubic_foot_table.item(row, 0).text()
                    == self.materials_list.selectedItems()[0].text()
                ):
                    self.pounds_per_cubic_foot_table.selectRow(row)
                    return

    def add_material(self):
        new_material_name, ok = QInputDialog.getText(
            self, "Add material", "Enter a material name:"
        )
        if new_material_name and ok:
            self.structural_steel_settings.add_material(new_material_name)
            self.structural_steel_settings.save_data()
            self.sync_changes()
            self.load_tabs()

    def remove_material(self):
        try:
            selected_row = self.structural_steel_settings.get_materials().index(
                self.materials_list.selectedItems()[0].text()
            )
        except IndexError:
            selected_row = 0
        material_to_remove, ok = QInputDialog.getItem(
            self,
            "Remove material",
            "Select a material to remove",
            self.structural_steel_settings.get_materials(),
            selected_row,
            False,
        )
        if material_to_remove and ok:
            self.structural_steel_settings.remove_material(material_to_remove)
            self.structural_steel_settings.save_data()
            self.sync_changes()
            self.load_tabs()

    def rename_material(self):
        selected_material = self.structural_steel_settings.materials.get(
            self.materials_list.selectedItems()[0].text()
        )
        text, ok = QInputDialog.getText(
            self, "Rename material", "Enter a new name:", text=selected_material.name
        )
        if text and ok:
            selected_material.name = text
            self.structural_steel_settings.save_data()
            self.sync_changes()
            self.load_tabs()

    def popout(self):
        self.popout_widget = PopoutWidget(self.layout(), self.parent)
        self.popout_widget.show()
        self.pushButton_popout.setIcon(Icons.redock_icon)
        self.pushButton_popout.clicked.disconnect()
        self.pushButton_popout.clicked.connect(self.popout_widget.close)

    def open_group_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def sync_changes(self):
        self.parent.sync_changes("structural_steel_settings_tab")

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
