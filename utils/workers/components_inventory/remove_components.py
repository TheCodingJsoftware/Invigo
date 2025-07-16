import msgspec
import requests

from utils.inventory.component import Component
from utils.workers.base_worker import BaseWorker


class RemoveComponentsWorker(BaseWorker):
    def __init__(self, components: list[Component]):
        super().__init__(name="RemoveComponentsWorker")
        self.components = components

    def do_work(self) -> tuple[list, list[Component]]:
        results: list[dict[str, str | int | bool]] = []

        with requests.Session() as session:
            for component in self.components:
                component_id = component.id
                url = f"{self.DOMAIN}/components_inventory/delete_component/{component_id}"
                self.logger.info(f"Attempting to delete component ID {component_id}")

                try:
                    response = session.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()

                    try:
                        result = msgspec.json.decode(response.content)
                        if isinstance(result, bool):
                            results.append({"deleted": result, "id": component_id})
                        else:
                            self.logger.warning(f"Invalid format deleting component {component_id}")
                            results.append({"error": "Invalid data format", "id": component_id})
                    except msgspec.DecodeError:
                        results.append({"error": "Failed to decode response", "id": component_id})
                except requests.exceptions.Timeout:
                    results.append({"error": "Request timed out", "id": component_id})
                except requests.exceptions.ConnectionError:
                    results.append({"error": "Connection error", "id": component_id})
                except requests.exceptions.HTTPError as e:
                    results.append({"error": f"HTTP Error: {str(e)}", "id": component_id})
                except requests.exceptions.RequestException as e:
                    results.append({"error": f"Request failed: {str(e)}", "id": component_id})

        return (results, self.components)
