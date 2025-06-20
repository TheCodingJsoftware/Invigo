import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class DownloadJobWorker(BaseWorker):
    def __init__(self, folder_name: str):
        super().__init__()
        self.folder_name = folder_name
        self.url = f"{self.DOMAIN}/download_job/{self.folder_name}"

    def do_work(self):
        with requests.Session() as session:
            response = session.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()

            try:
                response_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("Failed to decode server response")

            if not isinstance(response_data, dict):
                raise ValueError("Invalid data format received")

            return (response_data, self.folder_name)

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
            self.signals.error.emit({"error": f"Request failed: {str(e)}"}, 500)
        elif isinstance(e, ValueError):
            self.signals.error.emit({"error": str(e)}, 500)
        else:
            super().handle_exception(e)
