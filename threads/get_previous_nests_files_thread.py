import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetPreviousNestsFilesThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/get_previous_nests_files"

    def run(self) -> None:
        try:
            response = requests.get(self.url)
            data = response.json()

            if response.status_code == 200:
                self.signal.emit(data)
            else:
                self.signal.emit(f"Error sending command:{response.status_code}")
        except Exception as e:
            self.signal.emit(e)
