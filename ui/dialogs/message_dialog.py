from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog

from ui.dialogs.message_dialog_UI import Ui_Dialog
from ui.icons import Icons


class MessageDialog(QDialog, Ui_Dialog):
    def __init__(
        self,
        title: str,
        message: str,
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(Icons.invigo_icon))
        self.label_message.setText(message)
