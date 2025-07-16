import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class DeleteShippingAddressWorker(BaseWorker):
    def __init__(self, shipping_address_id: int):
        super().__init__(name="DeleteShippingAddressWorker")
        self.url = f"{self.DOMAIN}/shipping_addresses/delete/{shipping_address_id}"
        self.shipping_address_id = shipping_address_id

    def do_work(self):
        try:
            with requests.Session() as session:
                response = session.post(
                    self.url,
                    headers=self.headers,
                    timeout=10,
                )
                response.raise_for_status()
                return self.shipping_address_id
        except requests.HTTPError as http_err:
            self.signals.error.emit(f"HTTP error occurred: {http_err}", http_err.response.status_code)
        except requests.RequestException as err:
            self.signals.error.emit(f"An error occurred: {err}", 500)
        except msgspec.DecodeError:
            self.signals.error.emit("Failed to parse JSON response", 500)
        return None
