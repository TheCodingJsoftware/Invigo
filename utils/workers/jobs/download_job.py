import msgspec
import requests

from utils.workers.base_worker import BaseWorker


class DownloadJobWorker(BaseWorker):
    def __init__(self, folder_name: str):
        super().__init__()
        self.folder_name = folder_name
        self.url = f"{self.DOMAIN}/download_job/{self.folder_name}"

    def run(self):
        try:
            with requests.Session() as session:
                response = session.get(self.url, timeout=10)
                response.raise_for_status()

                response_data = msgspec.json.decode(response.content)
                self.signals.success.emit(response_data, self.folder_name)

        except requests.HTTPError as http_err:
            self.signals.error.emit(
                f"HTTP error occurred: {http_err}", self.folder_name
            )
        except requests.RequestException as err:
            self.signals.error.emit(f"An error occurred: {err}", self.folder_name)
        except msgspec.DecodeError:
            self.signals.error.emit("Failed to parse JSON response", self.folder_name)
