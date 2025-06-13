import msgspec
import requests
from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from utils.inventory.sheet import Sheet
from utils.ip_utils import get_server_ip_address, get_server_port


class UpdateSheetWorkerSignals(QObject):
    signal = pyqtSignal(object, int)


class UpdateSheetWorker(QRunnable):
    def __init__(self, sheet: Sheet):
        super().__init__()
        self.signals = UpdateSheetWorkerSignals()
        self.sheet = sheet
        self.sheet_id = sheet.id
        self.url = f"http://{get_server_ip_address()}:{get_server_port()}/sheets_inventory/update_sheet/{self.sheet_id}"

    def run(self):
        try:
            data = self.sheet.to_dict()
            with requests.Session() as session:
                response = session.post(self.url, json=data, timeout=10)
                response.raise_for_status()
                try:
                    job_data = msgspec.json.decode(response.content)
                except msgspec.DecodeError:
                    self.signals.signal.emit(
                        {"error": "Failed to decode server response"}, 500
                    )
                    return

                job_data["sheet_data"] = {"id": self.sheet_id, "data": data}
                self.signals.signal.emit(job_data, 200)
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
