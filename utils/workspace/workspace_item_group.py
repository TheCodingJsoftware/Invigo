from utils.workspace.workspace_item import WorkspaceItem


class WorkspaceItemGroup:
    def __init__(self) -> None:
        self.data: dict[str, list[WorkspaceItem]] = {}

    def add_item_to_group(self, group_name: str, item: WorkspaceItem) -> None:
        self.data.setdefault(group_name, []).append(item)

    def add_item(self, item: WorkspaceItem) -> None:
        self.data.setdefault(item.name, []).append(item)

    def get_item(self, item_name: str) -> WorkspaceItem | None:
        try:
            return self.data[item_name][0]
        except KeyError:
            return None

    def get_item_list(self, item_name: str) -> list[WorkspaceItem]:
        return self.data[item_name]

    def remove_item(self, item: WorkspaceItem) -> None:
        del self.data[item.name][item]

    def to_string(self, item_name: str) -> str:
        return "\n" + "\n".join(f'{i+1}. {item.parent_assembly.get_master_assembly().get_assembly_data(key="display_name")}: {item.name} Qty: {item.parts_per}' for i, item in enumerate(self.data.get(item_name, [])))

    def get_total_quantity(self, item_name: str) -> int:
        return sum(item.parts_per for item in self.data.get(item_name, []))

    def filter_items(self, flow_tag: str) -> None:
        filtered_data = {}
        for group_name, items in self.data.items():
            filtered_items = []
            for item in items:
                if item.completed:
                    continue
                if flow_tag != "Recut":
                    try:
                        item_flow_tag = item.get_current_flow_state()
                    except IndexError:
                        continue
                    if item_flow_tag == flow_tag:
                        filtered_items.append(item)
                elif item.recut:
                    filtered_items.append(item)
            if filtered_items:
                filtered_data[group_name] = filtered_items
        self.data = filtered_data
