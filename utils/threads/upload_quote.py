import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port
from utils.quote.quote import Quote


class UploadQuote(QThread):
    signal = pyqtSignal(str)

    def __init__(self, folder: str, quote: Quote, html_file_contents: str):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.folder = folder
        self.quote = quote
        self.html_file_contents = html_file_contents
        self.upload_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/upload_quote"

    def run(self):
        try:
            data = {
                "folder": self.folder,
                "html_file_contents": self.html_file_contents,
            }
            files = {
                "quote_data": (
                    "quote.json",
                    msgspec.json.encode(self.quote.to_dict()),
                    "application/json",
                )
            }
            response = requests.post(self.upload_url, data=data, files=files, timeout=10)
            if response.status_code == 200:
                self.signal.emit("Quote sent successfully")
            else:
                self.signal.emit(str(response.status_code))
        except Exception as e:
            self.signal.emit(str(e))
