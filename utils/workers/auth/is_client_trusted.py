import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class IsClientTrustedWorker(BaseWorker):
    def __init__(self):
        super().__init__(name="IsClientTrustedWorker")
        self.url = f"{self.DOMAIN}/is_client_trusted"

    def do_work(self):
        try:
            with requests.Session() as session:
                response = session.get(self.url, headers=self.headers, timeout=10)
                response.raise_for_status()
                response_data = response.json()
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
