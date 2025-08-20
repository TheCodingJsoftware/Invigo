from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from ui.custom_widgets import CustomTableWidget
from ui.theme import theme_var
from utils.inventory.laser_cut_part import LaserCutPart


class LaserCutPartPaintSettingsWidget(QWidget):
    settingsChanged = pyqtSignal()

    def __init__(self, laser_cut_part: LaserCutPart, parent: CustomTableWidget):
        super().__init__(parent)
        self.parent: CustomTableWidget = parent
        self.laser_cut_part = laser_cut_part
        self.paint_inventory = self.laser_cut_part.paint_inventory

        self.paint_settings_layout = QHBoxLayout(self)

        self.paint_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.paint_settings_layout.setSpacing(0)
        self.not_painted_label = QLabel("Not painted", self)
        self.paint_settings_layout.addWidget(self.not_painted_label)

        self.widget_primer = QWidget(self)
        self.widget_primer.setObjectName("widget_primer")
        self.widget_primer.setStyleSheet(f"QWidget#widget_primer{{border: 1px solid {theme_var('outline')};}}")
        self.primer_layout = QGridLayout(self.widget_primer)
        self.primer_layout.setContentsMargins(3, 3, 3, 3)
        self.primer_layout.setSpacing(0)
        self.combobox_primer = QComboBox(self.widget_primer)
        self.combobox_primer.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.combobox_primer.addItems(["None"] + self.paint_inventory.get_all_primers())
        if self.laser_cut_part.primer_data.primer_name:
            self.combobox_primer.setCurrentText(self.laser_cut_part.primer_data.primer_name)
        self.combobox_primer.currentTextChanged.connect(self.update_paint_settings)
        self.spinbox_primer_overspray = QDoubleSpinBox(self.widget_primer)
        self.spinbox_primer_overspray.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.spinbox_primer_overspray.setValue(self.laser_cut_part.primer_data.primer_overspray)
        self.spinbox_primer_overspray.setMaximum(100.0)
        self.spinbox_primer_overspray.setSuffix("%")
        self.spinbox_primer_overspray.textChanged.connect(self.update_paint_settings)
        self.primer_layout.addWidget(QLabel("Primer:", self.widget_primer), 0, 0)
        self.primer_layout.addWidget(self.combobox_primer, 1, 0)
        self.primer_layout.addWidget(QLabel("Overspray:", self.widget_primer), 0, 1)
        self.primer_layout.addWidget(self.spinbox_primer_overspray, 1, 1)
        self.widget_primer.setVisible(self.laser_cut_part.primer_data.uses_primer)
        self.paint_settings_layout.addWidget(self.widget_primer)

        # PAINT COLOR
        self.widget_paint_color = QWidget(self)
        self.widget_paint_color.setObjectName("widget_paint_color")
        self.widget_paint_color.setStyleSheet(f"QWidget#widget_paint_color{{border: 1px solid {theme_var('outline')};}}")
        self.paint_color_layout = QGridLayout(self.widget_paint_color)
        self.paint_color_layout.setContentsMargins(3, 3, 3, 3)
        self.paint_color_layout.setSpacing(0)
        self.combobox_paint_color = QComboBox(self.widget_paint_color)
        self.combobox_paint_color.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.combobox_paint_color.addItems(["None"] + self.paint_inventory.get_all_paints())
        if self.laser_cut_part.paint_data.paint_name:
            self.combobox_paint_color.setCurrentText(self.laser_cut_part.paint_data.paint_name)
        self.combobox_paint_color.currentTextChanged.connect(self.update_paint_settings)
        self.spinbox_paint_overspray = QDoubleSpinBox(self.widget_paint_color)
        self.spinbox_paint_overspray.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.spinbox_paint_overspray.setValue(self.laser_cut_part.paint_data.paint_overspray)
        self.spinbox_paint_overspray.setMaximum(100.0)
        self.spinbox_paint_overspray.setSuffix("%")
        self.spinbox_paint_overspray.textChanged.connect(self.update_paint_settings)
        self.paint_color_layout.addWidget(QLabel("Paint:", self.widget_paint_color), 0, 0)
        self.paint_color_layout.addWidget(self.combobox_paint_color, 1, 0)
        self.paint_color_layout.addWidget(QLabel("Overspray:", self.widget_paint_color), 0, 1)
        self.paint_color_layout.addWidget(self.spinbox_paint_overspray, 1, 1)
        self.widget_paint_color.setVisible(self.laser_cut_part.paint_data.uses_paint)
        self.paint_settings_layout.addWidget(self.widget_paint_color)

        # POWDER COATING COLOR
        self.widget_powder_coating = QWidget(self)
        self.widget_powder_coating.setObjectName("widget_powder_coating")
        self.widget_powder_coating.setStyleSheet(f"QWidget#widget_powder_coating{{border: 1px solid {theme_var('outline')};}}")
        self.powder_coating_layout = QGridLayout(self.widget_powder_coating)
        self.powder_coating_layout.setContentsMargins(3, 3, 3, 3)
        self.powder_coating_layout.setSpacing(0)
        self.combobox_powder_coating_color = QComboBox(self.widget_powder_coating)
        self.combobox_powder_coating_color.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.combobox_powder_coating_color.addItems(["None"] + self.paint_inventory.get_all_powders())
        if self.laser_cut_part.powder_data.powder_name:
            self.combobox_powder_coating_color.setCurrentText(self.laser_cut_part.powder_data.powder_name)
        self.combobox_powder_coating_color.currentTextChanged.connect(self.update_paint_settings)
        self.spinbox_powder_transfer_efficiency = QDoubleSpinBox(self.widget_powder_coating)
        self.spinbox_powder_transfer_efficiency.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.spinbox_powder_transfer_efficiency.setValue(self.laser_cut_part.powder_data.powder_transfer_efficiency)
        self.spinbox_powder_transfer_efficiency.setMaximum(100.0)
        self.spinbox_powder_transfer_efficiency.setSuffix("%")
        self.spinbox_powder_transfer_efficiency.textChanged.connect(self.update_paint_settings)
        self.powder_coating_layout.addWidget(QLabel("Powder:", self.widget_powder_coating), 0, 0)
        self.powder_coating_layout.addWidget(self.combobox_powder_coating_color, 1, 0)
        self.powder_coating_layout.addWidget(QLabel("Transfer eff:", self.widget_powder_coating), 0, 1)
        self.powder_coating_layout.addWidget(self.spinbox_powder_transfer_efficiency, 1, 1)
        self.widget_powder_coating.setVisible(self.laser_cut_part.powder_data.uses_powder)
        self.paint_settings_layout.addWidget(self.widget_powder_coating)

        self.setLayout(self.paint_settings_layout)

    def update_inputs(self):
        self.spinbox_primer_overspray.setValue(self.laser_cut_part.primer_data.primer_overspray)
        self.spinbox_paint_overspray.setValue(self.laser_cut_part.paint_data.paint_overspray)
        self.spinbox_powder_transfer_efficiency.setValue(self.laser_cut_part.powder_data.powder_transfer_efficiency)
        self.combobox_paint_color.setCurrentText(self.laser_cut_part.paint_data.paint_name)
        self.combobox_primer.setCurrentText(self.laser_cut_part.primer_data.primer_name)
        self.combobox_powder_coating_color.setCurrentText(self.laser_cut_part.powder_data.powder_name)

    def update_paint_settings(self):
        self.laser_cut_part.primer_data.primer_overspray = self.spinbox_primer_overspray.value()
        self.laser_cut_part.paint_data.paint_overspray = self.spinbox_paint_overspray.value()
        self.laser_cut_part.powder_data.powder_transfer_efficiency = self.spinbox_powder_transfer_efficiency.value()
        self.laser_cut_part.paint_data.paint_name = self.combobox_paint_color.currentText()
        self.laser_cut_part.paint_data.paint_item = self.paint_inventory.get_paint(self.laser_cut_part.paint_data.paint_name)
        self.laser_cut_part.primer_data.primer_name = self.combobox_primer.currentText()
        self.laser_cut_part.primer_data.primer_item = self.paint_inventory.get_primer(self.laser_cut_part.primer_data.primer_name)
        self.laser_cut_part.powder_data.powder_name = self.combobox_powder_coating_color.currentText()
        self.laser_cut_part.powder_data.powder_item = self.paint_inventory.get_powder(self.laser_cut_part.powder_data.powder_name)

        self.parent.resizeColumnsToContents()

        self.settingsChanged.emit()
