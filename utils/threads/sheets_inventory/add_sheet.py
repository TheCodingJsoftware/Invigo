import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.inventory.sheet import Sheet
from utils.ip_utils import get_server_ip_address, get_server_port


class AddSheetThread(QThread):
    signal = pyqtSignal(object, int, object)

    def __init__(self, sheet: Sheet):
        super().__init__()
        self.SERVER_IP = get_server_ip_address()
        self.SERVER_PORT = get_server_port()
        self.sheet = sheet
        self.url = (
            f"http://{self.SERVER_IP}:{self.SERVER_PORT}/sheets_inventory/add_sheet"
        )

    def run(self):
        try:
            data = self.sheet.to_dict()
            with requests.Session() as session:
                response = session.post(self.url, json=data, timeout=10)
                response.raise_for_status()

                try:
                    response_data = msgspec.json.decode(response.content)
                except msgspec.DecodeError:
                    self.signal.emit({"error": "Failed to decode server response"}, 500, self.sheet)
                    return

                if isinstance(response_data, dict) and "id" in response_data:
                    response_data["sheet_data"] = {
                        "id": response_data["id"],
                        "data": data,
                    }
                    self.signal.emit(response_data, 200, self.sheet)
                else:
                    self.signal.emit({"error": "Invalid data format received"}, 500, self.sheet)

        except requests.exceptions.Timeout:
            self.signal.emit({"error": "Request timed out"}, 408, self.sheet)
        except requests.exceptions.ConnectionError:
            self.signal.emit({"error": "Could not connect to the server"}, 503, self.sheet)
        except requests.exceptions.HTTPError as e:
            self.signal.emit({"error": f"HTTP Error: {str(e)}"}, response.status_code, self.sheet)
        except requests.exceptions.RequestException as e:
            self.signal.emit({"error": f"Request failed: {str(e)}"}, 500, self.sheet)
        finally:
            self.finished.emit()
