import os
import socket
import time

from PyQt5.QtCore import QThread, pyqtSignal

from utils.ip_utils import (
    get_buffer_size,
    get_server_ip_address,
    get_server_port,
    get_server_timeout,
    get_system_ip_address,
)
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class UploadThread(QThread):
    """
    Uploads client data to the server
    """

    signal = pyqtSignal(object)

    def __init__(self, file_to_upload: list[str]) -> None:
        """
        The function is a constructor for a class that inherits from QThread. It takes a list of strings
        as an argument and returns None

        Args:
          file_to_upload (list[str]): list[str] = list of files to upload
        """
        QThread.__init__(self)
        # Declaring server IP and port
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()

        # Declaring clients IP and port
        self.CLIENT_IP: str = get_system_ip_address()
        self.CLIENT_PORT: int = 4005

        self.BUFFER_SIZE = get_buffer_size()
        self.SEPARATOR = "<SEPARATOR>"

        self.files_to_upload = file_to_upload
        self.filesize = os.path.getsize(self.files_to_upload[0])

    def run(self) -> None:
        """
        It connects to a server, sends a message, and then sends the file
        """
        try:
            for file_to_upload in self.files_to_upload:
                self.server = (self.SERVER_IP, self.SERVER_PORT)
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(get_server_timeout())
                self.socket.connect(self.server)

                self.socket.send(
                    f"send_file{self.SEPARATOR}{file_to_upload}{self.SEPARATOR}{self.filesize}".encode()
                )
                time.sleep(0.5)  # ! IMPORTANT
                with open(file_to_upload, "rb") as f:
                    while True:
                        if bytes_read := f.read(self.BUFFER_SIZE):
                            self.socket.sendall(bytes_read)
                        else:
                            # file transmitting is done
                            time.sleep(0.5)  # ! IMPORTANT
                            break
                self.socket.shutdown(2)
                self.socket.close()
                time.sleep(0.5)
            self.signal.emit("Successfully uploaded")
        except Exception as e:
            self.signal.emit(e)
