import qdarktheme
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton

from json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class LicenseDialog(QDialog):
    """
    License dialog
    """

    def __init__(self):
        super(LicenseDialog, self).__init__()
        uic.loadUi("ui/license.ui", self)
        self.setWindowTitle("License")

        self.setWindowIcon(QIcon("icons/icon.png"))
        self.lblIcon.setFixedSize(128, 128)

        pixmap = QPixmap("icons/icon.png")
        myScaledPixmap = pixmap.scaled(self.lblIcon.size(), Qt.KeepAspectRatio)

        self.lblIcon.setPixmap(myScaledPixmap)
        self.licenseText = self.findChild(QLabel, "label_2")

        with open("LICENSE", "r") as f:
            self.licenseText.setText(f.read())

        self.btnClose.clicked.connect(self.close)

        self.setFixedSize(780, 470)
        if settings_file.get_value(item_name="dark_mode"):
            self.dark_mode()
        else:
            self.light_mode()

    def dark_mode(self) -> None:
        self.setStyleSheet(qdarktheme.load_stylesheet())

    def light_mode(self) -> None:
        self.setStyleSheet(qdarktheme.load_stylesheet("light"))
