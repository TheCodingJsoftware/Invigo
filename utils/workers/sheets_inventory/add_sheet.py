import msgspec
import requests

from utils.inventory.sheet import Sheet
from utils.workers.base_worker import BaseWorker


class AddSheetWorker(BaseWorker):
    def __init__(self, sheet: Sheet):
        super().__init__(name="AddSheetWorker")
        self.sheet = sheet
        self.url = f"{self.DOMAIN}/sheets_inventory/add_sheet"

    def do_work(self) -> tuple[dict, Sheet]:
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

            return (response_data, self.sheet)
