import msgspec
import requests

from utils.inventory.component import Component
from utils.workers.base_worker import BaseWorker


class AddComponentWorker(BaseWorker):
    def __init__(self, component: Component):
        super().__init__(name="AddComponentWorker")
        self.component = component
        self.url = f"{self.DOMAIN}/components_inventory/add_component"

    def do_work(self) -> tuple[dict, Component]:
        self.logger.info(f"Adding new component via POST to {self.url}")
        data = self.component.to_dict()

        with requests.Session() as session:
            response = session.post(self.url, json=data, headers=self.headers, timeout=10)
            response.raise_for_status()

            try:
                response_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("Failed to decode server response")

            if not isinstance(response_data, dict) or "id" not in response_data:
                raise ValueError("Invalid data format received")

            response_data["component_data"] = {
                "id": response_data["id"],
                "data": data,
            }

            return (response_data, self.component)
