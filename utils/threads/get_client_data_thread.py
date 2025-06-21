import os

import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class IsClientTrustedThread(QThread):
    signal = pyqtSignal(object, object)  # Emit signal with data or error message

    def __init__(self):
        QThread.__init__(self)
        self.SERVER_IP = get_server_ip_address()
        self.SERVER_PORT = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/is_client_trusted"
        self.headers = {"X-Client-Name": os.getlogin()}

    def run(self):
        try:
            with requests.Session() as session:
                response = session.get(self.url, headers=self.headers, timeout=10)
                response.raise_for_status()
                response_data = response.json()
                self.signal.emit(response_data, None)
        except requests.HTTPError as http_err:
            self.signal.emit(None, f"HTTP error occurred: {http_err}")
        except requests.RequestException as err:
            self.signal.emit(None, f"An error occurred: {err}")
        except ValueError:
            self.signal.emit(None, "Failed to parse JSON response")
        self.finished.emit()
