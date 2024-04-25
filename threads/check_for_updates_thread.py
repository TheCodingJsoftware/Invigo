import time

import requests
from PyQt6.QtCore import QThread, pyqtSignal


class CheckForUpdatesThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, parent, current_version: str) -> None:
        self.current_version = current_version
        QThread.__init__(self)

    def run(self) -> None:
        while True:
            try:
                response = requests.get("http://10.0.0.10:5051/version")
                if response.status_code == 200:
                    version = response.text
                    if version != self.current_version:
                        self.signal.emit(version)
                else:
                    continue
            except Exception as e:
                continue
            time.sleep(60)
