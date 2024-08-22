from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog

from ui.dialogs.about_dialog_UI import Ui_Form
from ui.icons import Icons


class AboutDialog(QDialog, Ui_Form):
    def __init__(self, parent, version: str, home: str):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent

        self.setWindowTitle("Invigo")
        self.setWindowIcon(QIcon(Icons.invigo_icon))
        self.setFixedSize(600, 500)

        pixmap = QPixmap(Icons.invigo_icon)
        scaled_pixmap = pixmap.scaled(self.lblIcon.size(), Qt.AspectRatioMode.KeepAspectRatio)

        self.lblIcon.setFixedSize(128, 128)
        self.lblIcon.setPixmap(scaled_pixmap)

        with open("LICENSE", "r", encoding="utf-8") as license_file:
            self.lblLicense.setText(license_file.read())

        self.lblTitle.setText(f"{version}")

        self.lblHome.setText(f"Home: <a style='text-decoration:none;color:yellow'href='{home}'>{home}</a>")

        self.scrollArea.setStyleSheet("border: 0px")

        self.btnClose.clicked.connect(self.close)
