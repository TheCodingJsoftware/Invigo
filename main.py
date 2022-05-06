__author__ = "Jared Gross"
__copyright__ = "Copyright 2022, TheCodingJ's"
__credits__: "list[str]" = ["Jared Gross"]
__license__ = "MIT"
__name__ = "Inventory Manager"
__version__ = "v0.0.1"
__updated__ = "2022-05-05 21:33:33"
__maintainer__ = "Jared Gross"
__email__ = "jared@pinelandfarms.ca"
__status__ = "Production"

import os
import socket
import sys
import urllib
import urllib.request
from datetime import datetime, timedelta
from functools import partial

import qdarktheme
import requests
from PyQt5 import uic
from PyQt5.QtCore import (
    QCoreApplication,
    QProcess,
    QRunnable,
    QSettings,
    Qt,
    QThreadPool,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QFont, QIcon, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QDialog,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
    qApp,
)

import license_menu
from json_file import JsonFile
from upload_thread import UploadThread

settings_file = JsonFile(file_name="settings")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main.ui", self)
        self.setWindowTitle(__name__)
        if settings_file.get_value(item_name="dark_mode"):
            self.setStyleSheet(qdarktheme.load_stylesheet())
        else:
            self.setStyleSheet(qdarktheme.load_stylesheet("light"))
        self.load_ui_elements()
        self.show()

    def load_ui_elements(self) -> None:
        # Action events
        self.actionView_License.triggered.connect(self.show_license_window)
        self.actionCheck_for_Updates.triggered.connect(self.check_for_updates)
        self.actionDarkmode.setChecked(settings_file.get_value(item_name="dark_mode"))
        self.actionDarkmode.triggered.connect(self.toggle_dark_mode)
        self.actionAbout_Qt.triggered.connect(qApp.aboutQt)
        self.actionAbout.triggered.connect(self.show_about_window)

        # Button events
        self.btnUploadChanges.clicked.connect(self.upload_changes)

    def show_license_window(self) -> None:
        self.licenseUI = license_menu.LicenseDialog()
        self.licenseUI.show()

    def show_about_window(self) -> None:
        QMessageBox.information(
            self,
            __name__,
            f"Developed by: TheCodingJ's\nVersion: {__version__}\nDate: {__updated__}",
            QMessageBox.Ok,
            QMessageBox.Ok,
        )

    def show_dialog(self, title: str, message: str) -> None:
        QMessageBox.information(
            self,
            title,
            message,
            QMessageBox.Ok,
            QMessageBox.Ok,
        )

    def toggle_dark_mode(self) -> None:
        settings_file.change_item(
            item_name="dark_mode", new_value=not settings_file.get_value("dark_mode")
        )
        QMessageBox.information(
            self,
            __name__,
            "The program must restart for this to take effect",
            QMessageBox.Ok,
            QMessageBox.Ok,
        )

    # TODO Still needs to be set up for the official gitub repository
    def check_for_updates(self, on_start_up: bool = False) -> None:
        try:
            response = requests.get(
                "https://api.github.com/repos/thecodingjsoftware/HBNI-Audio-Stream-Listener/releases/latest"
            )
            version: str = response.json()["name"].replace(" ", "")
            if version != __version__:
                QMessageBox.information(
                    self,
                    __name__,
                    "There is a new update available",
                    QMessageBox.Ok,
                    QMessageBox.Ok,
                )
            elif not on_start_up:
                QMessageBox.information(
                    self,
                    __name__,
                    "There are currently no updates available.",
                    QMessageBox.Ok,
                    QMessageBox.Ok,
                )
        except Exception as e:
            if not on_start_up:
                QMessageBox.information(
                    self,
                    __name__,
                    f"Error!\n\n{e}",
                    QMessageBox.Ok,
                    QMessageBox.Ok,
                )

    def upload_changes(self):
        self.threads = []
        upload_thread = UploadThread()
        upload_thread.signal.connect(self.data_received)
        self.threads.append(upload_thread)
        upload_thread.start()

    def data_received(self, data):
        if data == "Success":
            self.show_dialog(
                title="Successfully received",
                message=f"{data}\n\nData successfully received.\nWill take roughly 5 minutes to update database",
            )
        else:
            self.show_dialog(
                title="error",
                message=data,
            )


def main() -> None:
    default_settings()
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


def default_settings() -> None:
    check_settings(setting="dark_mode", default_value=False)


def check_settings(setting: str, default_value) -> None:
    if settings_file.get_value(item_name=setting) is None:
        settings_file.add_item(item_name=setting, value=default_value)


# if __name__ == "__main__":
main()
