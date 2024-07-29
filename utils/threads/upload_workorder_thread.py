import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port
from utils.workspace.workorder import Workorder


class UploadWorkorderThread(QThread):
    signal = pyqtSignal(str)

    def __init__(self, folder: str, workorder: Workorder, html_file_contents: str) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.folder = folder
        self.workorder = workorder
        self.html_file_contents = html_file_contents
        self.upload_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/upload_workorder"

    def run(self) -> None:
        try:
            data = {
                "folder": self.folder,
                "html_file_contents": self.html_file_contents,
            }
            files = {
                "workorder_data": (
                    "workorder.json",
                    msgspec.json.encode(self.workorder.to_dict()),
                    "application/json",
                )
            }
            response = requests.post(self.upload_url, data=data, files=files, timeout=10)
            if response.status_code == 200:
                self.signal.emit("Workorder sent successfully")
            else:
                self.signal.emit(str(response.status_code))
        except Exception as e:
            self.signal.emit(str(e))
