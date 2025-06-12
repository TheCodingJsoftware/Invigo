import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class AddJobToProductionPlannerThread(QThread):
    signal = pyqtSignal(object, str, int)

    def __init__(self, folder_name: str):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.folder_name: str = folder_name
        self.url = (
            f"http://{self.SERVER_IP}:{self.SERVER_PORT}/add_job/{self.folder_name}"
        )

    def run(self):
        try:
            response = requests.post(self.url, timeout=10)
            response_data = msgspec.json.decode(response.content)
            self.signal.emit(response_data, self.folder_name, response.status_code)
        except requests.HTTPError as http_err:
            self.signal.emit(
                f"HTTP error occurred: {http_err}",
                self.folder_name,
                response.status_code,
            )
        except requests.RequestException as err:
            self.signal.emit(
                f"An error occurred: {err}", self.folder_name, response.status_code
            )
        except msgspec.DecodeError:
            self.signal.emit(
                "Failed to parse JSON response", self.folder_name, response.status_code
            )
        return None
