import msgspec
import requests

from utils.inventory.laser_cut_part import LaserCutPart
from utils.workers.base_worker import BaseWorker


class AddLaserCutPartWorker(BaseWorker):
    def __init__(self, laser_cut_part: LaserCutPart):
        super().__init__(name="AddLaserCutPartWorker")
        self.laser_cut_part = laser_cut_part
        self.url = f"{self.DOMAIN}/laser_cut_parts_inventory/add_laser_cut_part"

    def do_work(self) -> tuple[dict, LaserCutPart]:
        self.logger.info(f"Adding new laser_cut_part via POST to {self.url}")
        data = self.laser_cut_part.to_dict()

        with requests.Session() as session:
            response = session.post(self.url, json=data, timeout=10)
            response.raise_for_status()

            try:
                response_data = msgspec.json.decode(response.content)
            except msgspec.DecodeError:
                raise ValueError("Failed to decode server response")

            if not isinstance(response_data, dict) or "id" not in response_data:
                raise ValueError("Invalid data format received")

            response_data["laser_cut_part_data"] = {
                "id": response_data["id"],
                "data": data,
            }

            return (response_data, self.laser_cut_part)
