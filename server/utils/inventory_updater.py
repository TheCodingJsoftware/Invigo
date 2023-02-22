import contextlib
import json
import os
import shutil
import sys
from datetime import datetime

from utils.json_file import JsonFile

inventory = JsonFile(file_name="data/testt")
price_of_steel_inventory = JsonFile(file_name="data/testt - Price of Steel")
parts_in_inventory = JsonFile(file_name="data/testt - Parts in Inventory")


def update_inventory(file_path: str) -> None:
    with open(file_path) as json_file:
        new_laser_batch_data = json.load(json_file)
    total_sheet_count: int = get_total_sheet_count(batch_data=new_laser_batch_data)
    name_of_sheet: str = get_sheet_name(batch_data=new_laser_batch_data)
    subtract_sheet_count(
        sheet_name_to_update=name_of_sheet, sheet_count=total_sheet_count
    )
    recut_parts: list[str] = get_recut_parts(batch_data=new_laser_batch_data)
    print(recut_parts)
    add_recut_parts(batch_data=new_laser_batch_data, recut_parts=recut_parts)
    no_recut_parts: list[str] = get_no_recut_parts(batch_data=new_laser_batch_data)


def add_recut_parts(batch_data: dict, recut_parts: list[str]) -> None:
    """
    It adds a new item to the "Recut" category of the inventory, and then changes the current quantity,
    unit quantity, modified date, and group of the new item

    Args:
      batch_data (dict)
      recut_parts (list[str])
    """
    for recut_part in recut_parts:
        if part_exists(category="Recut", part_name_to_find=recut_part):
            recut_part = f"{recut_part} - (Copy)"
        parts_in_inventory.add_item_in_object("Recut", recut_part)
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            recut_part,
            "current_quantity",
            batch_data[recut_part]["quantity"],
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            recut_part,
            "unit_quantity",
            1,
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut",
            recut_part,
            "modified_date",
            "Added @ " + str(datetime.now().strftime("%B %d %A %Y %I-%M-%S %p")),
        )
        parts_in_inventory.change_object_in_object_item(
            "Recut", recut_part, "group", None
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
            if batch_data[part_name]["recut"] == True:
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
            if batch_data[part_name]["recut"] == False:
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
    print(sheet_name_to_update, sheet_count)
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for sheet_name in list(category_data[category].keys()):
            if sheet_name_to_update == sheet_name:
                old_quantity: int = category_data[category][sheet_name][
                    "current_quantity"
                ]
                price_of_steel_inventory.change_object_in_object_item(
                    category, sheet_name, "quantity", old_quantity - sheet_count
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


if __name__ == "__main__":
    update_inventory(
        r"F:\Code\Python-Projects\Inventory Manager\server\data\laser_parts_new_batch.json"
    )
