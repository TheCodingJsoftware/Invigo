import copy
from typing import Any, Union

from utils.workspace.workspace_item import WorkspaceItem


class Assembly:
    def __init__(self, name: str, assembly_data: dict[str, object]) -> None:
        self.name = name
        self.sub_assemblies: list[Assembly] = []
        self.items: list[WorkspaceItem] = []
        self.parent_assembly: "Assembly" = None
        self.master_assembly: "Assembly" = None

        self.expected_time_to_complete: float = 0.0
        self.has_items: bool = False
        self.has_sub_assemblies: bool = False
        self.group: str = ""
        self.group_color: str = ""
        self.flow_tag: list[str] = []
        self.paint_color: str = None
        self.paint_type: str = None
        self.paint_amount: float = 0.0
        self.assembly_image: str = None
        # NOTE Used by user workspace
        self.timers: dict[str, dict] = {}
        self.display_name: str = ""
        self.completed: bool = False
        self.starting_date: str = ""
        self.ending_date: str = ""
        self.status: str = None
        self.current_flow_state: int = 0
        self.date_completed: str = ""
        self.load_data(assembly_data)

        # NOTE Non serializable variables
        self.show = True

    def load_data(self, data: dict[str, Union[float, bool, str, dict]]):
        self.expected_time_to_complete: float = data.get("expected_time_to_complete", 0.0)
        self.has_items: bool = data.get("has_items", False)
        self.has_sub_assemblies: bool = data.get("has_sub_assemblies", True)
        self.group: str = data.get("group", "")
        self.group_color: str = data.get("group_color", "")
        self.flow_tag: list[str] = data.get("flow_tag", [])
        self.paint_color: str = data.get("paint_color")
        self.paint_type: str = data.get("paint_type")
        self.paint_amount: float = data.get("paint_amount", 0.0)
        self.assembly_image: str = data.get("assembly_image")
        # NOTE Used by user workspace
        self.timers: dict[str, dict[str, object]] = data.get("timers", {})
        self.display_name: str = data.get("display_name", "")
        self.completed: bool = data.get("completed", False)
        self.starting_date: str = data.get("starting_date", "")
        self.ending_date: str = data.get("ending_date", "")
        self.status: str = data.get("status")
        self.current_flow_state: int = data.get("current_flow_state", 0)
        self.date_completed: str = data.get("date_completed", "")

    def set_parent_assembly_value(self, key: str, value: Any) -> None:
        if key == "show":
            self.show = value
            if self.parent_assembly is not None:
                self.parent_assembly.show = value

    def set_item(self, item: WorkspaceItem) -> None:
        item.parent_assembly = self
        self.items.append(item)

    def add_item(self, item: WorkspaceItem) -> None:
        item.parent_assembly = self
        self.items.append(item)

    def remove_item(self, item: WorkspaceItem) -> None:
        if self.exists(item):
            self.items.remove(item)

    def get_current_flow_state(self) -> str:
        return self.flow_tag[self.current_flow_state]

    def get_master_assembly(self) -> "Assembly":
        master_assembly = self
        while master_assembly.parent_assembly is not None:
            master_assembly = master_assembly.parent_assembly
        return master_assembly

    def delete_sub_assembly(self, assembly) -> "Assembly":
        copy = self.copy_sub_assembly(assembly)
        self.sub_assemblies.remove(assembly)
        return copy

    def set_sub_assembly(self, assembly: "Assembly") -> list["Assembly"]:
        assembly.parent_assembly = self
        assembly.master_assembly = assembly.get_master_assembly()
        self.sub_assemblies.append(assembly)

    def add_sub_assembly(self, assembly: "Assembly") -> list["Assembly"]:
        assembly.parent_assembly = self
        assembly.master_assembly = assembly.get_master_assembly()
        self.sub_assemblies.append(assembly)

    def get_sub_assemblies(self) -> list["Assembly"]:
        return self.sub_assemblies

    def get_sub_assembly(self, assembly_name: str) -> "Assembly":
        return next(
            (sub_assembly for sub_assembly in self.sub_assemblies if sub_assembly.name == assembly_name),
            None,
        )

    def copy_sub_assembly(self, assembly_name: Union[str, "Assembly"]) -> "Assembly":
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
        self.name = new_name

    def to_dict(self, processed_assemblies: set = None) -> dict:
        if processed_assemblies is None:
            processed_assemblies = set()
        processed_assemblies.add(self)

        data = {
            "items": {},
            "assembly_data": {
                "expected_time_to_complete": self.expected_time_to_complete,
                "has_items": self.has_items,
                "has_sub_assemblies": self.has_sub_assemblies,
                "group": self.group,
                "group_color": self.group_color,
                "flow_tag": self.flow_tag,
                "paint_color": self.paint_color,
                "paint_type": self.paint_type,
                "paint_amount": self.paint_amount,
                "assembly_image": self.assembly_image,
                "timers": self.timers,
                "display_name": self.display_name,
                "completed": self.completed,
                "starting_date": self.starting_date,
                "ending_date": self.ending_date,
                "status": self.status,
                "current_flow_state": self.current_flow_state,
                "date_completed": self.date_completed,
            },
            "sub_assemblies": {},
        }
        for sub_assembly in self.sub_assemblies:
            if sub_assembly not in processed_assemblies:  # Check if the sub-assembly is already processed
                data["sub_assemblies"][sub_assembly.name] = sub_assembly.to_dict(processed_assemblies)
        for item in self.items:
            if item.name == "":
                continue
            data["items"][item.name] = item.to_dict()
        return data

    def exists(self, other: WorkspaceItem | str) -> bool:
        if isinstance(other, WorkspaceItem):
            return any(other.name == item.name for item in self.items)
        elif isinstance(other, str):
            return any(other == item.name for item in self.items)

    def get_item(self, item_name: str) -> WorkspaceItem | None:
        return next((item for item in self.items if item.name == item_name), None)

    def get_all_items(self) -> list[WorkspaceItem]:
        all_items = self.items.copy()
        for sub_assembly in self.sub_assemblies:
            all_items.extend(sub_assembly.get_all_items())
        return all_items

    def get_item_by_index(self, index: int) -> WorkspaceItem:
        return self.items[index]

    def copy_item(self, item_name: str) -> WorkspaceItem | None:
        return copy.deepcopy(self.get_item(item_name))

    def set_timer(self, flow_tag: str, time: object) -> None:
        self.timers[flow_tag]["time_to_complete"] = time.value()

    def _set_data_to_all_sub_assemblies(self, sub_assembly: "Assembly", key: str, value: Any) -> None:
        if key == "show":
            sub_assembly.show = value
        elif key == "starting_date":
            sub_assembly.starting_date = value
        elif key == "ending_date":
            sub_assembly.ending_date = value
        if sub_assembly.sub_assemblies:
            for _sub_assembly in sub_assembly.sub_assemblies:
                self._set_data_to_all_sub_assemblies(sub_assembly=_sub_assembly, key=key, value=value)

    def set_data_to_all_sub_assemblies(self, key: str, value: Any) -> None:
        if key == "show":
            self.show = value
        elif key == "starting_date":
            self.starting_date = value
        elif key == "ending_date":
            self.ending_date = value
        for sub_assembly in self.sub_assemblies:
            self._set_data_to_all_sub_assemblies(sub_assembly=sub_assembly, key=key, value=value)

    def _set_default_value_to_all_items(self, sub_assembly: "Assembly", key: str, value: str) -> None:
        for item in sub_assembly.items:
            if key == "show":
                item.show = value
        if sub_assembly != None:
            for _sub_assembly in sub_assembly.sub_assemblies:
                for item in _sub_assembly.items:
                    if key == "show":
                        item.show = value
                if _sub_assembly.sub_assemblies:
                    self._set_default_value_to_all_items(sub_assembly=_sub_assembly, key=key, value=value)

    def set_default_value_to_all_items(self, key: str, value: str) -> None:
        for item in self.items:
            if key == "show":
                item.show = value
        for sub_assembly in self.sub_assemblies:
            for item in sub_assembly.items:
                if key == "show":
                    item.show = value
            if self.sub_assemblies:
                self._set_default_value_to_all_items(sub_assembly=sub_assembly, key=key, value=value)

    def any_items_to_show(self) -> bool:
        for item in self.items:
            if item.show and not item.completed:
                return True
        for sub_assembly in self.sub_assemblies:
            for item in sub_assembly.items:
                if item.show and not item.completed:
                    return True
        return False

    def _any_sub_assemblies_to_show(self, sub_assembly: "Assembly") -> bool:
        for _sub_assembly in sub_assembly.sub_assemblies:
            if _sub_assembly.show is True:
                return True
            if _sub_assembly._any_sub_assemblies_to_show(_sub_assembly):
                return True
        return False

    def any_sub_assemblies_to_show(self) -> bool:
        return any(assembly.show is True for assembly in self.sub_assemblies)

    def all_items_complete(self) -> bool:
        return all(item.completed != False for item in self.items)

    def all_sub_assemblies_complete(self) -> bool:
        return all(sub_assembly.completed != False for sub_assembly in self.sub_assemblies)
