from PyQt6.QtCore import QThread, pyqtSignal
from requests import Session

from utils.ip_utils import get_server_ip_address, get_server_port


class UploadThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, file_to_upload: list[str]) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.upload_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/upload"
        self.session = Session()
        self.files_to_upload = file_to_upload

    def run(self) -> None:
        try:
            for file_to_upload in self.files_to_upload:
                if file_to_upload.endswith(".json"):
                    with open(f"data/{file_to_upload}", "rb") as file:
                        file = {"file": (file_to_upload, file.read(), "application/json")}
                elif file_to_upload.endswith(".jpeg") or file_to_upload.endswith(".png") or file_to_upload.endswith(".jpg"):
                    with open(file_to_upload, "rb") as file:
                        file = {"file": (file_to_upload, file.read(), "image/jpeg")}
                response = self.session.post(self.upload_url, files=file, timeout=10)
                if response.status_code == 200:
                    self.signal.emit("Successfully uploaded")
                else:
                    self.signal.emit(response.status_code)
            self.session.close()
        except Exception as e:
            self.signal.emit(e)
            self.session.close()
