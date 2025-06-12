import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class DownloadJobThread(QThread):
    signal = pyqtSignal(object, object)

    def __init__(self, folder_name: str):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.folder_name: str = folder_name
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/download_job/{self.folder_name}"

    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            response_data = msgspec.json.decode(response.content)
            self.signal.emit(response_data, self.folder_name)
        except requests.HTTPError as http_err:
            self.signal.emit(f"HTTP error occurred: {http_err}", self.folder_name)
        except requests.RequestException as err:
            self.signal.emit(f"An error occurred: {err}", self.folder_name)
        except msgspec.DecodeError:
            self.signal.emit("Failed to parse JSON response", self.folder_name)
        return None
