import os
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from requests import Session

from config.environments import Environment
from utils.ip_utils import get_server_ip_address, get_server_port


class WorkspaceDownloadFile(QThread):
    signal = pyqtSignal(str, str, bool)

    def __init__(
        self,
        files_to_download: list[str],
        open_when_done: bool,
        download_directory: str = None,
    ):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.files_to_download = files_to_download
        self.download_directory = download_directory
        if not self.download_directory:
            self.download_directory = os.path.join(
                Environment.DATA_PATH, "data", "workspace"
            )
        self.session = Session()
        self.open_when_done = open_when_done
        self.file_url = (
            f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace/get_file/"
        )

    def run(self):
        for file_to_download in self.files_to_download:
            try:
                response = self.session.get(
                    self.file_url + file_to_download, timeout=10
                )
                file_name = os.path.basename(file_to_download)
                file_ext = file_name.split(".")[-1].upper()
                Path(f"{self.download_directory}/{file_ext}").mkdir(
                    parents=True, exist_ok=True
                )
                if response.status_code == 200:
                    with open(
                        f"{self.download_directory}/{file_ext}/{file_name}", "wb"
                    ) as file:
                        file.write(response.content)
                    if self.open_when_done:
                        self.signal.emit(file_ext, file_name, self.open_when_done)
                        self.session.close()
                        return
                else:
                    self.signal.emit(None, response.text, False)
            except Exception as e:
                self.signal.emit(None, str(e), False)
        self.signal.emit(
            "Successfully downloaded", "Successfully downloaded", self.open_when_done
        )
        self.session.close()
