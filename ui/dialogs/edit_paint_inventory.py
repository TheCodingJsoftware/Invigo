from typing import TYPE_CHECKING

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QMessageBox

from ui.dialogs.color_picker_dialog import ColorPicker
from ui.dialogs.edit_paint_inventory_UI import Ui_Form
from ui.icons import Icons
from utils.inventory.coating_item import CoatingItem, CoatingTypes
from utils.inventory.paint_inventory import PaintInventory
from utils.settings import Settings

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow

settings_file = Settings()


class EditPaintInventory(QDialog, Ui_Form):
    def __init__(self, paint_inventory: PaintInventory, parent):
        super().__init__(parent)
        self.setupUi(self)
        self._parent_widget: MainWindow = parent
        self.paint_inventory = paint_inventory
        self.components_inventory = paint_inventory.components_inventory
        self.selected_color: str = "#ffffff"
        self.selected_item: CoatingItem | None = None

        self.setWindowTitle("Add new paint")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.lineEdit_name.addItems(self.components_inventory.get_all_part_names())
        self.lineEdit_name.setCurrentText("")
        self.lineEdit_name.lineEdit().textChanged.connect(self.name_changed)

        self.pushButton_set_color.setStyleSheet(
            f"QPushButton{{background-color: {self.selected_color}}}"
        )
        self.pushButton_set_color.clicked.connect(self.get_color)

        self.pushButton_add.clicked.connect(self.add_item)
        self.pushButton_apply.clicked.connect(self.apply_changes)
        self.pushButton_close.clicked.connect(self.close)

        self.listWidget_primers.doubleClicked.connect(self.delete_primer)
        self.listWidget_primers.itemSelectionChanged.connect(self.primer_changed)
        self.listWidget_paints.doubleClicked.connect(self.delete_paint)
        self.listWidget_paints.itemSelectionChanged.connect(self.paint_changed)
        self.listWidget_powders.doubleClicked.connect(self.delete_powder)
        self.listWidget_powders.itemSelectionChanged.connect(self.powder_changed)

        self.load_inventory()

    def load_inventory(self):
        self.block_list_widget_signals(True)
        self.listWidget_primers.clear()
        self.listWidget_paints.clear()
        self.listWidget_powders.clear()
        self.listWidget_primers.addItems(self.paint_inventory.get_all_primers())
        self.listWidget_paints.addItems(self.paint_inventory.get_all_paints())
        self.listWidget_powders.addItems(self.paint_inventory.get_all_powders())
        self.block_list_widget_signals(False)

    def block_list_widget_signals(self, block_signals):
        self.listWidget_primers.blockSignals(block_signals)
        self.listWidget_paints.blockSignals(block_signals)
        self.listWidget_powders.blockSignals(block_signals)

    def get_color(self):
        color = ColorPicker(self)
        color.show()
        if color.exec():
            self.selected_color = color.getHex(True)
            self.pushButton_set_color.setStyleSheet(
                f"QPushButton{{background-color: {self.selected_color}}}"
            )

    def primer_changed(self):
        self.label_5.setText("Price per gallon:")
        self.doubleSpinBox_gravity.setEnabled(False)
        self.doubleSpinBox_average_coverage.setEnabled(True)

        self.listWidget_paints.blockSignals(True)
        self.listWidget_powders.blockSignals(True)
        self.listWidget_paints.clearSelection()
        self.listWidget_powders.clearSelection()
        self.listWidget_paints.blockSignals(False)
        self.listWidget_powders.blockSignals(False)
        if selected_item := self.listWidget_primers.currentItem():
            if primer := self.paint_inventory.get_primer(selected_item.text()):
                self.lineEdit_name.setCurrentText(primer.part_name)
                self.comboBox_type.setCurrentText(CoatingTypes.PRIMER.value)
                self.selected_color = primer.color
                self.pushButton_set_color.setStyleSheet(
                    f"QPushButton{{background-color: {primer.color}}}"
                )
                self.doubleSpinBox_gravity.setValue(0.0)
                self.doubleSpinBox_average_coverage.setValue(primer.average_coverage)
                self.pushButton_add.setEnabled(False)
                self.pushButton_apply.setEnabled(True)
                self.selected_item = primer

    def delete_primer(self):
        if selected_item := self.listWidget_primers.currentItem():
            if primer := self.paint_inventory.get_primer(selected_item.text()):
                msg = QMessageBox(
                    QMessageBox.Icon.Question,
                    "Are you sure",
                    f"Are you sure you want to delete: {primer.part_name}?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    self,
                )
                response = msg.exec()
                if response == QMessageBox.StandardButton.Yes:
                    self.paint_inventory.remove_primer(primer)
                    self.save_and_apply()

    def paint_changed(self):
        self.label_5.setText("Price per gallon:")
        self.doubleSpinBox_gravity.setEnabled(False)
        self.doubleSpinBox_average_coverage.setEnabled(True)

        self.listWidget_primers.blockSignals(True)
        self.listWidget_powders.blockSignals(True)
        self.listWidget_primers.clearSelection()
        self.listWidget_powders.clearSelection()
        self.listWidget_primers.blockSignals(False)
        self.listWidget_powders.blockSignals(False)
        if selected_item := self.listWidget_paints.currentItem():
            if paint := self.paint_inventory.get_paint(selected_item.text()):
                self.lineEdit_name.setCurrentText(paint.part_name)
                self.comboBox_type.setCurrentText(CoatingTypes.PAINT.value)
                self.selected_color = paint.color
                self.pushButton_set_color.setStyleSheet(
                    f"QPushButton{{background-color: {paint.color}}}"
                )
                self.doubleSpinBox_gravity.setValue(0.0)
                self.doubleSpinBox_average_coverage.setValue(paint.average_coverage)
                self.pushButton_add.setEnabled(False)
                self.pushButton_apply.setEnabled(True)
                self.selected_item = paint

    def delete_paint(self):
        if selected_item := self.listWidget_paints.currentItem():
            if paint := self.paint_inventory.get_paint(selected_item.text()):
                msg = QMessageBox(
                    QMessageBox.Icon.Question,
                    "Are you sure",
                    f"Are you sure you want to delete: {paint.part_name}?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    self,
                )
                response = msg.exec()
                if response == QMessageBox.StandardButton.Yes:
                    self.paint_inventory.remove_paint(paint)
                    self.save_and_apply()

    def powder_changed(self):
        self.label_5.setText("Price per pound:")
        self.doubleSpinBox_gravity.setEnabled(True)
        self.doubleSpinBox_average_coverage.setEnabled(False)

        self.listWidget_primers.blockSignals(True)
        self.listWidget_paints.blockSignals(True)
        self.listWidget_primers.clearSelection()
        self.listWidget_paints.clearSelection()
        self.listWidget_primers.blockSignals(False)
        self.listWidget_paints.blockSignals(False)
        if selected_item := self.listWidget_powders.currentItem():
            if powder := self.paint_inventory.get_powder(selected_item.text()):
                self.lineEdit_name.setCurrentText(powder.part_name)
                self.comboBox_type.setCurrentText(CoatingTypes.POWDER.value)
                self.selected_color = powder.color
                self.pushButton_set_color.setStyleSheet(
                    f"QPushButton{{background-color: {powder.color}}}"
                )
                self.doubleSpinBox_gravity.setValue(powder.gravity)
                self.doubleSpinBox_average_coverage.setValue(0.0)
                self.pushButton_add.setEnabled(False)
                self.pushButton_apply.setEnabled(True)
                self.selected_item = powder

    def delete_powder(self):
        if selected_item := self.listWidget_powders.currentItem():
            if powder := self.paint_inventory.get_powder(selected_item.text()):
                msg = QMessageBox(
                    QMessageBox.Icon.Question,
                    "Are you sure",
                    f"Are you sure you want to delete: {powder.part_name}?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    self,
                )
                response = msg.exec()
                if response == QMessageBox.StandardButton.Yes:
                    self.paint_inventory.remove_powder(powder)
                    self.save_and_apply()

    def save_and_apply(self):
        self.paint_inventory.save()
        self.load_inventory()
        self.sync_changes()

    def apply_changes(self):
        if not self.selected_item:
            return
        self.selected_item.color = self.selected_color
        if self.comboBox_type.currentText() == CoatingTypes.PRIMER.value:
            self.selected_item.average_coverage = (
                self.doubleSpinBox_average_coverage.value()
            )
            if self.selected_item.COATING_TYPE == CoatingTypes.PAINT:
                self.paint_inventory.remove_paint(self.selected_item)
                new = CoatingItem(
                    self.selected_item.to_dict(),
                    self.paint_inventory,
                )
                new.COATING_TYPE = CoatingTypes.PRIMER
                self.paint_inventory.add_primer(new)
                self.save_and_apply()
            elif self.selected_item.COATING_TYPE == CoatingTypes.POWDER:
                self.paint_inventory.remove_powder(self.selected_item)
                new = CoatingItem(
                    self.selected_item.to_dict(),
                    self.paint_inventory,
                )
                new.COATING_TYPE = CoatingTypes.PRIMER
                self.paint_inventory.add_primer(new)
                self.save_and_apply()
            for row in range(self.listWidget_primers.count()):
                if (
                    self.listWidget_primers.item(row).text()
                    == self.selected_item.part_name
                ):
                    self.listWidget_primers.setCurrentRow(row)
        elif self.comboBox_type.currentText() == CoatingTypes.PAINT.value:
            self.selected_item.average_coverage = (
                self.doubleSpinBox_average_coverage.value()
            )
            if self.selected_item.COATING_TYPE == CoatingTypes.PRIMER:
                self.paint_inventory.remove_primer(self.selected_item)
                new = CoatingItem(
                    self.selected_item.to_dict(),
                    self.paint_inventory,
                )
                new.COATING_TYPE = CoatingTypes.PAINT
                self.paint_inventory.add_paint(new)
                self.save_and_apply()
            elif self.selected_item.COATING_TYPE == CoatingTypes.POWDER:
                self.paint_inventory.remove_powder(self.selected_item)
                new = CoatingItem(
                    self.selected_item.to_dict(),
                    self.paint_inventory,
                )
                new.COATING_TYPE = CoatingTypes.PAINT
                self.paint_inventory.add_paint(new)
                self.save_and_apply()
            for row in range(self.listWidget_paints.count()):
                if (
                    self.listWidget_paints.item(row).text()
                    == self.selected_item.part_name
                ):
                    self.listWidget_paints.setCurrentRow(row)
        elif self.comboBox_type.currentText() == CoatingTypes.POWDER.value:
            self.selected_item.gravity = self.doubleSpinBox_gravity.value()
            if self.selected_item.COATING_TYPE == CoatingTypes.PRIMER:
                self.paint_inventory.remove_primer(self.selected_item)
                new = CoatingItem(
                    self.selected_item.to_dict(),
                    self.paint_inventory,
                )
                new.COATING_TYPE = CoatingTypes.POWDER
                self.paint_inventory.add_powder(new)
                self.save_and_apply()
            elif self.selected_item.COATING_TYPE == CoatingTypes.PAINT:
                self.paint_inventory.remove_paint(self.selected_item)
                new = CoatingItem(
                    self.selected_item.to_dict(),
                    self.paint_inventory,
                )
                new.COATING_TYPE = CoatingTypes.POWDER
                self.paint_inventory.add_powder(new)
                self.save_and_apply()
            for row in range(self.listWidget_powders.count()):
                if (
                    self.listWidget_powders.item(row).text()
                    == self.selected_item.part_name
                ):
                    self.listWidget_powders.setCurrentRow(row)

        self.save_and_apply()

    def add_item(self):
        if item := self.components_inventory.get_component_by_part_name(
            self.lineEdit_name.currentText()
        ):
            if self.comboBox_type.currentText() == CoatingTypes.PRIMER.value:
                primer = CoatingItem(
                    {
                        "name": item.part_name,
                        "color": self.selected_color,
                        "categories": [CoatingTypes.PRIMER.value],
                        "coating_type": CoatingTypes.PRIMER.value,
                    },
                    self.paint_inventory,
                )
                self.paint_inventory.add_primer(primer)
                self.save_and_apply()
                for row in range(self.listWidget_primers.count()):
                    if self.listWidget_primers.item(row).text() == primer.part_name:
                        self.listWidget_primers.setCurrentRow(row)
            elif self.comboBox_type.currentText() == CoatingTypes.PAINT.value:
                paint = CoatingItem(
                    {
                        "name": item.part_name,
                        "color": self.selected_color,
                        "categories": [CoatingTypes.PAINT.value],
                        "coating_type": CoatingTypes.PAINT.value,
                    },
                    self.paint_inventory,
                )
                self.paint_inventory.add_paint(paint)
                self.save_and_apply()
                for row in range(self.listWidget_paints.count()):
                    if self.listWidget_paints.item(row).text() == paint.part_name:
                        self.listWidget_paints.setCurrentRow(row)
            elif self.comboBox_type.currentText() == CoatingTypes.POWDER.value:
                powder = CoatingItem(
                    {
                        "name": item.part_name,
                        "color": self.selected_color,
                        "categories": [CoatingTypes.POWDER.value],
                        "coating_type": CoatingTypes.POWDER.value,
                    },
                    self.paint_inventory,
                )
                self.paint_inventory.add_powder(powder)
                self.save_and_apply()
                for row in range(self.listWidget_powders.count()):
                    if self.listWidget_powders.item(row).text() == powder.part_name:
                        self.listWidget_powders.setCurrentRow(row)
        else:
            msg = QMessageBox(
                QMessageBox.Icon.Warning,
                "Could not find component",
                f"Could not find the component: {self.lineEdit_name.currentText()} in components inventory.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()

    def autofill(self):
        for component in self.components_inventory.components:
            if component.part_name == self.lineEdit_name.currentText():
                self.lineEdit_name.setCurrentText(component.name)
                self.doubleSpinBox_price.setValue(component.price)

    def name_changed(self):
        for component in self.components_inventory.components:
            if component.part_name == self.lineEdit_name.currentText():
                self.pushButton_autofill.setEnabled(True)
                self.pushButton_add.setEnabled(True)
                self.pushButton_apply.setEnabled(False)
                self.doubleSpinBox_price.setValue(component.price)
                break
            else:
                self.pushButton_autofill.setEnabled(False)
                self.pushButton_add.setEnabled(False)
                self.pushButton_apply.setEnabled(False)

        does_exist = False

        if not does_exist:
            for primer in self.paint_inventory.primers:
                if primer.part_name == self.lineEdit_name.currentText():
                    does_exist = True
        if not does_exist:
            for paint in self.paint_inventory.paints:
                if paint.part_name == self.lineEdit_name.currentText():
                    does_exist = True
        if not does_exist:
            for powder in self.paint_inventory.powders:
                if powder.part_name == self.lineEdit_name.currentText():
                    does_exist = True

        self.pushButton_apply.setEnabled(does_exist)
        self.pushButton_add.setEnabled(not does_exist)

    def get_name(self) -> str:
        return self.lineEdit_name.currentText().encode("ascii", "ignore").decode()

    def sync_changes(self):
        self._parent_widget.upload_files(
            [
                "paint_inventory.json",
            ],
        )
