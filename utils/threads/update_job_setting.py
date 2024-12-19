import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class UpdateJobSetting(QThread):
    signal = pyqtSignal(object, str)

    def __init__(
        self, folder: str, key_to_change: str, new_value: str | float | int | bool
    ):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.folder = folder
        self.key_to_change = key_to_change
        self.new_value = new_value
        self.upload_url = (
            f"http://{self.SERVER_IP}:{self.SERVER_PORT}/update_job_settings"
        )

    def run(self):
        try:
            data = {
                "folder": self.folder,
                "key": self.key_to_change,
                "value": self.new_value,
            }
            response = requests.post(self.upload_url, data=data, timeout=10)
            self.signal.emit(response.json(), self.folder)
        except Exception as e:
            self.signal.emit(str(e), self.folder)
