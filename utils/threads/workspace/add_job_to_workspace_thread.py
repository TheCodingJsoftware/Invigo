import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port
from utils.workspace.job import Job


class AddJobToWorkspaceThread(QThread):
    signal = pyqtSignal(object, int)

    def __init__(self, job: Job):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.job: Job = job
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace/add_job"

    def run(self):
        """Sends a POST request with a job object to the server."""
        try:
            job_data = msgspec.json.encode(self.job.to_dict())  # Convert Job to JSON
            headers = {"Content-Type": "application/json"}

            response = requests.post(
                self.url, data=job_data, headers=headers, timeout=10
            )
            response.raise_for_status()  # Raise HTTP error if status != 200

            response_data = msgspec.json.decode(response.content)
            status_code = response.status_code

            self.signal.emit(response_data, status_code)

        except requests.HTTPError as http_err:
            self.signal.emit(
                f"HTTP error: {http_err}",
                response.status_code if "response" in locals() else 500,
            )

        except requests.RequestException as req_err:
            self.signal.emit(f"Request error: {req_err}", 500)

        except msgspec.DecodeError:
            self.signal.emit(
                "JSON parse error",
                response.status_code if "response" in locals() else 500,
            )

        return None
