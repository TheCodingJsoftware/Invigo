import contextlib
import socket
from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal

from utils.ip_utils import (
    get_buffer_size,
    get_server_ip_address,
    get_server_port,
    get_server_timeout,
    get_system_ip_address,
)


class ChangesThread(QThread):
    """
    Downloads server data to the client
    """

    signal = pyqtSignal(object)

    def __init__(self, files_to_download: list[str], delay: int) -> None:
        """
        The function is used to download a file from a server

        Args:
          file_to_download (str): The name of the file to download
          delay (int): The time to wait before sending the next packet.
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

        self.files_to_download: str = files_to_download
        self.delay = delay

    def run(self) -> None:
        """
        It connects to a server, sends a message, receives a file, and then closes the connection
        """
        # Give the app time to first download all files on startup
        sleep(30)
        while True:
            try:
                for file_to_download in self.files_to_download:
                    self.server = (self.SERVER_IP, self.SERVER_PORT)
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.settimeout(get_server_timeout())
                    self.socket.connect(self.server)

                    self.socket.send(
                        f"get_modified_date{self.SEPARATOR}{file_to_download}".encode(
                            "utf-8"
                        )
                    )
                    # self.socket.send(
                    #     f"get_file{self.SEPARATOR}{file_to_download}".encode("utf-8")
                    # )

                    # filesize: int = int(self.socket.recv(1024).decode("utf-8"))

                    new_name = file_to_download.replace(".json", " - Compare.json")
                    sleep(0.5)  # ! IMPORTANT
                    file_modified_date = self.socket.recv(self.BUFFER_SIZE).decode(
                        "utf-8"
                    )
                    with open(new_name, "w") as f:
                        f.write(file_modified_date)
                    #     while True:
                    #         if bytes_read := self.socket.recv(self.BUFFER_SIZE):
                    #             f.write(bytes_read)
                    #         else:
                    #             # file transmitting is done
                    #             sleep(1)  # ! IMPORTANT
                    #             break
                    self.socket.shutdown(2)
                    self.socket.close()
                self.signal.emit("")
            except Exception as error:
                with contextlib.suppress(AttributeError):
                    self.signal.emit(error)
            sleep(self.delay)
