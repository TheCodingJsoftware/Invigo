from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog

from ui.dialogs.update_dialog_UI import Ui_Form
from ui.icons import Icons


class UpdateDialog(QDialog, Ui_Form):
    def __init__(self, parent, current_version: str, new_version: str, update_notes: str):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent

        self.setWindowTitle("New Update Available")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        pixmap = QPixmap(Icons.invigo_icon)
        scaled_pixmap = pixmap.scaled(self.label_icon.size(), Qt.AspectRatioMode.KeepAspectRatio)

        self.label_icon.setFixedSize(128, 128)
        self.label_icon.setPixmap(scaled_pixmap)

        self.label_version.setText(f"Current Version: {current_version}\nNew Version: {new_version}")
        self.label_update_notes.setText(update_notes)

        self.scrollArea.setStyleSheet("border: 0px")

        self.pushButton_update.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)
