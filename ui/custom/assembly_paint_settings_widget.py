from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QWidget

from utils.workspace.assembly import Assembly


class AssemblyPaintSettingsWidget(QWidget):
    settingsChanged = pyqtSignal()

    def __init__(self, assembly: Assembly, parent) -> None:
        super(AssemblyPaintSettingsWidget, self).__init__(parent)
        self.parent = parent
        self.assembly = assembly
        self.paint_inventory = self.assembly.paint_inventory

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
        if self.assembly.primer_name:
            self.combobox_primer.setCurrentText(self.assembly.primer_name)
        self.combobox_primer.currentTextChanged.connect(self.update_paint_settings)
        self.spinbox_primer_overspray = QDoubleSpinBox(self.widget_primer)
        self.spinbox_primer_overspray.wheelEvent = lambda event: None
        self.spinbox_primer_overspray.setValue(self.assembly.primer_overspray)
        self.spinbox_primer_overspray.setMaximum(100.0)
        self.spinbox_primer_overspray.setSuffix("%")
        self.spinbox_primer_overspray.textChanged.connect(self.update_paint_settings)
        self.primer_layout.addWidget(QLabel("Primer:", self.widget_primer), 0, 0)
        self.primer_layout.addWidget(self.combobox_primer, 1, 0)
        self.primer_layout.addWidget(QLabel("Overspray:", self.widget_primer), 0, 1)
        self.primer_layout.addWidget(self.spinbox_primer_overspray, 1, 1)
        self.widget_primer.setVisible(self.assembly.uses_primer)
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
        if self.assembly.paint_name:
            self.combobox_paint_color.setCurrentText(self.assembly.paint_name)
        self.combobox_paint_color.currentTextChanged.connect(self.update_paint_settings)
        self.spinbox_paint_overspray = QDoubleSpinBox(self.widget_paint_color)
        self.spinbox_paint_overspray.wheelEvent = lambda event: None
        self.spinbox_paint_overspray.setValue(self.assembly.paint_overspray)
        self.spinbox_paint_overspray.setMaximum(100.0)
        self.spinbox_paint_overspray.setSuffix("%")
        self.spinbox_paint_overspray.textChanged.connect(self.update_paint_settings)
        self.paint_color_layout.addWidget(QLabel("Paint:", self.widget_paint_color), 0, 0)
        self.paint_color_layout.addWidget(self.combobox_paint_color, 1, 0)
        self.paint_color_layout.addWidget(QLabel("Overspray:", self.widget_paint_color), 0, 1)
        self.paint_color_layout.addWidget(self.spinbox_paint_overspray, 1, 1)
        self.widget_paint_color.setVisible(self.assembly.uses_paint)
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
        if self.assembly.powder_name:
            self.combobox_powder_coating_color.setCurrentText(self.assembly.powder_name)
        self.combobox_powder_coating_color.currentTextChanged.connect(self.update_paint_settings)
        self.spinbox_powder_transfer_efficiency = QDoubleSpinBox(self.widget_powder_coating)
        self.spinbox_powder_transfer_efficiency.wheelEvent = lambda event: None
        self.spinbox_powder_transfer_efficiency.setValue(self.assembly.powder_transfer_efficiency)
        self.spinbox_powder_transfer_efficiency.setMaximum(100.0)
        self.spinbox_powder_transfer_efficiency.setSuffix("%")
        self.spinbox_powder_transfer_efficiency.textChanged.connect(self.update_paint_settings)
        self.powder_coating_layout.addWidget(QLabel("Powder:", self.widget_powder_coating), 0, 0)
        self.powder_coating_layout.addWidget(self.combobox_powder_coating_color, 1, 0)
        self.powder_coating_layout.addWidget(QLabel("Transfer eff:", self.widget_powder_coating), 0, 1)
        self.powder_coating_layout.addWidget(self.spinbox_powder_transfer_efficiency, 1, 1)
        self.widget_powder_coating.setVisible(self.assembly.uses_powder)
        self.paint_settings_layout.addWidget(self.widget_powder_coating)

        self.setLayout(self.paint_settings_layout)

    def update_paint_settings(self):
        self.assembly.primer_overspray = self.spinbox_primer_overspray.value()
        self.assembly.paint_overspray = self.spinbox_paint_overspray.value()
        self.assembly.powder_transfer_efficiency = self.spinbox_powder_transfer_efficiency.value()
        self.assembly.paint_name = self.combobox_paint_color.currentText()
        self.assembly.primer_name = self.combobox_primer.currentText()
        self.assembly.powder_name = self.combobox_powder_coating_color.currentText()

        self.settingsChanged.emit()
