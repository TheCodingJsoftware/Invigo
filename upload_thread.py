import socket

from PyQt5.QtCore import QThread, pyqtSignal


class UploadThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self):
        QThread.__init__(self)
        # Declaring server IP and port
        self.server_ip = "10.0.0.162"
        self.server_port = 4000

        # Declaring clients IP and port
        self.client_ip = self.get_system_ip_address()
        self.client_port = 4005

    def run(self):
        try:
            self.signal.emit("Starting")

            self.server = (self.server_ip, self.server_port)
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.client_ip, self.client_port))

            message = "test"
            self.s.sendto(message.encode("utf-8"), self.server)
            data = self.s.recv(1024).decode("utf-8")
            self.s.close()
            self.signal.emit(data)
        except Exception as e:
            self.signal.emit(e)

    def get_system_ip_address(self) -> str:
        return socket.gethostbyname(socket.gethostname())
