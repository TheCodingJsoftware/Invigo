import sys
import os
import time
import zipfile

import requests
from PyQt5.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QThread,
    pyqtSignal,
)
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)


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
            self.signal.emit("Downloading update..")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.download()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.signal.emit("Installing...")
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
                    if "Invigo.exe" in str(e):
                        self.signal.emit("Close Invigo.exe to finish installing")
                time.sleep(1)
            os.remove(self.file_name)
            self.signal.emit("Updated successfully, have a wonderful day! :)")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            time.sleep(2)
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
            content_length = int(get_response.headers.get("content-length", 0))
            self.file_name = self.url.split("/")[-1]
            total_downloaded: int = 0
            with open(self.file_name, "wb") as f:
                for chunk in get_response.iter_content(chunk_size=8192):
                    if chunk:
                        total_downloaded += len(chunk)
                        f.write(chunk)
                        self.signal.emit(f"Downloading update... {((total_downloaded/content_length)*100):.2f}%")
        except Exception as e:
            self.signal.emit(f"{str(e)} ABORTING..")


class Window(QWidget):
    def __init__(self):
        super().__init__()
        WIDTH, HEIGHT = 440, 120
        BORDER_THICKNESS: int = 2
        OFFSET: int = 50
        PROGRESS_BAR_HEIGHT: int = 20
        MAX_PROGRESS_BAR_WIDTH: int = 120
        PROGRESS_BAR_COLOR: str = "#3daee9"
        ANIMATION_DURATION: int = 2000
        LOOP_DELAY: int = -1

        self.setFixedSize(WIDTH, HEIGHT)
        self.setWindowTitle("Inventory Manager Update")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        widget = QWidget(self)
        widget.resize(WIDTH, HEIGHT)
        widget.setObjectName("widget")
        widget.setStyleSheet(
            "QWidget#widget{border-top-left-radius:10px; border-bottom-left-radius:10px; border-top-right-radius:10px; border-bottom-right-radius:10px; border: 1px solid  rgb(0,120,212); background-color: #292929;}"
        )
        self.progress_text = QLabel(widget)
        self.progress_text.setStyleSheet("color: white;")
        self.progress_text.setText("Invigo Updater")
        self.progress_text.setFixedSize(WIDTH - 20, 20)
        self.progress_text.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.background = QWidget(widget)
        self.background.setStyleSheet("background-color: #404040; border: {BORDER_THICKNESS}px solid #191919; border-radius: 5px;")
        self.background.move(QPoint(OFFSET - BORDER_THICKNESS, HEIGHT - OFFSET - (BORDER_THICKNESS)))
        self.background.resize(
            WIDTH - ((OFFSET - BORDER_THICKNESS) * 2),
            PROGRESS_BAR_HEIGHT + BORDER_THICKNESS * 2,
        )

        self.progress_bar = QWidget(widget)
        self.progress_bar.setStyleSheet(f"background-color: {PROGRESS_BAR_COLOR}; border-radius: 5px;")
        self.progress_bar.resize(0, PROGRESS_BAR_HEIGHT)

        self.anim = QPropertyAnimation(self.progress_bar, b"pos")
        self.anim.setDuration(ANIMATION_DURATION)
        self.anim.setEasingCurve(QEasingCurve.OutBounce)
        self.anim.setStartValue(QPoint(OFFSET, HEIGHT - OFFSET))
        self.anim.setKeyValueAt(0.5, QPoint(WIDTH - OFFSET - 60, HEIGHT - OFFSET))
        # self.anim.setEndValue(QPoint(OFFSET, HEIGHT - OFFSET))
        # self.anim.setEndValue(QPoint(OFFSET, HEIGHT - OFFSET))
        self.anim.setEndValue(QPoint(OFFSET, HEIGHT - OFFSET))

        self.anim_2 = QPropertyAnimation(self.progress_bar, b"size")
        self.anim_2.setDuration(ANIMATION_DURATION)
        self.anim_2.setEasingCurve(QEasingCurve.BezierSpline)
        self.anim_2.setStartValue(QSize(60, PROGRESS_BAR_HEIGHT))
        # self.anim_2.setKeyValueAt(0.15, QSize(60, PROGRESS_BAR_HEIGHT))
        self.anim_2.setKeyValueAt(0.5, QSize(60, PROGRESS_BAR_HEIGHT))
        # self.anim_2.setKeyValueAt(0.85, QSize(60, PROGRESS_BAR_HEIGHT))
        self.anim_2.setEndValue(QSize(60, PROGRESS_BAR_HEIGHT))

        self.anim_group = QParallelAnimationGroup(widget)
        self.anim_group.addAnimation(self.anim)
        self.anim_group.addAnimation(self.anim_2)
        self.anim_group.setLoopCount(LOOP_DELAY)
        self.anim_group.start()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.progress_text)
        widget.setLayout(self.layout)
        self.threads = []

        download_thread = DownloadThread(url="https://github.com/TheCodingJsoftware/Inventory-Manager/releases/latest/download/Invigo.zip")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.start_thread(download_thread)

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
        self.progress_text.setText(data)
        if data == "":
            QApplication.restoreOverrideCursor()
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = Window()
    wizard.show()
    sys.exit(app.exec_())
