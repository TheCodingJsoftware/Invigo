import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from config.environments import Environment


class CheckForUpdatesThread(QThread):
    update_available = pyqtSignal(dict)

    def __init__(self, parent, current_version: str):
        super().__init__(parent)
        self.current_version = current_version
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            try:
                resp = requests.get(
                    f"{Environment.SOFTWARE_API_BASE}/version",
                    timeout=10,
                )

                if resp.status_code != 200:
                    time.sleep(60)
                    continue

                data = resp.json()
                latest_version = data.get("version")
                changelog = data.get("changelog")

                if not latest_version:
                    time.sleep(60)
                    continue

                if latest_version != self.current_version:
                    self.update_available.emit(latest_version, changelog)

            except Exception:
                pass

            time.sleep(60)
