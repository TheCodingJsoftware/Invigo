import contextlib
import math
import os
from datetime import datetime
from enum import Enum, auto
from functools import partial

from natsort import natsorted
from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QCursor, QFont, QPixmap
from PyQt6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QMenu, QMessageBox, QPushButton, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from ui.custom.components_quoting_table_widget import ComponentsQuotingTableWidget, ComponentsTableColumns
from ui.custom_widgets import ClickableLabel, CustomTableWidget, MachineCutTimeSpinBox, MultiToolBox, RecutButton
from ui.dialogs.add_component_dialog import AddComponentDialog
from ui.dialogs.add_laser_cut_part_dialog import AddLaserCutPartDialog
from ui.dialogs.add_sheet_dialog import AddSheetDialog
from ui.windows.image_viewer import QImageViewer
from utils.calulations import calculate_overhead
from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest
from utils.inventory.sheet import Sheet
from utils.inventory.sheets_inventory import SheetsInventory
from utils.quote.quote import Quote
from utils.settings import Settings
from utils.sheet_settings.sheet_settings import SheetSettings


class PaintSettingsWidget(QWidget):
    settingsChanged = pyqtSignal()

    def __init__(self, laser_cut_part: LaserCutPart, parent: "LaserCutPartsQuotingTableWidget") -> None:
        super().__init__(parent)
        self.parent: LaserCutPartsQuotingTableWidget = parent
        self.laser_cut_part = laser_cut_part
        self.paint_inventory = self.laser_cut_part.paint_inventory

        self.paint_settings_layout = QHBoxLayout(self)

        self.paint_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.paint_settings_layout.setSpacing(0)
        self.not_painted_label = QLabel("Not painted", self)
        self.paint_settings_layout.addWidget(self.not_painted_label)

        self.widget_primer = QWidget(self)
        self.widget_primer.setObjectName("widget_primer")
        self.widget_primer.setStyleSheet("QWidget#widget_primer{border: 1px solid rgba(120, 120, 120, 70);}")
        self.primer_layout = QGridLayout(self.widget_primer)
        self.primer_layout.setContentsMargins(3, 3, 3, 3)
        self.primer_layout.setSpacing(0)
        self.combobox_primer = QComboBox(self.widget_primer)
        self.combobox_primer.wheelEvent = lambda event: None
        self.combobox_primer.addItems(["None"] + self.paint_inventory.get_all_primers())
        if self.laser_cut_part.primer_name:
            self.combobox_primer.setCurrentText(self.laser_cut_part.primer_name)
        self.combobox_primer.currentTextChanged.connect(self.update_paint_settings)
        self.spinbox_primer_overspray = QDoubleSpinBox(self.widget_primer)
        self.spinbox_primer_overspray.wheelEvent = lambda event: None
        self.spinbox_primer_overspray.setValue(self.laser_cut_part.primer_overspray)
        self.spinbox_primer_overspray.setMaximum(100.0)
        self.spinbox_primer_overspray.setSuffix("%")
        self.spinbox_primer_overspray.editingFinished.connect(self.update_paint_settings)
        self.primer_layout.addWidget(QLabel("Primer:", self.widget_primer), 0, 0)
        self.primer_layout.addWidget(self.combobox_primer, 1, 0)
        self.primer_layout.addWidget(QLabel("Overspray:", self.widget_primer), 0, 1)
        self.primer_layout.addWidget(self.spinbox_primer_overspray, 1, 1)
        self.widget_primer.setVisible(self.laser_cut_part.uses_primer)
        self.paint_settings_layout.addWidget(self.widget_primer)

        # PAINT COLOR
        self.widget_paint_color = QWidget(self)
        self.widget_paint_color.setObjectName("widget_paint_color")
        self.widget_paint_color.setStyleSheet("QWidget#widget_paint_color{border: 1px solid rgba(120, 120, 120, 70);}")
        self.paint_color_layout = QGridLayout(self.widget_paint_color)
        self.paint_color_layout.setContentsMargins(3, 3, 3, 3)
        self.paint_color_layout.setSpacing(0)
        self.combobox_paint_color = QComboBox(self.widget_paint_color)
        self.combobox_paint_color.wheelEvent = lambda event: None
        self.combobox_paint_color.addItems(["None"] + self.paint_inventory.get_all_paints())
        if self.laser_cut_part.paint_name:
            self.combobox_paint_color.setCurrentText(self.laser_cut_part.paint_name)
        self.combobox_paint_color.currentTextChanged.connect(self.update_paint_settings)
        self.spinbox_paint_overspray = QDoubleSpinBox(self.widget_paint_color)
        self.spinbox_paint_overspray.wheelEvent = lambda event: None
        self.spinbox_paint_overspray.setValue(self.laser_cut_part.paint_overspray)
        self.spinbox_paint_overspray.setMaximum(100.0)
        self.spinbox_paint_overspray.setSuffix("%")
        self.spinbox_paint_overspray.editingFinished.connect(self.update_paint_settings)
        self.paint_color_layout.addWidget(QLabel("Paint:", self.widget_paint_color), 0, 0)
        self.paint_color_layout.addWidget(self.combobox_paint_color, 1, 0)
        self.paint_color_layout.addWidget(QLabel("Overspray:", self.widget_paint_color), 0, 1)
        self.paint_color_layout.addWidget(self.spinbox_paint_overspray, 1, 1)
        self.widget_paint_color.setVisible(self.laser_cut_part.uses_paint)
        self.paint_settings_layout.addWidget(self.widget_paint_color)

        # POWDER COATING COLOR
        self.widget_powder_coating = QWidget(self)
        self.widget_powder_coating.setObjectName("widget_powder_coating")
        self.widget_powder_coating.setStyleSheet("QWidget#widget_powder_coating{border: 1px solid rgba(120, 120, 120, 70);}")
        self.powder_coating_layout = QGridLayout(self.widget_powder_coating)
        self.powder_coating_layout.setContentsMargins(3, 3, 3, 3)
        self.powder_coating_layout.setSpacing(0)
        self.combobox_powder_coating_color = QComboBox(self.widget_powder_coating)
        self.combobox_powder_coating_color.wheelEvent = lambda event: None
        self.combobox_powder_coating_color.addItems(["None"] + self.paint_inventory.get_all_powders())
        if self.laser_cut_part.powder_name:
            self.combobox_powder_coating_color.setCurrentText(self.laser_cut_part.powder_name)
        self.combobox_powder_coating_color.currentTextChanged.connect(self.update_paint_settings)
        self.spinbox_powder_transfer_efficiency = QDoubleSpinBox(self.widget_powder_coating)
        self.spinbox_powder_transfer_efficiency.wheelEvent = lambda event: None
        self.spinbox_powder_transfer_efficiency.setValue(self.laser_cut_part.powder_transfer_efficiency)
        self.spinbox_powder_transfer_efficiency.setMaximum(100.0)
        self.spinbox_powder_transfer_efficiency.setSuffix("%")
        self.spinbox_powder_transfer_efficiency.editingFinished.connect(self.update_paint_settings)
        self.powder_coating_layout.addWidget(QLabel("Powder:", self.widget_powder_coating), 0, 0)
        self.powder_coating_layout.addWidget(self.combobox_powder_coating_color, 1, 0)
        self.powder_coating_layout.addWidget(QLabel("Transfer eff:", self.widget_powder_coating), 0, 1)
        self.powder_coating_layout.addWidget(self.spinbox_powder_transfer_efficiency, 1, 1)
        self.widget_powder_coating.setVisible(self.laser_cut_part.uses_powder)
        self.paint_settings_layout.addWidget(self.widget_powder_coating)

        self.setLayout(self.paint_settings_layout)

    def update_paint_settings(self):
        self.laser_cut_part.primer_overspray = self.spinbox_primer_overspray.value()
        self.laser_cut_part.paint_overspray = self.spinbox_paint_overspray.value()
        self.laser_cut_part.powder_transfer_efficiency = self.spinbox_powder_transfer_efficiency.value()
        self.laser_cut_part.paint_name = self.combobox_paint_color.currentText()
        self.laser_cut_part.primer_name = self.combobox_primer.currentText()
        self.laser_cut_part.powder_name = self.combobox_powder_coating_color.currentText()

        self.parent.resizeColumnsToContents()

        self.settingsChanged.emit()


class PaintWidget(QWidget):
    settingsChanged = pyqtSignal()

    def __init__(
        self,
        laser_cut_part: LaserCutPart,
        paint_settings_widget: PaintSettingsWidget,
        parent: "LaserCutPartsQuotingTableWidget",
    ) -> None:
        super().__init__(parent)
        self.parent: LaserCutPartsQuotingTableWidget = parent

        self.laser_cut_part = laser_cut_part
        self.paint_settings_widget = paint_settings_widget

        layout = QVBoxLayout(self)

        self.checkbox_primer = QCheckBox("Primer", self)
        self.checkbox_primer.setChecked(self.laser_cut_part.uses_primer)
        self.checkbox_primer.checkStateChanged.connect(self.update_paint)
        self.checkbox_paint = QCheckBox("Paint", self)
        self.checkbox_paint.setChecked(self.laser_cut_part.uses_paint)
        self.checkbox_paint.checkStateChanged.connect(self.update_paint)
        self.checkbox_powder = QCheckBox("Powder", self)
        self.checkbox_powder.setChecked(self.laser_cut_part.uses_powder)
        self.checkbox_powder.checkStateChanged.connect(self.update_paint)

        layout.addWidget(self.checkbox_primer)
        layout.addWidget(self.checkbox_paint)
        layout.addWidget(self.checkbox_powder)

        self.setLayout(layout)

        self.paint_settings_widget.widget_primer.setVisible(self.laser_cut_part.uses_primer)
        self.paint_settings_widget.widget_paint_color.setVisible(self.laser_cut_part.uses_paint)
        self.paint_settings_widget.widget_powder_coating.setVisible(self.laser_cut_part.uses_powder)
        self.paint_settings_widget.not_painted_label.setVisible(not (self.laser_cut_part.uses_primer or self.laser_cut_part.uses_paint or self.laser_cut_part.uses_powder))

        self.parent.resizeColumnsToContents()

    def update_paint(self):
        self.laser_cut_part.uses_primer = self.checkbox_primer.isChecked()
        self.laser_cut_part.uses_paint = self.checkbox_paint.isChecked()
        self.laser_cut_part.uses_powder = self.checkbox_powder.isChecked()

        self.paint_settings_widget.widget_primer.setVisible(self.laser_cut_part.uses_primer)
        self.paint_settings_widget.widget_paint_color.setVisible(self.laser_cut_part.uses_paint)
        self.paint_settings_widget.widget_powder_coating.setVisible(self.laser_cut_part.uses_powder)
        self.paint_settings_widget.not_painted_label.setVisible(not (self.laser_cut_part.uses_primer or self.laser_cut_part.uses_paint or self.laser_cut_part.uses_powder))

        self.parent.resizeColumnsToContents()

        self.settingsChanged.emit()


