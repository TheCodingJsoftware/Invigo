import os

import ujson as json


class JsonFile:
    """
    Json data file handler
    """

    def __init__(self, file_name: str = "json_file"):
        """
        It creates a file if it doesn't exist, and loads the data from the file into the class

        Args:
          file_name (str): The name of the file. Defaults to json_file
        """
        self.data = None
        self.file_name: str = file_name.replace(".json", "")
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/"
        self.__create_file()
        self.load_data()

    def __create_file(self) -> None:
        """
        If the file doesn't exist, create it
        """
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w") as json_file:
                json_file.write("{}")

    def load_data(self) -> None:
        """
        It opens the file, reads the data, and then closes the file
        """
        try:
            with open(
                f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r", encoding="utf-8"
            ) as json_file:
                self.data = json.load(json_file)
        except Exception as error:
            print(error)
            # self.load_data()

    def __save_data(self):
        """
        It opens a file, writes the data to it, and then closes the file
        """
        with open(
            f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8"
        ) as json_file:
            json.dump(self.data, json_file, ensure_ascii=False, indent=4)

    def add_item(self, item_name: str, value) -> None:
        """
        This function adds an item to the data dictionary

        Args:
          item_name (str): str
          value: The value to be stored in the file.
        """
        # sourcery skip: class-extract-method
        self.load_data()
        self.data.update({item_name: value})
        self.__save_data()

    def add_item_in_object(self, object_name: str, item_name: str) -> None:
        """
        It adds an item to an object in the data.json file

        Args:
          object_name (str): The name of the object you want to add the item to.
          item_name (str): str = The name of the item you want to add.
        """
        self.load_data()
        self.data[object_name].update({item_name: {}})
        self.__save_data()

    def add_group_to_category(self, category: str, group_name: str) -> None:
        """
        It adds a group to a category

        Args:
          category (str): The category you want to add the group to.
          group_name (str): The name of the group you want to add to the category.
        """
        self.load_data()
        self.data[category].update({group_name: {"group": True}})
        self.__save_data()

    def change_key_name(self, key_name: str, new_name: str) -> None:
        """
        It takes a key name and a new name, loads the data, changes the key name to the new name,
        deletes the old key name, and saves the data

        Args:
          key_name (str): The name of the key you want to change.
          new_name (str): The new name of the key.
        """  # Loading the data from the file into the class.

        self.load_data()
        self.data[new_name] = self.data[key_name]
        del self.data[key_name]
        self.__save_data()

    def clone_key(self, key_name) -> None:
        """
        It takes a key name as an argument, loads the data, clones the data, updates the data, and saves
        the data

        Args:
          key_name: The name of the key you want to clone.
        """
        self.load_data()
        clonded_data = self.data
        clonded_data[f"Clone from: {key_name} Double click me rename me"] = clonded_data[
            key_name
        ]
        self.data.update(clonded_data)
        self.__save_data()

    def change_item_name(self, object_name: str, item_name: str, new_name: str) -> None:
        """
        It takes an object name, an item name, and a new name, and changes the item name to the new name

        Args:
          object_name (str): The name of the object you want to change the item name of.
          item_name (str): The name of the item you want to change.
          new_name (str): The new name of the item
        """
        self.load_data()
        self.data[object_name][new_name] = self.data[object_name][item_name]
        del self.data[object_name][item_name]
        self.__save_data()

    def change_item(self, item_name: str, new_value) -> None:
        """
        It loads the data, updates the data with the new value, and then saves the data

        Args:
          item_name (str): The name of the item you want to change.
          new_value: The new value of the item.
        """
        self.load_data()
        self.data.update({item_name: new_value})
        self.__save_data()

    def change_object_item(self, object_name: str, item_name: str, new_value) -> None:
        """
        This function takes in a string, a string, and a value, and changes the value of the item in the
        object with the name of the first string to the value of the second string

        Args:
          object_name (str): The name of the object you want to change.
          item_name (str): The name of the item you want to change.
          new_value: The new value of the item.
        """
        self.load_data()
        self.data[object_name][item_name] = new_value
        self.__save_data()

    def change_object_in_object_item(
        self, object_name: str, item_name: str, value_name: str, new_value
    ) -> None:
        """
        It changes the value of a value in an item in an object in a dictionary

        Args:
          object_name (str): The name of the object you want to change.
          item_name (str): The name of the item in the object.
          value_name (str): str = The name of the value you want to change.
          new_value: The new value you want to change the value to.
        """
        self.load_data()
        self.data[object_name][item_name][value_name] = new_value
        self.__save_data()

    def remove_item(self, item_name) -> None:
        """
        It loads the data, removes the item, and saves the data

        Args:
          item_name: The name of the item to remove.
        """
        self.load_data()
        self.data.pop(item_name)
        self.__save_data()

    def remove_object_item(self, object_name: str, item_name: str) -> None:
        """
        It deletes the item from the object

        Args:
          object_name (str): The name of the object you want to remove an item from.
          item_name (str): The name of the item you want to remove.
        """
        self.load_data()
        del self.data[object_name][item_name]
        self.__save_data()

    def get_data(self) -> dict:
        """
        It returns the data attribute of the object

        Returns:
          The data attribute of the class.
        """
        return self.data

    def get_keys(self) -> list[str]:
        """
        It returns a list of keys in the dictionary.

        Returns:
          The keys of the dictionary.
        """
        return list(self.data.keys())

    def get_value(self, item_name: str) -> None:
        """
        It loads the data from the file, and then tries to return the value of the item_name key in the
        data dictionary. If the key doesn't exist, it returns None

        Args:
          item_name (str): The name of the item you want to get the value of.

        Returns:
          None
        """
        self.load_data()
        try:
            return self.data[item_name]
        except KeyError:
            return None

    def get_sum_of_items(self) -> int:
        """
        It loads the data, then it creates a variable called sum and sets it to 0. Then it loops through
        the categories in the data, and for each category it adds the number of items in that category
        to the sum. Finally, it returns the sum

        Returns:
          The number of items in the database.
        """
        self.load_data()
        return sum(len(self.data[category].keys()) for category in list(self.data.keys()))

    def sort(self, category: str, item_name: str, ascending: bool) -> None:
        """
        It sorts the data in the data.json file by the category and item_name specified by the user

        Args:
          category (str): str
          item_name (str): The name of the item to sort by.
          ascending (bool): bool
        """
        if item_name == "alphabet":
            sorted_data = dict(
                sorted(
                    self.data[category].items(),
                    key=lambda x: x[0],
                    reverse=ascending,
                )
            )
        else:
            sorted_data = dict(
                sorted(
                    self.data[category].items(),
                    key=lambda x: x[1][item_name],
                    reverse=ascending,
                )
            )
        self.data[category] = sorted_data
        self.__save_data()
