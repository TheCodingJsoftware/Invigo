import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class UploadSheetsSettingsThread(QThread):

    signal = pyqtSignal(str, str)

    def __init__(self) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()

        self.json_file_path = "price_of_steel_information.json"
        self.upload_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/upload_sheets_settings"

    def run(self) -> None:
        try:
            # Send the file as a POST request to the server
            with open(self.json_file_path, "rb") as file:
                file = {"file": (self.json_file_path, file.read(), "application/json")}
                response = requests.post(self.upload_url, data=file)

            if response.status_code == 200:
                self.signal.emit("Sheets settings sent successfully", self.json_file_path)
            else:
                self.signal.emit(str(response.status_code), self.json_file_path)
        except Exception as e:
            self.signal.emit(str(e), self.json_file_path)
