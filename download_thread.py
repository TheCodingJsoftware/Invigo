import logging
import socket

from PyQt5.QtCore import QThread, pyqtSignal

import log_config


class DownloadThread(QThread):
    """
    Uploads client data to the server
    """

    signal = pyqtSignal(object)

    def __init__(self):
        QThread.__init__(self)
        # Declaring server IP and port
        self.SERVER_IP: str = "10.0.0.162"
        self.SERVER_PORT: int = 4000

        # Declaring clients IP and port
        self.client_ip: str = self.get_system_ip_address()
        self.client_port: int = 4005

    def run(self):
        try:
            self.server = (self.SERVER_IP, self.SERVER_PORT)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.settimeout(10)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.client_ip, self.client_port))

            self.s.sendto("download".encode("utf-8"), self.server)

            data = self.s.recv(1024).decode("utf-8")
            with open("data/database.json", "w") as database:
                database.write(data)
            self.s.close()
            self.signal.emit("Successfully downloaded")
        except Exception as e:
            logging.exception("Exception occurred")
            self.signal.emit(e)

    def get_system_ip_address(self) -> str:
        return socket.gethostbyname(socket.gethostname())
