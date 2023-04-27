import contextlib
import json
import os
import shutil
import sys
from datetime import datetime

from utils.json_file import JsonFile

inventory = JsonFile(file_name="data/inventory")
price_of_steel_inventory = JsonFile(file_name="data/inventory - Price of Steel")
parts_in_inventory = JsonFile(file_name="data/inventory - Parts in Inventory")


def update_inventory(file_path: str) -> None:
    """
    It takes a json file, parses it, and updates a google sheet with the data

    Args:
      file_path (str): str = "data/testt - Laser Batch Data.json"
    """
    parts_in_inventory.load_data()
    price_of_steel_inventory.load_data()
    with open(file_path) as json_file:
        new_laser_batch_data = json.load(json_file)
    total_sheet_count: int = get_total_sheet_count(batch_data=new_laser_batch_data)
    name_of_sheet: str = get_sheet_name(batch_data=new_laser_batch_data)
    subtract_sheet_count(
        sheet_name_to_update=name_of_sheet, sheet_count=total_sheet_count
    )
    print(f'total_sheet_count: {total_sheet_count}')
    print(f'name_of_sheet: {name_of_sheet}')
    recut_parts: list[str] = get_recut_parts(batch_data=new_laser_batch_data)
    print(f'recut_parts: {recut_parts}')
    add_recut_parts(batch_data=new_laser_batch_data, recut_parts=recut_parts)
    no_recut_parts: list[str] = get_no_recut_parts(batch_data=new_laser_batch_data)
    print(f'norecut_parts: {no_recut_parts}')
    add_parts(batch_data=new_laser_batch_data, parts_to_add=no_recut_parts)
    sort_inventory()


def add_parts(batch_data: dict, parts_to_add: list[str]):
    """
    It takes a dictionary of parts and quantities and adds them to the inventory

    Args:
      batch_data (dict): dict = {
      parts_to_add (list[str]): list[str] = list(batch_data.keys())
    """
    parts_updated: list[str] = list(parts_to_add)
    for category in list(parts_in_inventory.get_data().keys()):
        if category == "Recut":
            continue
        for part_to_add in parts_to_add:
            if part_exists(category=category, part_name_to_find=part_to_add):
                update_quantity(
                    part_name_to_update=part_to_add,
                    quantity=batch_data[part_to_add]["quantity"],
                )
                with contextlib.suppress(ValueError):
                    parts_updated.remove(part_to_add)
    for part_to_add_to_custom in parts_updated:
        add_part_to_inventory(
            category="Custom", part_to_add=part_to_add_to_custom, batch_data=batch_data
        )


def add_part_to_inventory(category, part_to_add, batch_data) -> None:
    """
    It adds a part to the inventory

    Args:
      category: The category of the part.
      part_to_add: The name of the part to add
      batch_data: This is the data that is being imported.
    """
    parts_in_inventory.add_item_in_object(category, part_to_add)
    parts_in_inventory.change_object_in_object_item(
        category,
        part_to_add,
        "current_quantity",
        batch_data[part_to_add]["quantity"],
    )
    parts_in_inventory.change_object_in_object_item(
        category,
        part_to_add,
        "machine_time",
        batch_data[part_to_add]["machine_time"],
    )
    parts_in_inventory.change_object_in_object_item(
        category,
        part_to_add,
        "gauge",
        batch_data[part_to_add]["gauge"],
    )
    parts_in_inventory.change_object_in_object_item(
        category,
        part_to_add,
        "material",
        batch_data[part_to_add]["material"],
    )
    parts_in_inventory.change_object_in_object_item(
        category,
        part_to_add,
        "weight",
        batch_data[part_to_add]["weight"],
    )
    parts_in_inventory.change_object_in_object_item(
        category,
        part_to_add,
        "price",
        calculate_price(batch_data, part_to_add),
    )
    parts_in_inventory.change_object_in_object_item(
        category,
        part_to_add,
        "unit_quantity",
        1,
    )
    parts_in_inventory.change_object_in_object_item(
        category,
        part_to_add,
        "modified_date",
        "Added at " + str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")),
    )
    parts_in_inventory.change_object_in_object_item(category, part_to_add, "group", None)


def update_quantity(part_name_to_update: str, quantity: int) -> None:
    """
    It takes a category, part name, and quantity as arguments, and then adds the quantity to the current
    quantity of the part in the category

    Args:
      category (str): str = The category of the part you want to update.
      part_name_to_update (str): str = "part_name"
      quantity (int): int
    """
    for category in list(parts_in_inventory.get_data().keys()):
        if category == "Recut":
            continue
        if part_exists(category=category, part_name_to_find=part_name_to_update):
            current_quantity: int = parts_in_inventory.get_data()[category][
                part_name_to_update
            ]["current_quantity"]
            parts_in_inventory.change_object_in_object_item(
                category,
                part_name_to_update,
                "current_quantity",
                current_quantity + quantity,
            )
            parts_in_inventory.change_object_in_object_item(
                category,
                part_name_to_update,
                "modified_date",
                f"{quantity} quantity added at "
                + str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")),
            )


