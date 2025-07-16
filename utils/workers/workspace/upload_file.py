import requests

from utils.workers.base_worker import BaseWorker


class WorkspaceUploadWorker(BaseWorker):
    def __init__(self, files_to_upload: list[str]):
        super().__init__(name="WorkspaceUploadWorker")
        self.upload_url = f"{self.DOMAIN}/workspace_upload"
        self.files_to_upload = files_to_upload

    def do_work(self):
        for file_path in self.files_to_upload:
            self.logger.info(f"Uploading file: {file_path}")
            try:
                with open(file_path, "rb") as file:
                    files = {"file": (file_path, file.read())}
                    response = requests.post(self.upload_url, files=files, headers=self.headers, timeout=10)
                    response.raise_for_status()
            except FileNotFoundError:
                raise ValueError(f"File not found: {file_path}")
            except Exception as e:
                self.logger.warning(f"Failed to upload {file_path}: {str(e)}")
                raise e

        return "Successfully uploaded"

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
            self.signals.error.emit({"error": str(e)}, 400)
        else:
            super().handle_exception(e)
