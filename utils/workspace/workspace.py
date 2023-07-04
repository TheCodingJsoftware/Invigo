import contextlib
import copy
import math
import os
from typing import Union

import ujson as json
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateTimeEdit,
    QGroupBox,
    QLineEdit,
    QListWidget,
    QPushButton,
)

from utils.json_file import JsonFile
from utils.workspace.assembly import Assembly
from utils.workspace.item import Item
from utils.workspace.item_group import ItemGroup

workspace_tags = JsonFile(file_name="data/workspace_settings")


class Workspace:
    def __init__(self, file_name: str) -> None:
        self.data: dict[Assembly, dict[Item, object]] = {}

        self.file_name: str = file_name
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

    def load_assembly(self, assembly_name: str, data: dict) -> Assembly:
        """
        This function loads an assembly and its sub-assemblies from a dictionary of data.

        Args:
          assembly_name (str): A string representing the name of the assembly being loaded.
          data (dict): The data parameter is a dictionary that contains information about an assembly
        and its components. It has three keys: "assembly_data", "items", and "sub_assemblies". The
        "assembly_data" key contains information about the assembly itself, while the "items" and
        "sub_assemblies" keys contain

        Returns:
          an instance of the `Assembly` class.
        """
        assembly = Assembly(name=assembly_name, assembly_data=data["assembly_data"])
        for item_name, item_data in data["items"].items():
            item: Item = Item(name=item_name, data=item_data)
            item.parent_assembly = assembly
            item.master_assembly = assembly.get_master_assembly()
            assembly.set_item(item)
        for sub_assembly_name, sub_assembly_data in data["sub_assemblies"].items():
            sub_assembly: Assembly = self.load_assembly(sub_assembly_name, sub_assembly_data)
            assembly.set_sub_assembly(sub_assembly)
        return assembly

    def load_data(self) -> None:
        """
        It opens the file, reads the data, and then closes the file
        """
        self.data.clear()
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        for assembly_name in data:
            # assembly: Assembly = Assembly(name=assembly_name, assembly_data=data[assembly_name]["assembly_data"])
            self.set_assembly(self.load_assembly(assembly_name, data[assembly_name]))
        # for assembly in self.data:
        #     assembly.set_default_value_to_all_items(key="show", value=True)
        #     assembly.set_data_to_all_sub_assemblies(key="show", value=True)
        #     assembly.set_assembly_data(key="show", value=True)

    # TODO
    def get_users_data(self) -> dict:
        # Consider filtering items relevant to the user
        return {}

    def filter_assemblies(self, sub_assembly: Assembly, filter: dict):
        """
        This function filters sub-assemblies based on various criteria such as search text, selected
        materials, thicknesses, flow tags, statuses, paint colors, and due dates.

        Args:
          sub_assembly (Assembly): The assembly object that needs to be filtered.
          filter (dict): The `filter` parameter is a dictionary containing various filter options for
        the assemblies. These options include a search filter, material filter, thickness filter, flow
        tag filter, status filter, paint color filter, and due date filter. The values for these filters
        are obtained from various GUI elements such as QLineEdit,
        """
        lineEdit_search: QLineEdit = filter["search"]
        materials: list[QPushButton] = filter["materials"]
        thicknesses: list[QPushButton] = filter["thicknesses"]
        flow_tags: list[QPushButton] = filter["flow_tags"]
        statuses: list[QPushButton] = filter["statuses"]
        paint_colors: list[QPushButton] = filter["paint"]
        groupBox_due_dates: QGroupBox = filter["due_dates"]
        dateTimeEdit_after: QDateTimeEdit = filter["dateTimeEdit_after"]
        dateTimeEdit_before: QDateTimeEdit = filter["dateTimeEdit_before"]

        # Recursively filter sub-assemblies
        completed_items = 0
        for item in sub_assembly.items:
            item.set_value(key="show", value=False)
            if item.get_value(key="completed") == True:
                completed_items += 1
                continue

            if item.name == "":
                item.set_value(key="show", value=True)
                item.parent_assembly.set_parent_assembly_value(key="show", value=True)
                continue

            search_text = lineEdit_search.text().lower()
            if search_text != "" and search_text not in item.name.lower():
                continue

            if selected_materials := [button.text() for button in materials if button.isChecked()]:
                item_materials = item.get_value("material")
                if item_materials not in selected_materials:
                    continue

            if selected_thicknesses := [button.text() for button in thicknesses if button.isChecked()]:
                item_thicknesses = item.get_value("thickness")
                if item_thicknesses not in selected_thicknesses:
                    continue

            if selected_flow_tags := [button.text() for button in flow_tags if button.isChecked()]:
                with contextlib.suppress(IndexError):  # This means the part is 'completed'
                    item_flow_tag = item.get_value("flow_tag")[item.get_value("current_flow_state")]
                    if item_flow_tag not in selected_flow_tags:
                        continue

            if selected_statuses := [button.text() for button in statuses if button.isChecked()]:
                item_status = item.get_value("status")
                if item_status not in selected_statuses:
                    continue

            if selected_paint_colors := [button.text() for button in paint_colors if button.isChecked()]:
                item_paint = item.get_value("paint_color")
                if item_paint != None:
                    for color_name, color_code in workspace_tags.get_value("paint_colors").items():
                        if color_code == item_paint:
                            item_paint = color_name
                            break
                if item_paint is None:
                    item_paint = "None"
                if item_paint not in selected_paint_colors:
                    continue

            # Apply due dates filter
            with contextlib.suppress(TypeError):
                if groupBox_due_dates.isChecked():
                    assembly_due_date = item.get_value("due_date")
                    after_date = dateTimeEdit_after.dateTime().toPyDateTime().date()
                    before_date = dateTimeEdit_before.dateTime().toPyDateTime().date()
                    if assembly_due_date < after_date or assembly_due_date > before_date:
                        continue
            item.set_value(key="show", value=True)
            item.parent_assembly.set_parent_assembly_value(key="show", value=True)
        # Are all items completed
        if completed_items == len(sub_assembly.items):
            if selected_flow_tags := [button.text() for button in flow_tags if button.isChecked()]:
                with contextlib.suppress(IndexError):  # This means the part is 'completed'
                    assembly_flow_tag = sub_assembly.get_assembly_data("flow_tag")[sub_assembly.get_assembly_data("current_flow_state")]
                    if assembly_flow_tag in selected_flow_tags:
                        sub_assembly.set_assembly_data(key="show", value=True)
                        sub_assembly.set_parent_assembly_value(key="show", value=True)
                    else:
                        sub_assembly.set_assembly_data(key="show", value=False)
            if selected_statuses := [button.text() for button in statuses if button.isChecked()]:
                assembly_status = sub_assembly.get_assembly_data("status")
                if assembly_status is None:
                    assembly_status = "None"
                if assembly_status in selected_statuses:
                    sub_assembly.set_assembly_data(key="show", value=True)
                    sub_assembly.set_parent_assembly_value(key="show", value=True)
                else:
                    sub_assembly.set_assembly_data(key="show", value=False)
        for _sub_assembly in sub_assembly.sub_assemblies:
            self.filter_assemblies(sub_assembly=_sub_assembly, filter=filter)

    def get_filtered_data(self, filter: dict) -> dict:
        """
        This function filters data based on a given dictionary filter and returns the filtered data.

        Args:
          filter (dict): A dictionary containing filter options. The "use_filter" key contains a
        QPushButton object that determines whether to apply the filter or not.

        Returns:
          a dictionary.
        """
        workspace_tags.load_data()
        if not filter:
            for assembly in self.data:
                assembly.set_default_value_to_all_items(key="show", value=True)
                assembly.set_data_to_all_sub_assemblies(key="show", value=True)
                assembly.set_assembly_data(key="show", value=True)
            return self.data
        checkbox_use_filter: QPushButton = filter["use_filter"]
        flow_tags: list[QPushButton] = filter["flow_tags"]
        statuses: list[QPushButton] = filter["statuses"]

        if not checkbox_use_filter.isChecked():
            for assembly in self.data:
                assembly.set_default_value_to_all_items(key="show", value=True)
                assembly.set_data_to_all_sub_assemblies(key="show", value=True)
                assembly.set_assembly_data(key="show", value=True)
            return self.data
        else:
            for assembly in self.data:
                self.filter_assemblies(sub_assembly=assembly, filter=filter)
            for assembly in self.data:
                if (
                    not assembly.get_assembly_data("has_items")
                    and self.is_assembly_empty(assembly) == True
                    and assembly.get_assembly_data("has_sub_assemblies")
                ):
                    if not assembly.any_sub_assemblies_to_show() and self.is_assembly_empty(assembly) == True:
                        assembly.set_assembly_data(key="show", value=False)
                    if assembly.all_sub_assemblies_complete():
                        assembly.set_assembly_data(key="show", value=True)
                        if selected_flow_tags := [button.text() for button in flow_tags if button.isChecked()]:
                            with contextlib.suppress(IndexError):  # This means the part is 'completed'
                                assembly_flow_tag = assembly.get_assembly_data("flow_tag")[assembly.get_assembly_data("current_flow_state")]
                                if assembly_flow_tag not in selected_flow_tags:
                                    assembly.set_assembly_data(key="show", value=False)
                        if selected_statuses := [button.text() for button in statuses if button.isChecked()]:
                            assembly_status = assembly.get_assembly_data("status")
                            if assembly_status is None:
                                assembly_status = "None"
                            if assembly_status not in selected_statuses:
                                assembly.set_assembly_data(key="show", value=False)
        return self.data

    def __gather_sub_assembly_data(self, sub_assembly: Assembly, data: list) -> bool:
        """
        The function gathers data on whether each sub-assembly or item within a sub-assembly should be
        shown.

        Args:
          sub_assembly (Assembly): The `sub_assembly` parameter is an instance of the `Assembly` class.
        It represents a sub-assembly object that contains items and possibly other sub-assemblies.
          data (list): The `data` parameter is a list that is used to store the values of `should_show`
        for each sub-assembly and its items.

        Returns:
          a list of boolean values.
        """
        should_show = any(item.get_value(key="show") for item in sub_assembly.items)
        data.append(should_show)
        for _sub_assembly in sub_assembly.sub_assemblies:
            should_show = any(item.get_value(key="show") for item in _sub_assembly.items)
            data.append(should_show)
            # data.extend(self.__gather_sub_assembly_data(sub_assembly=_sub_assembly, data=data))
        return data

    def is_assembly_empty(self, assembly: Assembly) -> bool:
        """
        The function checks if an assembly and its sub-assemblies are empty based on a "show" attribute.

        Args:
          assembly (Assembly): The "assembly" parameter is an object of the "Assembly" class.

        Returns:
          a boolean value. It returns True if the assembly is empty, meaning that none of the items in
        the assembly or its sub-assemblies have the "show" attribute set to True. It returns False if at
        least one item in the assembly or its sub-assemblies has the "show" attribute set to True.
        """
        data = {assembly: []}
        should_show = any(item.get_value(key="show") for item in assembly.items)
        data[assembly].append(should_show)
        for sub_assembly in assembly.sub_assemblies:
            data[assembly].extend(self.__gather_sub_assembly_data(sub_assembly=sub_assembly, data=data[assembly]))
        return not any(data[assembly])

    def get_data(self) -> dict:
        """
        This function returns a deep copy of the data stored in the object.

        Returns:
          A deep copy of the dictionary `self.data` is being returned.
        """
        return self.data

    def to_dict(self) -> dict:
        """
        This function converts an object to a dictionary format.

        Returns:
          A dictionary containing the data of the assembly and its sub-assemblies in a nested format.
        """
        data = {}
        for assembly in self.data:
            processed_sub_assemblies = {assembly}
            data[assembly.name] = assembly.to_dict(processed_assemblies=processed_sub_assemblies)
        return data

    def duplicate_assembly(self, assembly_name: str | Assembly) -> Assembly:
        """
        This function duplicates an assembly and renames it with "(Copy)" appended to the original name.

        Args:
          assembly_name (str | Assembly): The name of the new assembly that will be created as a
        duplicate of the original assembly.

        Returns:
          an instance of the `Assembly` class.
        """
        assembly: Assembly = self.copy(assembly_name)
        assembly.rename(f"{assembly.name} - (Copy)")
        self.set_assembly(assembly)
        return assembly

    def copy(self, assembly_name: str | Assembly) -> Assembly | None:
        """
        This function makes a deep copy of an assembly object by searching for its name in a list of
        assemblies.

        Args:
          assembly_name (str | Assembly): The name of the assembly to be copied, which can be either a
        string or an instance of the Assembly class.

        Returns:
          The method `copy` returns a deep copy of an `Assembly` object with the specified name, or
        `None` if no such object exists in the `data` list.
        """
        if type(assembly_name) == Assembly:
            assembly_name = assembly_name.name
        return next(
            (copy.deepcopy(assembly) for assembly in self.data if assembly.name == assembly_name),
            None,
        )

    def set_assembly(self, assembly: Assembly) -> None:
        """
        This function sets an empty dictionary for a given assembly in a class attribute called "data".

        Args:
          assembly (Assembly): The parameter "assembly" is of type "Assembly". It is being passed as an
        argument to the method "set_assembly". The method is expected to take this assembly object and
        use it to set some data in the "self.data" dictionary.
        """
        self.data[assembly] = {}

    def add_assembly(self, assembly: Assembly) -> None:
        """
        This function sets an empty dictionary for a given assembly in a class attribute called "data".

        Args:
          assembly (Assembly): The parameter "assembly" is of type "Assembly". It is being passed as an
        argument to the method "set_assembly". The method is expected to take this assembly object and
        use it to set some data in the "self.data" dictionary.
        """
        self.data[assembly] = {}

    def get_assembly(self, assembly_name: str) -> Assembly | None:
        """
        This function searches for an assembly with a given name in a list of assemblies and returns it
        if found, otherwise it returns None.

        Args:
          assembly_name (str): A string representing the name of the assembly to be retrieved.

        Returns:
          an instance of the `Assembly` class if an assembly with the specified name is found in the
        `self.data` list. If no assembly is found, the function returns `None`.
        """
        return next(
            (assembly for assembly in self.data if assembly.name == assembly_name),
            None,
        )

    def remove_assembly(self, assembly: Assembly) -> Assembly:
        """
        This function removes an assembly from a data structure and returns a copy of the removed
        assembly.

        Args:
          assembly (Assembly): The "assembly" parameter is an object of the "Assembly" class that is
        being passed as an argument to the "remove_assembly" method. The method is expected to remove
        this assembly object from the data stored in the current object and return a copy of the removed
        assembly object.

        Returns:
          The method `remove_assembly` returns a copy of the `Assembly` object that was passed as an
        argument to the method.
        """
        copy = self.copy(assembly)
        self.data.pop(assembly)
        return copy

    def get_all_assembly_names(self) -> list[str]:
        """
        This function returns a list of names of all the assemblies in the data.

        Returns:
          A list of strings containing the names of all the assemblies in the data.
        """
        return [assembly.name for assembly in self.data]

    def __get_counts(self, sub_assembly: Assembly) -> tuple[int, int, int, int]:
        """
        The function recursively counts the number of items and sub-assemblies, as well as the number of
        completed items and sub-assemblies, within a given assembly.

        Args:
          sub_assembly (Assembly): The sub-assembly for which the counts are being calculated.

        Returns:
          a tuple of four integers: item_count, item_completion_count, assembly_count, and
        assembly_completion_count.
        """
        item_count: int = 0 + len(sub_assembly.items)
        item_completion_count: int = sum(bool(item.get_value("completed")) for item in sub_assembly.items)
        assembly_count: int = 0 + len(sub_assembly.sub_assemblies)
        assembly_completion_count: int = sum(bool(sub_assembly.get_assembly_data("completed")) for sub_assembly in sub_assembly.sub_assemblies)

        for _sub_assembly in sub_assembly.sub_assemblies:
            _item_count, _item_completion_count, _assembly_count, _assembly_completion_count = self.__get_counts(sub_assembly=_sub_assembly)
            item_count += _item_count
            item_completion_count += _item_completion_count
            assembly_count += _assembly_count
            assembly_completion_count += _assembly_completion_count
        return item_count, item_completion_count, assembly_count, assembly_completion_count

    def get_completion_percentage(self, assembly: Assembly) -> tuple[float, float]:
        """
        This function calculates the completion percentage of items and assemblies based on their
        counts.

        Args:
          assembly (Assembly): The "assembly" parameter is an instance of the "Assembly" class, which is
        being passed as an argument to the "get_completion_percentage" method.

        Returns:
          A tuple containing two float values - the completion percentage for items and the completion
        percentage for assemblies.
        """
        item_count, item_completion_count, assembly_count, assembly_completion_count = self.__get_counts(sub_assembly=assembly)
        try:
            item_completion_percentage = item_completion_count / item_count
        except ZeroDivisionError:
            item_completion_percentage = 0.0
        try:
            assembly_completion_percentage = assembly_completion_count / assembly_count
        except ZeroDivisionError:
            assembly_completion_percentage = 0.0
        return item_completion_percentage, assembly_completion_percentage

    def get_all_groups(self) -> list[str]:
        """
        This function returns a list of unique group names extracted from a list of assembly data
        objects.

        Returns:
          A list of unique group names extracted from the assembly data of the object's data attribute.
        """
        return list(set(assembly.get_assembly_data(key="group") for assembly in self.data if assembly.get_assembly_data("show")))

    def _get_all_groups(self) -> list[str]:
        """
        This function returns a list of unique group names extracted from a list of assembly data
        objects.

        Returns:
          A list of unique group names extracted from the assembly data of the object's data attribute.
        """
        return list(set(assembly.get_assembly_data(key="group") for assembly in self.data))

    def get_grouped_data(self) -> dict[str, list[Assembly]]:
        """
        The function `get_grouped_data` takes a list of `Assembly` objects and groups them based on a
        specified key, returning a dictionary where the keys are the groups and the values are lists of
        `Assembly` objects belonging to each group.

        Returns:
          a dictionary where the keys are strings representing groups, and the values are lists of
        Assembly objects.
        """
        data: dict[str, list[Assembly]] = {}
        for group in self.get_all_groups():
            data[group] = []
        for assembly in self.data:
            with contextlib.suppress(KeyError):
                data[assembly.get_assembly_data(key="group")].append(assembly)
        return data

    def __get_all_items(self, sub_assembly: Assembly) -> list[Item]:
        """
        The function `__get_all_items` recursively retrieves all items from a given sub-assembly and its
        sub-assemblies.

        Args:
          sub_assembly (Assembly): The parameter "sub_assembly" is of type "Assembly".

        Returns:
          a list of items.
        """
        items: list[Item] = []
        items.extend(sub_assembly.items)
        for _sub_assembly in sub_assembly.sub_assemblies:
            items.extend(self.__get_all_items(sub_assembly=_sub_assembly))
        return items

    def get_all_items(self) -> list[Item]:
        """
        The function `get_all_items` returns a list of all items in a given data structure, including
        items from sub-assemblies.

        Returns:
          a list of Item objects.
        """
        items: list[Item] = []
        for assembly in self.data:
            items.extend(assembly.items)
            for sub_assembly in assembly.sub_assemblies:
                items.extend(self.__get_all_items(sub_assembly=sub_assembly))
        return items

    def get_grouped_items(self) -> ItemGroup:
        """
        The function `get_grouped_items` takes all items and groups them together into an `ItemGroup`
        object.

        Returns:
          an instance of the ItemGroup class.
        """
        all_items: list[Item] = self.get_all_items()
        grouped_items: ItemGroup = ItemGroup()
        for item in all_items:
            if item.get_value(key="show"):
                grouped_items.add_item(item)
        return grouped_items

    def __get_all_assemblies(self, sub_assembly: Assembly) -> list[Assembly]:
        """
        The function recursively retrieves all sub-assemblies of a given assembly.

        Args:
          sub_assembly (Assembly): The parameter `sub_assembly` is an instance of the `Assembly` class.

        Returns:
          a list of Assembly objects.
        """
        all_assemblies: list[Assembly] = []
        all_assemblies.extend(sub_assembly.sub_assemblies)
        for _sub_assembly in sub_assembly.sub_assemblies:
            all_assemblies.extend(self.__get_all_assemblies(sub_assembly=_sub_assembly))
        return all_assemblies

    def get_all_assemblies(self) -> list[Assembly]:
        """
        The function `get_all_assemblies` returns a list of all assemblies and their sub-assemblies.

        Returns:
          a list of Assembly objects.
        """
        all_assemblies: list[Assembly] = []
        for assembly in self.data:
            all_assemblies.append(assembly)
            all_assemblies.extend(assembly.sub_assemblies)
            for sub_assembly in assembly.sub_assemblies:
                all_assemblies.extend(self.__get_all_assemblies(sub_assembly=sub_assembly))
        return all_assemblies

    def do_all_items_have_flow_tags(self) -> bool:
        """
        The function checks if all items in a collection have a non-empty "flow_tag" value.

        Returns:
          a boolean value. It returns True if all items in the self.get_all_items() list have a
        non-empty value for the "flow_tag" key, and False otherwise.
        """
        for item in self.get_all_items():
            if len(item.get_value(key="flow_tag")) == 0:
                return False
        return True

    def do_all_sub_assemblies_have_flow_tags(self) -> bool:
        """
        The function checks if all items in a collection have a non-empty "flow_tag" value.

        Returns:
          a boolean value. It returns True if all items in the self.get_all_items() list have a
        non-empty value for the "flow_tag" key, and False otherwise.
        """
        for assembly in self.get_all_assemblies():
            if len(assembly.get_assembly_data(key="flow_tag")) == 0:
                return False
        return True
