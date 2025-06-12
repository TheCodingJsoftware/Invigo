import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.inventory.sheet import Sheet
from utils.ip_utils import get_server_ip_address, get_server_port


class UpdateSheetThread(QThread):
    signal = pyqtSignal(object, int)

    def __init__(
        self,
        sheet: Sheet,
    ):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.sheet = sheet
        self.sheet_id: int = sheet.id
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/sheets_inventory/update_sheet/{self.sheet_id}"

    def run(self):
        try:
            data = self.sheet.to_dict()
            with requests.Session() as session:
                response = session.post(self.url, json=data, timeout=10)
                response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)

                try:
                    job_data = msgspec.json.decode(response.content)
                except msgspec.DecodeError:
                    self.signal.emit({"error": "Failed to decode server response"}, 500)
                    return

                job_data["sheet_data"] = {
                    "id": self.sheet_id,
                    "data": data,
                }
                if isinstance(job_data, dict):
                    self.signal.emit(
                        job_data, 200
                    )  # Emit the job data with HTTP 200 status
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
