import msgspec
import requests

from utils.inventory.coating_item import CoatingItem
from utils.workers.base_worker import BaseWorker


class UpdateCoatingsWorker(BaseWorker):
    def __init__(self, coatings: list[CoatingItem]):
        super().__init__(name="UpdateCoatingsWorker")
        self.coatings = coatings
        self.url = f"{self.DOMAIN}/coatings_inventory/update_coatings"

    def do_work(self):
        self.logger.info(f"Sending update for {len(self.coatings)} coatings to {self.url}")

        data = [coating.to_dict() for coating in self.coatings]

        with requests.Session() as session:
            response = session.post(self.url, json=data, headers=self.headers, timeout=10)
            response.raise_for_status()
            try:
                response_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("JSON parse error from server")
            return response_data
