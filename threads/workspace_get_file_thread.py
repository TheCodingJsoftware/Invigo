import os
from pathlib import Path

import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class WorkspaceDownloadFiles(QThread):
    """
    Downloads server data to the client
    """

    signal = pyqtSignal(object)

    def __init__(self, file_to_download: str) -> None:
        """
        The function is a constructor for a class that inherits from QThread. It takes a string as an
        argument and returns None

        Args:
          file_to_download (str): The file to download from the server
        """
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.file_to_download = file_to_download
        self.file_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace_get_file/"

    def run(self) -> None:
        """
        This function downloads files from a given URL and saves them to a local location.
        """
        try:
            response = requests.get(self.file_url + self.file_to_download)
            file_name = os.path.basename(self.file_to_download)
            file_ext = file_name.split(".")[-1].upper()
            Path(f"data/workspace/{file_ext}").mkdir(parents=True, exist_ok=True)
            if response.status_code == 200:
                # Save the received file to a local location
                with open(f"data/workspace/{file_ext}/{file_name}", "wb") as file:
                    file.write(response.content)
            else:
                self.signal.emit(response.text)
        except Exception as e:
            print(e)
            self.signal.emit(e)
        self.signal.emit(f"Successfully downloaded;{self.file_to_download}")
