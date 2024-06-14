from PyQt6.QtCore import QThread, pyqtSignal
from requests import Session

from utils.ip_utils import get_server_ip_address, get_server_port


class DownloadImagesThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, files_to_download: list[str]) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.files_to_download = files_to_download
        self.session = Session()
        self.file_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/"

    def run(self) -> None:
        for file_to_download in self.files_to_download:
            if not file_to_download.endswith(".jpeg"):
                file_to_download += ".jpeg"
            if "images" not in file_to_download:
                file_to_download = f"images/{file_to_download}"
            try:
                response = self.session.get(self.file_url + file_to_download, timeout=10)
                if response.status_code == 200:
                    with open(file_to_download, "wb") as file:
                        file.write(response.content)
                else:
                    self.signal.emit(response.text)
            except Exception as e:
                self.signal.emit(e)
        self.signal.emit("Successfully downloaded")
        self.session.close()
