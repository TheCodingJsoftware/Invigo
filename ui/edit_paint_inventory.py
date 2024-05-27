from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QComboBox, QDialog, QDoubleSpinBox, QListWidget, QMessageBox, QPushButton

from ui.color_picker_dialog import ColorPicker
from utils.paint_inventory.paint import Paint
from utils.paint_inventory.paint_inventory import PaintInventory
from utils.paint_inventory.powder import Powder
from utils.paint_inventory.primer import Primer
from utils.settings import Settings

settings_file = Settings()


class EditPaintInventory(QDialog):
    def __init__(self, paint_inventory: PaintInventory, parent) -> None:
        super(EditPaintInventory, self).__init__(parent)
        uic.loadUi("ui/edit_paint_inventory.ui", self)
        self.parent = parent
        self.paint_inventory = paint_inventory
        self.components_inventory = paint_inventory.components_inventory
        self.selected_color: str = "#ffffff"
        self.selected_item: Primer | Paint | Powder = None

        self.setWindowTitle("Add new paint")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lineEdit_name = self.findChild(QComboBox, "lineEdit_name")
        self.lineEdit_name.addItems(self.components_inventory.get_all_part_names())
        self.lineEdit_name.setCurrentText("")
        self.lineEdit_name.lineEdit().textChanged.connect(self.name_changed)

        self.comboBox_type = self.findChild(QComboBox, "comboBox_type")

        self.doubleSpinBox_average_coverage = self.findChild(QDoubleSpinBox, "doubleSpinBox_average_coverage")
        self.doubleSpinBox_gravity = self.findChild(QDoubleSpinBox, "doubleSpinBox_gravity")

        self.pushButton_set_color = self.findChild(QPushButton, "pushButton_set_color")
        self.pushButton_set_color.setStyleSheet(f"QPushButton{{background-color: {self.selected_color}}}")
        self.pushButton_set_color.clicked.connect(self.get_color)

        self.pushButton_add = self.findChild(QPushButton, "pushButton_add")
        self.pushButton_add.clicked.connect(self.add_item)

        self.pushButton_apply = self.findChild(QPushButton, "pushButton_apply")
        self.pushButton_apply.clicked.connect(self.apply_changes)

        self.listWidget_primers = self.findChild(QListWidget, "listWidget_primers")
        self.listWidget_primers.doubleClicked.connect(self.delete_primer)
        self.listWidget_primers.itemSelectionChanged.connect(self.primer_changed)
        self.listWidget_paints = self.findChild(QListWidget, "listWidget_paints")
        self.listWidget_paints.doubleClicked.connect(self.delete_paint)
        self.listWidget_paints.itemSelectionChanged.connect(self.paint_changed)
        self.listWidget_powders = self.findChild(QListWidget, "listWidget_powders")
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
            self.pushButton_set_color.setStyleSheet(f"QPushButton{{background-color: {self.selected_color}}}")

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
                self.lineEdit_name.setCurrentText(primer.name)
                self.comboBox_type.setCurrentText("Primer")
                self.selected_color = primer.color
                self.pushButton_set_color.setStyleSheet(f"QPushButton{{background-color: {primer.color}}}")
                self.doubleSpinBox_gravity.setValue(0.0)
                self.doubleSpinBox_average_coverage.setValue(primer.average_coverage)
                self.pushButton_add.setEnabled(False)
                self.pushButton_apply.setEnabled(True)
                self.selected_item = primer

    def delete_primer(self):
        if selected_item := self.listWidget_primers.currentItem():
            if primer := self.paint_inventory.get_primer(selected_item.text()):
                msg = QMessageBox(QMessageBox.Icon.Question, "Are you sure", f"Are you sure you want to delete: {primer.name}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel, self)
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
                self.lineEdit_name.setCurrentText(paint.name)
                self.comboBox_type.setCurrentText("Paint")
                self.selected_color = paint.color
                self.pushButton_set_color.setStyleSheet(f"QPushButton{{background-color: {paint.color}}}")
                self.doubleSpinBox_gravity.setValue(0.0)
                self.doubleSpinBox_average_coverage.setValue(paint.average_coverage)
                self.pushButton_add.setEnabled(False)
                self.pushButton_apply.setEnabled(True)
                self.selected_item = paint

    def delete_paint(self):
        if selected_item := self.listWidget_paints.currentItem():
            if paint := self.paint_inventory.get_paint(selected_item.text()):
                msg = QMessageBox(QMessageBox.Icon.Question, "Are you sure", f"Are you sure you want to delete: {paint.name}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel, self)
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
                self.lineEdit_name.setCurrentText(powder.name)
                self.comboBox_type.setCurrentText("Powder")
                self.selected_color = powder.color
                self.pushButton_set_color.setStyleSheet(f"QPushButton{{background-color: {powder.color}}}")
                self.doubleSpinBox_gravity.setValue(powder.gravity)
                self.doubleSpinBox_average_coverage.setValue(0.0)
                self.pushButton_add.setEnabled(False)
                self.pushButton_apply.setEnabled(True)
                self.selected_item = powder

    def delete_powder(self):
        if selected_item := self.listWidget_powders.currentItem():
            if powder := self.paint_inventory.get_powder(selected_item.text()):
                msg = QMessageBox(QMessageBox.Icon.Question, "Are you sure", f"Are you sure you want to delete: {powder.name}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel, self)
                response = msg.exec()
                if response == QMessageBox.StandardButton.Yes:
                    self.paint_inventory.remove_powder(powder)
                    self.save_and_apply()

    def save_and_apply(self):
        self.paint_inventory.save()
        self.load_inventory()
        self.sync_changes()

    def apply_changes(self):
        self.selected_item.color = self.selected_color
        if self.comboBox_type.currentText() == "Primer":
            self.selected_item.average_coverage = self.doubleSpinBox_average_coverage.value()
            if isinstance(self.selected_item, Paint):
                self.paint_inventory.remove_paint(self.selected_item)
                new = Primer(self.selected_item.name, self.selected_item.to_dict(), self.paint_inventory)
                self.paint_inventory.add_primer(new)
            elif isinstance(self.selected_item, Powder):
                self.paint_inventory.remove_powder(self.selected_item)
                new = Primer(self.selected_item.name, self.selected_item.to_dict(), self.paint_inventory)
                self.paint_inventory.add_primer(new)
        elif self.comboBox_type.currentText() == "Paint":
            self.selected_item.average_coverage = self.doubleSpinBox_average_coverage.value()
            if isinstance(self.selected_item, Primer):
                self.paint_inventory.remove_primer(self.selected_item)
                new = Paint(self.selected_item.name, self.selected_item.to_dict(), self.paint_inventory)
                self.paint_inventory.add_paint(new)
            elif isinstance(self.selected_item, Powder):
                self.paint_inventory.remove_powder(self.selected_item)
                new = Paint(self.selected_item.name, self.selected_item.to_dict(), self.paint_inventory)
                self.paint_inventory.add_paint(new)
        elif self.comboBox_type.currentText() == "Powder":
            self.selected_item.gravity = self.doubleSpinBox_gravity.value()
            if isinstance(self.selected_item, Primer):
                self.paint_inventory.remove_primer(self.selected_item)
                new = Powder(self.selected_item.name, self.selected_item.to_dict(), self.paint_inventory)
                self.paint_inventory.add_powder(new)
            elif isinstance(self.selected_item, Paint):
                self.paint_inventory.remove_paint(self.selected_item)
                new = Powder(self.selected_item.name, self.selected_item.to_dict(), self.paint_inventory)
                self.paint_inventory.add_powder(new)
        self.save_and_apply()

    def add_item(self):
        if item := self.components_inventory.get_component_by_part_name(self.lineEdit_name.currentText()):
            if self.comboBox_type.currentText() == "Primer":
                primer = Primer(item.part_name, {"color": self.selected_color, "categories": ["Primer"]}, self.paint_inventory)
                self.paint_inventory.add_primer(primer)
                self.save_and_apply()
            elif self.comboBox_type.currentText() == "Paint":
                paint = Paint(item.part_name, {"color": self.selected_color, "categories": ["Paint"]}, self.paint_inventory)
                self.paint_inventory.add_paint(paint)
                self.save_and_apply()
            elif self.comboBox_type.currentText() == "Powder":
                powder = Powder(item.part_name, {"color": self.selected_color, "categories": ["Powder"]}, self.paint_inventory)
                self.paint_inventory.add_powder(powder)
                self.save_and_apply()
        else:
            msg = QMessageBox(QMessageBox.Icon.Warning, "Could not find component", f"Could not find the component: {self.lineEdit_name.currentText()} in components inventory.", QMessageBox.StandardButton.Ok, self)
            msg.exec()

    def autofill(self) -> None:
        for component in self.components_inventory.components:
            if component.part_name == self.lineEdit_name.currentText():
                self.lineEdit_name.setCurrentText(component.name)
                self.doubleSpinBox_price.setValue(component.price)

    def name_changed(self) -> None:
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
                if primer.name == self.lineEdit_name.currentText():
                    does_exist = True
        if not does_exist:
            for paint in self.paint_inventory.paints:
                if paint.name == self.lineEdit_name.currentText():
                    does_exist = True
        if not does_exist:
            for powder in self.paint_inventory.powders:
                if powder.name == self.lineEdit_name.currentText():
                    does_exist = True

        self.pushButton_apply.setEnabled(does_exist)
        self.pushButton_add.setEnabled(not does_exist)

    def get_name(self) -> str:
        return self.lineEdit_name.currentText().encode("ascii", "ignore").decode()

    def get_exchange_rate(self) -> bool:
        return self.comboBox_exchange_price.currentText() == "USD"

    def get_part_number(self) -> str:
        return self.comboBox_part_number.currentText()

    def get_shelf_number(self) -> str:
        return self.shelf_number

    def sync_changes(self):
        self.parent.sync_changes()
