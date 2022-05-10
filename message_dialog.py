from PyQt5 import QtSvg, uic
from PyQt5.QtCore import QFile, Qt, QTextStream
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget

from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class MessageDialog(QWidget):
    """
    Message dialog
    """

    def __init__(self, icon_name: str, title: str, message: str):
        super(MessageDialog, self).__init__()
        uic.loadUi("ui/message_dialog.ui", self)

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.lblTitle.setText(title)
        self.lblMessage.setText(message)
        self.btnClose.clicked.connect(self.close)

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        self.load_theme()

    def load_theme(self):
        theme: str = "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        stylesheet_file = QFile(f"ui/BreezeStyleSheets/dist/qrc/{theme}/stylesheet.qss")
        stylesheet_file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(stylesheet_file)
        self.setStyleSheet(stream.readAll())

    def get_icon(self, path_to_icon: str) -> QtSvg.QSvgWidget:
        theme: str = "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        return QtSvg.QSvgWidget(f"ui/BreezeStyleSheets/dist/pyqt6/{theme}/{path_to_icon}")
