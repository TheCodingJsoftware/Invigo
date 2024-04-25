import copy
from typing import Any, Union

from utils.workspace.workspace_item import WorkspaceItem


class Assembly:
    def __init__(self, **kwargs: Union[str, list["Assembly"], list[WorkspaceItem]]) -> None:
        self.name = kwargs.get("name")
        self.assembly_data: dict[str, object] = kwargs.get("assembly_data")
        self.sub_assemblies: list["Assembly"] = kwargs.get("sub_assemblies")
        self.items: list[WorkspaceItem] = kwargs.get("items")
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

    def set_item(self, item: WorkspaceItem) -> None:
        item.parent_assembly = self
        self.items.append(item)

    def add_item(self, item: WorkspaceItem) -> None:
        item.parent_assembly = self
        self.items.append(item)

    def remove_item(self, item: WorkspaceItem) -> None:
        if self.exists(item):
            self.items.remove(item)

    def set_assembly_data(self, key: str, value: Any) -> None:
        self.assembly_data[key] = value

    def get_assembly_data(self, key: str) -> Any:
        try:
            return self.assembly_data[key]
        except KeyError:
            return None

    def delete_assembly_value(self, key: str) -> Any:
        try:
            value_copy = self.assembly_data[key]
            del self.assembly_data[key]
            return value_copy
        except KeyError:
            return None

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

    def get_data(self) -> dict:
        return self.data

    def set_timer(self, flow_tag: str, time: object) -> None:
        self.assembly_data["timers"][flow_tag]["time_to_complete"] = time.value()

    def _set_data_to_all_sub_assemblies(self, sub_assembly: "Assembly", key: str, value: Any) -> None:
        sub_assembly.set_assembly_data(key=key, value=value)
        if sub_assembly.sub_assemblies:
            for _sub_assembly in sub_assembly.sub_assemblies:
                self._set_data_to_all_sub_assemblies(sub_assembly=_sub_assembly, key=key, value=value)

    def set_data_to_all_sub_assemblies(self, key: str, value: Any) -> None:
        self.assembly_data[key] = value
        for sub_assembly in self.sub_assemblies:
            self._set_data_to_all_sub_assemblies(sub_assembly=sub_assembly, key=key, value=value)

    def _set_default_value_to_all_items(self, sub_assembly: "Assembly", key: str, value: str) -> None:
        for item in sub_assembly.items:
            item.set_value(key=key, value=value)
        if sub_assembly != None:
            for _sub_assembly in sub_assembly.sub_assemblies:
                for item in _sub_assembly.items:
                    item.set_value(key=key, value=value)
                if _sub_assembly.sub_assemblies:
                    self._set_default_value_to_all_items(sub_assembly=_sub_assembly, key=key, value=value)

    def set_default_value_to_all_items(self, key: str, value: str) -> None:
        for item in self.items:
            item.set_value(key=key, value=value)
        for sub_assembly in self.sub_assemblies:
            for item in sub_assembly.items:
                item.set_value(key=key, value=value)
            if self.sub_assemblies:
                self._set_default_value_to_all_items(sub_assembly=sub_assembly, key=key, value=value)

    def any_items_to_show(self) -> bool:
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
        for assembly in self.sub_assemblies:
            if assembly.get_assembly_data("show") is True:
                return True
            # for sub_assembly in assembly.sub_assemblies:
            #     if sub_assembly._any_sub_assemblies_to_show(sub_assembly):
            #         return True
        return False

    def all_items_complete(self) -> bool:
        return all(item.get_value("completed") != False for item in self.items)

    def all_sub_assemblies_complete(self) -> bool:
        return all(sub_assembly.get_assembly_data(key="completed") != False for sub_assembly in self.sub_assemblies)
