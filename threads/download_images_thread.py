import requests
from PyQt5.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class DownloadImagesThread(QThread):
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
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.files_to_download = files_to_download
        self.file_url = f'http://{self.SERVER_IP}:{self.SERVER_PORT}/image/'

    def run(self) -> None:
        """
        This function downloads files from a given URL and saves them to a local location.
        """
        for file_to_download in self.files_to_download:
            try:
                response = requests.get(self.file_url + file_to_download)
                if response.status_code == 200:
                    # Save the received file to a local location
                    with open(f'images/{file_to_download}', 'wb') as file:
                        file.write(response.content)
                else:
                    self.signal.emit(response.text)
            except Exception as e:
                print(e)
                self.signal.emit(e)
        self.signal.emit("Successfully downloaded")
