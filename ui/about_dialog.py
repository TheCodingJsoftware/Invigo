from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog


class AboutDialog(QDialog):
    def __init__(self, parent, version: str, updated: str, home: str) -> None:
        super(AboutDialog, self).__init__(parent)
        uic.loadUi("ui/about_dialog.ui", self)
        self.parent = parent

        self.setWindowTitle("Invigo")
        self.setWindowIcon(QIcon("icons/icon.png"))
        self.setFixedSize(600, 500)

        pixmap = QPixmap("icons/icon.png")
        scaled_pixmap = pixmap.scaled(self.lblIcon.size(), Qt.AspectRatioMode.KeepAspectRatio)

        self.lblIcon.setFixedSize(128, 128)
        self.lblIcon.setPixmap(scaled_pixmap)

        self.lblVersion.setText(f"Build time: {updated}")

        with open("LICENSE", "r", encoding="utf-8") as license_file:
            self.lblLicense.setText(license_file.read())

        self.lblTitle.setText(f"{version}")

        self.lblHome.setText(f"Home: <a style='text-decoration:none;color:yellow'href='{home}'>{home}</a>")

        self.scrollArea.setStyleSheet("border: 0px")

        self.btnClose.clicked.connect(self.close)
