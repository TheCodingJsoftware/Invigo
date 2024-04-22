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
                try:
                    response = requests.get("https://api.github.com/repos/thecodingjsoftware/Inventory-Manager/releases/latest")
                except ConnectionError:
                    continue
                version: str = response.json()["name"].replace(" ", "")
                if version != self.current_version:
                    self.signal.emit(version)
            except Exception as e:
                continue
            time.sleep(60)
