import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class GetAllSheetsWorker(BaseWorker):
    def __init__(self):
        super().__init__(name="GetAllSheetsWorker")
        self.url = f"{self.DOMAIN}/sheets_inventory/get_all"

    def do_work(self):
        self.logger.info(f"Requesting all sheets from {self.url}")
        with requests.Session() as session:
            response = session.get(self.url, timeout=10)
            response.raise_for_status()

            try:
                all_sheets = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("Failed to decode server response")

            if not isinstance(all_sheets, list):
                raise ValueError("Invalid data format received")

            return all_sheets

    def handle_exception(self, e):
        if isinstance(e, requests.exceptions.Timeout):
            self.signals.error.emit({"error": "Request timed out"}, 408)
        elif isinstance(e, requests.exceptions.ConnectionError):
            self.signals.error.emit({"error": "Could not connect to the server"}, 503)
        elif isinstance(e, requests.exceptions.HTTPError):
            self.signals.error.emit(
                {"error": f"HTTP Error: {str(e)}"}, e.response.status_code
            )
        elif isinstance(e, requests.exceptions.RequestException):
            self.signals.error.emit({"error": f"Request failed: {str(e)}"}, 500)
        elif isinstance(e, ValueError):
            self.signals.error.emit({"error": str(e)}, 500)
        else:
            super().handle_exception(e)
