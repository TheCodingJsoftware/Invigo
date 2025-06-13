# get_all_jobs_from_workspace_worker.py

import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class GetAllWorkspaceJobsWorker(BaseWorker):
    def __init__(self):
        super().__init__(name="GetAllWorkspaceJobsWorker")
        self.url = f"{self.DOMAIN}/workspace/get_all_jobs"

    def do_work(self):
        self.logger.info(f"Requesting all jobs from: {self.url}")

        with requests.Session() as session:
            response = session.get(self.url, timeout=10)
            response.raise_for_status()

            try:
                job_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("Failed to decode server response")

            if not isinstance(job_data, dict):
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
