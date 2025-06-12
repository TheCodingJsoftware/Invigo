from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.edit_category_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.inventory.category import Category
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.sheets_inventory import SheetSettings


class EditCategoryDialog(QDialog, Ui_Form):
    def __init__(
        self,
        title,
        message,
        placeholder_text,
        category: Category,
        inventory: ComponentsInventory | SheetSettings | LaserCutInventory,
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.inputText: str | int = ""
        self.category = category
        self.inventory = inventory

        self.action: str = ""
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.setWindowTitle(title)
        self.lblMessage.setText(message)
        self.lineEditInput.setText(str(placeholder_text))
        self.lineEditInput.setPlaceholderText(message)

        self.pushButton_delete.clicked.connect(self.delete)
        self.pushButton_duplicate.clicked.connect(self.duplicate)
        self.pushButton_rename.clicked.connect(self.rename)
        self.pushButton_cancel.clicked.connect(self.cancel)

        self.lineEditInput.selectAll()

    def delete(self):
        self.action = "DELETE"
        self.accept()

    def duplicate(self):
        self.action = "DUPLICATE"
        self.accept()

    def rename(self):
        self.action = "RENAME"
        self.accept()

    def cancel(self):
        self.reject()
