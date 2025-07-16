import msgspec
import requests

from utils.inventory.component import Component
from utils.workers.base_worker import BaseWorker


class UpdateComponentsWorker(BaseWorker):
    def __init__(self, components: list[Component]):
        super().__init__(name="UpdateComponentsWorker")
        self.components = components
        self.url = f"{self.DOMAIN}/components_inventory/update_components"

    def do_work(self):
        self.logger.info(f"Sending update for {len(self.components)} components to {self.url}")

        data = [component.to_dict() for component in self.components]

        with requests.Session() as session:
            response = session.post(self.url, json=data, headers=self.headers, timeout=10)
            response.raise_for_status()
            try:
                response_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("JSON parse error from server")
            return response_data
