import msgspec
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QTreeWidgetItem

from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class LoadJobFromWorkspaceThread(QThread):
    signal = pyqtSignal(Job, object, object, int)

    def __init__(
        self,
        job: Job,
        item: QTreeWidgetItem,
        job_id: int,
        laser_cut_inventory: LaserCutInventory,
        components_inventory: ComponentsInventory,
    ):
        QThread.__init__(self)
        self.SERVER_IP: str = get_server_ip_address()
        self.SERVER_PORT: int = get_server_port()
        self.job = job
        self.item = item
        self.job_id: int = job_id
        self.laser_cut_inventory = laser_cut_inventory
        self.components_inventory = components_inventory
        self.url = f"http://{self.SERVER_IP}:{self.SERVER_PORT}/workspace/get_job/{self.job_id}"

    def process_children(
        self, job: Job, parent: Assembly, children: list[dict[str, dict | list | str]]
    ):
        """
        Recursively processes child elements within an assembly or job.
        """
        for child in children:
            if child["type"] == "assembly":
                assembly = Assembly({"assembly_data": child["data"]}, job)
                assembly.id = child["id"]
                parent.add_sub_assembly(assembly)
                self.process_children(
                    job, assembly, child.get("children", [])
                )  # Recursive for sub-assemblies
            elif child["type"] == "laser_cut_part":
                laser_cut_part = LaserCutPart(child["data"], self.laser_cut_inventory)
                laser_cut_part.id = child["id"]
                parent.add_laser_cut_part(laser_cut_part)
            elif child["type"] == "component":
                component = Component(child["data"], self.components_inventory)
                component.id = child["id"]
                parent.add_component(component)

    def run(self):
        """Sends a GET request to retrieve a job object from the server."""
        try:
            with requests.Session() as session:
                response = session.get(self.url, timeout=10)
                response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
                job_data = msgspec.json.decode(
                    response.content
                )  # Convert response to JSON using msgspec

                self.job.load_data({"job_data": job_data["data"]})

                for child in job_data.get("children", []):
                    if child["type"] == "assembly":
                        assembly = Assembly({"assembly_data": child["data"]}, self.job)
                        assembly.id = child["id"]
                        self.job.add_assembly(assembly)
                        self.process_children(
                            self.job, assembly, child.get("children", [])
                        )

                if isinstance(job_data, dict):
                    self.signal.emit(
                        self.job, self.item, job_data, 200
                    )  # Emit the job data with HTTP 200 status
                else:
                    self.signal.emit(
                        self.job,
                        self.item,
                        {"error": "Invalid data format received"},
                        500,
                    )

        except requests.exceptions.Timeout:
            self.signal.emit(self.job, self.item, {"error": "Request timed out"}, 408)
        except requests.exceptions.ConnectionError:
            self.signal.emit(
                self.job, self.item, {"error": "Could not connect to the server"}, 503
            )
        except requests.exceptions.HTTPError as e:
            self.signal.emit(
                self.job,
                self.item,
                {"error": f"HTTP Error: {str(e)}"},
                response.status_code,
            )
        except requests.exceptions.RequestException as e:
            self.signal.emit(
                self.job, self.item, {"error": f"Request failed: {str(e)}"}, 500
            )
        finally:
            self.finished.emit()
