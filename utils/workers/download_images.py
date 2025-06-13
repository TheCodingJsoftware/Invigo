import os

import requests

from utils.workers.base_worker import BaseWorker


class DownloadImagesWorker(BaseWorker):
    def __init__(self, files_to_download: list[str]):
        super().__init__()
        self.files_to_download = files_to_download
        self.file_url = f"{self.DOMAIN}/images/"

    def run(self):
        try:
            with requests.Session() as session:
                for file_to_download in self.files_to_download:
                    try:
                        url = self.file_url + file_to_download
                        response = session.get(url, timeout=10)
                        response.raise_for_status()

                        os.makedirs(os.path.dirname(file_to_download), exist_ok=True)
                        with open(file_to_download, "wb") as file:
                            file.write(response.content)

                    except requests.RequestException as e:
                        self.signals.error.emit(f"{e} - {file_to_download}")
                        return  # Exit early on failure

            self.signals.success.emit("Successfully downloaded")

        except Exception as e:
            self.signals.error.emit(str(e), 200)
