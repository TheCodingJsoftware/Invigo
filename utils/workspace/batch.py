from utils.workspace.item import Item


class Batch:
    def __init__(self, name: str) -> None:
        self.name = name
        self.data = {}

    def set_item(self, item: Item) -> None:
        self.data[item] = item.to_dict()

    def rename(self, new_name: str) -> None:
        self.name = new_name

    def to_dict(self) -> dict:
        return self.data

    def get_item(self, item_name: str) -> Item | None:
        for item in self.data:
            if item.name == item_name:
                return item
        return None
