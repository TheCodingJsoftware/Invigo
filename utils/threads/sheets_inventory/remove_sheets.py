# remove_sheets_worker.py
import msgspec
import requests
from PyQt6.QtCore import QObject, pyqtSignal

from utils.inventory.sheet import Sheet
from utils.threads.base_worker import BaseWorker


class RemoveSheetsSignals(QObject):
    success = pyqtSignal(object, int, object)  # (results, status_code, original sheets)
    finished = pyqtSignal()


class RemoveSheetsWorker(BaseWorker):
    def __init__(self, sheets: list[Sheet]):
        super().__init__(name="RemoveSheetsWorker")
        self.sheets = sheets
        self.signals = RemoveSheetsSignals()  # Override default signal set

    def run(self):
        import time

        start = time.perf_counter()
        results: list[dict[str, str | int | bool]] = []
        status_code = 200

        try:
            with requests.Session() as session:
                for sheet in self.sheets:
                    sheet_id = sheet.id
                    url = f"{self.DOMAIN}/sheets_inventory/delete_sheet/{sheet_id}"
                    self.logger.info(f"Attempting to delete sheet ID {sheet_id}")

                    try:
                        response = session.get(url, timeout=10)
                        response.raise_for_status()

                        try:
                            result = msgspec.json.decode(response.content)
                            if isinstance(result, bool):
                                results.append({"deleted": result, "id": sheet_id})
                            else:
                                self.logger.warning(
                                    f"Invalid format deleting sheet {sheet_id}"
                                )
                                results.append(
                                    {"error": "Invalid data format", "id": sheet_id}
                                )
                                status_code = 500

                        except msgspec.DecodeError:
                            results.append(
                                {"error": "Failed to decode response", "id": sheet_id}
                            )
                            status_code = 500

                    except requests.exceptions.Timeout:
                        results.append({"error": "Request timed out", "id": sheet_id})
                        status_code = 408
                    except requests.exceptions.ConnectionError:
                        results.append({"error": "Connection error", "id": sheet_id})
                        status_code = 503
                    except requests.exceptions.HTTPError as e:
                        results.append(
                            {"error": f"HTTP Error: {str(e)}", "id": sheet_id}
                        )
                        status_code = response.status_code
                    except requests.exceptions.RequestException as e:
                        results.append(
                            {"error": f"Request failed: {str(e)}", "id": sheet_id}
                        )
                        status_code = 500

        except Exception as e:
            self.logger.exception("Unexpected error in RemoveSheetsWorker")
            results.append({"error": f"Unhandled error: {str(e)}"})
            status_code = 500

        finally:
            self.signals.success.emit(results, status_code, self.sheets)
            self.signals.finished.emit()
            self.logger.info(
                f"Finished deleting {len(self.sheets)} sheets in {time.perf_counter() - start:.2f}s"
            )
