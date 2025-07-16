import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class GetComponentWorker(BaseWorker):
    def __init__(self, component_id: int | str):
        super().__init__(name="GetComponentWorker")
        self.component_id = component_id
        self.url = f"{self.DOMAIN}/components_inventory/get_component/{self.component_id}"

    def do_work(self):
        self.logger.info(f"Fetching component ID {self.component_id} from {self.url}")
        with requests.Session() as session:
            response = session.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()

            try:
                component_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("Failed to decode server response")

            if not isinstance(component_data, dict):
                raise ValueError("Invalid data format received")

            return component_data

    def handle_exception(self, e):
        if isinstance(e, requests.exceptions.Timeout):
            self.signals.error.emit({"error": "Request timed out"}, 408)
        elif isinstance(e, requests.exceptions.ConnectionError):
            self.signals.error.emit({"error": "Could not connect to the server"}, 503)
        elif isinstance(e, requests.exceptions.HTTPError):
            self.signals.error.emit({"error": f"HTTP Error: {str(e)}"}, e.response.status_code)
        elif isinstance(e, requests.exceptions.RequestException):
            self.signals.error.emit({"error": f"Request failed: {str(e)}"}, 500)
        elif isinstance(e, ValueError):
            self.signals.error.emit({"error": str(e)}, 500)
        else:
            super().handle_exception(e)
