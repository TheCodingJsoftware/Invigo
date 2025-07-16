import contextlib
import logging
import os
import time

import msgspec
import websocket
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port

logging.getLogger("websocket").setLevel(logging.CRITICAL)


class ChangesThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, parent):
        QThread.__init__(self)
        self.parent = parent
        self.SERVER_IP = get_server_ip_address()
        self.SERVER_PORT = get_server_port()
        self.client_name = os.getlogin()
        self.websocket_url = f"ws://{self.SERVER_IP}:{self.SERVER_PORT}/ws?client_name={self.client_name}"

    def run(self):
        while True:
            try:

                def handle_file_data(ws, message) -> None:
                    data: dict[str, list[str] | str] = msgspec.json.decode(message)
                    if data.get("action") == "download":
                        self.signal.emit(data.get("files"))
                    else:
                        self.signal.emit("Unrecognized message format")

                self.websocket = websocket.WebSocketApp(
                    self.websocket_url,
                    on_message=lambda ws, message: handle_file_data(ws, message),
                )
                self.websocket.run_forever()
            except Exception as error:
                with contextlib.suppress(AttributeError):
                    self.signal.emit(str(error))
            time.sleep(5)

    def quit(self):
        self.websocket.close()
