# add_sheet_worker.py
import msgspec
import requests
from PyQt6.QtCore import QObject, pyqtSignal

from utils.inventory.sheet import Sheet
from utils.threads.base_worker import BaseWorker


class AddSheetSignals(QObject):
    success = pyqtSignal(object, int, object)  # (data, status_code, original_sheet)
    error = pyqtSignal(object, int, object)  # (error dict, status_code, original_sheet)
    finished = pyqtSignal()


class AddSheetWorker(BaseWorker):
    def __init__(self, sheet: Sheet):
        super().__init__(name="AddSheetWorker")
        self.sheet = sheet
        self.url = f"{self.DOMAIN}/sheets_inventory/add_sheet"
        self.signals = AddSheetSignals()  # Override default signals

    def do_work(self):
        self.logger.info(f"Adding new sheet via POST to {self.url}")
        data = self.sheet.to_dict()

        with requests.Session() as session:
            response = session.post(self.url, json=data, timeout=10)
            response.raise_for_status()

            try:
                response_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("Failed to decode server response")

            if not isinstance(response_data, dict) or "id" not in response_data:
                raise ValueError("Invalid data format received")

            response_data["sheet_data"] = {
                "id": response_data["id"],
                "data": data,
            }

            return response_data

    def run(self):
        import time

        start = time.perf_counter()
        try:
            self.logger.info("Worker started.")
            result = self.do_work()
            self.signals.success.emit(result, 200, self.sheet)
        except requests.exceptions.Timeout:
            self.signals.error.emit({"error": "Request timed out"}, 408, self.sheet)
        except requests.exceptions.ConnectionError:
            self.signals.error.emit(
                {"error": "Could not connect to the server"}, 503, self.sheet
            )
        except requests.exceptions.HTTPError as e:
            self.signals.error.emit(
                {"error": f"HTTP Error: {str(e)}"}, e.response.status_code, self.sheet
            )
        except requests.exceptions.RequestException as e:
            self.signals.error.emit(
                {"error": f"Request failed: {str(e)}"}, 500, self.sheet
            )
        except Exception as e:
            self.logger.exception("Worker error:")
            self.signals.error.emit({"error": str(e)}, 500, self.sheet)
        finally:
            self.signals.finished.emit()
            self.logger.info(f"Worker finished in {time.perf_counter() - start:.2f}s")
