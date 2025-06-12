import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetJobsThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/get_job_directories"

    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            data = response.json()

            if response.status_code == 200:
                self.signal.emit(data)
            else:
                self.signal.emit(f"Error sending command:{response.status_code}")
        except requests.exceptions.RequestException as e:
            self.signal.emit(e)
