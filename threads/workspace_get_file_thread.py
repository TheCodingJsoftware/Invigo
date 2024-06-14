import os
from pathlib import Path

import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart


class WorkspaceDownloadFile(QThread):
    signal = pyqtSignal(str, str, bool)

    def __init__(self, file_to_download: str, open_when_done: bool) -> None:
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.file_to_download = file_to_download
        self.open_when_done = open_when_done
        self.file_url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace_get_file/"

    def run(self) -> None:
        try:
            response = requests.get(self.file_url + self.file_to_download, timeout=10)
            file_name = os.path.basename(self.file_to_download)
            file_ext = file_name.split(".")[-1].upper()
            Path(f"data/workspace/{file_ext}").mkdir(parents=True, exist_ok=True)
            if response.status_code == 200:
                # Save the received file to a local location
                with open(f"data/workspace/{file_ext}/{file_name}", "wb") as file:
                    file.write(response.content)
                self.signal.emit(file_ext, file_name, self.open_when_done)
            else:
                self.signal.emit(None, response.text, False)
        except Exception as e:
            print(e)
            self.signal.emit(None, str(e), False)
