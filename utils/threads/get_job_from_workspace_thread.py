import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port
from utils.workspace.job import Job


class GetJobFromWorkspaceThread(QThread):
    signal = pyqtSignal(Job, object, int)

    def __init__(self, job: Job, job_id: int):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.job = job
        self.job_id: int = job_id
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace_get_job/{self.job_id}"

    def run(self):
        """Sends a GET request to retrieve a job object from the server."""
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)

            job_data = msgspec.json.decode(response.content)  # Convert response to JSON using msgspec

            if isinstance(job_data, dict):
                self.signal.emit(self.job, job_data, 200)  # Emit the job data with HTTP 200 status
            else:
                self.signal.emit(self.job, {"error": "Invalid data format received"}, 500)

        except requests.exceptions.Timeout:
            self.signal.emit(self.job, {"error": "Request timed out"}, 408)
        except requests.exceptions.ConnectionError:
            self.signal.emit(self.job, {"error": "Could not connect to the server"}, 503)
        except requests.exceptions.HTTPError as e:
            self.signal.emit(self.job, {"error": f"HTTP Error: {str(e)}"}, response.status_code)
        except requests.exceptions.RequestException as e:
            self.signal.emit(self.job, {"error": f"Request failed: {str(e)}"}, 500)