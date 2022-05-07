# sourcery skip: avoid-builtin-shadow
__author__ = "Jared Gross"
__copyright__ = "Copyright 2022, TheCodingJ's"
__credits__: "list[str]" = ["Jared Gross"]
__license__ = "MIT"
__name__ = "Inventory Manager"
__version__ = "v0.0.1"
__updated__ = "2022-05-06 20:42:50"
__maintainer__ = "Jared Gross"
__email__ = "jared@pinelandfarms.ca"
__status__ = "Production"

import logging
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

import log_config
from download_thread import DownloadThread
from json_file import JsonFile
from license_dialog import LicenseDialog
from upload_thread import UploadThread

settings_file = JsonFile(file_name="settings")


class MainWindow(QMainWindow):
    """
    Main program
    """

    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main.ui", self)
        self.setWindowTitle(__name__)
        self.setWindowIcon(QIcon("icons/icon.png"))

        if settings_file.get_value(item_name="dark_mode"):
            self.setStyleSheet(qdarktheme.load_stylesheet())
        else:
            self.setStyleSheet(qdarktheme.load_stylesheet("light"))
        self.__load_ui()
        self.show()

    def __load_ui(self) -> None:
        # Action events
        # HELP
        self.actionView_License.triggered.connect(self.show_license_window)
        self.actionCheck_for_Updates.triggered.connect(self.check_for_updates)
        self.actionAbout_Qt.triggered.connect(qApp.aboutQt)
        self.actionAbout.triggered.connect(self.show_about_window)
        # SETTINGS
        self.actionDarkmode.setChecked(settings_file.get_value(item_name="dark_mode"))
        self.actionDarkmode.triggered.connect(self.toggle_dark_mode)
        # FILE
        self.actionUpload_Changes.triggered.connect(self.upload_changes)
        self.actionGet_Changes.triggered.connect(self.download_database)
        self.actionExit.triggered.connect(self.close)

    def show_license_window(self) -> None:
        self.dialog = LicenseDialog()
        self.dialog.show()

    def show_about_window(self) -> None:
        self.show_dialog(
            title=__name__,
            message=f"Developed by: TheCodingJ's\nVersion: {__version__}\nDate: {__updated__}",
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
        self.show_dialog(
            title=__name__, message="The program must restart for this to take effect"
        )

    def check_for_updates(self, on_start_up: bool = False) -> None:
        try:
            response = requests.get(
                "https://api.github.com/repos/thecodingjsoftware/Inventory-Manager/releases/latest"
            )
            version: str = response.json()["name"].replace(" ", "")
            if version != __version__:
                self.show_dialog(
                    title=__name__, message="There is a new update available"
                )
            elif not on_start_up:
                self.show_dialog(
                    title=__name__, message="There are currently no updates available."
                )
        except Exception as e:
            if not on_start_up:
                self.show_dialog(title=__name__, message=f"Error\n\n{e}")

    def upload_changes(self):
        self.threads = []
        upload_thread = UploadThread()
        upload_thread.signal.connect(self.data_received)
        self.threads.append(upload_thread)
        upload_thread.start()

    def data_received(self, data):
        print(data)
        if data == "Successfully uploaded":
            self.show_dialog(
                title=data,
                message=f"{data}\n\nDatabase successfully uploaded.\nWill take roughly 5 minutes to update database",
            )
            logging.info(f"Server: {data}")
        elif data == "Successfully downloaded":
            self.show_dialog(
                title=data,
                message=f"{data}\n\nDatabase successfully downloaded.",
            )
            logging.info(f"Server: {data}")
        elif str(data) == "timed out":
            self.show_dialog(
                title="Time out",
                message="Server is offline, contact server administrator.",
            )
        else:
            self.show_dialog(
                title="error",
                message=str(data),
            )

    def download_database(self):
        self.threads = []
        download_thread = DownloadThread()
        download_thread.signal.connect(self.data_received)
        self.threads.append(download_thread)
        download_thread.start()


def default_settings() -> None:
    check_settings(setting="dark_mode", default_value=False)


def check_settings(setting: str, default_value) -> None:
    if settings_file.get_value(item_name=setting) is None:
        settings_file.add_item(item_name=setting, value=default_value)


def main() -> None:
    default_settings()
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


# if __name__ == "__main__":
main()
