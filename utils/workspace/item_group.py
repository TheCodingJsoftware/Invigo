from typing import Any

from utils.workspace.item import Item


class ItemGroup:
    def __init__(self) -> None:
        self.data: dict[str, list[Item]] = {}

    def add_item(self, item: Item) -> None:
        """
        The function adds an item to a dictionary, using the item's name as the key and appending the
        item to the list of values for that key.

        Args:
          item (Item): The parameter "item" is of type "Item".
        """
        self.data.setdefault(item.name, []).append(item)

    def get_item(self, item_name: str) -> Item | None:
        """
        The function `get_item` retrieves an item from a dictionary based on its name, or returns `None`
        if the item does not exist.

        Args:
          item_name (str): A string representing the name of the item to retrieve.

        Returns:
          The method `get_item` returns an instance of the `Item` class if the `item_name` is found in
        the `self.data` dictionary. If the `item_name` is not found, it returns `None`.
        """
        try:
            return self.data[item_name][0]
        except KeyError:
            return None

    def get_item_list(self, item_name: str) -> list[Item]:
        return self.data[item_name]

    def remove_item(self, item: Item) -> None:
        """
        The function removes an item from a data structure.

        Args:
          item (Item): The parameter "item" is of type "Item".
        """
        del self.data[item.name][item]

    def to_string(self, item_name: str) -> str:
        """
        The function `to_string` takes in an item name as input and returns a string representation of
        the item's parent assembly, name, and quantity.

        Args:
          item_name (str): The `item_name` parameter is a string that represents the name of the item
        for which you want to generate a string representation.

        Returns:
          a string that contains a formatted list of items. Each item in the list includes the item's
        parent assembly's display name, the item's name, and the item's quantity. The items are numbered
        in the list.
        """
        return "\n" + "\n".join(
            f'{i+1}. {item.parent_assembly.get_master_assembly().get_assembly_data(key="display_name")}: {item.name} Qty: {item.get_value("parts_per")}'
            for i, item in enumerate(self.data.get(item_name, []))
        )

    def update_values(self, item_to_update: str, key: str, value: Any) -> None:
        """
        The function updates the values of a specific item in a data structure by setting a key-value
        pair.

        Args:
          item_to_update (Item): The item that needs to be updated. It is of type Item.
          key (str): The `key` parameter is a string that represents the key of the attribute that you
        want to update in the `item_to_update`.
          value (Any): The `value` parameter is the new value that you want to update for the specified
        key in the `item_to_update`.
        """
        for item in self.data[item_to_update]:
            item.set_value(key=key, value=value)

    def get_total_quantity(self, item_name: str) -> int:
        """
        The function calculates the total quantity of a specific item by summing up the values of the
        "parts_per" key in a list of items.

        Args:
          item_name (str): The `item_name` parameter is a string that represents the name of the item
        for which we want to calculate the total quantity.

        Returns:
          the total quantity of a specific item.
        """
        return sum(item.get_value(key="parts_per") for item in self.data.get(item_name, []))

    def filter_items(self, flow_tag: str) -> None:
        """
        The function filters items based on a specified flow tag.

        Args:
          flow_tag (str): The `flow_tag` parameter is a string that represents a specific flow tag.
        """
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
