import logging
import socket
from time import sleep

from PyQt5.QtCore import QThread, pyqtSignal

import log_config
from utils.ip_utils import get_server_ip_address, get_server_port, get_system_ip_address
from utils.json_file import JsonFile


class ChangesThread(QThread):
    """
    Downloads server data to the client
    """

    signal = pyqtSignal(object)

    def __init__(self, file_to_download: str, delay: int):
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
        self.delay = delay

    def run(self):
        while True:
            try:
                self.server = (self.SERVER_IP, self.SERVER_PORT)
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.settimeout(10)
                self.s.connect(self.server)

                self.s.send(
                    f"get_file{self.SEPARATOR}{self.file_to_download}".encode("utf-8")
                )

                filesize: int = int(self.s.recv(1024).decode("utf-8"))

                new_name = self.file_to_download.replace(".json", " - Compare.json")

                with open(new_name, "wb") as f:
                    while True:
                        bytes_read = self.s.recv(self.BUFFER_SIZE)
                        if not bytes_read:
                            # file transmitting is done
                            break
                        f.write(bytes_read)

                self.s.close()
                self.signal.emit("")
            except Exception as e:
                logging.exception("Exception occurred")
                self.signal.emit(e)
            sleep(self.delay)
