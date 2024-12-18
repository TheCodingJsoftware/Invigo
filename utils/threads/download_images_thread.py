from PyQt6.QtCore import QThread, pyqtSignal
from requests import Session

from utils.ip_utils import get_server_ip_address, get_server_port


class DownloadImagesThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, files_to_download: list[str]):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.files_to_download = files_to_download
        self.session = Session()
        self.file_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/images/"

    def run(self):
        for file_to_download in self.files_to_download:
            try:
                response = self.session.get(
                    self.file_url + file_to_download, timeout=10
                )
                if response.status_code == 200:
                    with open(file_to_download, "wb") as file:
                        file.write(response.content)
                else:
                    self.signal.emit(
                        f"{response.status_code} {file_to_download} not found"
                    )
            except Exception as e:
                self.signal.emit(f"{e} - {file_to_download}")
        self.signal.emit("Successfully downloaded")
        self.session.close()
