import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class GetAllJobsFromWorkspaceThread(QThread):
    signal = pyqtSignal(object, int)

    def __init__(self):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace/get_all_jobs"

    def run(self):
        try:
            with requests.Session() as session:
                response = session.get(self.url, timeout=10)
                response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)

                job_data = msgspec.json.decode(
                    response.content
                )  # Convert response to JSON using msgspec

                if isinstance(job_data, dict):
                    self.signal.emit(
                        job_data, 200
                    )  # Emit the job data with HTTP 200 status
                else:
                    self.signal.emit({"error": "Invalid data format received"}, 500)

        except requests.exceptions.Timeout as e:
            self.signal.emit({"error": f"Request timed out: {str(e)}"}, 408)
        except requests.exceptions.ConnectionError as e:
            self.signal.emit(
                {"error": f"Could not connect to the server: {str(e)}"}, 503
            )
        except requests.exceptions.HTTPError as e:
            self.signal.emit({"error": f"HTTP Error: {str(e)}"}, response.status_code)
        except requests.exceptions.RequestException as e:
            self.signal.emit({"error": f"Request failed: {str(e)}"}, 500)
        except Exception as e:
            self.signal.emit({"error": f"Unknown error: {str(e)}"}, 500)
        finally:
            self.finished.emit()
