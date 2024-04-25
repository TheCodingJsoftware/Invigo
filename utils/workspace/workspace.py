import contextlib
import copy
import math
import os
from typing import Union

import ujson as json
from PyQt6.QtCore import QDate
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
from utils.workspace.workspace_item import WorkspaceItem
from utils.workspace.workspace_item_group import WorkspaceItemGroup

workspace_tags = JsonFile(file_name="data/workspace_settings")


class Workspace:
    def __init__(self, file_name: str) -> None:
        self.data: list[Assembly] = []

        self.file_name: str = file_name
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"
        self.__create_file()
        self.load_data()

    def __create_file(self) -> None:
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w") as json_file:
                json_file.write("{}")

    def save(self) -> None:
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(self.to_dict(), json_file, ensure_ascii=False, indent=4)

    def save_data(self, data: dict) -> None:
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    def load_assembly(self, assembly_name: str, data: dict) -> Assembly:
        assembly = Assembly(name=assembly_name, assembly_data=data["assembly_data"])
        for item_name, item_data in data["items"].items():
            item: WorkspaceItem = WorkspaceItem(name=item_name, data=item_data)
            item.parent_assembly = assembly
            item.master_assembly = assembly.get_master_assembly()
            assembly.set_item(item)
        for sub_assembly_name, sub_assembly_data in data["sub_assemblies"].items():
            sub_assembly: Assembly = self.load_assembly(sub_assembly_name, sub_assembly_data)
            assembly.set_sub_assembly(sub_assembly)
        return assembly

    def load_data(self) -> None:
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
        # self.set_assembly_parents()

    # def set_subassembly_parents(self, sub_assembly: Assembly) -> None:
    #     for _sub_assembly in sub_assembly.sub_assemblies:
    #         _sub_assembly.parent_assembly = sub_assembly
    #         self.set_subassembly_parents(_sub_assembly)

    # def set_assembly_parents(self) -> None:
    #     for assembly in self.data:
    #         assembly.parent_assembly = None
    #         assembly.master_assembly = None
    #         for sub_assembly in assembly.sub_assemblies:
    #             # sub_assembly.parent_assembly = assembly
    #             self.set_subassembly_parents(sub_assembly)

    # TODO
    def get_users_data(self) -> dict:
        # Consider filtering items relevant to the user
        return {}

    def filter_assemblies(self, sub_assembly: Assembly, filter: dict):
        lineEdit_search: QLineEdit = filter["search"]
        materials: list[QPushButton] = filter["materials"]
        thicknesses: list[QPushButton] = filter["thicknesses"]
        flow_tags: list[QPushButton] = filter["flow_tags"]
        statuses: list[QPushButton] = filter["statuses"]
        paint_colors: list[QPushButton] = filter["paint"]
        groupBox_due_dates: QGroupBox = filter["due_dates"]
        calendar = filter["calendar"]
        dateTimeEdit_after, dateTimeEdit_before = calendar.get_timeline()  # end date
        show_recut: bool = filter["show_recut"]

        # Recursively filter sub-assemblies
        completed_items = 0
        for item in sub_assembly.items:
            item.set_value(key="show", value=False)
            if show_recut and item.get_value(key="recut") == False:
                continue
            if item.get_value(key="completed") == True:
                completed_items += 1
                #     item.parent_assembly.set_parent_assembly_value(key="show", value=True)
                #     item.set_value(key="show", value=True)
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
            # with contextlib.suppress(TypeError, AttributeError):
            if groupBox_due_dates.isChecked():
                item_start_date = QDate.fromString(item.get_value("starting_date"), "yyyy-M-d")
                item_ending_date = QDate.fromString(item.get_value("ending_date"), "yyyy-M-d")
                if dateTimeEdit_after is not None and dateTimeEdit_before is not None:
                    if not (item_start_date.daysTo(dateTimeEdit_before) >= 0 and item_ending_date.daysTo(dateTimeEdit_after) <= 0):
                        continue
                elif dateTimeEdit_after is not None and dateTimeEdit_before is None:
                    if not (item_start_date.daysTo(dateTimeEdit_after) >= 0 and item_ending_date.daysTo(dateTimeEdit_after) <= 0):
                        continue
            item.set_value(key="show", value=True)
            item.parent_assembly.set_parent_assembly_value(key="show", value=True)
        if self.get_completion_percentage(assembly=sub_assembly)[0] == 1:  # is item completeion 100%
            sub_assembly.set_assembly_data(key="show", value=False)
            if selected_flow_tags := [button.text() for button in flow_tags if button.isChecked()]:
                with contextlib.suppress(IndexError):  # This means the part is 'completed'
                    assembly_flow_tag = sub_assembly.get_assembly_data("flow_tag")[sub_assembly.get_assembly_data("current_flow_state")]
                    if assembly_flow_tag in selected_flow_tags:
                        sub_assembly.set_assembly_data(key="show", value=True)
                        sub_assembly.set_parent_assembly_value(key="show", value=True)
            if selected_statuses := [button.text() for button in statuses if button.isChecked()]:
                assembly_status = sub_assembly.get_assembly_data("status")
                if assembly_status is None:
                    assembly_status = "None"
                if assembly_status in selected_statuses:
                    sub_assembly.set_assembly_data(key="show", value=True)
                    sub_assembly.set_parent_assembly_value(key="show", value=True)
            if groupBox_due_dates.isChecked():
                assembly_start_date = QDate.fromString(sub_assembly.get_assembly_data("starting_date"), "yyyy-M-d")
                assembly_ending_date = QDate.fromString(sub_assembly.get_assembly_data("ending_date"), "yyyy-M-d")
                if dateTimeEdit_after is not None and dateTimeEdit_before is not None:
                    if assembly_start_date.daysTo(dateTimeEdit_before) >= 0 and assembly_ending_date.daysTo(dateTimeEdit_after) <= 0:
                        sub_assembly.set_assembly_data(key="show", value=True)
                        sub_assembly.set_parent_assembly_value(key="show", value=True)
                    else:
                        sub_assembly.set_assembly_data(key="show", value=False)
                elif dateTimeEdit_after is not None and dateTimeEdit_before is None:
                    if assembly_start_date.daysTo(dateTimeEdit_after) >= 0 and assembly_ending_date.daysTo(dateTimeEdit_after) <= 0:
                        sub_assembly.set_assembly_data(key="show", value=True)
                        sub_assembly.set_parent_assembly_value(key="show", value=True)
                    else:
                        sub_assembly.set_assembly_data(key="show", value=False)
            with contextlib.suppress(TypeError, IndexError):
                assembly_flow_tag = sub_assembly.get_assembly_data("flow_tag")[sub_assembly.get_assembly_data("current_flow_state")]
                if workspace_tags.get_value("attributes")[assembly_flow_tag]["show_all_items"]:
                    for item in sub_assembly.items:
                        item.set_value(key="show", value=True)
            if not (sub_assembly.all_sub_assemblies_complete() and sub_assembly.all_items_complete()):
                sub_assembly.set_assembly_data(key="show", value=False)

        for _sub_assembly in sub_assembly.sub_assemblies:
            self.filter_assemblies(sub_assembly=_sub_assembly, filter=filter)

    def get_filtered_data(self, filter: dict) -> dict:
        workspace_tags.load_data()
        if not filter:
            for assembly in self.data:
                assembly.set_default_value_to_all_items(key="show", value=True)
                assembly.set_data_to_all_sub_assemblies(key="show", value=True)
                assembly.set_assembly_data(key="show", value=True)
            return self.data
        try:
            checkbox_use_filter: QPushButton = filter["use_filter"]
            flow_tags: list[QPushButton] = filter["flow_tags"]
            statuses: list[QPushButton] = filter["statuses"]
        except KeyError:  # For a wierd bug if the filter loads before the gui
            return {}

        if not checkbox_use_filter.isChecked():
            for assembly in self.data:
                assembly.set_default_value_to_all_items(key="show", value=True)
                assembly.set_data_to_all_sub_assemblies(key="show", value=True)
                assembly.set_assembly_data(key="show", value=True)
            return self.data
        else:
            for assembly in self.data:
                self.filter_assemblies(sub_assembly=assembly, filter=filter)
            # for assembly in self.data:
            #     if self.is_assembly_empty(assembly) == True and (assembly.any_sub_assemblies_to_show() and assembly.all_sub_assemblies_complete()):
            #         assembly.set_assembly_data(key="show", value=True)
            #         if selected_flow_tags := [button.text() for button in flow_tags if button.isChecked()]:
            #             with contextlib.suppress(IndexError):  # This means the part is 'completed'
            #                 assembly_flow_tag = assembly.get_assembly_data("flow_tag")[assembly.get_assembly_data("current_flow_state")]
            #                 if assembly_flow_tag not in selected_flow_tags:
            #                     assembly.set_assembly_data(key="show", value=False)
            #         if selected_statuses := [button.text() for button in statuses if button.isChecked()]:
            #             assembly_status = assembly.get_assembly_data("status")
            #             if assembly_status is None:
            #                 assembly_status = "None"
            #             if assembly_status not in selected_statuses:
            #                 assembly.set_assembly_data(key="show", value=False)
            # assembly.set_assembly_data(key="show", value=assembly.any_sub_assemblies_to_show() or assembly.all_sub_assemblies_complete())
        return self.data

    def __gather_sub_assembly_data(self, sub_assembly: Assembly, data: list) -> bool:
        should_show = any(item.get_value(key="show") for item in sub_assembly.items)
        data.append(should_show)
        for _sub_assembly in sub_assembly.sub_assemblies:
            should_show = any(item.get_value(key="show") for item in _sub_assembly.items)
            data.append(should_show)
            # data.extend(self.__gather_sub_assembly_data(sub_assembly=_sub_assembly, data=data))
        return data

    def is_assembly_empty(self, assembly: Assembly) -> bool:
        data = {assembly: []}
        should_show = any(item.get_value(key="show") for item in assembly.items)
        data[assembly].append(should_show)
        for sub_assembly in assembly.sub_assemblies:
            data[assembly].extend(self.__gather_sub_assembly_data(sub_assembly=sub_assembly, data=data[assembly]))
        return not any(data[assembly])

    def get_data(self) -> dict:
        return self.data

    def to_dict(self) -> dict:
        data = {}
        for assembly in self.data:
            processed_sub_assemblies = {assembly}
            data[assembly.name] = assembly.to_dict(processed_assemblies=processed_sub_assemblies)
        return data

    def duplicate_assembly(self, assembly_name: str | Assembly) -> Assembly:
        assembly: Assembly = self.copy(assembly_name)
        assembly.rename(f"{assembly.name} - (Copy)")
        self.set_assembly(assembly)
        return assembly

    def copy(self, assembly_name: str | Assembly) -> Assembly | None:
        if isinstance(assembly_name, Assembly):
            assembly_name = assembly_name.name
        return next(
            (copy.deepcopy(assembly) for assembly in self.data if assembly.name == assembly_name),
            None,
        )

    def set_assembly(self, assembly: Assembly) -> None:
        assembly.master_assembly = None
        assembly.parent_assembly = None
        self.data.append(assembly)

    def add_assembly(self, assembly: Assembly) -> None:
        assembly.master_assembly = None
        assembly.parent_assembly = None
        self.data.append(assembly)

    def get_assembly(self, assembly_name: str) -> Assembly | None:
        return next(
            (assembly for assembly in self.data if assembly.name == assembly_name),
            None,
        )

    def remove_assembly(self, assembly_to_delete: Assembly) -> Assembly:
        copy = self.copy(assembly_to_delete)
        for i, assembly in enumerate(self.data):
            if assembly == assembly_to_delete:
                self.data.pop(i)
                break
        return copy

    def get_all_assembly_names(self) -> list[str]:
        return [assembly.name for assembly in self.data]

    def __get_counts(self, sub_assembly: Assembly) -> tuple[int, int, int, int]:
        item_count: int = 0 + len(sub_assembly.items)
        item_completion_count: int = sum(bool(item.get_value("completed")) for item in sub_assembly.items)
        assembly_count: int = 0 + len(sub_assembly.sub_assemblies)
        assembly_completion_count: int = sum(bool(sub_assembly.get_assembly_data("completed")) for sub_assembly in sub_assembly.sub_assemblies)

        for _sub_assembly in sub_assembly.sub_assemblies:
            (
                _item_count,
                _item_completion_count,
                _assembly_count,
                _assembly_completion_count,
            ) = self.__get_counts(sub_assembly=_sub_assembly)
            item_count += _item_count
            item_completion_count += _item_completion_count
            assembly_count += _assembly_count
            assembly_completion_count += _assembly_completion_count
        return (
            item_count,
            item_completion_count,
            assembly_count,
            assembly_completion_count,
        )

    def get_completion_percentage(self, assembly: Assembly) -> tuple[float, float]:
        (
            item_count,
            item_completion_count,
            assembly_count,
            assembly_completion_count,
        ) = self.__get_counts(sub_assembly=assembly)
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
        return list(set(assembly.get_assembly_data(key="group") for assembly in self.data if assembly.get_assembly_data("show")))

    def _get_all_groups(self) -> list[str]:
        return list(set(assembly.get_assembly_data(key="group") for assembly in self.data))

    def get_group_color(self, group: str) -> str | None:
        return next(
            (assembly.get_assembly_data(key="group_color") for assembly in self.data if assembly.get_assembly_data(key="group") == group),
            None,
        )

    def _get_all_groups(self) -> list[str]:
        return list(set(assembly.get_assembly_data(key="group") for assembly in self.data))

    def get_grouped_data(self) -> dict[str, list[Assembly]]:
        data: dict[str, list[Assembly]] = {}
        for group in self.get_all_groups():
            data[group] = []
        for assembly in self.data:
            with contextlib.suppress(KeyError):
                data[assembly.get_assembly_data(key="group")].append(assembly)
        return data

    def _get_grouped_data(self) -> dict[str, list[Assembly]]:
        data: dict[str, list[Assembly]] = {}
        for group in self._get_all_groups():
            data[group] = []
        for assembly in self.data:
            with contextlib.suppress(KeyError):
                data[assembly.get_assembly_data(key="group")].append(assembly)
        return data

    def __get_all_items(self, sub_assembly: Assembly) -> list[WorkspaceItem]:
        items: list[WorkspaceItem] = []
        items.extend(sub_assembly.items)
        for _sub_assembly in sub_assembly.sub_assemblies:
            items.extend(self.__get_all_items(sub_assembly=_sub_assembly))
        return items

    def get_all_items(self) -> list[WorkspaceItem]:
        items: list[WorkspaceItem] = []
        for assembly in self.data:
            items.extend(assembly.items)
            for sub_assembly in assembly.sub_assemblies:
                items.extend(self.__get_all_items(sub_assembly=sub_assembly))
        return items

    def get_grouped_items(self) -> WorkspaceItemGroup:
        all_items: list[WorkspaceItem] = self.get_all_items()
        grouped_items: WorkspaceItemGroup = WorkspaceItemGroup()
        for item in all_items:
            if item.get_value(key="show"):
                grouped_items.add_item(item)
        return grouped_items

    def __get_all_assemblies(self, sub_assembly: Assembly) -> list[Assembly]:
        all_assemblies: list[Assembly] = []
        all_assemblies.extend(sub_assembly.sub_assemblies)
        for _sub_assembly in sub_assembly.sub_assemblies:
            all_assemblies.extend(self.__get_all_assemblies(sub_assembly=_sub_assembly))
        return all_assemblies

    def get_all_assemblies(self) -> list[Assembly]:
        all_assemblies: list[Assembly] = []
        for assembly in self.data:
            all_assemblies.append(assembly)
            all_assemblies.extend(assembly.sub_assemblies)
            for sub_assembly in assembly.sub_assemblies:
                all_assemblies.extend(self.__get_all_assemblies(sub_assembly=sub_assembly))
        return all_assemblies

    def do_all_items_have_flow_tags(self) -> bool:
        for item in self.get_all_items():
            if len(item.get_value(key="flow_tag")) == 0:
                return False
        return True

    def do_all_sub_assemblies_have_flow_tags(self) -> bool:
        for assembly in self.get_all_assemblies():
            if len(assembly.get_assembly_data(key="flow_tag")) == 0:
                return False
        return True
