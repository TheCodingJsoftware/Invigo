import msgspec
import requests

from utils.inventory.sheet import Sheet
from utils.workers.base_worker import BaseWorker


class RemoveSheetsWorker(BaseWorker):
    def __init__(self, sheets: list[Sheet]):
        super().__init__(name="RemoveSheetsWorker")
        self.sheets = sheets

    def do_work(self) -> tuple[list, list[Sheet]]:
        results: list[dict[str, str | int | bool]] = []

        with requests.Session() as session:
            for sheet in self.sheets:
                sheet_id = sheet.id
                url = f"{self.DOMAIN}/sheets_inventory/delete_sheet/{sheet_id}"
                self.logger.info(f"Attempting to delete sheet ID {sheet_id}")

                try:
                    response = session.get(url, headers=self.headers, timeout=10)
                    response.raise_for_status()

                    try:
                        result = msgspec.json.decode(response.content)
                        if isinstance(result, bool):
                            results.append({"deleted": result, "id": sheet_id})
                        else:
                            self.logger.warning(f"Invalid format deleting sheet {sheet_id}")
                            results.append({"error": "Invalid data format", "id": sheet_id})
                    except msgspec.DecodeError:
                        results.append({"error": "Failed to decode response", "id": sheet_id})
                except requests.exceptions.Timeout:
                    results.append({"error": "Request timed out", "id": sheet_id})
                except requests.exceptions.ConnectionError:
                    results.append({"error": "Connection error", "id": sheet_id})
                except requests.exceptions.HTTPError as e:
                    results.append({"error": f"HTTP Error: {str(e)}", "id": sheet_id})
                except requests.exceptions.RequestException as e:
                    results.append({"error": f"Request failed: {str(e)}", "id": sheet_id})

        return (results, self.sheets)
