from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog


class MessageDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        parent,
    ):
        super().__init__(parent)
        uic.loadUi("ui/dialogs/message_dialog.ui", self)

        self.setWindowTitle(title)
        self.setWindowIcon(QIcon("icons/icon.png"))
        self.label_message.setText(message)
