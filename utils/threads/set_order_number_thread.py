import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class SetOrderNumberThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, order_number: float):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/set_order_number/{int(order_number)}"

    def run(self):
        try:
            response = requests.post(self.url, timeout=10)

            if response.status_code == 200:
                self.signal.emit("success")
            else:
                self.signal.emit(f"Error sending command: {response.text}")
        except Exception as e:
            self.signal.emit(e)
