import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.structural_profile import StructuralProfile
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class UpdateWorkspaceEntriesThread(QThread):
    signal = pyqtSignal(object, int)

    def __init__(
        self,
        entries: list[Job | Assembly | LaserCutPart | Component | StructuralProfile],
    ):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.entries = entries
        self.entry_type: str = ""
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace/bulk_update_entries"

    def run(self):
        try:
            batch_payload = []
            for entry in self.entries:
                if isinstance(entry, Job):
                    data = entry.to_dict()["job_data"]
                    type_ = "job"
                elif isinstance(entry, Assembly):
                    data = entry.to_dict()["assembly_data"]
                    type_ = "assembly"
                elif isinstance(entry, LaserCutPart):
                    data = entry.to_dict()
                    type_ = "laser_cut_part"
                elif isinstance(entry, Component):
                    data = entry.to_dict()
                    type_ = "component"
                elif isinstance(entry, StructuralProfile):
                    data = entry.to_dict()
                    type_ = "structural_steel_part"
                else:
                    continue

                batch_payload.append({"id": entry.id, "type": type_, "data": data})
            if not batch_payload:
                self.signal.emit({"error": "No valid entries to update"}, 400)
                return

            with requests.Session() as session:
                response = session.post(
                    self.url,
                    data=msgspec.json.encode(batch_payload),
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                response.raise_for_status()
                result = msgspec.json.decode(response.content)
                self.signal.emit(result, 200)

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
