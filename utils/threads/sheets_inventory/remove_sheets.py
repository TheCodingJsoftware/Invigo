import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.inventory.sheet import Sheet
from utils.ip_utils import get_server_ip_address, get_server_port


class RemoveSheetsThread(QThread):
    # Emits (list of results, status_code, list of original sheets)
    signal = pyqtSignal(object, int, object)

    def __init__(self, sheets: list[Sheet]):
        super().__init__()
        self.SERVER_IP = get_server_ip_address()
        self.SERVER_PORT = get_server_port()
        self.sheets = sheets

    def run(self):
        results: list[dict[str, str | int]] = []
        status_code = 200

        try:
            with requests.Session() as session:
                for sheet in self.sheets:
                    sheet_id = sheet.id
                    url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/sheets_inventory/delete_sheet/{sheet_id}"

                    try:
                        response = session.get(url, timeout=10)
                        response.raise_for_status()

                        try:
                            result = msgspec.json.decode(response.content)
                            if isinstance(result, bool):
                                results.append({"deleted": result, "id": sheet_id})
                            else:
                                results.append({"error": "Invalid data format", "id": sheet_id})
                                status_code = 500

                        except msgspec.DecodeError:
                            results.append({"error": "Failed to decode response", "id": sheet_id})
                            status_code = 500

                    except requests.exceptions.Timeout:
                        results.append({"error": "Request timed out", "id": sheet_id})
                        status_code = 408
                    except requests.exceptions.ConnectionError:
                        results.append({"error": "Connection error", "id": sheet_id})
                        status_code = 503
                    except requests.exceptions.HTTPError as e:
                        results.append({"error": f"HTTP Error: {str(e)}", "id": sheet_id})
                        status_code = response.status_code
                    except requests.exceptions.RequestException as e:
                        results.append({"error": f"Request failed: {str(e)}", "id": sheet_id})
                        status_code = 500

        finally:
            self.signal.emit(results, status_code, self.sheets)
            self.finished.emit()
