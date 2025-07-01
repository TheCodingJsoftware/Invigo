from typing import Literal

import msgspec
import requests

from utils.inventory.laser_cut_part import LaserCutPart
from utils.workers.base_worker import BaseWorker


class UpsertQuantitiesWorker(BaseWorker):
    def __init__(
        self, laser_cut_parts: list[LaserCutPart], operation: Literal["ADD", "SUBTRACT"]
    ):
        super().__init__(name="UpsertQuantitiesWorker")
        self.laser_cut_parts = laser_cut_parts
        self.operation = operation
        self.url = f"{self.DOMAIN}/laser_cut_parts_inventory/upsert_quantities?operation={self.operation}"

    def do_work(self) -> tuple[dict, list[LaserCutPart]]:
        data = []
        for laser_cut_part in self.laser_cut_parts:
            data.append(laser_cut_part.to_dict())

        with requests.Session() as session:
            response = session.post(
                self.url, json=data, headers=self.headers, timeout=10
            )
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

            return (response_data, self.laser_cut_parts)
