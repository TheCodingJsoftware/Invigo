import msgspec
import requests
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetAllSheetsSignals(QObject):
    signal = pyqtSignal(object, int)  # (data or error, status_code)


class GetAllSheetsWorker(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = GetAllSheetsSignals()
        self.SERVER_IP = get_server_ip_address()
        self.SERVER_PORT = get_server_port()
        self.url = (
            f"http://{self.SERVER_IP}:{self.SERVER_PORT}/sheets_inventory/get_all"
        )

    def run(self):
        try:
            with requests.Session() as session:
                response = session.get(self.url, timeout=10)
                response.raise_for_status()

                try:
                    all_sheets = msgspec.json.decode(response.content)
                except msgspec.DecodeError:
                    self.signals.signal.emit(
                        {"error": "Failed to decode server response"}, 500
                    )
                    return

                if isinstance(all_sheets, list):
                    self.signals.signal.emit(all_sheets, 200)
                else:
                    self.signals.signal.emit(
                        {"error": "Invalid data format received"}, 500
                    )

        except requests.exceptions.Timeout:
            self.signals.signal.emit({"error": "Request timed out"}, 408)
        except requests.exceptions.ConnectionError:
            self.signals.signal.emit({"error": "Could not connect to the server"}, 503)
        except requests.exceptions.HTTPError as e:
            self.signals.signal.emit(
                {"error": f"HTTP Error: {str(e)}"}, response.status_code
            )
        except requests.exceptions.RequestException as e:
            self.signals.signal.emit({"error": f"Request failed: {str(e)}"}, 500)
