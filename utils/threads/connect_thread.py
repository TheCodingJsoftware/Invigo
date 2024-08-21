import os

import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class ConnectThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, version: str):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/connect"
        self.version: str = version
        self.client_name = os.getlogin()

    def run(self):
        payload = {"client_name": self.client_name, "version": self.version}
        try:
            response = requests.post(self.url, json=payload, timeout=10)
            response.raise_for_status()
            response_data = msgspec.json.decode(response.content)
            self.signal.emit(response_data)
        except requests.HTTPError as http_err:
            self.signal.emit(f"HTTP error occurred: {http_err}")
        except requests.RequestException as err:
            self.signal.emit(f"An error occurred: {err}")
        except msgspec.DecodeError:
            self.signal.emit("Failed to parse JSON response")
        return None
