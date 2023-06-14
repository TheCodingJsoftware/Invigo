import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class SendReportThread(QThread):
    """
    The SendReportThread class is a subclass of QThread in Python.
    """

    signal = pyqtSignal(object)

    def __init__(self) -> None:
        """
        The function is a constructor for a class that inherits from QThread. It takes a list of strings
        as an argument and returns None

        Args:
          file_to_upload (list[str]): list[str] = list of files to upload
        """
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.command_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/command"
        self.data = {"command": "send_sheet_report"}

    def run(self) -> None:
        """
        This function sends a POST request to a specified URL with provided data and emits a signal
        indicating success or failure.
        """
        try:
            response = requests.post(self.command_url, data=self.data)

            if response.status_code == 200:
                # Process the received response
                self.signal.emit("Successfully uploaded")
            else:
                self.signal.emit(f"Error sending command:{response.status_code}")
        except Exception as e:
            self.signal.emit(e)
