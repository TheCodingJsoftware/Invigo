import msgspec
import requests

from utils.inventory.laser_cut_part import LaserCutPart
from utils.workers.base_worker import BaseWorker


class UpdateLaserCutPartsWorker(BaseWorker):
    def __init__(self, laser_cut_parts: list[LaserCutPart]):
        super().__init__(name="UpdateLaserCutPartsWorker")
        self.laser_cut_parts = laser_cut_parts
        self.url = f"{self.DOMAIN}/laser_cut_parts_inventory/update_laser_cut_parts"

    def do_work(self):
        self.logger.info(
            f"Sending update for {len(self.laser_cut_parts)} laser_cut_parts to {self.url}"
        )

        data = [laser_cut_part.to_dict() for laser_cut_part in self.laser_cut_parts]

        with requests.Session() as session:
            response = session.post(self.url, json=data, timeout=10)
            response.raise_for_status()
            try:
                response_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("JSON parse error from server")
            return response_data
