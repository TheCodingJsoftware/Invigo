from typing import Any

from utils.workspace.item import Item


class ItemGroup:
    def __init__(self) -> None:
        self.data: dict[str, list[Item]] = {}

    def add_item_to_group(self, group_name: str, item: Item) -> None:
        self.data.setdefault(group_name, []).append(item)

    def add_item(self, item: Item) -> None:
        self.data.setdefault(item.name, []).append(item)

    def get_item(self, item_name: str) -> Item | None:
        try:
            return self.data[item_name][0]
        except KeyError:
            return None

    def get_item_list(self, item_name: str) -> list[Item]:
        return self.data[item_name]

    def remove_item(self, item: Item) -> None:
        del self.data[item.name][item]

    def to_string(self, item_name: str) -> str:
        return "\n" + "\n".join(
            f'{i+1}. {item.parent_assembly.get_master_assembly().get_assembly_data(key="display_name")}: {item.name} Qty: {item.get_value("parts_per")}'
            for i, item in enumerate(self.data.get(item_name, []))
        )

    def update_values(self, item_to_update: str, key: str, value: Any) -> None:
        for item in self.data[item_to_update]:
            item.set_value(key=key, value=value)

    def get_total_quantity(self, item_name: str) -> int:
        return sum(item.get_value(key="parts_per") for item in self.data.get(item_name, []))

    def filter_items(self, flow_tag: str) -> None:
        filtered_data = {}
        for group_name, items in self.data.items():
            filtered_items = []
            for item in items:
                if item.get_value("completed"):
                    continue
                if flow_tag != "Recut":
                    try:
                        item_flow_tag = item.get_value("flow_tag")[item.get_value("current_flow_state")]
                    except IndexError:
                        continue
                    if item_flow_tag == flow_tag:
                        filtered_items.append(item)
                else:
                    if item.get_value("recut"):
                        filtered_items.append(item)
            if filtered_items:
                filtered_data[group_name] = filtered_items
        self.data = filtered_data
