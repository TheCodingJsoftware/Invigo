import contextlib
import math
import os

from utils.workspace.batch import Batch
from utils.workspace.item import Item

import ujson as json


class Workspace:
    def __init__(self, user: str) -> None:
        self.user: str = user
        self.data: dict[Batch, dict[Item, object]] = {}

        self.file_name: str = "workspace"
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"
        self.__create_file()
        self.load_data()

    def __create_file(self) -> None:
        """
        If the file doesn't exist, create it
        """
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w") as json_file:
                json_file.write("{}")

    def save(self) -> None:
        """
        It opens a file, writes the data to it, and then closes the file
        """
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(self.to_dict(), json_file, ensure_ascii=False, indent=4)

    def save_data(self, data: dict) -> None:
        """
        This function saves a dictionary as a JSON file with specified file name and folder location.

        Args:
          data (dict): The data parameter is a dictionary that contains the data that needs to be saved
        to a JSON file.
        """
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    def load_data(self) -> None:
        """
        It opens the file, reads the data, and then closes the file
        """
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
            for batch_name in data:
                batch: Batch = Batch(batch_name)
                self.data[batch] = {}
                for item_name in data[batch_name]:
                    item: Item = Item(item_name)
                    item.set_data(data[batch_name][item_name])
                    batch.set_item(item)

        except Exception as error:
            print(error)

    # TODO
    def get_users_data(self) -> dict:
        # Consider filtering items relevant to the user
        return {}

    # TODO
    def get_filtered_data(self, filter: dict) -> dict:
        """
        filters should be for each tab there is in the prats in inventory
        {      tag ID     tag name
            "material": "304 SS",
            "thickness": "12 Gauge"
        }
        """
        return {}

    def get_data(self) -> dict:
        return self.data

    def to_dict(self) -> dict:
        data = {}
        for batch in self.data:
            data[batch.name] = {}
            for item in batch.to_dict():
                data[batch.name][item.name] = item.to_dict()
        return data

    def copy_batch(self, batch_name: str) -> Batch:
        batch: Batch = self.get_batch(batch_name)
        batch.rename(f"{batch.name} - (Copy)")
        self.set_batch(batch)
        return batch

    def set_batch(self, batch: Batch) -> None:
        self.data[batch] = batch.to_dict()

    def get_batch(self, batch_name: str) -> Batch | None:
        for batch in self.data:
            if batch.name == batch_name:
                return batch
        return None
