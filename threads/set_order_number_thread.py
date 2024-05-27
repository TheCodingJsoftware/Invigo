import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class SetOrderNumberThread(QThread):
    """This is a class for a thread that sets an order number."""

    signal = pyqtSignal(object)

    def __init__(self, order_number: float) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/set_order_number"
        self.data = {"order_number": order_number}

    def run(self) -> None:
        try:
            response = requests.post(self.url, data=self.data)

            if response.status_code == 200:
                # Process the received response
                self.signal.emit("success")
            else:
                self.signal.emit(f"Error sending command:{response.status_code}")
        except Exception as e:
            self.signal.emit(e)
