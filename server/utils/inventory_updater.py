import json
import os
import shutil
import sys

from utils.json_file import JsonFile

inventory = JsonFile(file_name="data/testt")
price_of_steel_inventory = JsonFile(file_name="data/testt - Price of Steel")
laser_parts_list_inventory = JsonFile(file_name="data/testt - Laser Parts List")


def update_inventory(file_path: str) -> None:
    with open(file_path) as json_file:
        new_laser_batch_data = json.load(json_file)
    total_sheet_count: int = get_total_sheet_count(batch_data=new_laser_batch_data)
    name_of_sheet: str = get_sheet_name(batch_data=new_laser_batch_data)
    print(total_sheet_count)
    print(name_of_sheet)


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
