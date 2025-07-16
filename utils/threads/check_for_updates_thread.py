import time

import requests
from PyQt6.QtCore import QThread, pyqtSignal


class CheckForUpdatesThread(QThread):
    signal = pyqtSignal(object, object)

    def __init__(self, parent, current_version: str):
        self.parent = parent
        self.current_version = current_version
        QThread.__init__(self)

    def run(self):
        while True:
            try:
                response_version = requests.get("http://10.0.0.10:5051/version", timeout=10)
                response_message = requests.get("http://10.0.0.10:5051/update_message", timeout=10)
                if response_version.status_code != 200 or response_message.status_code != 200:
                    continue
                version = response_version.text
                message = response_message.text
                if version != self.current_version:
                    self.signal.emit(version, message)
            except Exception:
                continue
            time.sleep(60)
