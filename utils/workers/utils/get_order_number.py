import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class GetOrderNumberWorker(BaseWorker):
    def __init__(self):
        super().__init__(name="GetOrderNumberWorker")
        self.url = f"{self.DOMAIN}/get_order_number"

    def do_work(self):
        self.logger.info(f"Requesting order number from {self.url}")
        try:
            with requests.Session() as session:
                response = session.get(self.url, headers=self.headers, timeout=10)
                response.raise_for_status()
                response_data = msgspec.json.decode(response.content)
                return response_data
        except requests.HTTPError as http_err:
            self.signals.error.emit(
                f"HTTP error occurred: {http_err}", http_err.response.status_code
            )
        except requests.RequestException as err:
            self.signals.error.emit(f"An error occurred: {err}", 500)
        except msgspec.DecodeError:
            self.signals.error.emit("Failed to parse JSON response", 500)
        return None
