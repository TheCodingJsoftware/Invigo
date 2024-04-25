import os
import socket
import time

import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port
from utils.json_file import JsonFile


class UploadBatch(QThread):

    signal = pyqtSignal(str, str)

    def __init__(self, json_file_path: str) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()

        self.json_file_path = json_file_path
        self.upload_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/upload"

    def run(self) -> None:
        try:
            # Send the file as a POST request to the server
            with open(self.json_file_path, "rb") as file:
                files = {"file": (self.json_file_path, file.read(), "application/json")}
                response = requests.post(self.upload_url, files=files)

            if response.status_code == 200:
                self.signal.emit("Batch sent successfully", self.json_file_path)
            else:
                self.signal.emit(str(response.status_code), self.json_file_path)
        except Exception as e:
            self.signal.emit(str(e), self.json_file_path)
