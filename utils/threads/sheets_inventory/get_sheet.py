import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetSheetThread(QThread):
    signal = pyqtSignal(object, int)

    def __init__(self, sheet_id: int | str):
        super().__init__()
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
                    self.signal.emit({"error": "Failed to decode server response"}, 500)
                    return

                if isinstance(sheet_data, dict):
                    self.signal.emit(sheet_data, 200)
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
