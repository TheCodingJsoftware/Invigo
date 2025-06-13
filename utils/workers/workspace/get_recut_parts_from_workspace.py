import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class GetRecutPartsFromWorkspaceWorker(BaseWorker):
    def __init__(self, job_id: int | None = None):
        super().__init__(name="GetRecutPartsFromWorkspaceWorker")
        self.job_id = job_id
        if job_id is not None:
            self.url = f"{self.DOMAIN}/workspace/get_recut_parts_from_job/{job_id}"
        else:
            self.url = f"{self.DOMAIN}/workspace/get_all_recut_parts"

    def do_work(self):
        self.logger.info(f"Requesting recut parts from: {self.url}")
        with requests.Session() as session:
            response = session.get(self.url, timeout=10)
            response.raise_for_status()

            try:
                job_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("Failed to decode server response")

            if not isinstance(job_data, (list, dict)):
                raise ValueError("Invalid data format received")

            return job_data

    def handle_exception(self, e):
        if isinstance(e, requests.exceptions.Timeout):
            self.signals.error.emit({"error": f"Request timed out: {str(e)}"}, 408)
        elif isinstance(e, requests.exceptions.ConnectionError):
            self.signals.error.emit(
                {"error": f"Could not connect to the server: {str(e)}"}, 503
            )
        elif isinstance(e, requests.exceptions.HTTPError):
            self.signals.error.emit(
                {"error": f"HTTP Error: {str(e)}"}, e.response.status_code
            )
        elif isinstance(e, requests.exceptions.RequestException):
            self.signals.error.emit({"error": f"Request failed: {str(e)}"}, 500)
        elif isinstance(e, ValueError):
            self.signals.error.emit({"error": str(e)}, 500)
        else:
            super().handle_exception(e)
