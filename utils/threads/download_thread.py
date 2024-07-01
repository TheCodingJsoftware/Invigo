from PyQt6.QtCore import QThread, pyqtSignal
from requests import Session

from utils.ip_utils import get_server_ip_address, get_server_port


class DownloadThread(QThread):
    signal = pyqtSignal(object, list)

    def __init__(self, files_to_download: list[str]) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.files_to_download = files_to_download
        self.session = Session()
        self.file_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/file/"

    def run(self) -> None:
        successful_downloads = []
        failed_downloads = []

        for file_to_download in self.files_to_download:
            try:
                response = self.session.get(self.file_url + file_to_download, timeout=10)

                if response.status_code == 200:
                    filepath = f"data/{file_to_download}"
                    with open(filepath, "wb") as file:
                        file.write(response.content)
                    successful_downloads.append(file_to_download)
                else:
                    failed_downloads.append(file_to_download)
            except Exception as e:
                failed_downloads.append((file_to_download, str(e)))

        if failed_downloads:
            self.signal.emit({"status": "failed", "failed_files": failed_downloads}, self.files_to_download)
        else:
            self.signal.emit({"status": "success", "successful_files": successful_downloads}, self.files_to_download)

        self.session.close()
