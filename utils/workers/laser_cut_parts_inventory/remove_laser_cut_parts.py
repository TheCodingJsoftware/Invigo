import msgspec
import requests

from utils.inventory.laser_cut_part import LaserCutPart
from utils.workers.base_worker import BaseWorker


class RemoveLaserCutPartsWorker(BaseWorker):
    def __init__(self, laser_cut_parts: list[LaserCutPart]):
        super().__init__(name="RemoveLaserCutPartsWorker")
        self.laser_cut_parts = laser_cut_parts
        self.url = f"{self.DOMAIN}/laser_cut_parts_inventory/delete_laser_cut_parts"

    def do_work(self) -> tuple[list, list[LaserCutPart]]:
        data = []

        for laser_cut_part in self.laser_cut_parts:
            data.append(laser_cut_part.id)

        with requests.Session() as session:
            response = session.post(self.url, json=data, headers=self.headers, timeout=10)
            response.raise_for_status()
            response_data = msgspec.json.decode(response.content)

            return (response_data, self.laser_cut_parts)