class AutoNumber(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count


class LaserCutTableColumns(AutoNumber):
    PICTURE = auto()
    PART_NAME = auto()
    FILES = auto()
    MATERIAL = auto()
    THICKNESS = auto()
    UNIT_QUANTITY = auto()
    QUANTITY = auto()
    PART_DIM = auto()
    SHELF_NUMBER = auto()
    PAINTING = auto()
    PAINT_SETTINGS = auto()
    PAINT_COST = auto()
    BEND_COST = auto()
    LABOR_COST = auto()
    COST_OF_GOODS = auto()
    UNIT_PRICE = auto()
    PRICE = auto()
    RECUT = auto()
    ADD_TO_INVENTORY = auto()


class LaserCutPartsQuotingTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_height = 70

        editable_columns = [
            LaserCutTableColumns.UNIT_QUANTITY,
            LaserCutTableColumns.BEND_COST,
            LaserCutTableColumns.LABOR_COST,
            LaserCutTableColumns.SHELF_NUMBER,
        ]

        self.set_editable_column_index([col.value for col in editable_columns])
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        headers = {
            "Picture": LaserCutTableColumns.PICTURE.value,
            "Part name": LaserCutTableColumns.PART_NAME.value,
            "Files": LaserCutTableColumns.FILES.value,
            "Material": LaserCutTableColumns.MATERIAL.value,
            "Thickness": LaserCutTableColumns.THICKNESS.value,
            "Unit Qty": LaserCutTableColumns.UNIT_QUANTITY.value,
            "Qty": LaserCutTableColumns.QUANTITY.value,
            "Part Dim": LaserCutTableColumns.PART_DIM.value,
            "Shelf #": LaserCutTableColumns.SHELF_NUMBER.value,
            "Painting": LaserCutTableColumns.PAINTING.value,
            "Paint Settings": LaserCutTableColumns.PAINT_SETTINGS.value,
            "Paint Cost": LaserCutTableColumns.PAINT_COST.value,
            "Cost of\nGoods": LaserCutTableColumns.COST_OF_GOODS.value,
            "Bend Cost": LaserCutTableColumns.BEND_COST.value,
            "Labor Cost": LaserCutTableColumns.LABOR_COST.value,
            "Unit Price": LaserCutTableColumns.UNIT_PRICE.value,
            "Price": LaserCutTableColumns.PRICE.value,
            "Recut": LaserCutTableColumns.RECUT.value,
            "Add Part to Inventory": LaserCutTableColumns.ADD_TO_INVENTORY.value,
        }
        self.setColumnCount(len(headers))
        for header, column in headers.items():
            self.setHorizontalHeaderItem(column, QTableWidgetItem(header))

        self.setStyleSheet("border-color: transparent;")


class QuoteWidget(QWidget):
    quote_unsaved_changes = pyqtSignal(Quote)

    def __init__(
        self,
        quote: Quote,
        components_inventory: ComponentsInventory,
        laser_cut_inventory: LaserCutInventory,
        sheets_inventory: SheetsInventory,
        sheet_settings: SheetSettings,
        parent: QWidget,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/widgets/quote_widget.ui", self)

        self.parent = parent
        self.quote = quote
        self.components_inventory = components_inventory
        self.laser_cut_inventory = laser_cut_inventory
        self.paint_inventory = self.laser_cut_inventory.paint_inventory
        self.sheets_inventory = sheets_inventory
        self.sheet_settings = sheet_settings

        self.settings_file = Settings()
        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        self.load_ui()

        self.nests_tool_box: MultiToolBox = None
        self.nest_items: dict[Nest, dict[str, QComboBox | QDoubleSpinBox | QLabel | MachineCutTimeSpinBox]] = {}
        self.laser_cut_table_widget: LaserCutPartsQuotingTableWidget = None
        self.laser_cut_table_items: dict[
            LaserCutPart,
            dict[
                str,
                QTableWidgetItem | QCheckBox | QDoubleSpinBox | QComboBox | QWidget | PaintSettingsWidget | PaintWidget,
            ],
        ] = {}
        self.components_table_widget: ComponentsQuotingTableWidget = None
        self.components_table_items: dict[Component, dict[str, QTableWidgetItem]] = {}

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        self.splitter_2.setSizes([1, 0, 1])
        self.splitter_2.setStretchFactor(0, 0)
        self.splitter_2.setStretchFactor(1, 0)
        self.splitter_2.setStretchFactor(2, 1)

        self.splitter_3.setSizes([1, 0])
        self.splitter_3.setStretchFactor(0, 0)
        self.splitter_3.setStretchFactor(1, 1)

        self.load_quote()

    def load_ui(self):
        # * Nest, Sheet, and Item Quoting Settings
        self.comboBox_laser_cutting_2: QComboBox = self.findChild(QComboBox, "comboBox_laser_cutting_2")
        self.comboBox_laser_cutting_2.setCurrentText(self.quote.laser_cutting_method)
        self.comboBox_laser_cutting_2.currentTextChanged.connect(
            lambda: (
                self.global_quote_settings_changed(),
                self.update_sheet_price(),
                self.update_laser_cut_parts_price(),
            )
        )
        self.doubleSpinBox_cost_for_laser_2: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_cost_for_laser_2")
        self.doubleSpinBox_cost_for_laser_2.setValue(self.quote.laser_cutting_cost)
        self.doubleSpinBox_cost_for_laser_2.valueChanged.connect(
            lambda: (
                self.global_quote_settings_changed(),
                self.update_sheet_price(),
                self.update_laser_cut_parts_price(),
            )
        )
        self.comboBox_global_sheet_material_2: QComboBox = self.findChild(QComboBox, "comboBox_global_sheet_material_2")
        self.comboBox_global_sheet_material_2.addItems(self.sheet_settings.get_materials())
        self.comboBox_global_sheet_material_2.currentTextChanged.connect(lambda: (self.update_sheet_price(), self.global_sheet_materials_changed()))
        self.comboBox_global_sheet_thickness_2: QComboBox = self.findChild(QComboBox, "comboBox_global_sheet_thickness_2")
        self.comboBox_global_sheet_thickness_2.addItems(self.sheet_settings.get_thicknesses())
        self.comboBox_global_sheet_thickness_2.currentTextChanged.connect(lambda: (self.update_sheet_price(), self.global_sheet_thickness_changed()))

        self.doubleSpinBox_overhead_items_2: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_overhead_items_2")
        self.doubleSpinBox_overhead_items_2.setValue(self.quote.item_overhead)
        self.doubleSpinBox_overhead_items_2.valueChanged.connect(
            lambda: (
                self.global_quote_settings_changed(),
                self.update_components_price(),
                self.update_laser_cut_parts_price(),
            )
        )
        self.doubleSpinBox_profit_margin_items_2: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_profit_margin_items_2")
        self.doubleSpinBox_profit_margin_items_2.setValue(self.quote.item_profit_margin)
        self.doubleSpinBox_profit_margin_items_2.valueChanged.connect(
            lambda: (
                self.global_quote_settings_changed(),
                self.update_components_price(),
                self.update_laser_cut_parts_price(),
            )
        )

        self.doubleSpinBox_overhead_sheets_2: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_overhead_sheets_2")
        self.doubleSpinBox_overhead_sheets_2.setValue(self.quote.sheet_overhead)
        self.doubleSpinBox_overhead_sheets_2.valueChanged.connect(lambda: (self.global_quote_settings_changed(), self.update_sheet_price()))
        self.doubleSpinBox_profit_margin_sheets_2: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_profit_margin_sheets_2")
        self.doubleSpinBox_profit_margin_sheets_2.setValue(self.quote.sheet_profit_margin)
        self.doubleSpinBox_profit_margin_sheets_2.valueChanged.connect(lambda: (self.global_quote_settings_changed(), self.update_sheet_price()))

        self.pushButton_item_to_sheet: QPushButton = self.findChild(QPushButton, "pushButton_item_to_sheet")
        self.pushButton_item_to_sheet.setChecked(self.quote.match_item_to_sheet_cost)
        self.pushButton_item_to_sheet.clicked.connect(
            lambda: (
                self.global_quote_settings_changed(),
                self.update_laser_cut_parts_price(),
            )
        )
        self.pushButton_match_sheet_to_item_2: QPushButton = self.findChild(QPushButton, "pushButton_match_sheet_to_item_2")
        self.pushButton_match_sheet_to_item_2.setChecked(self.quote.match_sheet_cost_to_item)
        self.pushButton_match_sheet_to_item_2.clicked.connect(
            lambda: (
                self.global_quote_settings_changed(),
                self.update_laser_cut_parts_price(),
            )
        )

        self.pushButton_add_laser_cut_part_2 = self.findChild(QPushButton, "pushButton_add_laser_cut_part_2")
        self.pushButton_add_laser_cut_part_2.clicked.connect(self.add_laser_cut_part)

        self.pushButton_add_component_2: QPushButton = self.findChild(QPushButton, "pushButton_add_component_2")
        self.pushButton_add_component_2.clicked.connect(self.add_component)

        self.pushButton_clear_all_components_2: QPushButton = self.findChild(QPushButton, "pushButton_clear_all_components_2")
        self.pushButton_clear_all_components_2.clicked.connect(self.clear_all_components)

        self.pushButton_clear_all_nests: QPushButton = self.findChild(QPushButton, "pushButton_clear_all_nests")
        self.pushButton_clear_all_nests.clicked.connect(self.clear_all_nests)

        self.doubleSpinBox_global_sheet_length_2: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_global_sheet_length_2")
        self.doubleSpinBox_global_sheet_length_2.valueChanged.connect(self.global_sheet_dimension_changed)
        self.doubleSpinBox_global_sheet_width_2: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_global_sheet_width_2")
        self.doubleSpinBox_global_sheet_width_2.valueChanged.connect(self.global_sheet_dimension_changed)

        self.checkBox_components_use_overhead_2: QCheckBox = self.findChild(QCheckBox, "checkBox_components_use_overhead_2")
        self.checkBox_components_use_overhead_2.setChecked(self.quote.component_use_overhead)
        self.checkBox_components_use_overhead_2.checkStateChanged.connect(
            lambda: (
                self.global_quote_settings_changed(),
                self.update_components_price(),
            )
        )
        self.checkBox_components_use_profit_margin_2: QCheckBox = self.findChild(QCheckBox, "checkBox_components_use_profit_margin_2")
        self.checkBox_components_use_profit_margin_2.setChecked(self.quote.component_use_profit_margin)
        self.checkBox_components_use_profit_margin_2.checkStateChanged.connect(
            lambda: (
                self.global_quote_settings_changed(),
                self.update_components_price(),
            )
        )

        # * Paint Settings
        self.pushButton_toggle_primer: QPushButton = self.findChild(QPushButton, "pushButton_toggle_primer")
        self.pushButton_toggle_primer.clicked.connect(self.global_toggle_primer_clicked)
        self.comboBox_primer_color: QComboBox = self.findChild(QComboBox, "comboBox_primer_color")
        self.comboBox_primer_color.addItems(["None"] + self.paint_inventory.get_all_primers())
        self.comboBox_primer_color.currentTextChanged.connect(self.global_primer_color_changed)
        self.doubleSpinBox_primer_overspray: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_primer_overspray")
        self.doubleSpinBox_primer_overspray.setValue(self.quote.primer_overspray)
        self.doubleSpinBox_primer_overspray.valueChanged.connect(self.global_primer_overspray_changed)

        self.pushButton_toggle_paint: QPushButton = self.findChild(QPushButton, "pushButton_toggle_paint")
        self.pushButton_toggle_paint.clicked.connect(self.global_toggle_paint_clicked)
        self.comboBox_paint_color: QComboBox = self.findChild(QComboBox, "comboBox_paint_color")
        self.comboBox_paint_color.addItems(["None"] + self.paint_inventory.get_all_paints())
        self.comboBox_paint_color.currentTextChanged.connect(self.global_paint_color_changed)
        self.doubleSpinBox_paint_overspray: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_paint_overspray")
        self.doubleSpinBox_paint_overspray.setValue(self.quote.paint_overspray)
        self.doubleSpinBox_paint_overspray.valueChanged.connect(self.global_paint_overspray_changed)

        self.pushButton_toggle_powder_coating: QPushButton = self.findChild(QPushButton, "pushButton_toggle_powder_coating")
        self.pushButton_toggle_powder_coating.clicked.connect(self.global_toggle_powder_clicked)
        self.comboBox_powder_color: QComboBox = self.findChild(QComboBox, "comboBox_powder_color")
        self.comboBox_powder_color.addItems(["None"] + self.paint_inventory.get_all_powders())
        self.comboBox_powder_color.currentTextChanged.connect(self.global_powder_color_changed)
        self.doubleSpinBox_transfer_efficiency: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_transfer_efficiency")
        self.doubleSpinBox_transfer_efficiency.setValue(self.quote.transfer_efficiency)
        self.doubleSpinBox_transfer_efficiency.valueChanged.connect(self.global_powder_transfer_efficiency_changed)
        self.doubleSpinBox_mil_thickness: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_mil_thickness")
        self.doubleSpinBox_mil_thickness.setValue(self.quote.mil_thickness)
        self.doubleSpinBox_mil_thickness.valueChanged.connect(
            lambda: (
                self.global_quote_settings_changed(),
                self.update_laser_cut_parts_price(),
            )
        )

        # * Quote Settings
        self.doubleSpinBox_order_number: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_order_number")
        self.doubleSpinBox_order_number.setValue(self.quote.order_number)
        self.doubleSpinBox_order_number.wheelEvent = lambda event: None
        self.doubleSpinBox_order_number.valueChanged.connect(self.global_quote_settings_changed)
        self.pushButton_get_order_number: QPushButton = self.findChild(QPushButton, "pushButton_get_order_number")

        def get_latest_order_number():
            self.doubleSpinBox_order_number.setValue(self.parent.parent.order_number)
            self.global_quote_settings_changed()

        self.pushButton_get_order_number.clicked.connect(get_latest_order_number)
        self.comboBox_quote_status: QComboBox = self.findChild(QComboBox, "comboBox_quote_status")
        self.comboBox_quote_status.setCurrentText(self.quote.status)
        self.comboBox_quote_status.currentTextChanged.connect(self.global_quote_settings_changed)
        self.comboBox_quote_status.wheelEvent = lambda event: None
        self.dateEdit_shipped: QDateEdit = self.findChild(QDateEdit, "dateEdit_shipped")
        try:
            year, month, day = map(int, self.quote.date_shipped.split("-"))
            self.dateEdit_shipped.setDate(QDate(year, month, day))
        except ValueError:
            self.dateEdit_shipped.setDate(QDate.currentDate())
        self.dateEdit_shipped.dateChanged.connect(self.global_quote_settings_changed)
        self.dateEdit_shipped.wheelEvent = lambda event: None
        self.dateEdit_expected: QDateEdit = self.findChild(QDateEdit, "dateEdit_expected")
        try:
            year, month, day = map(int, self.quote.date_expected.split("-"))
            self.dateEdit_expected.setDate(QDate(year, month, day))
        except ValueError:
            self.dateEdit_expected.setDate(QDate.currentDate())
        self.dateEdit_expected.dateChanged.connect(self.global_quote_settings_changed)
        self.dateEdit_expected.wheelEvent = lambda event: None
        self.textEdit_ship_to: QTextEdit = self.findChild(QTextEdit, "textEdit_ship_to")
        self.textEdit_ship_to.setText(self.quote.ship_to)
        self.textEdit_ship_to.textChanged.connect(self.global_quote_settings_changed)

        # * Layouts
        self.laser_cut_layout: QVBoxLayout = self.findChild(QVBoxLayout, "verticalLayout_55")
        self.components_layout: QVBoxLayout = self.findChild(QVBoxLayout, "verticalLayout_49")
        self.nests_layout: QVBoxLayout = self.findChild(QVBoxLayout, "verticalLayout_sheets_2")
        self.gridLayout_nest_summary_2: QGridLayout = self.findChild(QGridLayout, "gridLayout_nest_summary_2")

        self.label_total_sheet_cost_2: QLabel = self.findChild(QLabel, "label_total_sheet_cost_2")
        self.label_total_item_cost_2: QLabel = self.findChild(QLabel, "label_total_item_cost_2")

    def quote_changed(self):
        self.quote.changes_made()
        self.quote_unsaved_changes.emit(self.quote)

    def load_quote(self):
        self.load_nests()
        self.load_nest_summary()
        self.load_laser_cut_parts()
        self.load_component_parts()

    def global_quote_settings_changed(self):
        self.quote.laser_cutting_method = self.comboBox_laser_cutting_2.currentText()
        self.doubleSpinBox_cost_for_laser_2.setValue(self.sheet_settings.get_laser_cost(self.quote.laser_cutting_method))
        self.quote.laser_cutting_cost = self.doubleSpinBox_cost_for_laser_2.value()

        self.quote.item_overhead = self.doubleSpinBox_overhead_items_2.value()
        self.quote.item_profit_margin = self.doubleSpinBox_profit_margin_items_2.value()

        self.quote.sheet_overhead = self.doubleSpinBox_overhead_sheets_2.value()
        self.quote.sheet_profit_margin = self.doubleSpinBox_profit_margin_sheets_2.value()

        self.quote.match_sheet_cost_to_item = self.pushButton_match_sheet_to_item_2.isChecked()
        self.quote.match_item_to_sheet_cost = self.pushButton_item_to_sheet.isChecked()

        self.quote.component_use_overhead = self.checkBox_components_use_overhead_2.isChecked()
        self.quote.component_use_profit_margin = self.checkBox_components_use_profit_margin_2.isChecked()

        self.quote.primer_overspray = self.doubleSpinBox_primer_overspray.value()
        self.quote.paint_overspray = self.doubleSpinBox_paint_overspray.value()
        self.quote.transfer_efficiency = self.doubleSpinBox_transfer_efficiency.value()
        self.quote.mil_thickness = self.doubleSpinBox_mil_thickness.value()

        self.quote.order_number = self.doubleSpinBox_order_number.value()
        self.quote.status = self.comboBox_quote_status.currentText()
        self.quote.date_shipped = self.dateEdit_shipped.date().toString("yyyy-MM-dd")
        self.quote.date_expected = self.dateEdit_expected.date().toString("yyyy-MM-dd")
        self.quote.ship_to = self.textEdit_ship_to.toPlainText()

        self.quote_changed()

    def global_sheet_materials_changed(self):
        for _, table_data in self.nest_items.items():
            table_data["material"].setCurrentText(self.comboBox_global_sheet_material_2.currentText())
        self.load_nest_summary()
        self.quote_changed()

    def global_sheet_thickness_changed(self):
        for _, table_data in self.nest_items.items():
            table_data["thickness"].setCurrentText(self.comboBox_global_sheet_thickness_2.currentText())
        self.load_nest_summary()
        self.quote_changed()

    def global_sheet_dimension_changed(self):
        for nest, table_data in self.nest_items.items():
            table_data["length"].setValue(self.doubleSpinBox_global_sheet_length_2.value())
            table_data["width"].setValue(self.doubleSpinBox_global_sheet_width_2.value())
        self.quote_changed()

    def global_toggle_primer_clicked(self):
        for _, table_data in self.laser_cut_table_items.items():
            table_data["paint_type"].checkbox_primer.blockSignals(True)
            table_data["paint_type"].checkbox_primer.setChecked(self.pushButton_toggle_primer.isChecked())
            table_data["paint_type"].checkbox_primer.blockSignals(False)
            table_data["paint_type"].update_paint()
        self.update_laser_cut_parts_price()
        self.quote_changed()

    def global_toggle_paint_clicked(self):
        for _, table_data in self.laser_cut_table_items.items():
            table_data["paint_type"].checkbox_paint.blockSignals(True)
            table_data["paint_type"].checkbox_paint.setChecked(self.pushButton_toggle_paint.isChecked())
            table_data["paint_type"].checkbox_paint.blockSignals(False)
            table_data["paint_type"].update_paint()
        self.update_laser_cut_parts_price()
        self.quote_changed()

    def global_toggle_powder_clicked(self):
        for _, table_data in self.laser_cut_table_items.items():
            table_data["paint_type"].checkbox_powder.blockSignals(True)
            table_data["paint_type"].checkbox_powder.setChecked(self.pushButton_toggle_powder_coating.isChecked())
            table_data["paint_type"].checkbox_powder.blockSignals(False)
            table_data["paint_type"].update_paint()
        self.update_laser_cut_parts_price()
        self.quote_changed()

    def global_primer_overspray_changed(self):
        for laser_cut_part, table_data in self.laser_cut_table_items.items():
            if laser_cut_part.uses_primer:
                table_data["paint_settings"].spinbox_primer_overspray.blockSignals(True)
                table_data["paint_settings"].spinbox_primer_overspray.setValue(self.doubleSpinBox_primer_overspray.value())
                table_data["paint_settings"].spinbox_primer_overspray.blockSignals(False)
                table_data["paint_settings"].update_paint_settings()
        self.update_laser_cut_parts_price()
        self.quote_changed()

    def global_paint_overspray_changed(self):
        for laser_cut_part, table_data in self.laser_cut_table_items.items():
            if laser_cut_part.uses_paint:
                table_data["paint_settings"].spinbox_paint_overspray.blockSignals(True)
                table_data["paint_settings"].spinbox_paint_overspray.setValue(self.doubleSpinBox_paint_overspray.value())
                table_data["paint_settings"].spinbox_paint_overspray.blockSignals(False)
                table_data["paint_settings"].update_paint_settings()
        self.update_laser_cut_parts_price()
        self.quote_changed()

    def global_primer_color_changed(self):
        for laser_cut_part, table_data in self.laser_cut_table_items.items():
            if laser_cut_part.uses_primer:
                table_data["paint_settings"].combobox_primer.blockSignals(True)
                table_data["paint_settings"].combobox_primer.setCurrentText(self.comboBox_primer_color.currentText())
                table_data["paint_settings"].combobox_primer.blockSignals(False)
                table_data["paint_settings"].update_paint_settings()
        self.update_laser_cut_parts_price()
        self.quote_changed()

    def global_paint_color_changed(self):
        for laser_cut_part, table_data in self.laser_cut_table_items.items():
            if laser_cut_part.uses_paint:
                table_data["paint_settings"].combobox_paint_color.blockSignals(True)
                table_data["paint_settings"].combobox_paint_color.setCurrentText(self.comboBox_paint_color.currentText())
                table_data["paint_settings"].combobox_paint_color.blockSignals(False)
                table_data["paint_settings"].update_paint_settings()
        self.update_laser_cut_parts_price()
        self.quote_changed()

    def global_powder_color_changed(self):
        for laser_cut_part, table_data in self.laser_cut_table_items.items():
            if laser_cut_part.uses_powder:
                table_data["paint_settings"].combobox_powder_coating_color.blockSignals(True)
                table_data["paint_settings"].combobox_powder_coating_color.setCurrentText(self.comboBox_powder_color.currentText())
                table_data["paint_settings"].combobox_powder_coating_color.blockSignals(False)
                table_data["paint_settings"].update_paint_settings()
        self.update_laser_cut_parts_price()
        self.quote_changed()

    def global_powder_transfer_efficiency_changed(self):
        for laser_cut_part, table_data in self.laser_cut_table_items.items():
            if laser_cut_part.uses_powder:
                table_data["paint_settings"].spinbox_powder_transfer_efficiency.blockSignals(True)
                table_data["paint_settings"].spinbox_powder_transfer_efficiency.setValue(self.doubleSpinBox_transfer_efficiency.value())
                table_data["paint_settings"].spinbox_powder_transfer_efficiency.blockSignals(False)
                table_data["paint_settings"].update_paint_settings()
        self.update_laser_cut_parts_price()
        self.quote_changed()

    def set_global_settings(self, nest: Nest):
        self.comboBox_global_sheet_material_2.setCurrentText(nest.sheet.material)
        self.comboBox_global_sheet_thickness_2.setCurrentText(nest.sheet.thickness)

        self.doubleSpinBox_global_sheet_length_2.setValue(nest.sheet.length)
        self.doubleSpinBox_global_sheet_width_2.setValue(nest.sheet.width)
        self.quote_changed()

    def load_nests(self):
        self.clear_layout(self.nests_layout)
        self.nest_items.clear()
        self.nests_tool_box = MultiToolBox(self)
        self.nests_tool_box.layout().setSpacing(0)
        self.nests_layout.addWidget(self.nests_tool_box)
        tab_index = 0
        for nest in [self.quote.custom_nest] + self.quote.nests:
            if not nest.laser_cut_parts:
                continue
            self.nest_items.update({nest: {}})
            self.nest_items[nest].update({"tab_index": tab_index})
            layout_widget = QWidget(self.nests_tool_box)
            layout = QVBoxLayout(layout_widget)
            widget = QWidget(layout_widget)
            layout.addWidget(widget)
            # layout_widget.setMinimumHeight(600)
            # layout_widget.setMaximumHeight(600)
            grid_layout = QGridLayout(widget)
            labels = [
                "Sheet Scrap Percentage:",
                "Cost for Sheets:",
                "Cutting Costs:",
                "Sheet Cut Time:",
                "Nest Cut Time:",
                "Sheet Count:",
                "Sheet Material:",
                "Sheet Thickness:",
                "Sheet Dimension (len x wid):",
            ]
            for i, label in enumerate(labels, start=1):
                label = QLabel(label, widget)
                grid_layout.addWidget(label, i, 0)

            label_status = QLabel("Sheet status", widget)
            grid_layout.addWidget(label_status, 0, 0)
            self.nest_items[nest].update({"label_sheet_status": label_status})

            button_add_sheet = QPushButton("Add Sheet to Inventory", widget)
            button_add_sheet.setHidden(True)
            button_add_sheet.clicked.connect(partial(self.add_nested_sheet_to_inventory, nest))
            grid_layout.addWidget(button_add_sheet, 0, 2)
            self.nest_items[nest].update({"button_sheet_status": button_add_sheet})

            label_scrap_percentage = QLabel(
                f"{nest.calculate_scrap_percentage():,.2f}%",
                widget,
            )
            grid_layout.addWidget(label_scrap_percentage, 1, 2)
            self.nest_items[nest].update({"scrap_percentage": label_scrap_percentage})

            label_sheet_cost = QLabel("")
            grid_layout.addWidget(label_sheet_cost, 2, 2)
            self.nest_items[nest].update({"sheet_cost": label_sheet_cost})

            label_cutting_cost = QLabel("")
            grid_layout.addWidget(label_cutting_cost, 3, 2)
            self.nest_items[nest].update({"cutting_cost": label_cutting_cost})

            sheet_cut_time = MachineCutTimeSpinBox(widget)
            sheet_cut_time.setValue(nest.sheet_cut_time)

            def change_sheet_cut_time(nest_to_change: Nest, spinbox: MachineCutTimeSpinBox):
                nest_to_change.sheet_cut_time = spinbox.value()
                self.update_cutting_time()
                self.update_sheet_price()
                self.load_nest_summary()
                self.quote_changed()

            sheet_cut_time.valueChanged.connect(partial(change_sheet_cut_time, nest, sheet_cut_time))
            sheet_cut_time.setToolTip(f"Original: {self.get_sheet_cut_time(nest)}")
            grid_layout.addWidget(sheet_cut_time, 4, 2)

            nest_cut_time = QLabel(widget)
            nest_cut_time.setText(f"{self.get_total_cutting_time(nest)}")
            grid_layout.addWidget(nest_cut_time, 5, 2)
            self.nest_items[nest].update({"cut_time": nest_cut_time})

            spinBox_sheet_count = QDoubleSpinBox(widget)
            spinBox_sheet_count.setMaximum(9999999999.9)
            spinBox_sheet_count.wheelEvent = lambda event: None
            spinBox_sheet_count.setValue(nest.sheet_count)

            def change_sheet_count(nest_to_change: Nest, spinbox: QDoubleSpinBox):
                nest_to_change.sheet_count = spinbox.value()
                self.laser_cut_table_widget.blockSignals(True)
                for laser_cut_part in nest_to_change.laser_cut_parts:
                    self.laser_cut_table_items[laser_cut_part]["quantity"].setText(str(int(laser_cut_part.quantity_in_nest * nest_to_change.sheet_count)))
                self.laser_cut_table_widget.blockSignals(False)
                self.update_cutting_time()
                self.update_sheet_price()
                self.update_laser_cut_parts_price()
                self.load_nest_summary()
                self.quote_changed()

            spinBox_sheet_count.valueChanged.connect(partial(change_sheet_count, nest, spinBox_sheet_count))
            self.nest_items[nest].update({"sheet_count": spinBox_sheet_count})

            grid_layout.addWidget(spinBox_sheet_count, 6, 2)

            comboBox_sheet_material = QComboBox(widget)
            comboBox_sheet_material.wheelEvent = lambda event: event.ignore()
            comboBox_sheet_material.addItems(self.sheet_settings.get_materials())
            comboBox_sheet_material.setCurrentText(nest.sheet.material)
            # if nest.sheet.material in {
            #     "304 SS",
            #     "409 SS",
            #     "Aluminium",
            # }:
            #     self.comboBox_laser_cutting_2.setCurrentText("Nitrogen")
            # else:
            #     self.comboBox_laser_cutting_2.setCurrentText("CO2")

            def change_sheet_material(nest_to_change: Nest, combobox: QComboBox):
                nest_to_change.sheet.material = combobox.currentText()
                for laser_cut_part in nest_to_change.laser_cut_parts:
                    laser_cut_part.material = nest_to_change.sheet.material
                    self.laser_cut_table_items[laser_cut_part]["material"].blockSignals(True)
                    self.laser_cut_table_items[laser_cut_part]["material"].setCurrentText(nest_to_change.sheet.material)
                    self.laser_cut_table_items[laser_cut_part]["material"].blockSignals(False)
                self.nests_tool_box.setItemText(
                    self.nest_items[nest_to_change]["tab_index"],
                    nest_to_change.get_name(),
                )
                self.update_sheet_price()
                self.update_laser_cut_parts_price()
                self.load_nest_summary()
                self.update_sheet_statuses()
                self.quote_changed()

            comboBox_sheet_material.currentTextChanged.connect(partial(change_sheet_material, nest, comboBox_sheet_material))
            self.nest_items[nest].update({"material": comboBox_sheet_material})
            grid_layout.addWidget(comboBox_sheet_material, 7, 2)

            comboBox_sheet_thickness = QComboBox(widget)
            comboBox_sheet_thickness.wheelEvent = lambda event: event.ignore()
            comboBox_sheet_thickness.addItems(self.sheet_settings.get_thicknesses())
            comboBox_sheet_thickness.setCurrentText(nest.sheet.thickness)

            def change_sheet_thickness(nest_to_change: Nest, combobox: QComboBox):
                nest_to_change.sheet.thickness = combobox.currentText()
                for laser_cut_part in nest_to_change.laser_cut_parts:
                    laser_cut_part.gauge = nest_to_change.sheet.thickness
                    self.laser_cut_table_items[laser_cut_part]["thickness"].blockSignals(True)
                    self.laser_cut_table_items[laser_cut_part]["thickness"].setCurrentText(nest_to_change.sheet.thickness)
                    self.laser_cut_table_items[laser_cut_part]["thickness"].blockSignals(False)
                self.nests_tool_box.setItemText(
                    self.nest_items[nest_to_change]["tab_index"],
                    nest_to_change.get_name(),
                )
                self.update_sheet_price()
                self.update_laser_cut_parts_price()
                self.load_nest_summary()
                self.update_sheet_statuses()
                self.quote_changed()

            comboBox_sheet_thickness.currentTextChanged.connect(partial(change_sheet_thickness, nest, comboBox_sheet_thickness))
            self.nest_items[nest].update({"thickness": comboBox_sheet_thickness})
            grid_layout.addWidget(comboBox_sheet_thickness, 8, 2)
            lineEdit_sheet_size_x = QDoubleSpinBox(widget)
            lineEdit_sheet_size_x.setMaximum(9999999999.9)
            lineEdit_sheet_size_x.wheelEvent = lambda event: None
            lineEdit_sheet_size_x.setDecimals(3)
            lineEdit_sheet_size_x.setSuffix(" in")
            lineEdit_sheet_size_x.setValue(nest.sheet.length)

            def change_length(nest_to_change: Nest, spinbox: QDoubleSpinBox):
                nest_to_change.sheet.length = spinbox.value()
                self.nests_tool_box.setItemText(
                    self.nest_items[nest_to_change]["tab_index"],
                    nest_to_change.get_name(),
                )
                self.update_scrap_percentage()
                self.update_sheet_price()
                self.load_nest_summary()
                self.update_sheet_statuses()
                self.quote_changed()

            lineEdit_sheet_size_x.valueChanged.connect(partial(change_length, nest, lineEdit_sheet_size_x))
            self.nest_items[nest].update({"length": lineEdit_sheet_size_x})
            grid_layout.addWidget(lineEdit_sheet_size_x, 11, 0)
            label = QLabel("x", widget)
            label.setFixedWidth(20)
            grid_layout.addWidget(label, 11, 1)
            lineEdit_sheet_size_y = QDoubleSpinBox(widget)
            lineEdit_sheet_size_y.setMaximum(9999999999.9)
            lineEdit_sheet_size_y.wheelEvent = lambda event: None
            lineEdit_sheet_size_y.setDecimals(3)
            lineEdit_sheet_size_y.setSuffix(" in")
            lineEdit_sheet_size_y.setValue(nest.sheet.width)

            def change_width(nest_to_change: Nest, spinbox: QDoubleSpinBox):
                nest_to_change.sheet.width = spinbox.value()
                self.nests_tool_box.setItemText(
                    self.nest_items[nest_to_change]["tab_index"],
                    nest_to_change.get_name(),
                )
                self.update_scrap_percentage()
                self.update_sheet_price()
                self.load_nest_summary()
                self.update_sheet_statuses()
                self.quote_changed()

            lineEdit_sheet_size_y.valueChanged.connect(partial(change_width, nest, lineEdit_sheet_size_y))
            self.nest_items[nest].update({"width": lineEdit_sheet_size_y})
            grid_layout.addWidget(lineEdit_sheet_size_y, 11, 2)
            thumbnail = ClickableLabel(widget)
            thumbnail.setToolTip("Click to make bigger.")
            thumbnail.setFixedSize(485, 345)
            pixmap = QPixmap(nest.image_path)
            scaled_pixmap = pixmap.scaled(thumbnail.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
            thumbnail.setPixmap(scaled_pixmap)
            thumbnail.clicked.connect(
                partial(
                    self.open_image,
                    nest.image_path,
                    nest.name,
                )
            )
            layout.addWidget(thumbnail)

            self.nests_tool_box.addItem(
                layout_widget,
                nest.get_name(),
            )
            tab_index += 1
        self.nests_tool_box.close_all()
        self.update_sheet_price()
        self.update_sheet_statuses()
        self.update_scrap_percentage()

    def load_nest_summary(self):
        self.clear_layout(self.gridLayout_nest_summary_2)
        headers = ["Sheet Name", "Total Sheet Count", "Total Cut Time"]
        for i, header in enumerate(headers):
            label = QLabel(header, self)
            self.gridLayout_nest_summary_2.addWidget(label, 0, i)

        summary = {}

        for nest in [self.quote.custom_nest] + self.quote.nests:
            if not nest.laser_cut_parts:
                continue
            summary.setdefault(nest.sheet.get_name(), {"total_sheet_count": 0, "total_seconds": 0})
            summary.setdefault(nest.sheet.material, {"total_sheet_count": 0, "total_seconds": 0})
            summary[nest.sheet.get_name()]["total_sheet_count"] += nest.sheet_count
            summary[nest.sheet.get_name()]["total_seconds"] += nest.sheet_cut_time * nest.sheet_count
            summary[nest.sheet.material]["total_seconds"] += nest.sheet_cut_time * nest.sheet_count
            summary[nest.sheet.material]["total_sheet_count"] += nest.sheet_count

        sorted_summary_keys = natsorted(summary.keys())
        sorted_summary = {key: summary[key] for key in sorted_summary_keys}

        for i, (sheet_name, sheet_data) in enumerate(sorted_summary.items(), start=1):
            label_sheet_name = QLabel(sheet_name, self)
            if "x" not in sheet_name:
                label_sheet_name.setStyleSheet("border-top: 1px solid #8C8C8C; border-bottom: 1px solid #8C8C8C")
            self.gridLayout_nest_summary_2.addWidget(label_sheet_name, i + 1, 0)

            if "x" not in sheet_name:
                label_sheet_count = QLabel("Total Cut Time:", self)
            else:
                label_sheet_count = QLabel(str(sheet_data["total_sheet_count"]), self)
            if "x" not in sheet_name:
                label_sheet_count.setStyleSheet("border-top: 1px solid #8C8C8C; border-bottom: 1px solid #8C8C8C")
            self.gridLayout_nest_summary_2.addWidget(label_sheet_count, i + 1, 1)

            total_seconds = sheet_data["total_seconds"]
            try:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                total_seconds_string = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
            except KeyError:
                total_seconds_string = "Null"

            if "x" not in sheet_name:
                label_sheet_cuttime = QLabel(f"{total_seconds_string}", self)
            else:
                label_sheet_cuttime = QLabel(total_seconds_string, self)
            if "x" not in sheet_name:
                label_sheet_cuttime.setStyleSheet("border-top: 1px solid #8C8C8C; border-bottom: 1px solid #8C8C8C")
            self.gridLayout_nest_summary_2.addWidget(label_sheet_cuttime, i + 1, 2)

    def open_image(self, path: str, title: str) -> None:
        image_viewer = QImageViewer(self, path, title)
        image_viewer.show()

    def get_cutting_cost(self, nest: Nest) -> float:
        return ((nest.sheet_cut_time * nest.sheet_count) / 3600) * self.doubleSpinBox_cost_for_laser_2.value()

    def get_total_cutting_time(self, nest: Nest) -> str:
        total_seconds = nest.sheet_cut_time * nest.sheet_count
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def get_sheet_cut_time(self, nest: Nest) -> str:
        total_seconds = nest.sheet_cut_time
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"

    def delete_selected_laser_cut_parts(self):
        self.quote.group_laser_cut_parts()
        update_nests = False
        selected_rows: set[int] = {selection.row() for selection in self.laser_cut_table_widget.selectedItems()}
        for laser_cut_part, table_item_data in self.laser_cut_table_items.items():
            if table_item_data["row"] in selected_rows:
                laser_cut_part.nest.remove_laser_cut_part(laser_cut_part)
                if len(laser_cut_part.nest.laser_cut_parts) == 0:
                    if not laser_cut_part.nest.is_custom:
                        self.quote.remove_nest(laser_cut_part.nest)
                    update_nests = True
        self.quote.group_laser_cut_parts()
        self.load_laser_cut_parts()
        if update_nests:
            self.load_nests()
        self.quote_changed()

    def update_selected_laser_cut_parts_paint_types(self, paint_type: str, enable: bool):
        selected_rows: set[int] = {selection.row() for selection in self.laser_cut_table_widget.selectedItems()}
        for _, table_item_data in self.laser_cut_table_items.items():
            if table_item_data["row"] in selected_rows:
                if paint_type == "primer":
                    table_item_data["paint_type"].checkbox_primer.blockSignals(True)
                    table_item_data["paint_type"].checkbox_primer.setChecked(enable)
                    table_item_data["paint_type"].checkbox_primer.blockSignals(False)
                elif paint_type == "paint":
                    table_item_data["paint_type"].checkbox_paint.blockSignals(True)
                    table_item_data["paint_type"].checkbox_paint.setChecked(enable)
                    table_item_data["paint_type"].checkbox_paint.blockSignals(False)
                elif paint_type == "powder":
                    table_item_data["paint_type"].checkbox_powder.blockSignals(True)
                    table_item_data["paint_type"].checkbox_powder.setChecked(enable)
                    table_item_data["paint_type"].checkbox_powder.blockSignals(False)
                table_item_data["paint_type"].update_paint()
        self.quote_changed()
        self.update_laser_cut_parts_price()

    def update_selected_laser_cut_parts_paint_settings(self, paint_type: str, paint_color: str):
        selected_rows: set[int] = {selection.row() for selection in self.laser_cut_table_widget.selectedItems()}
        for laser_cut_part, table_item_data in self.laser_cut_table_items.items():
            if table_item_data["row"] in selected_rows:
                if paint_type == "primer":
                    laser_cut_part.uses_primer = True
                    table_item_data["paint_type"].checkbox_primer.blockSignals(True)
                    table_item_data["paint_type"].checkbox_primer.setChecked(True)
                    table_item_data["paint_type"].checkbox_primer.blockSignals(False)
                    table_item_data["paint_settings"].combobox_primer.blockSignals(True)
                    table_item_data["paint_settings"].combobox_primer.setCurrentText(paint_color)
                    table_item_data["paint_settings"].combobox_primer.blockSignals(False)
                elif paint_type == "paint":
                    laser_cut_part.uses_paint = True
                    table_item_data["paint_type"].checkbox_paint.blockSignals(True)
                    table_item_data["paint_type"].checkbox_paint.setChecked(True)
                    table_item_data["paint_type"].checkbox_paint.blockSignals(False)
                    table_item_data["paint_settings"].combobox_paint_color.blockSignals(True)
                    table_item_data["paint_settings"].combobox_paint_color.setCurrentText(paint_color)
                    table_item_data["paint_settings"].combobox_paint_color.blockSignals(False)
                elif paint_type == "powder":
                    laser_cut_part.uses_powder = True
                    table_item_data["paint_type"].checkbox_powder.blockSignals(True)
                    table_item_data["paint_type"].checkbox_powder.setChecked(True)
                    table_item_data["paint_type"].checkbox_powder.blockSignals(False)
                    table_item_data["paint_settings"].combobox_powder_coating_color.blockSignals(True)
                    table_item_data["paint_settings"].combobox_powder_coating_color.setCurrentText(paint_color)
                    table_item_data["paint_settings"].combobox_powder_coating_color.blockSignals(False)
                table_item_data["paint_type"].update_paint()
                table_item_data["paint_settings"].update_paint_settings()
        self.quote_changed()
        self.update_laser_cut_parts_price()

    def update_selected_laser_cut_parts_settings(self, setting_name: str, value: str):
        selected_rows: set[int] = {selection.row() for selection in self.laser_cut_table_widget.selectedItems()}
        for laser_cut_part, table_item_data in self.laser_cut_table_items.items():
            if table_item_data["row"] in selected_rows:
                if setting_name == "material":
                    laser_cut_part.material = value
                elif setting_name == "thickness":
                    laser_cut_part.gauge = value
                table_item_data[setting_name].blockSignals(True)
                table_item_data[setting_name].setCurrentText(value)
                table_item_data[setting_name].blockSignals(False)
        self.quote_changed()
        self.update_laser_cut_parts_price()

    def load_context_menu(self) -> QMenu:
        menu = QMenu("Options", self)

        delete_selected_parts_action = QAction("Delete selected items", self)
        delete_selected_parts_action.triggered.connect(self.delete_selected_laser_cut_parts)

        primer_menu = QMenu("Primer", menu)
        enable_primer = QAction("Enable Primer", primer_menu)
        enable_primer.triggered.connect(partial(self.update_selected_laser_cut_parts_paint_types, "primer", True))
        disable_primer = QAction("Disable Primer", primer_menu)
        disable_primer.triggered.connect(partial(self.update_selected_laser_cut_parts_paint_types, "primer", False))
        primer_menu.addAction(enable_primer)
        primer_menu.addAction(disable_primer)
        primer_color_menu = QMenu("Set Primer Color", primer_menu)
        primer_menu.addMenu(primer_color_menu)
        for primer_color in self.paint_inventory.get_all_primers():
            primer_action = QAction(primer_color, primer_color_menu)
            primer_action.triggered.connect(
                partial(
                    self.update_selected_laser_cut_parts_paint_settings,
                    "primer",
                    primer_color,
                )
            )
            primer_color_menu.addAction(primer_action)

        paint_menu = QMenu("Paint", menu)
        enable_primer = QAction("Enable Paint", paint_menu)
        enable_primer.triggered.connect(partial(self.update_selected_laser_cut_parts_paint_types, "paint", True))
        disable_primer = QAction("Disable Paint", paint_menu)
        disable_primer.triggered.connect(partial(self.update_selected_laser_cut_parts_paint_types, "paint", False))
        paint_menu.addAction(enable_primer)
        paint_menu.addAction(disable_primer)
        primer_color_menu = QMenu("Set Paint Color", paint_menu)
        paint_menu.addMenu(primer_color_menu)
        for paint_color in self.paint_inventory.get_all_paints():
            paint_action = QAction(paint_color, primer_color_menu)
            paint_action.triggered.connect(
                partial(
                    self.update_selected_laser_cut_parts_paint_settings,
                    "paint",
                    paint_color,
                )
            )
            primer_color_menu.addAction(paint_action)

        powder_menu = QMenu("Powder Coating", menu)
        enable_primer = QAction("Enable Powder Coating", powder_menu)
        enable_primer.triggered.connect(partial(self.update_selected_laser_cut_parts_paint_types, "powder", True))
        disable_primer = QAction("Disable Powder Coating", powder_menu)
        disable_primer.triggered.connect(partial(self.update_selected_laser_cut_parts_paint_types, "powder", False))
        powder_menu.addAction(enable_primer)
        powder_menu.addAction(disable_primer)
        powder_color_menu = QMenu("Set Powder Color", powder_menu)
        powder_menu.addMenu(powder_color_menu)
        for powder_color in self.paint_inventory.get_all_powders():
            powder_action = QAction(powder_color, powder_color_menu)
            powder_action.triggered.connect(
                partial(
                    self.update_selected_laser_cut_parts_paint_settings,
                    "powder",
                    powder_color,
                )
            )
            powder_color_menu.addAction(powder_action)

        material_menu = QMenu("Set Material", menu)
        for material in self.sheet_settings.get_materials():
            material_action = QAction(material, material_menu)
            material_action.triggered.connect(partial(self.update_selected_laser_cut_parts_settings, "material", material))
            material_menu.addAction(material_action)

        thickness_menu = QMenu("Set Thickness", menu)
        for thickness in self.sheet_settings.get_thicknesses():
            thickness_action = QAction(thickness, material_menu)
            thickness_action.triggered.connect(
                partial(
                    self.update_selected_laser_cut_parts_settings,
                    "thickness",
                    thickness,
                )
            )
            thickness_menu.addAction(thickness_action)

        menu.addAction(delete_selected_parts_action)
        menu.addSeparator()
        menu.addMenu(paint_menu)
        menu.addMenu(primer_menu)
        menu.addMenu(powder_menu)
        menu.addSeparator()
        menu.addMenu(material_menu)
        menu.addMenu(thickness_menu)

        return menu

    def add_laser_cut_part(self):
        add_item_dialog = AddLaserCutPartDialog(self)
        if add_item_dialog.exec():
            if laser_cut_parts := add_item_dialog.get_selected_laser_cut_parts():
                for laser_cut_part in laser_cut_parts:
                    new_laser_cut_part = LaserCutPart(laser_cut_part.to_dict(), self.laser_cut_inventory)
                    new_laser_cut_part.quantity = add_item_dialog.get_current_quantity()
                    new_laser_cut_part.quantity_in_nest = 1
                    self.quote.add_laser_cut_part_to_custom_nest(new_laser_cut_part)
                    self.parent.parent.download_required_images_thread([new_laser_cut_part.image_index])
            else:
                if not (laser_cut_part := self.laser_cut_inventory.get_laser_cut_part_by_name(add_item_dialog.get_name())):
                    msg = QMessageBox(
                        QMessageBox.Icon.Critical,
                        "Does not exist",
                        f"{add_item_dialog.get_name()} does not exist in the laser cut parts inventory",
                        QMessageBox.StandardButton.Ok,
                        self,
                    )
                    msg.show()
                    return
                new_laser_cut_part = LaserCutPart(laser_cut_part.to_dict(), self.laser_cut_inventory)
                new_laser_cut_part.quantity = add_item_dialog.get_current_quantity()
                new_laser_cut_part.quantity_in_nest = 1
                self.quote.add_laser_cut_part_to_custom_nest(new_laser_cut_part)
                self.parent.parent.download_required_images_thread([new_laser_cut_part.image_index])
            self.load_laser_cut_parts()
            self.load_nests()
            self.load_nest_summary()
        self.quote_changed()

    def load_laser_cut_parts(self):
        self.laser_cut_table_items.clear()
        self.clear_layout(self.laser_cut_layout)
        self.laser_cut_table_widget = LaserCutPartsQuotingTableWidget(self)
        self.laser_cut_table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.laser_cut_table_widget.customContextMenuRequested.connect(partial(self.open_group_menu, self.load_context_menu()))

        self.laser_cut_layout.addWidget(self.laser_cut_table_widget)
        row_index = 0
        self.laser_cut_table_widget.setRowCount(0)
        for nest in [self.quote.custom_nest] + self.quote.nests:
            if not nest.laser_cut_parts:
                continue
            self.laser_cut_table_widget.insertRow(row_index)
            item = QTableWidgetItem(nest.name)
            item.setTextAlignment(4)
            font = QFont()
            font.setPointSize(15)
            item.setFont(font)
            self.laser_cut_table_widget.setItem(row_index, 0, item)
            self.laser_cut_table_widget.setSpan(row_index, 0, 1, self.laser_cut_table_widget.columnCount())
            self.set_table_row_color(self.laser_cut_table_widget, row_index, "#141414")
            row_index += 1
            for laser_cut_part in nest.laser_cut_parts:
                self.laser_cut_table_items.update({laser_cut_part: {"nest": nest}})
                self.laser_cut_table_items[laser_cut_part].update({"row": row_index})

                self.laser_cut_table_widget.insertRow(row_index)
                self.laser_cut_table_widget.setRowHeight(row_index, 70)
                image_item = QTableWidgetItem()
                if "images" not in laser_cut_part.image_index:
                    laser_cut_part.image_index = "images/" + laser_cut_part.image_index
                if not laser_cut_part.image_index.endswith(".jpeg"):
                    laser_cut_part.image_index += ".jpeg"
                image = QPixmap(laser_cut_part.image_index)
                if image.isNull():
                    image = QPixmap("images/404.jpeg")
                    does_part_exist = False
                else:
                    does_part_exist = True
                original_width = image.width()
                original_height = image.height()
                new_height = 70
                new_width = int(original_width * (new_height / original_height))
                pixmap = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio)
                image_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)

                self.laser_cut_table_widget.setItem(row_index, LaserCutTableColumns.PICTURE.value, image_item)

                table_widget_item_name = QTableWidgetItem(laser_cut_part.name)
                table_widget_item_name.setFont(self.tables_font)
                table_widget_item_name.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.PART_NAME.value,
                    table_widget_item_name,
                )

                def material_changed(laser_cut_part_changed: LaserCutPart, combobox: QComboBox):
                    laser_cut_part_changed.material = combobox.currentText()
                    self.quote_changed()
                    self.update_laser_cut_parts_price()

                material_combobox = QComboBox(self)
                material_combobox.addItems(self.sheet_settings.get_materials())
                material_combobox.setCurrentText(laser_cut_part.material)
                material_combobox.wheelEvent = lambda event: None
                material_combobox.setStyleSheet("border-radius: none;")
                material_combobox.currentTextChanged.connect(partial(material_changed, laser_cut_part, material_combobox))
                self.laser_cut_table_widget.setCellWidget(
                    row_index,
                    LaserCutTableColumns.MATERIAL.value,
                    material_combobox,
                )
                self.laser_cut_table_items[laser_cut_part].update({"material": material_combobox})

                def thickness_changed(laser_cut_part_changed: LaserCutPart, combobox: QComboBox):
                    laser_cut_part_changed.gauge = combobox.currentText()
                    self.quote_changed()

                thickness_combobox = QComboBox(self)
                thickness_combobox.addItems(self.sheet_settings.get_thicknesses())
                thickness_combobox.setCurrentText(laser_cut_part.gauge)
                thickness_combobox.wheelEvent = lambda event: None
                thickness_combobox.setStyleSheet("border-radius: none;")
                thickness_combobox.currentTextChanged.connect(partial(thickness_changed, laser_cut_part, thickness_combobox))
                self.laser_cut_table_widget.setCellWidget(
                    row_index,
                    LaserCutTableColumns.THICKNESS.value,
                    thickness_combobox,
                )
                self.laser_cut_table_items[laser_cut_part].update({"thickness": thickness_combobox})

                if not laser_cut_part.quantity_in_nest:  # I dont understand why I need to check, it throws TypeError in the following lines
                    laser_cut_part.quantity_in_nest = laser_cut_part.quantity
                table_widget_item_quantity = QTableWidgetItem(str(laser_cut_part.quantity_in_nest * nest.sheet_count))
                table_widget_item_quantity.setFont(self.tables_font)
                table_widget_item_quantity.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                table_widget_item_quantity.setToolTip(f"One sheet has: {laser_cut_part.quantity_in_nest}")
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.QUANTITY.value,
                    table_widget_item_quantity,
                )
                self.laser_cut_table_items[laser_cut_part].update({"quantity": table_widget_item_quantity})

                table_widget_item_part_dim = QTableWidgetItem(f"{laser_cut_part.part_dim}\n\n{laser_cut_part.surface_area} in²")
                table_widget_item_part_dim.setFont(self.tables_font)
                table_widget_item_part_dim.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.PART_DIM.value,
                    table_widget_item_part_dim,
                )

                # PAINT TYPE
                paint_settings_widget = PaintSettingsWidget(laser_cut_part, self.laser_cut_table_widget)
                paint_settings_widget.settingsChanged.connect(lambda: (self.quote_changed(), self.update_laser_cut_parts_price()))
                self.laser_cut_table_items[laser_cut_part].update({"paint_settings": paint_settings_widget})

                paint_widget = PaintWidget(laser_cut_part, paint_settings_widget, self.laser_cut_table_widget)
                paint_widget.settingsChanged.connect(lambda: (self.quote_changed(), self.update_laser_cut_parts_price()))
                self.laser_cut_table_items[laser_cut_part].update({"paint_type": paint_widget})

                self.laser_cut_table_widget.setCellWidget(row_index, LaserCutTableColumns.PAINTING.value, paint_widget)

                self.laser_cut_table_widget.setCellWidget(
                    row_index,
                    LaserCutTableColumns.PAINT_SETTINGS.value,
                    paint_settings_widget,
                )

                # COGS
                table_widget_item_paint_cost = QTableWidgetItem("$0.00")
                table_widget_item_paint_cost.setFont(self.tables_font)
                table_widget_item_paint_cost.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.PAINT_COST.value,
                    table_widget_item_paint_cost,
                )
                self.laser_cut_table_items[laser_cut_part].update({"paint_cost": table_widget_item_paint_cost})

                # COGS
                table_widget_item_cost_of_goods = QTableWidgetItem("$0.00")
                table_widget_item_cost_of_goods.setFont(self.tables_font)
                table_widget_item_cost_of_goods.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.COST_OF_GOODS.value,
                    table_widget_item_cost_of_goods,
                )
                self.laser_cut_table_items[laser_cut_part].update({"cost_of_goods": table_widget_item_cost_of_goods})

                # Bend Cost
                table_widget_item_bend_cost = QTableWidgetItem(f"${laser_cut_part.bend_cost:,.2f}")
                table_widget_item_bend_cost.setFont(self.tables_font)
                table_widget_item_bend_cost.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.BEND_COST.value,
                    table_widget_item_bend_cost,
                )
                self.laser_cut_table_items[laser_cut_part].update({"bend_cost": table_widget_item_bend_cost})

                # Labor Cost
                table_widget_item_bend_cost = QTableWidgetItem(f"${laser_cut_part.labor_cost:,.2f}")
                table_widget_item_bend_cost.setFont(self.tables_font)
                table_widget_item_bend_cost.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.LABOR_COST.value,
                    table_widget_item_bend_cost,
                )
                self.laser_cut_table_items[laser_cut_part].update({"labor_cost": table_widget_item_bend_cost})

                # Unit Price
                table_widget_item_unit_price = QTableWidgetItem("$0.00")
                table_widget_item_unit_price.setFont(self.tables_font)
                table_widget_item_unit_price.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.UNIT_PRICE.value,
                    table_widget_item_unit_price,
                )
                self.laser_cut_table_items[laser_cut_part].update({"unit_price": table_widget_item_unit_price})

                # Price
                table_widget_item_price = QTableWidgetItem("$0.00")
                table_widget_item_price.setFont(self.tables_font)
                table_widget_item_price.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.PRICE.value,
                    table_widget_item_price,
                )
                self.laser_cut_table_items[laser_cut_part].update({"price": table_widget_item_price})

                # Shelf Number
                table_widget_item_shelf_number = QTableWidgetItem(laser_cut_part.shelf_number)
                table_widget_item_shelf_number.setFont(self.tables_font)
                table_widget_item_shelf_number.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.laser_cut_table_widget.setItem(
                    row_index,
                    LaserCutTableColumns.SHELF_NUMBER.value,
                    table_widget_item_shelf_number,
                )

                def recut_pressed(recut_part: LaserCutPart, button: RecutButton):
                    recut_part.recut = button.isChecked()
                    self.quote_changed()

                recut_button = RecutButton(self)
                recut_button.clicked.connect(partial(recut_pressed, laser_cut_part, recut_button))
                recut_button.setStyleSheet("margin: 5%;")
                self.laser_cut_table_widget.setCellWidget(row_index, LaserCutTableColumns.RECUT.value, recut_button)

                send_part_to_inventory = QPushButton(self)
                send_part_to_inventory.setText("Add to Inventory")
                send_part_to_inventory.setStyleSheet("margin: 5%;")
                send_part_to_inventory.setFixedWidth(120)
                send_part_to_inventory.clicked.connect(
                    partial(
                        self.add_laser_cut_part_to_inventory,
                        laser_cut_part,
                    )
                )
                self.laser_cut_table_widget.setCellWidget(
                    row_index,
                    LaserCutTableColumns.ADD_TO_INVENTORY.value,
                    send_part_to_inventory,
                )

                if not does_part_exist:
                    self.set_table_row_color(self.laser_cut_table_widget, row_index, "#3F1E25")
                row_index += 1
        self.laser_cut_table_widget.resizeColumnsToContents()
        self.laser_cut_table_widget.cellChanged.connect(self.update_laser_cut_parts_price)
        self.update_laser_cut_parts_price()
        self.update_laser_cut_parts_to_sheet_price()

    def add_laser_cut_part_to_inventory(self, laser_cut_part_to_add: LaserCutPart):
        self.parent.parent.add_laser_cut_part_to_inventory(laser_cut_part_to_add, self.quote.name)
        self.laser_cut_inventory.save()
        self.sync_changes()

    def get_total_cost_for_laser_cut_parts(self) -> float:
        total_laser_cut_parts_cost = 0.0
        for _, table_item_data in self.laser_cut_table_items.items():
            price = float(table_item_data["price"].text().strip().replace(",", "").replace("$", ""))
            total_laser_cut_parts_cost += price
        return total_laser_cut_parts_cost

    def get_laser_cut_part_cost(
        self,
        profit_margin: float,
        overhead: float,
        cost_of_goods: float,
        bend_cost: float,
        labor_cost: float,
        cost_for_priming: float,
        cost_for_painting: float,
        cost_for_powder_coating: float,
    ) -> float:
        return (
            calculate_overhead(
                cost_of_goods,
                profit_margin,
                overhead,
            )
            + calculate_overhead(
                bend_cost,
                profit_margin,
                overhead,
            )
            + calculate_overhead(
                labor_cost,
                profit_margin,
                overhead,
            )
            + calculate_overhead(
                cost_for_priming,
                profit_margin,
                overhead,
            )
            + calculate_overhead(
                cost_for_painting,
                profit_margin,
                overhead,
            )
            + calculate_overhead(
                cost_for_powder_coating,
                profit_margin,
                overhead,
            )
        )

    def update_laser_cut_parts_to_sheet_price(self) -> None:
        target_value = self.get_total_cost_for_sheets()
        profit_margin = self.doubleSpinBox_profit_margin_items_2.value() / 100
        overhead = self.doubleSpinBox_overhead_items_2.value() / 100

        max_iterations = 200
        tolerance = 1
        iteration_count = 0

        def _calculate_total_cost(laser_cut_parts: list[LaserCutPart]):
            total_item_cost = sum(
                self.get_laser_cut_part_cost(
                    profit_margin,
                    overhead,
                    part.matched_to_sheet_cost_price,
                    part.bend_cost,
                    part.labor_cost,
                    part.cost_for_primer,
                    part.cost_for_paint,
                    part.cost_for_powder_coating,
                )
                * part.quantity
                for part in laser_cut_parts
            )
            return total_item_cost

        def _adjust_item_price(laser_cut_parts: list[LaserCutPart], amount: float):
            for laser_cut_part in laser_cut_parts:
                laser_cut_part.matched_to_sheet_cost_price += amount

        all_laser_cut_parts = list(self.laser_cut_table_items.keys())
        for laser_cut_part in all_laser_cut_parts:
            laser_cut_part.matched_to_sheet_cost_price = laser_cut_part.cost_of_goods
        new_item_cost = _calculate_total_cost(all_laser_cut_parts)
        difference = round(new_item_cost - target_value, 2)
        amount_changed: float = 0
        run_count: int = 0
        while abs(difference) > tolerance and iteration_count < max_iterations:
            run_count += 1
            if difference > 0:  # Need to decrease cost for items
                _adjust_item_price(all_laser_cut_parts, -(abs(difference) / 1000))
            else:  # Need to increase cost for items
                _adjust_item_price(all_laser_cut_parts, abs(difference) / 1000)
            new_item_cost = _calculate_total_cost(all_laser_cut_parts)
            amount_changed += abs(difference) / 10000
            difference = round(new_item_cost - target_value, 2)
            iteration_count += 1
            if (math.isinf(difference) and difference > 0) or (math.isinf(difference) and difference < 0):
                break

    def update_laser_cut_parts_price(self):
        profit_margin = self.doubleSpinBox_profit_margin_items_2.value() / 100
        overhead = self.doubleSpinBox_overhead_items_2.value() / 100
        for laser_cut_part, table_item_data in self.laser_cut_table_items.items():
            bend_cost = float(table_item_data["bend_cost"].text().strip().replace("$", "").replace(",", "").replace('"', "").replace("'", ""))
            labor_cost = float(table_item_data["labor_cost"].text().strip().replace("$", "").replace(",", "").replace('"', "").replace("'", ""))
            quantity = float(table_item_data["quantity"].text().strip().replace(",", "").replace('"', "").replace("'", ""))
            material = table_item_data["material"].currentText()

            laser_cut_part.quantity = quantity
            laser_cut_part.bend_cost = bend_cost
            laser_cut_part.labor_cost = labor_cost

            price_per_pound: float = self.sheet_settings.get_price_per_pound(material)
            cost_for_laser: float = self.doubleSpinBox_cost_for_laser_2.value()
            laser_cut_part.cost_of_goods = (laser_cut_part.machine_time * (cost_for_laser / 60)) + (laser_cut_part.weight * price_per_pound)

            cost_for_priming = self.paint_inventory.get_primer_cost(laser_cut_part)
            cost_for_painting = self.paint_inventory.get_paint_cost(laser_cut_part)
            cost_for_powder_coating = self.paint_inventory.get_powder_cost(laser_cut_part, self.doubleSpinBox_mil_thickness.value())

            laser_cut_part.cost_for_primer = cost_for_priming
            laser_cut_part.cost_for_paint = cost_for_painting
            laser_cut_part.cost_for_powder_coating = cost_for_powder_coating

            unit_price = self.get_laser_cut_part_cost(
                profit_margin,
                overhead,
                (laser_cut_part.matched_to_sheet_cost_price if self.pushButton_item_to_sheet.isChecked() else laser_cut_part.cost_of_goods),
                bend_cost,
                labor_cost,
                cost_for_priming,
                cost_for_painting,
                cost_for_powder_coating,
            )

            laser_cut_part.price = round(unit_price, 2)

        if self.pushButton_item_to_sheet.isChecked():
            self.update_laser_cut_parts_to_sheet_price()

        self.update_table_costs()

    def update_table_costs(self):
        profit_margin = self.doubleSpinBox_profit_margin_items_2.value() / 100
        overhead = self.doubleSpinBox_overhead_items_2.value() / 100
        self.laser_cut_table_widget.blockSignals(True)
        for laser_cut_part, table_item_data in self.laser_cut_table_items.items():
            unit_price = self.get_laser_cut_part_cost(
                profit_margin,
                overhead,
                (laser_cut_part.matched_to_sheet_cost_price if self.pushButton_item_to_sheet.isChecked() else laser_cut_part.cost_of_goods),
                laser_cut_part.bend_cost,
                laser_cut_part.labor_cost,
                laser_cut_part.cost_for_primer,
                laser_cut_part.cost_for_paint,
                laser_cut_part.cost_for_powder_coating,
            )
            price = round(unit_price, 2) * laser_cut_part.quantity
            table_item_data["paint_cost"].setText(f"${laser_cut_part.cost_for_primer + laser_cut_part.cost_for_paint + laser_cut_part.cost_for_powder_coating:,.2f}")
            table_item_data["paint_cost"].setToolTip(f"Cost for priming: ${laser_cut_part.cost_for_primer:,.2f}\nCost for painting: ${laser_cut_part.cost_for_paint:,.2f}\nCost for powder coating: ${laser_cut_part.cost_for_powder_coating:,.2f}")
            table_item_data["cost_of_goods"].setText(f"${laser_cut_part.matched_to_sheet_cost_price if self.pushButton_item_to_sheet.isChecked() else laser_cut_part.cost_of_goods:,.2f}")
            table_item_data["bend_cost"].setText(f"${laser_cut_part.bend_cost:,.2f}")
            table_item_data["labor_cost"].setText(f"${laser_cut_part.labor_cost:,.2f}")
            table_item_data["unit_price"].setText(f"${unit_price:,.2f}")
            table_item_data["price"].setText(f"${price:,.2f}")
        self.laser_cut_table_widget.blockSignals(False)
        self.laser_cut_table_widget.resizeColumnsToContents()
        self.label_total_item_cost_2.setText(f"Total Cost for Items: ${(self.get_total_cost_for_laser_cut_parts() + self.get_total_cost_for_components()):,.2f}")

    def clear_all_nests(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle("Are you sure?")
        msg_box.setText("Are you sure you want to remove all nests from this quote?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response in [
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Cancel,
        ]:
            return
        self.quote.custom_nest = Nest({"name": "Custom"}, self.sheet_settings, self.laser_cut_inventory)
        self.quote.custom_nest.name = "Custom"
        self.quote.custom_nest.is_custom = True
        self.quote.nests.clear()
        self.quote.grouped_laser_cut_parts.clear()
        self.laser_cut_table_items.clear()
        self.laser_cut_table_widget.clearContents()
        self.laser_cut_table_widget.setRowCount(0)
        self.load_quote()
        self.quote_changed()

    def add_component(self):
        add_item_dialog = AddComponentDialog(self)
        if add_item_dialog.exec():
            if components := add_item_dialog.get_selected_components():
                for component in components:
                    new_component = Component(component.to_dict(), self.components_inventory)
                    new_component.quantity = 1.0
                    self.quote.add_component(new_component)
            else:
                component = Component(
                    {
                        "part_number": add_item_dialog.get_name(),
                        "quantity": add_item_dialog.get_current_quantity(),
                        "part_name": add_item_dialog.get_name(),
                    },
                    self.components_inventory,
                )
                self.quote.add_component(component)
            self.load_component_parts()
        self.quote_changed()

    def delete_selected_components(self):
        selected_rows: set[int] = {selection.row() for selection in self.components_table_widget.selectedItems()}
        for component, table_item_data in self.components_table_items.items():
            if table_item_data["row"] in selected_rows:
                self.quote.remove_component(component)
        self.load_component_parts()

    def load_component_parts(self):
        self.components_table_items.clear()
        self.clear_layout(self.components_layout)
        self.components_table_widget = ComponentsQuotingTableWidget(self)

        self.components_table_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        menu = QMenu(self)
        deleted_selected_parts_action = QAction("Delete selected items", self)
        deleted_selected_parts_action.triggered.connect(self.delete_selected_components)
        menu.addAction(deleted_selected_parts_action)
        self.components_table_widget.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

        self.components_table_widget.imagePasted.connect(self.component_image_pasted)
        self.components_layout.addWidget(self.components_table_widget)
        self.components_table_widget.blockSignals(True)
        self.components_table_widget.setRowCount(0)
        for row_index, component in enumerate(self.quote.components):
            self.components_table_items.update({component: {}})
            self.components_table_items[component].update({"row": row_index})
            self.components_table_widget.insertRow(row_index)
            self.components_table_widget.setRowHeight(row_index, 60)

            self.components_table_widget.setItem(row_index, ComponentsTableColumns.PICTURE.value, QTableWidgetItem(""))
            self.components_table_widget.item(row_index, ComponentsTableColumns.PICTURE.value).setData(Qt.ItemDataRole.DecorationRole, QPixmap(component.image_path))

            table_widget_part_name = QTableWidgetItem(component.part_name)
            table_widget_part_name.setFont(self.tables_font)
            self.components_table_widget.setItem(row_index, ComponentsTableColumns.PART_NAME.value, table_widget_part_name)
            self.components_table_items[component].update({"part_name": table_widget_part_name})

            table_widget_part_number = QTableWidgetItem(component.part_number)
            table_widget_part_name.setFont(self.tables_font)
            self.components_table_widget.setItem(row_index, ComponentsTableColumns.PART_NUMBER.value, table_widget_part_number)
            self.components_table_widget.item(row_index, ComponentsTableColumns.PART_NUMBER.value).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.components_table_items[component].update({"part_number": table_widget_part_number})

            table_widget_shelf_number = QTableWidgetItem(component.shelf_number)
            table_widget_shelf_number.setFont(self.tables_font)
            self.components_table_widget.setItem(row_index, ComponentsTableColumns.SHELF_NUMBER.value, table_widget_shelf_number)
            self.components_table_widget.item(row_index, ComponentsTableColumns.SHELF_NUMBER.value).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.components_table_items[component].update({"shelf_number": table_widget_shelf_number})

            table_widget_notes = QTableWidgetItem(component.notes)
            table_widget_notes.setFont(self.tables_font)
            self.components_table_widget.setItem(row_index, ComponentsTableColumns.NOTES.value, table_widget_notes)
            self.components_table_items[component].update({"notes": table_widget_notes})

            table_widget_item_quantity = QTableWidgetItem(str(component.quantity))
            table_widget_item_quantity.setFont(self.tables_font)
            self.components_table_widget.setItem(row_index, ComponentsTableColumns.UNIT_QUANTITY.value, table_widget_item_quantity)
            self.components_table_widget.item(row_index, ComponentsTableColumns.UNIT_QUANTITY.value).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.components_table_items[component].update({"quantity": table_widget_item_quantity})

            self.components_table_widget.setItem(row_index, ComponentsTableColumns.QUANTITY.value, QTableWidgetItem("<- This column\nis quantity"))
            self.components_table_widget.item(row_index, ComponentsTableColumns.QUANTITY.value).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            table_widget_item_unit_price = QTableWidgetItem(f"${component.price:,.2f}")
            table_widget_item_unit_price.setFont(self.tables_font)
            self.components_table_widget.setItem(row_index, ComponentsTableColumns.UNIT_PRICE.value, table_widget_item_unit_price)
            self.components_table_widget.item(row_index, ComponentsTableColumns.UNIT_PRICE.value).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.components_table_items[component].update({"unit_price": table_widget_item_unit_price})

            table_widget_item_price = QTableWidgetItem("$0.00")
            table_widget_item_price.setFont(self.tables_font)
            self.components_table_widget.setItem(row_index, ComponentsTableColumns.PRICE.value, table_widget_item_price)
            self.components_table_widget.item(row_index, ComponentsTableColumns.PRICE.value).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.components_table_items[component].update({"price": table_widget_item_price})

        self.components_table_widget.blockSignals(False)
        self.components_table_widget.cellChanged.connect(self.update_components_price)
        self.update_components_price()
        self.components_table_widget.resizeColumnsToContents()
        self.components_table_widget.setColumnWidth(0, 60)
        self.components_table_widget.setColumnWidth(1, 250)

    def get_total_cost_for_components(self) -> float:
        total_components_cost = 0.0
        for _, table_item_data in self.components_table_items.items():
            total_components_cost += float(table_item_data["price"].text().strip().replace(",", "").replace("$", ""))
        return total_components_cost

    def update_components_price(self):
        self.components_table_widget.blockSignals(True)
        profit_margin = self.doubleSpinBox_profit_margin_items_2.value() if self.checkBox_components_use_profit_margin_2.isChecked() else 0
        overhead = self.doubleSpinBox_overhead_items_2.value() if self.checkBox_components_use_overhead_2.isChecked() else 0
        for component, table_item_data in self.components_table_items.items():
            component.part_name = table_item_data["part_name"].text()
            component.name = table_item_data["part_number"].text()
            component.shelf_number = table_item_data["shelf_number"].text()
            component.notes = table_item_data["notes"].text()
            quantity = float(table_item_data["quantity"].text().strip().replace(",", ""))
            component.quantity = quantity
            unit_price = float(table_item_data["unit_price"].text().strip().replace(",", "").replace("$", ""))
            component.price = unit_price
            if self.checkBox_components_use_profit_margin_2.isChecked() or self.checkBox_components_use_overhead_2.isChecked():
                table_item_data["price"].setText(f"${calculate_overhead(round(unit_price, 2)*quantity, profit_margin / 100, overhead / 100):,.2f}")
            else:
                table_item_data["price"].setText(f"${unit_price*quantity:,.2f}")
            table_item_data["unit_price"].setText(f"${unit_price:,.2f}")
        self.components_table_widget.blockSignals(False)
        self.label_total_item_cost_2.setText(f"Total Cost for Items: ${(self.get_total_cost_for_laser_cut_parts() + self.get_total_cost_for_components()):,.2f}")
        self.components_table_widget.resizeColumnsToContents()
        self.quote_changed()

    def get_component_by_name(self, component_name: str) -> Component:
        for component in self.quote.components:
            if component.name == component_name:
                return component

    def clear_all_components(self) -> None:
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle("Are you sure?")
        msg_box.setText("Are you sure you want to remove all components from this quote?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        response = msg_box.exec()
        if response in [
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Cancel,
        ]:
            return
        self.quote.components.clear()
        self.components_table_widget.clearContents()
        self.components_table_widget.setRowCount(0)
        self.components_table_items.clear()

    def component_image_pasted(self, image_file_name: str, row: int) -> None:
        component_name = self.components_table_widget.item(row, 2).text()
        component = self.get_component_by_name(component_name)
        component.image_path = image_file_name
        # component.components_inventory.save()
        self.quote_changed()

    def get_total_cost_for_sheets(self) -> float:
        total_sheet_cost = 0.0
        profit_margin = self.doubleSpinBox_profit_margin_sheets_2.value() / 100
        overhead = self.doubleSpinBox_overhead_sheets_2.value() / 100
        for nest, _ in self.nest_items.items():
            total_sheet_cost += calculate_overhead(
                (self.get_cutting_cost(nest) + (nest.get_sheet_cost() * nest.sheet_count)),
                profit_margin,
                overhead,
            )
        return total_sheet_cost

    # TODO OMNIGEN
    def match_sheet_to_item_price(self) -> None:
        return
        target_value: float = float(self.label_total_item_cost.text().replace("Total Cost for Items: $", "").replace(",", ""))
        best_difference = float("inf")
        best_profit_margin_index = 0

        for profit_margin_index in range(101):
            new_sheet_cost: float = self._get_total_sheet_cost(profit_margin_index, self.spinBox_overhead_sheets.value())
            difference = abs(new_sheet_cost - target_value)

            if difference < best_difference:
                best_difference = difference
                best_profit_margin_index = profit_margin_index
        self.spinBox_profit_margin_sheets.setValue(best_profit_margin_index)

    def update_sheet_price(self):
        for nest, table_item_data in self.nest_items.items():
            table_item_data["cutting_cost"].setText(f"${self.get_cutting_cost(nest):,.2f}")
            table_item_data["sheet_cost"].setText(f"${nest.get_sheet_cost() * nest.sheet_count:,.2f}")
        self.label_total_sheet_cost_2.setText(f"Total Cost for Nested Sheets: ${self.get_total_cost_for_sheets():,.2f}")

    def update_cutting_time(self):
        for nest, table_item_data in self.nest_items.items():
            table_item_data["cut_time"].setText(self.get_total_cutting_time(nest))

    # Disabled for now.
    def update_scrap_percentage(self):
        return
        for nest, table_item_data in self.nest_items.items():
            table_item_data["scrap_percentage"].setText(f"{nest.calculate_scrap_percentage():,.2f}%")
            nest.scrap_percentage = nest.calculate_scrap_percentage()

    def add_nested_sheet_to_inventory(self, nest: Nest):
        add_sheet_dialog = AddSheetDialog(nest.sheet, None, self.sheets_inventory, self.sheet_settings, self)

        if add_sheet_dialog.exec():
            new_sheet = Sheet(
                {
                    "quantity": add_sheet_dialog.get_quantity(),
                    "length": add_sheet_dialog.get_length(),
                    "width": add_sheet_dialog.get_width(),
                    "thickness": add_sheet_dialog.get_thickness(),
                    "material": add_sheet_dialog.get_material(),
                    "latest_change_quantity": f'{os.getlogin().title()} - Sheet was added via quote generator at {str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"))}',
                },
                self.sheets_inventory,
            )
            new_sheet.add_to_category(self.sheets_inventory.get_category(add_sheet_dialog.get_category()))
            for sheet in self.sheets_inventory.sheets:
                if new_sheet.get_name() == sheet.get_name():
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Warning)
                    msg.setWindowTitle("Exists")
                    msg.setText(f"'{new_sheet.get_name()}'\nAlready exists.")
                    msg.exec()
                    return
            nest.sheet = new_sheet
            self.nest_items[nest]["material"].setCurrentText(new_sheet.material)
            self.nest_items[nest]["thickness"].setCurrentText(new_sheet.thickness)
            self.nest_items[nest]["length"].setValue(new_sheet.length)
            self.nest_items[nest]["width"].setValue(new_sheet.width)
            for laser_cut_part in nest.laser_cut_parts:
                laser_cut_part.gauge = new_sheet.thickness
                laser_cut_part.material = new_sheet.material
                self.laser_cut_table_items[laser_cut_part]["thickness"].setCurrentText(new_sheet.thickness)
                self.laser_cut_table_items[laser_cut_part]["material"].setCurrentText(new_sheet.material)
            self.sheets_inventory.add_sheet(new_sheet)
            self.sheets_inventory.save()
            self.sync_changes()
            self.nests_tool_box.setItemText(self.nest_items[nest]["tab_index"], nest.get_name())
            self.update_laser_cut_parts_price()
            self.update_scrap_percentage()
            self.update_sheet_price()
            self.load_nest_summary()
            self.update_sheet_statuses()

    def update_sheet_statuses(self):
        for nest, table_item_data in self.nest_items.items():
            if self.sheets_inventory.exists(nest.sheet):
                table_item_data["button_sheet_status"].setHidden(True)
                if sheet := self.sheets_inventory.get_sheet_by_name(nest.sheet.get_name()):
                    table_item_data["label_sheet_status"].setText(f"This sheet exists in sheets inventory with {sheet.quantity} in stock.")
            else:
                table_item_data["button_sheet_status"].setHidden(False)
                table_item_data["label_sheet_status"].setText("This sheet does not exist in sheets inventory.")

    def set_table_row_color(
        self,
        table: LaserCutPartsQuotingTableWidget | ComponentsQuotingTableWidget,
        row_index: int,
        color: str,
    ):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def open_group_menu(self, menu: QMenu) -> None:
        menu.exec(QCursor.pos())

    def sync_changes(self):
        self.parent.parent.sync_changes()

    def clear_layout(self, layout: QVBoxLayout | QWidget) -> None:
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
