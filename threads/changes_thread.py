import contextlib
import time

import websocket
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class ChangesThread(QThread):
    """
    Downloads server data to the client
    """

    signal = pyqtSignal(object)

    def __init__(self, parent, files_to_download: list[str]) -> None:
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
        self.files_to_download: list[str] = files_to_download
        self.websocket_url = f"ws://{self.SERVER_IP}:{self.SERVER_PORT}/ws"

    def run(self) -> None:
        """
        It connects to a server, sends a message, receives a file, and then closes the connection
        """
        # Give the app time to first download all files on startup
        while True:
            try:
                # Callback function for handling received file data
                def handle_file_data(ws, message):
                    self.signal.emit(message)

                # Create a WebSocket connection
                self.websocket = websocket.WebSocketApp(self.websocket_url, on_message=lambda ws, message: handle_file_data(ws, message))
                self.websocket.run_forever()
            except Exception as error:
                with contextlib.suppress(AttributeError):
                    self.signal.emit(error)

    def quit(self) -> None:
        self.websocket.close()
