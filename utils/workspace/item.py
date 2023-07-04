import copy
from typing import Any, Union


class Item:
    def __init__(self, **kwargs: Union[str, object]) -> None:
        """
        This is a constructor function that initializes two instance variables "name" and "data" with
        values passed as keyword arguments.

        Args:
           (Union[str, object]): This is a constructor method for a Python class. It takes in keyword
        arguments using the **kwargs syntax, which allows for an arbitrary number of keyword arguments
        to be passed in. The expected keyword arguments are "name" and "data". The method uses the get()
        method to retrieve the values of these
        """
        self.name: str = kwargs.get("name")
        self.data: dict = kwargs.get("data")
        self.parent_assembly = None
        self.master_assembly = None

    def set_data(self, data: object) -> None:
        """
        This function sets the value of the "data" attribute of an object.

        Args:
          data (object): The "data" parameter is an object that is being passed into the "set_data"
        method. This method sets the value of the "data" attribute of the object to the value of the
        "data" parameter. The type annotation for the "data" parameter indicates that it should be an
        object
        """
        self.data = data

    def set_value(self, key: str, value: Any) -> None:
        """
        This function sets a value in a dictionary with a given key.

        Args:
          key (str): The key parameter is a string that represents the key of the data that we want to
        set the value for. In other words, it is the identifier that we use to access the value in the
        dictionary.
          value (Any): The value that needs to be assigned to the key in the dictionary. It can be of
        any data type.
        """
        self.data[key] = value

    def get_value(self, key: str) -> Any:
        """
        This function takes a key as input and returns the corresponding value from a dictionary-like
        object.

        Args:
          key (str): The parameter "key" is a string that represents the key of the value that we want
        to retrieve from the data dictionary.

        Returns:
          The function `get_value` is returning the value associated with the given `key` in the `data`
        dictionary of the object. The type of the returned value is `Any`, which means it can be any
        Python object.
        """
        try:
            return self.data[key]
        except KeyError:
            return None

    def delete_value(self, key: str) -> Any:
        """
        This function deletes a key-value pair from a dictionary and returns the value that was deleted.

        Args:
          key (str): The key parameter is a string that represents the key of the value that needs to be
        deleted from the data dictionary.

        Returns:
          The value associated with the given key is being returned after deleting it from the
        dictionary.
        """
        try:
            value_copy = self.data[key]
            del self.data[key]
            return value_copy
        except KeyError:
            return None

    def copy_data(self) -> dict:
        """
        The function `copy_data` returns a deep copy of the `data` attribute of the object.

        Returns:
          a deep copy of the `self.data` dictionary.
        """
        return copy.deepcopy(self.data)

    def rename(self, new_name: str) -> None:
        """
        This function takes a new name as input and sets it as the name attribute of an object.

        Args:
          new_name (str): new_name is a parameter of type string that represents the new name that we
        want to assign to an object. This parameter is used in the method "rename" to update the name
        attribute of the object to the new name provided.
        """
        self.name = new_name

    def set_timer(self, flow_tag: str, time: object) -> None:
        self.data["timers"][flow_tag]["time_to_complete"] = time.value()

    def get_timer(self, flow_tag: str) -> float:
        self.data["timers"][flow_tag]['time_to_complete"']

    def to_dict(self) -> dict[str, object]:
        """
        The function returns a deep copy of the data attribute as a dictionary.

        Returns:
          A dictionary containing a deep copy of the `data` attribute of the object. The keys of the
        dictionary are strings and the values are objects.
        """
        return self.data
