import msgspec
import requests

from utils.inventory.sheet import Sheet
from utils.workers.base_worker import BaseWorker


class UpdateSheetsWorker(BaseWorker):
    def __init__(self, sheets: list[Sheet]):
        super().__init__(name="UpdateSheetsWorker")
        self.sheets = sheets
        self.url = f"{self.DOMAIN}/sheets_inventory/update_sheets"

    def do_work(self):
        self.logger.info(f"Sending update for {len(self.sheets)} sheets to {self.url}")

        data = [sheet.to_dict() for sheet in self.sheets]

        with requests.Session() as session:
            response = session.post(self.url, json=data, timeout=10)
            response.raise_for_status()
            try:
                response_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("JSON parse error from server")
            return response_data
