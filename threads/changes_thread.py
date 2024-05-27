import contextlib

import ujson as json
import websocket
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class ChangesThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, parent) -> None:
        QThread.__init__(self)
        self.parent = parent
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.websocket_url = f"ws://{self.SERVER_IP}:{self.SERVER_PORT}/ws"

    def run(self) -> None:
        while True:
            try:

                def handle_file_data(ws, message):
                    data: dict[str, list[str] | str] = json.loads(message)
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

    def quit(self) -> None:
        self.websocket.close()
