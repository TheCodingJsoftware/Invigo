import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetOrderNumberThread(QThread):
    """This is a class for a thread that retrieves an order number."""

    signal = pyqtSignal(int)

    def __init__(self) -> None:
        """
        This function initializes a QThread object and sets the url to retrieve an order number from a
        server.
        """
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/get_order_number"

    def run(self) -> None:
        """
        This function sends a POST request to a specified URL with provided data and emits a signal
        indicating success or failure.
        """
        try:
            response = requests.get(self.url)
            data = response.json()
            order_number = data.get("order_number")

            if response.status_code == 200:
                # Process the received response
                self.signal.emit(order_number)
            else:
                self.signal.emit(f"Error sending command:{response.status_code}")
        except Exception as e:
            self.signal.emit(e)
