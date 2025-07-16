import os

import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class SendEmailThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, title: str, message: str, emails: list[str]):
        super().__init__()
        self.title = title
        self.message = message
        self.emails = ",".join(emails)

        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/send_email"
        self.headers = {"X-Client-Name": os.getlogin()}

    def run(self):
        data = {"title": self.title, "message": self.message, "emails": self.emails}
        try:
            response = requests.post(self.url, data=data, headers=self.headers, timeout=10)
            if response.status_code == 200:
                self.signal.emit("Email sent successfully")
            else:
                self.signal.emit(f"Failed to send email: {response.text}")
        except requests.exceptions.RequestException as e:
            self.signal.emit(str(e))
