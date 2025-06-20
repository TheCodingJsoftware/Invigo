# workspace_download_worker.py

import os

import requests

from config.environments import Environment
from utils.workers.base_worker import BaseWorker


class WorkspaceDownloadWorker(BaseWorker):
    def __init__(
        self,
        files_to_download: list[str],
        open_when_done: bool,
        download_directory: str | None = None,
    ):
        super().__init__(name="WorkspaceDownloadWorker")
        self.files_to_download = files_to_download
        self.open_when_done = open_when_done
        self.download_directory = download_directory or os.path.join(
            Environment.DATA_PATH, "data", "workspace"
        )
        self.file_url = f"{self.DOMAIN}/workspace/get_file/"

    def do_work(self):
        try:
            with requests.Session() as session:
                for file_to_download in self.files_to_download:
                    response = session.get(
                        f"{self.file_url}{file_to_download}",
                        headers=self.headers,
                        timeout=10,
                    )
                    file_name = os.path.basename(file_to_download)
                    file_ext = file_name.split(".")[-1].upper()
                    save_dir = os.path.join(self.download_directory, file_ext)
                    os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(save_dir, file_name)

                    if response.status_code == 200:
                        with open(save_path, "wb") as file:
                            file.write(response.content)

                        self.signals.success.emit(
                            file_ext, file_name, self.open_when_done
                        )
                        self.logger.info(f"Downloaded: {file_name}")

                        if self.open_when_done:
                            return  # Stop after the first download if we need to open it
                    else:
                        self.signals.error.emit(None, response.text, False)
                        self.logger.error(
                            f"Failed to download {file_name}: {response.text}"
                        )

        except Exception as e:
            self.signals.error.emit(None, str(e), False)
            self.logger.exception("Download error")

        if not self.open_when_done:
            self.signals.success.emit(
                "Successfully downloaded", "Successfully downloaded", False
            )
