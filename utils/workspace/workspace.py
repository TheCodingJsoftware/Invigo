import contextlib
import copy
import math
import os
from typing import Union

import ujson as json
from PyQt6.QtWidgets import QListWidget, QCheckBox, QDateTimeEdit, QGroupBox, QLineEdit, QPushButton
from utils.workspace.assembly import Assembly
from utils.workspace.item import Item


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
            assembly: Assembly = Assembly(name=assembly_name, assembly_data=data[assembly_name]["assembly_data"])
            self.set_assembly(self.load_assembly(assembly_name, data[assembly_name]))

    # TODO
    def get_users_data(self) -> dict:
        # Consider filtering items relevant to the user
        return {}

    def filter_assemblies(self, sub_assembly: Assembly, filter: dict):
        lineEdit_search: QLineEdit = filter['search']
        listWidget_materials: QListWidget = filter['materials']
        listWidget_thicknesses: QListWidget = filter['thicknesses']
        listWidget_flow_tags: QListWidget = filter['flow_tags']
        listWidget_statuses: QListWidget = filter['statuses']
        groupBox_due_dates: QGroupBox = filter['due_dates']
        dateTimeEdit_after: QDateTimeEdit = filter['dateTimeEdit_after']
        dateTimeEdit_before: QDateTimeEdit = filter['dateTimeEdit_before']

        # Recursively filter sub-assemblies
        for item in sub_assembly.items:
            # Apply search filter
            item.set_value(key='show', value=False)
            search_text = lineEdit_search.text().lower()
            if search_text and search_text not in item.name.lower():
                continue

            # Apply materials filter
            selected_materials = [item.text() for item in listWidget_materials.selectedItems()]
            if selected_materials:
                item_materials = item.get_value('material')
                if item_materials not in selected_materials:
                    continue

            # Apply thicknesses filter
            selected_thicknesses = [item.text() for item in listWidget_thicknesses.selectedItems()]
            if selected_thicknesses:
                item_thicknesses = item.get_value('thickness')
                if item_thicknesses not in selected_thicknesses:
                    continue

            # Apply flow tags filter
            selected_flow_tags = [item.text() for item in listWidget_flow_tags.selectedItems()]
            if selected_flow_tags:
                item_tag = item.get_value('flow_tag')[item.get_value('current_flow_state')]
                if item_tag not in selected_flow_tags:
                    continue

            # Apply statuses filter
            selected_statuses = [item.text() for item in listWidget_statuses.selectedItems()]
            if selected_statuses:
                item_status = item.get_value('status')
                if item_status not in selected_statuses:
                    continue

            # Apply due dates filter
            if groupBox_due_dates.isChecked():
                assembly_due_date = item.get_value('due_date')
                after_date = dateTimeEdit_after.dateTime().toPyDateTime().date()
                before_date = dateTimeEdit_before.dateTime().toPyDateTime().date()
                if assembly_due_date < after_date or assembly_due_date > before_date:
                    continue
            item.set_value(key='show', value=True)
        for _sub_assembly in sub_assembly.sub_assemblies:
            self.filter_assemblies(sub_assembly=_sub_assembly, filter=filter)

    def get_filtered_data(self, filter: dict) -> dict:
        checkBox_use_filter: QPushButton = filter['use_filter']

        if not checkBox_use_filter.isChecked():
            for assembly in self.data:
                assembly.set_default_value_to_all_items(key='show', value=True)
            return self.data
        else:
            for assembly in self.data:
                self.filter_assemblies(sub_assembly=assembly, filter=filter)
        return self.data

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
        copy = self.copy(assembly)
        self.data.pop(assembly)
        return copy

    def get_all_assembly_names(self) -> list[str]:
        return [assembly.name for assembly in self.data]
