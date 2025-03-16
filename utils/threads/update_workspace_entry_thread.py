import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.structural_profile import StructuralProfile
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class UpdateWorkspaceEntryThread(QThread):
    signal = pyqtSignal(object, int)

    def __init__(self, entry_id: int, entry: Job | Assembly | LaserCutPart | Component | StructuralProfile):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.entry_id: int = entry_id
        self.entry = entry
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace_update_entry/{self.entry_id}"

    def run(self):
        try:
            if isinstance(self.entry, Job):
                data = self.entry.to_dict()['job_data']
            elif isinstance(self.entry, Assembly):
                data = self.entry.to_dict()['assembly_data']
            elif isinstance(self.entry, LaserCutPart):
                data = self.entry.to_dict()
            elif isinstance(self.entry, Component):
                data = self.entry.to_dict()
            else:
                return
            with requests.Session() as session:
                response = session.post(self.url, json=data, timeout=10)
                response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)

                job_data = msgspec.json.decode(response.content)  # Convert response to JSON using msgspec

                if isinstance(job_data, dict):
                    self.signal.emit(job_data, 200)  # Emit the job data with HTTP 200 status
                else:
                    self.signal.emit({"error": "Invalid data format received"}, 500)

        except requests.exceptions.Timeout:
            self.signal.emit({"error": "Request timed out"}, 408)
        except requests.exceptions.ConnectionError:
            self.signal.emit({"error": "Could not connect to the server"}, 503)
        except requests.exceptions.HTTPError as e:
            self.signal.emit({"error": f"HTTP Error: {str(e)}"}, response.status_code)
        except requests.exceptions.RequestException as e:
            self.signal.emit({"error": f"Request failed: {str(e)}"}, 500)
        finally:
            self.finished.emit()
