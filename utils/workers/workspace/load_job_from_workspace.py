import msgspec
import requests
from PyQt6.QtWidgets import QTreeWidgetItem

from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.workers.base_worker import BaseWorker
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job


class LoadJobFromWorkspaceWorker(BaseWorker):
    def __init__(
        self,
        job: Job,
        item: QTreeWidgetItem,
        job_id: int,
        laser_cut_inventory: LaserCutInventory,
        components_inventory: ComponentsInventory,
    ):
        super().__init__(name="LoadJobFromWorkspaceWorker")
        self.job = job
        self.item = item
        self.job_id = job_id
        self.laser_cut_inventory = laser_cut_inventory
        self.components_inventory = components_inventory
        self.url = f"{self.DOMAIN}/workspace/get_job/{self.job_id}"

    def do_work(self):
        self.logger.debug(f"Sending GET request to: {self.url}")
        with requests.Session() as session:
            response = session.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()

            job_data = msgspec.json.decode(response.content)

            self.job.load_data({"job_data": job_data["data"]})

            for child in job_data.get("children", []):
                if child["type"] == "assembly":
                    assembly = Assembly({"assembly_data": child["data"]}, self.job)
                    assembly.id = child["id"]
                    self.job.add_assembly(assembly)
                    self._process_children(
                        self.job, assembly, child.get("children", [])
                    )

            return (self.job, self.item, job_data, 200)

    def _process_children(self, job: Job, parent: Assembly, children: list[dict]):
        for child in children:
            if child["type"] == "assembly":
                assembly = Assembly({"assembly_data": child["data"]}, job)
                assembly.id = child["id"]
                parent.add_sub_assembly(assembly)
                self._process_children(job, assembly, child.get("children", []))
            elif child["type"] == "laser_cut_part":
                lcp = LaserCutPart(child["data"], self.laser_cut_inventory)
                lcp.id = child["id"]
                parent.add_laser_cut_part(lcp)
            elif child["type"] == "component":
                component = Component(child["data"], self.components_inventory)
                component.id = child["id"]
                parent.add_component(component)
