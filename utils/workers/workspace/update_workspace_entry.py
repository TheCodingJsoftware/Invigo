# update_workspace_entry_worker.py

import msgspec
import requests

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.structural_profile import StructuralProfile
from utils.workers.base_worker import BaseWorker
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class UpdateWorkspaceEntryWorker(BaseWorker):
    def __init__(
        self,
        entry_id: int,
        entry: Job | Assembly | LaserCutPart | Component | StructuralProfile,
    ):
        super().__init__(name="UpdateWorkspaceEntryWorker")
        self.entry_id = entry_id
        self.entry = entry
        self.entry_type = None
        self.url = f"{self.DOMAIN}/workspace/update_entry/{self.entry_id}"

    def do_work(self):
        if isinstance(self.entry, Job):
            data = self.entry.to_dict()["job_data"]
            self.entry_type = "job"
        elif isinstance(self.entry, Assembly):
            data = self.entry.to_dict()["assembly_data"]
            self.entry_type = "assembly"
        elif isinstance(self.entry, LaserCutPart):
            data = self.entry.to_dict()
            self.entry_type = "laser_cut_part"
        elif isinstance(self.entry, Component):
            data = self.entry.to_dict()
            self.entry_type = "component"
        elif isinstance(self.entry, StructuralProfile):
            data = self.entry.to_dict()
            self.entry_type = "structural_steel_part"
        else:
            raise ValueError("Unsupported entry type")

        self.logger.info(f"Updating entry {self.entry_id} of type {self.entry_type}")

        with requests.Session() as session:
            response = session.post(self.url, json=data, headers=self.headers, timeout=10)
            response.raise_for_status()

            job_data = msgspec.json.decode(response.content)
            job_data["entry_data"] = {
                "id": self.entry_id,
                "type": self.entry_type,
                "data": data,
            }

            if not isinstance(job_data, dict):
                raise ValueError("Invalid data format received")

            return job_data

    def handle_exception(self, e):
        if isinstance(e, requests.exceptions.Timeout):
            self.signals.error.emit({"error": "Request timed out"}, 408)
        elif isinstance(e, requests.exceptions.ConnectionError):
            self.signals.error.emit({"error": "Could not connect to the server"}, 503)
        elif isinstance(e, requests.exceptions.HTTPError):
            self.signals.error.emit({"error": f"HTTP Error: {str(e)}"}, e.response.status_code)
        elif isinstance(e, requests.exceptions.RequestException):
            self.signals.error.emit({"error": f"Request failed: {str(e)}"}, 500)
        elif isinstance(e, ValueError):
            self.signals.error.emit({"error": str(e)}, 400)
        else:
            super().handle_exception(e)
