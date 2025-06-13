# update_sheet_worker.py
import msgspec
import requests

from utils.inventory.sheet import Sheet
from utils.threads.base_worker import BaseWorker


class UpdateSheetWorker(BaseWorker):
    def __init__(self, sheet: Sheet):
        super().__init__(name="UpdateSheetWorker")
        self.sheet = sheet
        self.sheet_id = sheet.id
        self.url = f"{self.DOMAIN}/sheets_inventory/update_sheet/{self.sheet_id}"

    def do_work(self):
        self.logger.info(f"Sending update for sheet {self.sheet_id} to {self.url}")
        data = self.sheet.to_dict()

        with requests.Session() as session:
            response = session.post(self.url, json=data, timeout=10)
            response.raise_for_status()

            try:
                job_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("Failed to decode server response")

            job_data["sheet_data"] = {
                "id": self.sheet_id,
                "data": data,
            }

            return job_data

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
