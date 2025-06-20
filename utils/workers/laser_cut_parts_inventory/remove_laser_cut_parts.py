import msgspec
import requests

from utils.inventory.laser_cut_part import LaserCutPart
from utils.workers.base_worker import BaseWorker


class RemoveLaserCutPartsWorker(BaseWorker):
    def __init__(self, laser_cut_parts: list[LaserCutPart]):
        super().__init__(name="RemoveLaserCutPartsWorker")
        self.laser_cut_parts = laser_cut_parts

    def do_work(self) -> tuple[list, list[LaserCutPart]]:
        results: list[dict[str, str | int | bool]] = []

        with requests.Session() as session:
            for laser_cut_part in self.laser_cut_parts:
                laser_cut_part_id = laser_cut_part.id
                url = f"{self.DOMAIN}/laser_cut_parts_inventory/delete_laser_cut_part/{laser_cut_part_id}"
                self.logger.info(
                    f"Attempting to delete laser_cut_part ID {laser_cut_part_id}"
                )

                try:
                    response = session.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()

                    try:
                        result = msgspec.json.decode(response.content)
                        if isinstance(result, bool):
                            results.append({"deleted": result, "id": laser_cut_part_id})
                        else:
                            self.logger.warning(
                                f"Invalid format deleting laser_cut_part {laser_cut_part_id}"
                            )
                            results.append(
                                {
                                    "error": "Invalid data format",
                                    "id": laser_cut_part_id,
                                }
                            )
                    except msgspec.DecodeError:
                        results.append(
                            {
                                "error": "Failed to decode response",
                                "id": laser_cut_part_id,
                            }
                        )
                except requests.exceptions.Timeout:
                    results.append(
                        {"error": "Request timed out", "id": laser_cut_part_id}
                    )
                except requests.exceptions.ConnectionError:
                    results.append(
                        {"error": "Connection error", "id": laser_cut_part_id}
                    )
                except requests.exceptions.HTTPError as e:
                    results.append(
                        {"error": f"HTTP Error: {str(e)}", "id": laser_cut_part_id}
                    )
                except requests.exceptions.RequestException as e:
                    results.append(
                        {"error": f"Request failed: {str(e)}", "id": laser_cut_part_id}
                    )

        return (results, self.laser_cut_parts)
