import msgspec
import requests

from utils.workers.base_worker import BaseWorker
from utils.workspace.job import Job


class SaveJobWorker(BaseWorker):
    def __init__(self, job: Job):
        super().__init__(name="SaveJobWorker")
        self.job = job
        self.upload_url = f"{self.DOMAIN}/jobs/save"

    def do_work(self):
        try:
            self.job.update_inventory_items_data()
            files = {
                "job_data": (
                    "job.json",
                    msgspec.json.encode(self.job.to_dict()),
                    "application/json",
                )
            }
            with requests.Session() as session:
                response = session.post(
                    self.upload_url,
                    files=files,
                    headers=self.headers,
                    timeout=10,
                )
                response.raise_for_status()
                response_data = msgspec.json.decode(response.content)
                return response_data
        except requests.HTTPError as http_err:
            self.signals.error.emit(f"HTTP error occurred: {http_err}", http_err.response.status_code)
        except requests.RequestException as err:
            self.signals.error.emit(f"An error occurred: {err}", 500)
        except msgspec.DecodeError:
            self.signals.error.emit("Failed to parse JSON response", 500)
        return None

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
