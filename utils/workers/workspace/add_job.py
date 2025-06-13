import msgspec
import requests

from utils.workers.base_worker import BaseWorker
from utils.workspace.job import Job


class AddJobWorker(BaseWorker):
    def __init__(self, job: Job):
        super().__init__(name="AddJobToWorkspaceWorker")
        self.job = job
        self.url = f"{self.DOMAIN}/workspace/add_job"

    def do_work(self):
        self.logger.info(f"Adding job to workspace: {self.job}")
        job_data = msgspec.json.encode(self.job.to_dict())

        with requests.Session() as session:
            response = session.post(self.url, data=job_data, timeout=10)
            response.raise_for_status()

            try:
                response_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("JSON parse error from server")

            if not isinstance(response_data, dict):
                raise ValueError("Unexpected response format")

            return response_data

    def handle_exception(self, e):
        if isinstance(e, requests.exceptions.Timeout):
            self.signals.error.emit({"error": "Request timed out"}, 408)
        elif isinstance(e, requests.exceptions.ConnectionError):
            self.signals.error.emit({"error": "Could not connect to the server"}, 503)
        elif isinstance(e, requests.exceptions.HTTPError):
            self.signals.error.emit(
                {"error": f"HTTP Error: {str(e)}"}, e.response.status_code
            )
        elif isinstance(e, requests.exceptions.RequestException):
            self.signals.error.emit({"error": f"Request error: {str(e)}"}, 500)
        elif isinstance(e, ValueError):
            self.signals.error.emit({"error": str(e)}, 500)
        else:
            super().handle_exception(e)