def add_recut_parts(batch_data: dict, recut_parts: list[str]) -> None:
    """
    It adds a new item to the "Recut" category of the inventory, and then changes the current quantity,
    unit quantity, modified date, and group of the new item

    Args:
      batch_data (dict)
      recut_parts (list[str])
    """
    for recut_part in recut_parts:
        name = recut_part
        recut_count: int = 0
        if part_exists(category="Recut", part_name_to_find=recut_part):
            recut_count = (
                parts_in_inventory.get_data()["Recut"][recut_part]["recut_count"] + 1
            )
            parts_in_inventory.change_object_in_object_item(
                "Recut",
                name,
                "recut_count",
                recut_count,
            )
            name = f"{recut_part} - (Recut {recut_count} time(s))"
        parts_in_inventory.add_item_in_object("Recut", name)
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            name,
            "current_quantity",
            batch_data[recut_part]["quantity"],
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            name,
            "price",
            calculate_price(batch_data, recut_part),
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            name,
            "recut_count",
            recut_count,
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            name,
            "machine_time",
            batch_data[recut_part]["machine_time"],
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            name,
            "gauge",
            batch_data[recut_part]["gauge"],
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            name,
            "material",
            batch_data[recut_part]["material"],
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            name,
            "weight",
            batch_data[recut_part]["weight"],
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            name,
            "unit_quantity",
            1,
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            name,
            "modified_date",
            "Added at " + str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")),
        )
        parts_in_inventory.change_object_in_object_item("Recut", name, "group", None)


def calculate_price(batch_data: dict, part_name: str) -> float:
    """
    > Calculate the price of a part by multiplying the weight of the part by the price per pound of the
    material, and adding the cost of the laser time

    Args:
      batch_data (dict): dict = {
      part_name (str): str = "part_name"

    Returns:
      The price of the part.
    """
    round_number = lambda x, n: eval(
        f'"%.{int(n)}f" % '
        + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
    )
    weight: float = batch_data[part_name]["weight"]
    machine_time: float = batch_data[part_name]["machine_time"]
    material: str = batch_data[part_name]["material"]
    price_per_pound: float = price_of_steel_inventory.get_data()["Price Per Pound"][
        material
    ]["price"]
    cost_for_laser: float = 250 if material in {"304 SS", "409 SS", "Aluminium"} else 150
    return float(
        # Rounding the number to 2 decimal places.
        round_number(
            (machine_time * (cost_for_laser / 60)) + (weight * price_per_pound), 2
        )
    )


def part_exists(category: str, part_name_to_find: str) -> bool:
    """
    > Given a category and a part name, return True if the part exists in the inventory, False otherwise

    Args:
      category (str): str
      part_name_to_find (str): The name of the part you want to find.

    Returns:
      A boolean value.
    """
    return part_name_to_find in list(parts_in_inventory.get_data()[category].keys())


def get_recut_parts(batch_data) -> list[str]:
    """
    > This function takes a dictionary of part names and their attributes, and returns a list of part
    names that have the attribute "recut" set to True

    Args:
      batch_data: dict

    Returns:
      A list of strings.
    """
    recut_parts: list[str] = []
    for part_name in list(batch_data.keys()):
        with contextlib.suppress(KeyError):
            if batch_data[part_name]["recut"] is True:
                recut_parts.append(part_name)
    return recut_parts


def get_no_recut_parts(batch_data) -> list[str]:
    """
    > This function takes a dictionary of part names and their attributes, and returns a list of part
    names that have a `recut` attribute of `False`

    Args:
      batch_data: dict

    Returns:
      A list of part names that have a recut value of False.
    """
    no_recut_parts: list[str] = []
    for part_name in list(batch_data.keys()):
        with contextlib.suppress(KeyError):
            if batch_data[part_name]["recut"] is False:
                no_recut_parts.append(part_name)
    return no_recut_parts


def subtract_sheet_count(sheet_name_to_update: str, sheet_count: int) -> None:
    """
    It takes a sheet name and a sheet count, and subtracts the sheet count from the sheet name's current
    quantity

    Args:
      sheet_name_to_update (str): str = "Sheet Name"
      sheet_count (int): int = the number of sheets to subtract from the inventory
    """
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for sheet_name in list(category_data[category].keys()):
            if sheet_name_to_update == sheet_name:
                old_quantity: int = category_data[category][sheet_name][
                    "current_quantity"
                ]
                print(old_quantity)
                price_of_steel_inventory.change_object_in_object_item(
                    category, sheet_name, "current_quantity", old_quantity - sheet_count
                )


def get_sheet_name(batch_data: dict) -> str:
    """
    It takes a dictionary of dictionaries, and returns a string that is the concatenation of the values
    of the keys 'gauge', 'material', and 'sheet_dim' of the first dictionary in the dictionary

    Args:
      batch_data (dict): a dictionary of dictionaries. The keys are the batch numbers, and the values
    are dictionaries of the batch data.

    Returns:
      The sheet name is being returned.
    """
    return f"{batch_data[list(batch_data.keys())[0]]['gauge']} {batch_data[list(batch_data.keys())[0]]['material']} {batch_data[list(batch_data.keys())[0]]['sheet_dim']}"


def get_total_sheet_count(batch_data: dict) -> int:
    """
    > It opens the JSON file, loads the data, and then sums the quantity_multiplier

    Args:
      json_file_path: The path to the JSON file that contains the data for the parts.

    Returns:
      The total number of sheets in the json file.
    """
    sheet_count: int = sum(
        batch_data[part_name]["quantity_multiplier"]
        for part_name in list(batch_data.keys())
        if part_name[0] == "_"
    )
    return sheet_count


def sort_inventory() -> None:
    """
    This function sorts the parts in inventory by category and then by current quantity
    """
    for category in parts_in_inventory.get_data():
        parts_in_inventory.sort(
            category=category, item_name="current_quantity", ascending=True
        )


if __name__ == "__main__":
    update_inventory(
        r"F:\Code\Python-Projects\Inventory Manager\server\data\laser_parts_new_batch.json"
    )
