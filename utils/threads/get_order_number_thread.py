import os

import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetOrderNumberThread(QThread):
    signal = pyqtSignal(int)

    def __init__(self):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/get_order_number"
        self.headers = {"X-Client-Name": os.getlogin()}

    def run(self):
        try:
            with requests.Session() as session:
                response = session.get(self.url, headers=self.headers, timeout=10)
                data = response.json()
                order_number = data.get("order_number")

            if response.status_code == 200:
                # Process the received response
                self.signal.emit(order_number)
            else:
                self.signal.emit(f"Error sending command:{response.status_code}")
        except Exception as e:
            self.signal.emit(e)
