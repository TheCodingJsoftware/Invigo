import math
import os
import sys
import time
import zipfile

import psutil
import requests
from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    Qt,
    QThread,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from config.environments import Environment


class DownloadThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, url):
        QThread.__init__(self)
        self.url = url
        self.file_name = "Invigo.zip"

    def run(self):
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.download()
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.signal.emit("Installing...")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            extracted = False
            retry_count = 0
            while not extracted and retry_count < 5:
                try:
                    with zipfile.ZipFile(self.file_name, "r") as zip_ref:
                        zip_ref.extractall(".")
                        extracted = True
                except Exception as e:
                    error_message = str(e)
                    if "update.exe" in error_message:
                        extracted = True
                        continue
                    # self.signal.emit(f"Error during installation: {error_message}")
                    if "Invigo.exe" in error_message:
                        if not self.close_process("Invigo.exe"):
                            self.signal.emit("Failed to close Invigo.exe. Please close it manually.")
                            # break  # Exit if we can't close the process after trying
                        else:
                            self.signal.emit("Installing...")
                    time.sleep(2)
                    retry_count += 1
                time.sleep(1)
            os.remove(self.file_name)
            if retry_count >= 5:
                self.signal.emit("Updated failed, please try again later.")
            else:
                self.signal.emit("Update was successful!")
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            time.sleep(2)
            self.signal.emit("")
        except Exception as e:
            self.signal.emit(e)

    def close_process(self, process_name):
        for proc in psutil.process_iter(["pid", "name"]):
            if proc.info["name"] == process_name:
                try:
                    self.signal.emit(f"Closing {process_name}.")
                    proc.terminate()
                    proc.wait()
                    return True
                except psutil.NoSuchProcess:
                    self.signal.emit(f"Process {process_name} does not exist.")
                except psutil.AccessDenied:
                    self.signal.emit(f"Access denied when trying to terminate {process_name}.")
                except Exception as e:
                    self.signal.emit(f"An error occurred: {e}")
        return False

    def download(self):
        try:
            get_response = requests.get(self.url, stream=True)
            content_length = int(get_response.headers.get("content-length", 0))
            total_downloaded: int = 0
            with open(self.file_name, "wb") as f:
                for chunk in get_response.iter_content(chunk_size=8192):
                    if chunk:
                        total_downloaded += len(chunk)
                        f.write(chunk)
                        self.signal.emit(f"Downloading update... {((total_downloaded / content_length) * 100):.2f}%")
        except Exception as e:
            self.signal.emit(f"ABORTING: {str(e)}")


class CircleWidget(QWidget):
    angleChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(QColor(139, 143, 148))
        painter.setPen(QColor(46, 46, 48))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = 100
        painter.drawEllipse(
            self.width() // 2 - radius // 2,
            self.height() // 2 - radius // 2 - 50,
            radius,
            radius,
        )
        painter.setBrush(QColor(41, 41, 41))
        painter.setPen(QColor(41, 41, 41))
        for i in range(6):
            angle = self._angle + i * (360 / 6)
            radian = angle * math.pi / 180
            x = self.width() // 2 + int(60 * math.cos(radian)) - 20
            y = self.height() // 2 + int(60 * math.sin(radian)) - 20 - 50
            painter.drawEllipse(QRect(x, y, 40, 40))
        painter.setBrush(QColor(46, 46, 48))
        painter.setPen(QColor(139, 143, 148))
        painter.drawEllipse(self.width() // 2 - 25, self.height() // 2 - 25 - 50, 50, 50)
        painter.setBrush(QColor(61, 174, 233))
        painter.setPen(QColor(46, 46, 48))
        painter.drawEllipse(self.width() // 2 - 20, self.height() // 2 - 20 - 50, 40, 40)

    @pyqtProperty(int)
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        if self._angle != value:
            self._angle = value
            self.angleChanged.emit(self._angle)
            self.update()


class Window(QWidget):
    def __init__(self):
        super().__init__()
        WIDTH, HEIGHT = 240, 300
        ANIMATION_DURATION: int = 2000
        LOOP_DELAY: int = -1

        self.setFixedSize(WIDTH, HEIGHT)
        self.setWindowTitle("Invigo Updater")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        widget = QWidget(self)
        widget.resize(WIDTH, HEIGHT)
        widget.setObjectName("widget")
        widget.setStyleSheet(
            """QWidget#widget {
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                border: 1px solid rgb(139, 143, 148);
                background-color: #292929;
            }"""
        )
        self.progress_text = QLabel(widget)
        self.progress_text.setWordWrap(True)
        self.progress_text.setStyleSheet("color: rgb(169, 163, 168); font-size: 16px;")
        self.progress_text.setText("Updated successfully!")
        self.progress_text.move(10, HEIGHT // 2)
        self.progress_text.setFixedSize(WIDTH - 20, 100)
        self.progress_text.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.circle_widget = CircleWidget(self)
        layout = QVBoxLayout()
        layout.addWidget(self.circle_widget)
        self.setLayout(layout)

        self.anim = QPropertyAnimation(self.circle_widget, b"angle")

        self.anim.setDuration(ANIMATION_DURATION)
        self.anim.setStartValue(0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        self.anim.setKeyValueAt(0.4, 180)
        self.anim.setEndValue(360)
        self.anim.setLoopCount(LOOP_DELAY)
        self.anim.start()

        self.threads = []

        download_thread = DownloadThread(url=f"{Environment.SOFTWARE_API_BASE}/download")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.start_thread(download_thread)

    def start_thread(self, thread: DownloadThread):
        thread.signal.connect(self.data_received)
        self.threads.append(thread)
        thread.start()

    def data_received(self, data):
        self.progress_text.setText(data)
        if data == "":
            QApplication.restoreOverrideCursor()
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    wizard = Window()
    wizard.show()
    sys.exit(app.exec())
