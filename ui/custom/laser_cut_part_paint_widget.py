from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QVBoxLayout, QWidget

from ui.custom.laser_cut_part_paint_settings_widget import (
    LasserCutPartPaintSettingsWidget,
)
from ui.custom_widgets import CustomTableWidget
from utils.inventory.laser_cut_part import LaserCutPart


class LaserCutPartPaintWidget(QWidget):
    settingsChanged = pyqtSignal()

    def __init__(
        self,
        laser_cut_part: LaserCutPart,
        paint_settings_widget: LasserCutPartPaintSettingsWidget,
        parent: CustomTableWidget,
    ):
        super().__init__(parent)
        self.parent: CustomTableWidget = parent

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

        self.paint_settings_widget.widget_primer.setVisible(
            self.laser_cut_part.uses_primer
        )
        self.paint_settings_widget.widget_paint_color.setVisible(
            self.laser_cut_part.uses_paint
        )
        self.paint_settings_widget.widget_powder_coating.setVisible(
            self.laser_cut_part.uses_powder
        )
        self.paint_settings_widget.not_painted_label.setVisible(
            not (
                self.laser_cut_part.uses_primer
                or self.laser_cut_part.uses_paint
                or self.laser_cut_part.uses_powder
            )
        )

        self.parent.resizeColumnsToContents()

    def update_paint(self):
        self.laser_cut_part.uses_primer = self.checkbox_primer.isChecked()
        self.laser_cut_part.uses_paint = self.checkbox_paint.isChecked()
        self.laser_cut_part.uses_powder = self.checkbox_powder.isChecked()

        self.paint_settings_widget.widget_primer.setVisible(
            self.laser_cut_part.uses_primer
        )
        self.paint_settings_widget.widget_paint_color.setVisible(
            self.laser_cut_part.uses_paint
        )
        self.paint_settings_widget.widget_powder_coating.setVisible(
            self.laser_cut_part.uses_powder
        )
        self.paint_settings_widget.not_painted_label.setVisible(
            not (
                self.laser_cut_part.uses_primer
                or self.laser_cut_part.uses_paint
                or self.laser_cut_part.uses_powder
            )
        )

        self.parent.resizeColumnsToContents()

        self.settingsChanged.emit()
