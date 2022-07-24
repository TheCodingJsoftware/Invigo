import os
import time
import urllib.request
import zipfile
from turtle import width

import requests
from PyQt5.QtCore import (
    QEasingCurve,
    QFile,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QTextStream,
    QThread,
    pyqtSignal,
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class DownloadThread(QThread):
    """This class is a QThread that downloads a file."""

    signal = pyqtSignal(object)

    def __init__(self, url) -> None:
        QThread.__init__(self)
        self.url = url
        self.file_name = ""

    def run(self) -> None:
        """
        It downloads a zip file, extracts it, and then deletes the zip file.
        """
        try:
            self.signal.emit("Do. NOT. close. this. window. >:(")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            time.sleep(2)
            self.signal.emit("Downloading.. :|")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.download()
            self.signal.emit("Download finished... :)")
            time.sleep(1)
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.signal.emit("Installing.... :O")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            extracted: bool = False
            while not extracted:
                try:
                    with zipfile.ZipFile(self.file_name, "r") as zip_ref:
                        zip_ref.extractall(".")
                        extracted = True
                except Exception as e:
                    if "update.exe" in str(e):
                        extracted = True
                    if "Inventory Manager.exe" in str(e):
                        self.signal.emit("Close Inventory Manager.exe (NOT THIS WINDOW)")
                time.sleep(1)
            os.remove(self.file_name)

            self.signal.emit("Finished. :D")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            time.sleep(1)
            self.signal.emit("Closing. >:)")
            time.sleep(1)
            self.signal.emit("")
        except Exception as e:
            self.signal.emit(e)

    def download(self):
        """
        Downloads a file from a url and displays a progress bar using tqdm

        Args:
        url: The URL of the file you want to download.
        """
        try:
            get_response = requests.get(self.url, stream=True)
            self.file_name = self.url.split("/")[-1]
            total_download: int = 0
            with open(self.file_name, "wb") as f:
                for chunk in get_response.iter_content(chunk_size=1024):
                    if chunk:
                        total_download += len(chunk)
                        f.write(chunk)
        except Exception as e:
            print(f"{str(e)} ABORTING..")


class Window(QWidget):
    def __init__(self):
        super().__init__()
        WIDTH, HEIGHT = 440, 120
        BORDER_THICKNESS: int = 1
        OFFSET: int = 50
        PROGRESS_BAR_HEIGHT: int = 20
        MAX_PROGRESS_BAR_WIDTH: int = 120
        PROGRESS_BAR_COLOR: str = "#3daee9"
        ANIMATION_DURATION: int = 2000
        LOOP_DELAY: int = 2000
        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

        self.setFixedSize(WIDTH, HEIGHT)
        self.setWindowTitle("Inventory Manager Update")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        widget = QWidget(self)
        widget.resize(WIDTH, HEIGHT)
        widget.setObjectName("widget")
        widget.setStyleSheet(
            "QWidget#widget{border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:10px; border-bottom-right-radius:10px; border: 1px solid  rgb(0,120,212);}"
        )
        self.progress_text = QLabel(widget)
        self.progress_text.setFixedSize(WIDTH - 20, 20)
        self.progress_text.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.background = QWidget(widget)
        if self.theme == "dark":
            self.background.setStyleSheet(
                "background-color: #626568; border: {BORDER_THICKNESS}px solid #222222; border-radius: 3px;"
            )
        else:
            self.background.setStyleSheet(
                "background-color: rgba(106, 105, 105, 0.7); border: {BORDER_THICKNESS}px solid  #eff0f1; border-radius: 3px;"
            )
        self.background.move(
            QPoint(OFFSET - BORDER_THICKNESS, HEIGHT - OFFSET - (BORDER_THICKNESS))
        )
        self.background.resize(
            WIDTH - ((OFFSET - BORDER_THICKNESS) * 2),
            PROGRESS_BAR_HEIGHT + BORDER_THICKNESS * 2,
        )

        self.progress_bar = QWidget(widget)
        self.progress_bar.setStyleSheet(
            f"background-color: {PROGRESS_BAR_COLOR}; border-radius: 3px"
        )
        self.progress_bar.resize(0, PROGRESS_BAR_HEIGHT)

        self.anim = QPropertyAnimation(self.progress_bar, b"pos")
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.anim.setStartValue(QPoint(OFFSET, HEIGHT - OFFSET))
        self.anim.setEndValue(QPoint(WIDTH - (40 * 2) + 30, HEIGHT - OFFSET))
        self.anim.setDuration(ANIMATION_DURATION)

        self.anim_2 = QPropertyAnimation(self.progress_bar, b"size")
        self.anim_2.setDuration(ANIMATION_DURATION)
        self.anim_2.setStartValue(QSize(0, PROGRESS_BAR_HEIGHT))
        self.anim_2.setEasingCurve(QEasingCurve.InOutCubic)
        self.anim_2.setKeyValueAt(0.0, QSize(0, PROGRESS_BAR_HEIGHT))
        self.anim_2.setKeyValueAt(0.1, QSize(40, PROGRESS_BAR_HEIGHT))
        self.anim_2.setKeyValueAt(0.6, QSize(MAX_PROGRESS_BAR_WIDTH, PROGRESS_BAR_HEIGHT))
        self.anim_2.setEndValue(QSize(0, PROGRESS_BAR_HEIGHT))

        self.anim_group = QParallelAnimationGroup(widget)
        self.anim_group.addAnimation(self.anim)
        self.anim_group.addAnimation(self.anim_2)
        self.anim_group.setLoopCount(LOOP_DELAY)
        self.anim_group.start()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.progress_text)
        widget.setLayout(self.layout)
        self.threads = []

        download_thread = DownloadThread(
            url="https://github.com/TheCodingJsoftware/Inventory-Manager/releases/latest/download/Inventory.Manager.zip"
        )
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.start_thread(download_thread)

        self.load_theme()

    def load_theme(self) -> None:
        """
        It loads the stylesheet.qss file from the theme folder
        """
        stylesheet_file = QFile(
            f"ui/BreezeStyleSheets/dist/qrc/{self.theme}/stylesheet.qss"
        )
        stylesheet_file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(stylesheet_file)
        self.setStyleSheet(stream.readAll())

    def start_thread(self, thread) -> None:
        """
        It connects the signal from the thread to the data_received function, then appends the thread to
        the threads list, and finally starts the thread

        Args:
          thread: The thread to start
        """
        thread.signal.connect(self.data_received)
        self.threads.append(thread)
        thread.start()

    def data_received(self, data) -> None:
        """
        If the data received is "Successfully uploaded" or "Successfully downloaded", then show a
        message dialog with the title and message

        Args:
          data: the data received from the server
        """
        self.progress_text.setText(data + "\n")
        QApplication.restoreOverrideCursor()
        if data == "":
            self.close()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    wizard = Window()
    wizard.show()
    sys.exit(app.exec_())
