from PyQt6.QtCore import QThread, pyqtSignal
from requests import Session

from utils.ip_utils import get_server_ip_address, get_server_port


class UploadThread(QThread):
    signal = pyqtSignal(object, list)

    def __init__(self, files_to_upload: list[str]):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.upload_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/upload"
        self.session = Session()
        self.files_to_upload = files_to_upload

    def run(self):
        try:
            successful_uploads = []
            failed_uploads = []
            for file_to_upload in self.files_to_upload:
                file = None
                if file_to_upload.endswith(".json"):
                    with open(f"data/{file_to_upload}", "rb") as f:
                        file = {"file": (file_to_upload, f.read(), "application/json")}
                elif file_to_upload.endswith((".jpeg", ".png", ".jpg")):
                    with open(file_to_upload, "rb") as f:
                        file = {"file": (file_to_upload, f.read(), "image/jpeg")}

                if file:
                    response = self.session.post(self.upload_url, files=file, timeout=10)
                    if response.status_code == 200:
                        successful_uploads.append(file_to_upload)
                    else:
                        failed_uploads.append(file_to_upload)

            if failed_uploads:
                self.signal.emit(
                    {"status": "failed", "failed_files": failed_uploads},
                    self.files_to_upload,
                )
            else:
                self.signal.emit(
                    {"status": "success", "successful_files": successful_uploads},
                    self.files_to_upload,
                )
        except Exception as e:
            self.signal.emit({"status": "error", "error": str(e)}, self.files_to_upload)
        finally:
            self.session.close()
