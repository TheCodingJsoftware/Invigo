from typing import Union
import copy


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
        self.name = kwargs.get("name")
        self.data = kwargs.get("data")

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

    def rename(self, new_name: str) -> None:
        """
        This function takes a new name as input and sets it as the name attribute of an object.

        Args:
          new_name (str): new_name is a parameter of type string that represents the new name that we
        want to assign to an object. This parameter is used in the method "rename" to update the name
        attribute of the object to the new name provided.
        """
        self.name = new_name

    def to_dict(self) -> dict[str, object]:
        """
        The function returns a deep copy of the data attribute as a dictionary.

        Returns:
          A dictionary containing a deep copy of the `data` attribute of the object. The keys of the
        dictionary are strings and the values are objects.
        """
        return copy.deepcopy(self.data)
