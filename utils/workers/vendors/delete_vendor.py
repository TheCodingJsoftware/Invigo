import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class DeleteVendorWorker(BaseWorker):
    def __init__(self, vendor_id: int):
        super().__init__(name="DeleteVendorWorker")
        self.url = f"{self.DOMAIN}/vendors/delete/{vendor_id}"
        self.vendor_id = vendor_id

    def do_work(self):
        try:
            with requests.Session() as session:
                response = session.post(
                    self.url,
                    headers=self.headers,
                    timeout=10,
                )
                response.raise_for_status()
                return self.vendor_id
        except requests.HTTPError as http_err:
            self.signals.error.emit(f"HTTP error occurred: {http_err}", http_err.response.status_code)
        except requests.RequestException as err:
            self.signals.error.emit(f"An error occurred: {err}", 500)
        except msgspec.DecodeError:
            self.signals.error.emit("Failed to parse JSON response", 500)
        return None
