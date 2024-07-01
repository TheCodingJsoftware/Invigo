from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QVBoxLayout, QWidget

from ui.custom.assembly_paint_settings_widget import \
    AssemblyPaintSettingsWidget
from utils.workspace.assembly import Assembly


class AssemblyPaintWidget(QWidget):
    settingsChanged = pyqtSignal()

    def __init__(self, assembly: Assembly, paint_settings_widget: AssemblyPaintSettingsWidget, parent) -> None:
        super(AssemblyPaintWidget, self).__init__(parent)
        self.parent = parent

        self.assembly = assembly
        self.paint_settings_widget = paint_settings_widget

        layout = QVBoxLayout(self)

        self.checkbox_primer = QCheckBox("Primer", self)
        self.checkbox_primer.setChecked(self.assembly.uses_primer)
        self.checkbox_primer.checkStateChanged.connect(self.update_paint)
        self.checkbox_paint = QCheckBox("Paint", self)
        self.checkbox_paint.setChecked(self.assembly.uses_paint)
        self.checkbox_paint.checkStateChanged.connect(self.update_paint)
        self.checkbox_powder = QCheckBox("Powder", self)
        self.checkbox_powder.setChecked(self.assembly.uses_powder)
        self.checkbox_powder.checkStateChanged.connect(self.update_paint)

        layout.addWidget(self.checkbox_primer)
        layout.addWidget(self.checkbox_paint)
        layout.addWidget(self.checkbox_powder)

        self.setLayout(layout)

        self.paint_settings_widget.widget_primer.setVisible(self.assembly.uses_primer)
        self.paint_settings_widget.widget_paint_color.setVisible(self.assembly.uses_paint)
        self.paint_settings_widget.widget_powder_coating.setVisible(self.assembly.uses_powder)
        self.paint_settings_widget.not_painted_label.setVisible(not (self.assembly.uses_primer or self.assembly.uses_paint or self.assembly.uses_powder))

    def update_paint(self):
        self.assembly.uses_primer = self.checkbox_primer.isChecked()
        self.assembly.uses_paint = self.checkbox_paint.isChecked()
        self.assembly.uses_powder = self.checkbox_powder.isChecked()

        self.paint_settings_widget.widget_primer.setVisible(self.assembly.uses_primer)
        self.paint_settings_widget.widget_paint_color.setVisible(self.assembly.uses_paint)
        self.paint_settings_widget.widget_powder_coating.setVisible(self.assembly.uses_powder)
        self.paint_settings_widget.not_painted_label.setVisible(not (self.assembly.uses_primer or self.assembly.uses_paint or self.assembly.uses_powder))

        self.settingsChanged.emit()
