from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.items_change_quantity_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.settings import Settings

settings_file = Settings()


class ItemsChangeQuantityDialog(QDialog, Ui_Form):
    def __init__(
        self,
        title,
        add_or_remove: str,
        items: list[Component] | list[LaserCutPart],
        parent=None,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.title = title
        self.items = items
        self.add_or_remove = add_or_remove

        settings_file.load_data()

        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        if self.add_or_remove == "ADD":
            self.pushButton_remove.setHidden(True)
        else:
            self.pushButton_add.setHidden(True)

        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_remove.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        if self.items:
            self.pushButton_category.clicked.connect(
                lambda: (
                    self.pushButton_item.setChecked(False),
                    self.quantity_changed(),
                )
            )
            self.pushButton_item.clicked.connect(
                lambda: (
                    self.pushButton_category.setChecked(False),
                    self.quantity_changed(),
                )
            )
        else:
            self.pushButton_item.setEnabled(False)
            self.pushButton_item.setChecked(False)
            self.pushButton_category.setChecked(True)
            self.pushButton_category.clicked.connect(self.quantity_changed)
            self.label_component_selected.setText("* You don't have any items selected.")

        self.pushButton_category.setChecked(False)
        self.pushButton_item.setChecked(False)

        self.doubleSpinBox_quantity.valueChanged.connect(self.quantity_changed)
        self.quantity_changed()

    def quantity_changed(self):
        self.pushButton_add.setEnabled(self.doubleSpinBox_quantity.value() > 0 and (self.pushButton_item.isChecked() or self.pushButton_category.isChecked()))
        self.pushButton_remove.setEnabled(self.doubleSpinBox_quantity.value() > 0 and (self.pushButton_item.isChecked() or self.pushButton_category.isChecked()))
        if self.pushButton_category.isChecked():
            self.lblMessage.setText(f"Before proceeding, it is important to confirm your intention to {self.add_or_remove} quantities.\n\nEach item in {self.title} will {self.add_or_remove} a multiple of {self.doubleSpinBox_quantity.value()} quantities with respect to its unit quantity.\n\nKindly ensure the accuracy of your decision.")
        elif self.pushButton_item.isChecked() and self.items:
            items_string = "\n"
            for i, item in enumerate(self.items):
                if self.add_or_remove == "ADD":
                    items_string += f"  {i+1}. {item.part_name if isinstance(item, Component) else item.name}\n\twill go from {item.quantity} to {item.quantity + self.doubleSpinBox_quantity.value()}\n"
                elif self.add_or_remove == "REMOVE":
                    items_string += f"  {i+1}. {item.part_name if isinstance(item, Component) else item.name}\n\twill go from {item.quantity} to {item.quantity - self.doubleSpinBox_quantity.value()}\n"
            self.lblMessage.setText(
                f'Before proceeding, it is important to confirm your intention to {self.add_or_remove} quantities.\n\nFor each of the selected {len(self.items)} items {self.doubleSpinBox_quantity.value()} quantities will be {"ADDED" if self.add_or_remove == "ADD" else "REMOVED"}:{items_string}\nKindly ensure the accuracy of your decision.'
            )
        if self.doubleSpinBox_quantity.value() == 0:
            self.lblMessage.setText("Nothing will happen since quantity is set to zero.")
        if not self.pushButton_category.isChecked() and not self.items:
            self.lblMessage.setText("Nothing will happen since no option is selected.")
        if not self.pushButton_category.isChecked() and not self.pushButton_item.isChecked():
            self.lblMessage.setText("Nothing will happen since no option is selected.")

    def get_multiplier(self) -> float:
        return self.doubleSpinBox_quantity.value()

    def get_option(self) -> str:
        return "Item" if self.pushButton_item.isChecked() else "Category"
