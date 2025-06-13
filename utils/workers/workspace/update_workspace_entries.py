# update_workspace_entries_worker.py

import msgspec
import requests

from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.structural_profile import StructuralProfile
from utils.workers.base_worker import BaseWorker
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class UpdateWorkspaceEntriesWorker(BaseWorker):
    def __init__(
        self,
        entries: list[Job | Assembly | LaserCutPart | Component | StructuralProfile],
    ):
        super().__init__(name="UpdateWorkspaceEntriesWorker")
        self.entries = entries
        self.url = f"{self.DOMAIN}/workspace/bulk_update_entries"

    def do_work(self):
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
                self.logger.warning(f"Skipping unknown entry type: {type(entry)}")
                continue

            batch_payload.append({"id": entry.id, "type": type_, "data": data})

        if not batch_payload:
            raise ValueError("No valid entries to update")

        self.logger.info(f"Sending {len(batch_payload)} entries for update")

        with requests.Session() as session:
            response = session.post(
                self.url,
                data=msgspec.json.encode(batch_payload),
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            return msgspec.json.decode(response.content)

    def handle_exception(self, e):
        if isinstance(e, requests.exceptions.Timeout):
            self.signals.error.emit({"error": "Request timed out"}, 408)
        elif isinstance(e, requests.exceptions.ConnectionError):
            self.signals.error.emit({"error": "Could not connect to the server"}, 503)
        elif isinstance(e, requests.exceptions.HTTPError):
            self.signals.error.emit(
                {"error": f"HTTP Error: {str(e)}"}, e.response.status_code
            )
        elif isinstance(e, requests.exceptions.RequestException):
            self.signals.error.emit({"error": f"Request failed: {str(e)}"}, 500)
        elif isinstance(e, ValueError):
            self.signals.error.emit({"error": str(e)}, 400)
        else:
            super().handle_exception(e)
