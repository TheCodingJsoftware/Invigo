import msgspec
import requests
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetSheetSignals(QObject):
    signal = pyqtSignal(object, int)  # (sheet_data or error dict, status_code)


class GetSheetWorker(QRunnable):
    def __init__(self, sheet_id: int | str):
        super().__init__()
        self.signals = GetSheetSignals()
        self.SERVER_IP = get_server_ip_address()
        self.SERVER_PORT = get_server_port()
        self.sheet_id = sheet_id
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/sheets_inventory/get_sheet/{self.sheet_id}"

    def run(self):
        try:
            with requests.Session() as session:
                response = session.get(self.url, timeout=10)
                response.raise_for_status()

                try:
                    sheet_data = msgspec.json.decode(response.content)
                except msgspec.DecodeError:
                    self.signals.signal.emit(
                        {"error": "Failed to decode server response"}, 500
                    )
                    return

                if isinstance(sheet_data, dict):
                    self.signals.signal.emit(sheet_data, 200)
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
