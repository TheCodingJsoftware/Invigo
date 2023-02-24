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


class DownloadThread(QThread):
    """
    Downloads server data to the client
    """

    signal = pyqtSignal(object)

    def __init__(self, files_to_download: list[str]) -> None:
        """
        The function is a constructor for a class that inherits from QThread. It takes a string as an
        argument and returns None

        Args:
          file_to_download (str): The file to download from the server
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

        self.files_to_download = files_to_download

    def run(self) -> None:
        """
        It connects to a server, sends a command to download a file, receives the file size, receives
        the file, and then closes the connection
        """
        for file_to_download in self.files_to_download:
            try:
                self.server = (self.SERVER_IP, self.SERVER_PORT)
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(get_server_timeout())
                self.socket.connect(self.server)

                self.socket.send(
                    f"get_file{self.SEPARATOR}{file_to_download}".encode("utf-8")
                )
                time.sleep(0.5)  # ! IMPORTANT

                filesize: int = int(self.socket.recv(1024).decode("utf-8"))
                time.sleep(0.5)  # ! IMPORTANT
                print(filesize)
                with open(file_to_download, "wb") as f:
                    while True:
                        if bytes_read := self.socket.recv(self.BUFFER_SIZE):
                            f.write(bytes_read)
                        else:
                            # file transmitting is done
                            time.sleep(0.5)  # ! IMPORTANT
                            break
                self.socket.shutdown(2)
                self.socket.close()
                time.sleep(0.5)
            except Exception as e:
                print(e)
                self.signal.emit(e)
        self.signal.emit("Successfully downloaded")
