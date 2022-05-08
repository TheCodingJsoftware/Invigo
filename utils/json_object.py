import json
import os

from utils.json_file import JsonFile


class JsonObject:
    """
    Create an object from the json_file
    """

    def __init__(self, JsonFile, object_name: str) -> None:
        self.object_name = object_name
        self.JsonFile = JsonFile
        self.load_object()

    def load_object(self) -> None:
        self.data = self.JsonFile.get_value(item_name=self.object_name)

    def set_value(self, item_name: str, value) -> None:
        self.JsonFile.change_item(
            object_name=self.object_name, item_name=item_name, new_value=value
        )

    def get_value(self, item_name: str):
        return self.data[item_name]
