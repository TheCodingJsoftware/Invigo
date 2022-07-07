import json
import os

from utils.json_file import JsonFile


class JsonObject:
    """
    Create an object from the json_file
    """

    def __init__(self, JsonFile, object_name: str) -> None:
        """
        The function takes a json file and an object name as parameters and loads the object from the
        json file

        Args:
          JsonFile: The file that contains the JSON data.
          object_name (str): The name of the object you want to load.
        """
        self.object_name = object_name
        self.JsonFile = JsonFile
        self.load_object()

    def load_object(self) -> None:
        """
        It loads the object from the json file
        """
        self.data = self.JsonFile.get_value(item_name=self.object_name)

    def set_value(self, item_name: str, value) -> None:
        """
        It takes a string and a value, and changes the value of the item in the json file with the same
        name as the string

        Args:
          item_name (str): The name of the item you want to change.
          value: The value to be set
        """
        self.JsonFile.change_object_item(
            object_name=self.object_name, item_name=item_name, new_value=value
        )

    def get_value(self, item_name: str) -> dict:
        """
        It returns the value of the item in the dictionary with the key of the item_name parameter

        Args:
          item_name (str): The name of the item you want to get the value of.

        Returns:
          The value of the item_name key in the data dictionary.
        """
        return self.data[item_name]
