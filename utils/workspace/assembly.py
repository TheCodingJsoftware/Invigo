import copy
from typing import Any, Union

from utils.workspace.item import Item


class Assembly:
    """An assembly that can have child assemblies and items"""

    def __init__(self, **kwargs: Union[str, list["Assembly"], list[Item]]) -> None:
        """
        This is the constructor for a class called "Assembly" that initializes its attributes based on
        the keyword arguments passed in.

        Args:
           (Union[str, list["Assembly"], list[Item]]): This is the initialization method for a class
        called "Assembly". It takes in keyword arguments (kwargs) that can include the following:
        """
        self.name = kwargs.get("name")
        self.assembly_data: dict[str, object] = kwargs.get("assembly_data")
        self.sub_assemblies: list["Assembly"] = kwargs.get("sub_assemblies")
        self.items: list[Item] = kwargs.get("items")
        self.parent_assembly: "Assembly" = None
        self.master_assembly: "Assembly" = None
        if not self.items:
            self.items = []
        if not self.sub_assemblies:
            self.sub_assemblies = []
        if not self.assembly_data:
            self.assembly_data = {}
        self.data = {"assembly_data": self.assembly_data, "sub_assemblies": self.sub_assemblies, "items": self.items}

    def set_parent_assembly_value(self, key: str, value: Any) -> None:
        self.set_assembly_data(key=key, value=value)
        if self.parent_assembly is not None:
            self.parent_assembly.set_assembly_data(key=key, value=value)

    def set_item(self, item: Item) -> None:
        """
        This function adds an item to a list of items in an object.

        Args:
          item (Item): The parameter "item" is of type "Item", which means it is expecting an object of
        the class "Item" to be passed as an argument. The method "set_item" is designed to add this item
        to a list of items stored in the object that the method is called on.
        """
        item.parent_assembly = self
        self.items.append(item)

    def add_item(self, item: Item) -> None:
        """
        This function adds an item to a list of items in an object.

        Args:
          item (Item): The parameter "item" is of type "Item", which means it is expecting an object of
        the class "Item" to be passed as an argument. The method "set_item" is designed to add this item
        to a list of items stored in the object that the method is called on.
        """
        item.parent_assembly = self
        self.items.append(item)

    def remove_item(self, item: Item) -> None:
        """
        This function removes an item from a list of items if it exists in the list.

        Args:
          item (Item): The "item" parameter is an instance of the "Item" class that the method is
        designed to remove from the list of items in the current instance of the class.
        """
        if self.exists(item):
            self.items.remove(item)

    def set_assembly_data(self, key: str, value: Any) -> None:
        """
        This function sets a value for a given key in a dictionary called "assembly_data".

        Args:
          key (str): The key parameter is a string that represents the name of the data that is being
        stored in the assembly_data dictionary. It is used as the key to access the corresponding value
        in the dictionary.
          value (object): The value parameter is an object that can be of any data type (e.g. int, str,
        list, dict, etc.) that the user wants to store in the assembly_data dictionary.
        """
        self.assembly_data[key] = value

    def get_assembly_data(self, key: str) -> Any:
        """
        This function returns the value associated with a given key in a dictionary called
        "assembly_data".

        Args:
          key (str): The key parameter is a string that represents the key of the value that we want to
        retrieve from the assembly_data dictionary.

        Returns:
          the value associated with the input key in the assembly_data dictionary. The type of the
        returned value is not specified, but it will be of the same type as the value stored in the
        dictionary for the given key.
        """
        try:
            return self.assembly_data[key]
        except KeyError:
            return None

    def delete_assembly_value(self, key: str) -> Any:
        """
        This function deletes a key-value pair from a dictionary and returns the value of the deleted
        key, or None if the key does not exist.

        Args:
          key (str): The key is a string that represents the key of the value that needs to be deleted
        from the assembly_data dictionary.

        Returns:
          the value associated with the given key in the assembly_data dictionary, and then deleting the
        key-value pair from the dictionary. If the key is not found in the dictionary, the function
        returns None.
        """
        try:
            value_copy = self.assembly_data[key]
            del self.assembly_data[key]
            return value_copy
        except KeyError:
            return None

    def get_master_assembly(self) -> "Assembly":
        """
        The function returns the top-level assembly object by traversing through the parent assemblies.

        Returns:
          The method `get_master_assembly` returns the master assembly object.
        """
        master_assembly = self
        while master_assembly.parent_assembly is not None:
            master_assembly = master_assembly.parent_assembly
        return master_assembly

    def delete_sub_assembly(self, assembly) -> "Assembly":
        """
        This function removes a sub-assembly from an assembly and returns a copy of the removed
        sub-assembly.

        Args:
          assembly: The parameter "assembly" is an object of the class "Assembly" that represents a
        sub-assembly. The method "delete_sub_assembly" takes this object as input and removes it from
        the list of sub-assemblies of the current object (which is also an instance of the class
        "Assembly").

        Returns:
          The method is returning a copy of the sub-assembly that was removed from the main assembly.
        """
        copy = self.copy_sub_assembly(assembly)
        self.sub_assemblies.remove(assembly)
        return copy

    def set_sub_assembly(self, assembly: "Assembly") -> list["Assembly"]:
        """
        This function adds an assembly to a list of sub-assemblies for a given assembly.

        Args:
          assembly ("Assembly"): The "assembly" parameter is of type "Assembly", which means it expects
        an object of the "Assembly" class to be passed as an argument. This method is likely a part of a
        larger class that deals with assemblies and sub-assemblies, and this particular method is used
        to add a sub-
        """
        assembly.parent_assembly = self
        assembly.master_assembly = assembly.get_master_assembly()
        self.sub_assemblies.append(assembly)

    def add_sub_assembly(self, assembly: "Assembly") -> list["Assembly"]:
        """
        This function adds an assembly to a list of sub-assemblies for a given assembly.

        Args:
          assembly ("Assembly"): The "assembly" parameter is of type "Assembly", which means it expects
        an object of the "Assembly" class to be passed as an argument. This method is likely a part of a
        larger class that deals with assemblies and sub-assemblies, and this particular method is used
        to add a sub-
        """
        assembly.parent_assembly = self
        assembly.master_assembly = assembly.get_master_assembly()
        self.sub_assemblies.append(assembly)

    def get_sub_assemblies(self) -> list["Assembly"]:
        """
        This function returns a list of sub-assemblies.

        Returns:
          The method `get_sub_assemblies` is returning a list of sub-assemblies. The specific content of
        the list depends on the implementation of the `sub_assemblies` attribute in the class.
        """
        return self.sub_assemblies

    def get_sub_assembly(self, assembly_name: str) -> "Assembly":
        """
        This function returns a sub-assembly object with a given name from a list of sub-assemblies.

        Args:
          assembly_name (str): a string representing the name of the sub-assembly that is being searched
        for.

        Returns:
          an instance of the "Assembly" class that matches the given "assembly_name" parameter. If no
        matching assembly is found, the function returns "None".
        """
        return next(
            (sub_assembly for sub_assembly in self.sub_assemblies if sub_assembly.name == assembly_name),
            None,
        )

    def copy_sub_assembly(self, assembly_name: Union[str, "Assembly"]) -> "Assembly":
        """
        This function copies a sub-assembly and renames it with "(Copy)" appended to the original name.

        Args:
          assembly_name (Union[str, "Assembly"]): The name of the sub-assembly that needs to be copied.
        It can be either a string or an instance of the "Assembly" class.

        Returns:
          The method returns an instance of the "Assembly" class that is a copy of a sub-assembly with
        the specified name. If no sub-assembly with the specified name is found, the method returns
        None.
        """
        if isinstance(assembly_name, Assembly):
            assembly_name = assembly_name.name
        for sub_assembly in self.sub_assemblies:
            if sub_assembly.name == assembly_name:
                sub_assembly = copy.deepcopy(sub_assembly)
                sub_assembly.rename(f"{sub_assembly.name} - (Copy)")
                return sub_assembly
        return None

    def copy_assembly(self) -> "Assembly":
        return copy.deepcopy(self)

    def rename(self, new_name: str) -> None:
        """
        This function takes a new name as input and sets it as the name attribute of an object.

        Args:
          new_name (str): new_name is a parameter of type string that represents the new name that we
        want to assign to an object. This parameter is used in the method "rename" to update the name
        attribute of the object with the new name provided as an argument.
        """
        self.name = new_name

    def to_dict(self, processed_assemblies: set = None) -> dict:
        """
        This function converts an assembly object and its sub-assemblies and items into a dictionary
        format.

        Args:
          processed_assemblies (set): processed_assemblies is a set that keeps track of the assemblies
        that have already been processed to avoid infinite recursion. It is an optional parameter with a
        default value of None. If it is not provided, a new empty set is created.

        Returns:
          A dictionary containing information about the assembly and its sub-assemblies and items.
        """
        if processed_assemblies is None:
            processed_assemblies = set()
        processed_assemblies.add(self)

        data = {"items": {}, "assembly_data": self.assembly_data, "sub_assemblies": {}}
        self.delete_assembly_value(key="show")
        for sub_assembly in self.sub_assemblies:
            sub_assembly.delete_assembly_value(key="show")
            if sub_assembly not in processed_assemblies:  # Check if the sub-assembly is already processed
                data["sub_assemblies"][sub_assembly.name] = sub_assembly.to_dict(processed_assemblies)
        for item in self.items:
            if item.name == "":
                continue
            item.delete_value(key="show")
            data["items"][item.name] = item.data
        return data

    def exists(self, other: Item | str) -> bool:
        if isinstance(other, Item):
            return any(other.name == item.name for item in self.items)
        elif isinstance(other, str):
            return any(other == item.name for item in self.items)

    def get_item(self, item_name: str) -> Item | None:
        """
        This function searches for an item in a data dictionary by name and returns it if found,
        otherwise it returns None.

        Args:
          item_name (str): A string representing the name of the item that needs to be retrieved.

        Returns:
          an instance of the `Item` class or `None` if the item with the given name is not found in the
        list of items.
        """
        return next((item for item in self.items if item.name == item_name), None)

    def get_all_items(self) -> list[Item]:
        all_items = self.items.copy()
        for sub_assembly in self.sub_assemblies:
            all_items.extend(sub_assembly.get_all_items())
        return all_items

    def get_item_by_index(self, index: int) -> Item:
        """
        This function returns an item from a list based on its index.

        Args:
          index (int): The index parameter is an integer that represents the position of the item in the
        list that we want to retrieve. The first item in the list has an index of 0, the second item has
        an index of 1, and so on.

        Returns:
          an item from the list of items stored in the object, based on the index provided as an
        argument. The returned value is an instance of the Item class.
        """
        return self.items[index]

    def copy_item(self, item_name: str) -> Item | None:
        """
        This Python function searches for an item with a given name in a list of items and returns a
        deep copy of the item if found, or None if not found.

        Args:
          item_name (str): A string representing the name of the item that needs to be copied.

        Returns:
          either a deep copy of an item with the specified name (if it exists in the list of items), or
        None if no such item exists.
        """
        return copy.deepcopy(self.get_item(item_name))

    def get_data(self) -> dict:
        """
        The function returns a dictionary containing the data.

        Returns:
          A dictionary containing the data stored in the object.
        """
        return self.data

    def set_timer(self, flow_tag: str, time: object) -> None:
        """
        This function sets a timer value for a specific flow tag in the assembly data dictionary.

        Args:
          flow_tag (str): A string that serves as a unique identifier for a specific flow or process in
        the program.
          time (object): The "time" parameter is an object that has a method called "value()" which
        returns the value of the time in seconds. This method is used to set the value of a timer for a
        specific flow_tag in the assembly_data dictionary.
        """
        self.assembly_data["timers"][flow_tag]["time_to_complete"] = time.value()

    def _set_data_to_all_sub_assemblies(self, sub_assembly: "Assembly", key: str, value: Any) -> None:
        """
        This function sets a key-value pair to all sub-assemblies recursively.

        Args:
          sub_assembly ("Assembly"): This is an instance of the "Assembly" class, which represents a
        sub-assembly of the current assembly.
          key (str): The key is a string that represents the name of the data attribute that is being
        set for the sub-assemblies. It is used to identify the data attribute when retrieving or
        updating it later.
          value (Any): The value that needs to be set for the given key in the sub-assemblies.
        """
        sub_assembly.set_assembly_data(key=key, value=value)
        if sub_assembly.sub_assemblies:
            for _sub_assembly in sub_assembly.sub_assemblies:
                self._set_data_to_all_sub_assemblies(sub_assembly=_sub_assembly, key=key, value=value)

    def set_data_to_all_sub_assemblies(self, key: str, value: Any) -> None:
        """
        This function sets a key-value pair to the assembly data and recursively sets the same data to
        all sub-assemblies.

        Args:
          key (str): a string representing the key of the data to be set
          value (Any): The value that needs to be set for the given key in the assembly_data dictionary
        and all its sub-assemblies.
        """
        self.assembly_data[key] = value
        for sub_assembly in self.sub_assemblies:
            self._set_data_to_all_sub_assemblies(sub_assembly=sub_assembly, key=key, value=value)

    def _set_default_value_to_all_items(self, sub_assembly: "Assembly", key: str, value: str) -> None:
        """
        This function sets a default value to all items in an assembly and its sub-assemblies.

        Args:
          sub_assembly ("Assembly"): An instance of the "Assembly" class that represents a sub-assembly
        within the current assembly.
          key (str): The key is a string that represents the name of the attribute or property that
        needs to be set to a default value.
          value (str): The value to be set as the default value for all items in the assembly and its
        sub-assemblies.
        """
        for item in sub_assembly.items:
            item.set_value(key=key, value=value)
        if sub_assembly != None:
            for _sub_assembly in sub_assembly.sub_assemblies:
                for item in _sub_assembly.items:
                    item.set_value(key=key, value=value)
                if _sub_assembly.sub_assemblies:
                    self._set_default_value_to_all_items(sub_assembly=_sub_assembly, key=key, value=value)

    def set_default_value_to_all_items(self, key: str, value: str) -> None:
        """
        This function sets a default value to all items in a given assembly and its sub-assemblies.

        Args:
          key (str): a string representing the key for the value to be set
          value (str): The value that will be set as the default value for all items in the assembly and
        its sub-assemblies.
        """
        for item in self.items:
            item.set_value(key=key, value=value)
        for sub_assembly in self.sub_assemblies:
            for item in sub_assembly.items:
                item.set_value(key=key, value=value)
            if self.sub_assemblies:
                self._set_default_value_to_all_items(sub_assembly=sub_assembly, key=key, value=value)

    def any_items_to_show(self) -> bool:
        """
        The function checks if there are any items that should be shown and are not completed.

        Returns:
          a boolean value. It returns True if there are any items to show (items that have the "show"
        key set to True and the "completed" key set to False), and False otherwise.
        """
        for item in self.items:
            if item.get_value(key="show") and not item.get_value(key="completed"):
                return True
        for sub_assembly in self.sub_assemblies:
            for item in sub_assembly.items:
                if item.get_value(key="show") and not item.get_value(key="completed"):
                    return True
        return False

    def _any_sub_assemblies_to_show(self, sub_assembly: "Assembly") -> bool:
        for _sub_assembly in sub_assembly.sub_assemblies:
            if _sub_assembly.get_assembly_data("show") is True:
                return True
            if _sub_assembly._any_sub_assemblies_to_show(_sub_assembly):
                return True
        return False

    def any_sub_assemblies_to_show(self) -> bool:
        """
        The function checks if there are any sub-assemblies that have the "show" attribute set to True.

        Returns:
          a boolean value. It returns True if there are any sub-assemblies that have the "show"
        attribute set to True, and False otherwise.
        """
        for assembly in self.sub_assemblies:
            if assembly.get_assembly_data("show") is True:
                return True
            # for sub_assembly in assembly.sub_assemblies:
            #     if sub_assembly._any_sub_assemblies_to_show(sub_assembly):
            #         return True
        return False

    def all_items_complete(self) -> bool:
        """
        This function checks if all items in a list have a "completed" value of True.

        Returns:
          The function `all_items_complete` is returning a boolean value. It is checking if all the
        items in the `self.items` list have a value of `True` for the key "completed" using a generator
        expression with the `all()` function. If all items have a value of `True`, then the function
        returns `True`, otherwise it returns `False`.
        """
        return all(item.get_value("completed") != False for item in self.items)

    def all_sub_assemblies_complete(self) -> bool:
        """
        This function checks if all sub-assemblies have been completed.

        Returns:
          a boolean value indicating whether all sub-assemblies in the object have their "completed"
        attribute set to a truthy value (i.e. not False).
        """
        return all(sub_assembly.get_assembly_data(key="completed") != False for sub_assembly in self.sub_assemblies)
