# sourcery skip: avoid-builtin-shadow
__author__ = "Jared Gross"
__copyright__ = "Copyright 2022, TheCodingJ's"
__credits__: "list[str]" = ["Jared Gross"]
__license__ = "MIT"
__name__ = "Inventory Manager"
__version__ = "v0.0.1"
__updated__ = "2022-05-09 12:45:24"
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

import requests
from PyQt5 import uic
from PyQt5.QtCore import (
    QCoreApplication,
    QFile,
    QProcess,
    QRunnable,
    QSettings,
    Qt,
    QTextStream,
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
import ui.BreezeStyleSheets.breeze_resources
from about_dialog import AboutDialog
from download_thread import DownloadThread
from upload_thread import UploadThread
from utils.compress import compress_file
from utils.json_file import JsonFile
from utils.json_object import JsonObject

settings_file = JsonFile(file_name="settings")
geometry = JsonObject(JsonFile=settings_file, object_name="geometry")


class MainWindow(QMainWindow):
    """
    Main program
    """

    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main.ui", self)
        self.setWindowTitle(__name__)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.check_for_updates(on_start_up=True)

        self.__load_ui()
        self.show()

    def __load_ui(self) -> None:
        self.update_theme()
        self.setGeometry(
            geometry.get_value("x"),
            geometry.get_value("y"),
            geometry.get_value("width"),
            geometry.get_value("height"),
        )

        # Action events
        # HELP
        self.actionCheck_for_Updates.triggered.connect(self.check_for_updates)
        self.actionAbout_Qt.triggered.connect(qApp.aboutQt)
        self.actionAbout.triggered.connect(self.show_about_dialog)
        # SETTINGS
        self.actionDarkmode.setChecked(settings_file.get_value(item_name="dark_mode"))
        self.actionDarkmode.triggered.connect(self.toggle_dark_mode)
        # FILE
        self.actionUpload_Changes.triggered.connect(self.upload_changes)
        self.actionGet_Changes.triggered.connect(self.download_database)
        self.actionBackup.triggered.connect(self.backup_database)
        self.actionExit.triggered.connect(self.close)

    def save_geometry(self):
        geometry.set_value("x", value=self.pos().x())
        geometry.set_value("y", value=self.pos().y())
        geometry.set_value("width", value=self.size().width())
        geometry.set_value("height", value=self.size().height())

    def show_about_dialog(self) -> None:
        self.dialog = AboutDialog(
            __name__,
            __version__,
            __updated__,
            "https://github.com/TheCodingJsoftware/Inventory-Manager",
        )
        self.dialog.show()

    def show_message_dialog(self, title: str, message: str) -> None:
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
        self.update_theme()

    def update_theme(self) -> None:
        if settings_file.get_value(item_name="dark_mode"):
            file = QFile("ui/BreezeStyleSheets/dist/qrc/dark/stylesheet.qss")
        else:
            file = QFile("ui/BreezeStyleSheets/dist/qrc/light/stylesheet.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        self.setStyleSheet(stream.readAll())

    def check_for_updates(self, on_start_up: bool = False) -> None:
        try:
            response = requests.get(
                "https://api.github.com/repos/thecodingjsoftware/Inventory-Manager/releases/latest"
            )
            version: str = response.json()["name"].replace(" ", "")
            if version != __version__:
                self.show_message_dialog(
                    title=__name__, message="There is a new update available"
                )
            elif not on_start_up:
                self.show_message_dialog(
                    title=__name__, message="There are currently no updates available."
                )
        except Exception as e:
            if not on_start_up:
                self.show_message_dialog(title=__name__, message=f"Error\n\n{e}")

    def upload_changes(self):
        self.threads = []
        upload_thread = UploadThread()
        upload_thread.signal.connect(self.data_received)
        self.threads.append(upload_thread)
        upload_thread.start()

    def data_received(self, data):
        print(data)
        if data == "Successfully uploaded":
            self.show_message_dialog(
                title=data,
                message=f"{data}\n\nDatabase successfully uploaded.\nWill take roughly 5 minutes to update database",
            )
            logging.info(f"Server: {data}")
        elif data == "Successfully downloaded":
            self.show_message_dialog(
                title=data,
                message=f"{data}\n\nDatabase successfully downloaded.",
            )
            logging.info(f"Server: {data}")
        elif str(data) == "timed out":
            self.show_message_dialog(
                title="Time out",
                message="Server is offline, contact server administrator.\n\nOr try again.",
            )
        else:
            self.show_message_dialog(
                title="error",
                message=str(data),
            )

    def download_database(self):
        self.threads = []
        download_thread = DownloadThread()
        download_thread.signal.connect(self.data_received)
        self.threads.append(download_thread)
        download_thread.start()

    def backup_database(self):
        compress_file(path_to_file="data/database.json")
        self.show_message_dialog(title="Success", message="Backup was successful!")

    def closeEvent(self, event):
        self.save_geometry()
        super().closeEvent(event)


def default_settings() -> None:
    check_settings(setting="dark_mode", default_value=False)
    check_settings(setting="server_ip", default_value="10.0.0.162")
    check_settings(setting="server_port", default_value=4000)
    check_settings(
        setting="geometry",
        default_value={"x": 200, "y": 200, "width": 600, "height": 400},
    )


def check_settings(setting: str, default_value) -> None:
    if settings_file.get_value(item_name=setting) is None:
        settings_file.add_item(item_name=setting, value=default_value)


def check_folders(folders: list) -> None:
    for folder in folders:
        if not os.path.exists(f"{os.path.dirname(os.path.realpath(__file__))}/{folder}"):
            os.makedirs(f"{os.path.dirname(os.path.realpath(__file__))}/{folder}")


def main() -> None:
    default_settings()
    check_folders(folders=["logs", "data", "backups"])
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


# if __name__ == "__main__":
main()
