import socket

from PyQt5.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port, get_system_ip_address
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class DownloadThread(QThread):
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
        # Declaring server IP and port
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()

        # Declaring clients IP and port
        self.CLIENT_IP: str = get_system_ip_address()
        self.CLIENT_PORT: int = 4005

        self.BUFFER_SIZE = 4096
        self.SEPARATOR = "<SEPARATOR>"

        self.file_to_download: str = file_to_download

    def run(self) -> None:
        """
        It connects to a server, sends a command to download a file, receives the file size, receives
        the file, and then closes the connection
        """
        try:
            self.server = (self.SERVER_IP, self.SERVER_PORT)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(10)
            self.s.connect(self.server)

            self.s.send(
                f"get_file{self.SEPARATOR}{self.file_to_download}".encode("utf-8")
            )

            filesize: int = int(self.s.recv(1024).decode("utf-8"))

            with open(self.file_to_download, "wb") as f:
                while True:
                    bytes_read = self.s.recv(self.BUFFER_SIZE)
                    if not bytes_read:
                        # file transmitting is done
                        break
                    f.write(bytes_read)

            self.s.close()

            self.signal.emit("Successfully downloaded")
        except Exception as e:
            self.signal.emit(e)
