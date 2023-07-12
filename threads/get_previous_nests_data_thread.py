import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetPreviousNestsDataThread(QThread):
    """This is a class for a thread that retrieves data."""

    signal = pyqtSignal(object)

    def __init__(self, files_to_load: list[str]) -> None:
        """
        This function initializes a QThread object and sets the url to retrieve an order number from a
        server.
        """
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.files_to_load: list[str] = files_to_load
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/get_previous_nests_data"

    def run(self) -> None:
        """
        This function sends a POST request to a specified URL with provided data and emits a signal
        indicating success or failure.
        """
        try:
            # Create the request payload as a dictionary
            data = {"file_names": ";".join(self.files_to_load)}

            # Send the POST request
            response = requests.post(self.url, data=data)

            # Check the response status code
            if response.status_code == 200:
                combined_data = response.json()
                self.signal.emit(combined_data)
            else:
                self.signal.emit(f"Error sending command:{response.status_code}")
        except Exception as e:
            self.signal.emit(str(e))
