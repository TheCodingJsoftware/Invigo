# sourcery skip: avoid-builtin-shadow
__author__ = "Jared Gross"
__copyright__ = "Copyright 2022, TheCodingJ's"
__credits__: "list[str]" = ["Jared Gross"]
__license__ = "MIT"
__name__ = "Inventory Manager"
__version__ = "v0.0.1"
__updated__ = "2022-05-10 22:49:08"
__maintainer__ = "Jared Gross"
__email__ = "jared@pinelandfarms.ca"
__status__ = "Production"

import logging
import os
import shutil
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
from PyQt5.QtGui import QFont, QIcon, QImage, QPalette, QPixmap
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
from message_dialog import MessageDialog
from upload_thread import UploadThread
from utils.compress import compress_database, compress_folder
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
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
        uic.loadUi("ui/main_menu.ui", self)
        self.setWindowTitle(__name__)
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.check_for_updates(on_start_up=True)
        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

        self.__load_ui()
        self.show_error_dialog("test1", "test2\n" * 100)
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

    def show_message_dialog(
        self, title: str, message: str, dialog_buttons: DialogButtons = DialogButtons.ok
    ) -> str:
        self.message_dialog = MessageDialog(
            self, Icons.information, dialog_buttons, title, message
        )
        self.message_dialog.show()

        response: str = ""

        if self.message_dialog.exec_():
            response = self.message_dialog.get_response()

        return response

    def show_error_dialog(
        self,
        title: str,
        message: str,
        dialog_buttons: DialogButtons = DialogButtons.ok_save_copy_cancel,
    ) -> str:
        self.message_dialog = MessageDialog(
            self, Icons.critical, dialog_buttons, title, message
        )
        self.message_dialog.show()

        response: str = ""

        if self.message_dialog.exec_():
            response = self.message_dialog.get_response()

        if response == DialogButtons.copy:
            pixmap = QPixmap(self.message_dialog.grab())
            QApplication.clipboard().setPixmap(pixmap)
        elif response == DialogButtons.save:
            self.generate_error_log(message_dialog=self.message_dialog)
        return response

    def generate_error_log(self, message_dialog: MessageDialog) -> None:
        output_directory: str = (
            f"logs/ErrorLog_{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
        )
        check_folders([output_directory])
        pixmap = QPixmap(message_dialog.grab())
        pixmap.save(f"{output_directory}/screenshot.png")
        with open(f"{output_directory}/error.log", "w") as error_log:
            error_log.write(message_dialog.message)
        shutil.copyfile("logs/app.log", f"{output_directory}/app.log")
        compress_folder(foldername=output_directory, target_dir=output_directory)
        shutil.rmtree(output_directory)

    def toggle_dark_mode(self) -> None:
        settings_file.change_item(
            item_name="dark_mode", new_value=not settings_file.get_value("dark_mode")
        )

        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

        self.update_theme()

    def update_theme(self) -> None:
        file = QFile(f"ui/BreezeStyleSheets/dist/qrc/{self.theme}/stylesheet.qss")
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

    def data_received(self, data) -> None:
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
            self.show_error_dialog(
                title="Time out",
                message="Server is either offline or try again. \n\nMake sure VPN's are disabled, else\n\ncontact server administrator.\n\n",
            )
        else:
            self.show_error_dialog(
                title="error",
                message=str(data),
            )

    def upload_changes(self) -> None:
        self.threads = []
        upload_thread = UploadThread()
        self.start_thread(upload_thread)

    def download_database(self) -> None:
        self.threads = []
        download_thread = DownloadThread()
        self.start_thread(download_thread)

    def start_thread(self, thread) -> None:
        thread.signal.connect(self.data_received)
        self.threads.append(thread)
        thread.start()

    def backup_database(self) -> None:
        compress_database(path_to_file="data/database.json")
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
