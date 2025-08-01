import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class DeleteWorkorderWorker(BaseWorker):
    def __init__(self, workorder_id: int):
        super().__init__(name="DeleteJobWorker")
        self.url = f"{self.DOMAIN}/workorders/delete/{workorder_id}"

    def do_work(self):
        try:
            response = requests.post(self.url, headers=self.headers, timeout=10)
            response_data = msgspec.json.decode(response.content)
            return response_data
        except requests.HTTPError as http_err:
            self.signals.error.emit(f"HTTP error occurred: {http_err}", http_err.response.status_code)
        except requests.RequestException as err:
            self.signals.error.emit(f"An error occurred: {err}", 500)
        except msgspec.DecodeError:
            self.signals.error.emit("Failed to parse JSON response", 500)
        return None
