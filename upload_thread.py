import logging
import os
import socket

from PyQt5.QtCore import QThread, pyqtSignal

import log_config
from utils.ip_utils import get_server_ip_address, get_server_port, get_system_ip_address
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class UploadThread(QThread):
    """
    Uploads client data to the server
    """

    signal = pyqtSignal(object)

    def __init__(self, file_to_upload: str) -> None:
        """
        A constructor function.

        Args:
          file_to_upload (str): str = The file to upload
        """
        QThread.__init__(self)
        # Declaring server IP and port
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()

        # Declaring clients IP and port
        self.CLIENT_IP: str = get_system_ip_address()
        self.CLIENT_PORT: int = 4005

        self.BUFFER_SIZE = 4096
        self.SEPARATOR = "<SEPARATOR>"

        self.file_to_upload = file_to_upload
        self.filesize = os.path.getsize(self.file_to_upload)

    def run(self) -> None:
        """
        It connects to a server, sends a message, and then sends the file
        """
        try:
            self.server = (self.SERVER_IP, self.SERVER_PORT)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(10)
            self.s.connect(self.server)

            self.s.send(
                f"send_file{self.SEPARATOR}{self.file_to_upload}{self.SEPARATOR}{self.filesize}".encode()
            )
            with open(self.file_to_upload, "rb") as f:
                while True:
                    bytes_read = f.read(self.BUFFER_SIZE)
                    if not bytes_read:
                        break
                    self.s.sendall(bytes_read)

            self.s.close()

            self.signal.emit("Successfully uploaded")
        except Exception as e:
            logging.exception("Exception occurred")
            self.signal.emit(e)
