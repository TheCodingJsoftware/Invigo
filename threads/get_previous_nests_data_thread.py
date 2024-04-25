import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetPreviousNestsDataThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, files_to_load: list[str]) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.files_to_load: list[str] = files_to_load
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/get_previous_nests_data"

    def run(self) -> None:
        try:
            data = {"file_names": ";".join(self.files_to_load)}
            response = requests.post(self.url, data=data)
            if response.status_code == 200:
                combined_data = response.json()
                self.signal.emit(combined_data)
            else:
                self.signal.emit(f"Error sending command:{response.status_code}")
        except Exception as e:
            self.signal.emit(str(e))
