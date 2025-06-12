import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetWorkspaceEntryThread(QThread):
    signal = pyqtSignal(object, int)

    def __init__(self, entry_id: int):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.entry_id: int = entry_id
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace/get_entry/{self.entry_id}"

    def run(self):
        try:
            with requests.Session() as session:
                response = session.get(self.url, timeout=10)
                response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
                entry_data = msgspec.json.decode(response.content)

                if isinstance(entry_data, dict):
                    self.signal.emit(entry_data, 200)
                else:
                    self.signal.emit({"error": "Invalid data format received"}, 500)

        except requests.exceptions.Timeout:
            self.signal.emit({"error": "Request timed out"}, 408)
        except requests.exceptions.ConnectionError:
            self.signal.emit({"error": "Could not connect to the server"}, 503)
        except requests.exceptions.HTTPError as e:
            self.signal.emit({"error": f"HTTP Error: {str(e)}"}, response.status_code)
        except requests.exceptions.RequestException as e:
            self.signal.emit({"error": f"Request failed: {str(e)}"}, 500)
        finally:
            self.finished.emit()
