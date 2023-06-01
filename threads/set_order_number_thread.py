import requests
from PyQt5.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class SetOrderNumberThread(QThread):
    """This is a class for a thread that sets an order number."""

    signal = pyqtSignal(object)

    def __init__(self, order_number: int) -> None:
        """
        This function initializes a QThread object with a server IP address, port number, URL, and order
        number data.

        Args:
          order_number (int): The order number is an integer value that is passed as an argument to the
        constructor of a class. It is used to create a data dictionary that will be sent to a server
        using an HTTP request. The order number is a unique identifier for an order that is being
        processed by the system.
        """
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/set_order_number"
        self.data = {"order_number": order_number}

    def run(self) -> None:
        """
        This function sends a POST request to a specified URL with provided data and emits a signal
        indicating success or failure.
        """
        try:
            response = requests.post(self.url, data=self.data)

            if response.status_code == 200:
                # Process the received response
                self.signal.emit("success")
            else:
                self.signal.emit(f"Error sending command:{response.status_code}")
        except Exception as e:
            self.signal.emit(e)
