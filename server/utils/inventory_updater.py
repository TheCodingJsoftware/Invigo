import contextlib
import json
import os
from datetime import datetime

from utils.colors import Colors
from utils.custom_print import CustomPrint
from utils.json_file import JsonFile

with open("utils/inventory_file_to_use.txt", "r") as f:
    inventory_file_name: str = f.read()

inventory = JsonFile(file_name=f"data/{inventory_file_name}")
price_of_steel_inventory = JsonFile(file_name=f"data/{inventory_file_name} - Price of Steel")
parts_in_inventory = JsonFile(file_name=f"data/{inventory_file_name} - Parts in Inventory")

connected_clients = set()


def update_inventory(file_path: str, clients) -> None:
    """
    It takes a json file, parses it, and updates a google sheet with the data

    Args:
      file_path (str): str = "data/testt - Laser Batch Data.json"
    """
    global connected_clients
    connected_clients = clients
    CustomPrint.print("INFO - Updating inventory", connected_clients=connected_clients)
    parts_in_inventory.load_data()
    price_of_steel_inventory.load_data()
    with open(file_path) as json_file:
        new_laser_batch_data = json.load(json_file)
    sheet_count_and_type: dict = get_sheet_information(batch_data=new_laser_batch_data)
    remove_sheet_quantities(sheets_information=sheet_count_and_type)
    recut_parts: list[str] = get_recut_parts(batch_data=new_laser_batch_data)
    add_recut_parts(batch_data=new_laser_batch_data, recut_parts=recut_parts)
    no_recut_parts: list[str] = get_no_recut_parts(batch_data=new_laser_batch_data)
    add_parts(batch_data=new_laser_batch_data, parts_to_add=no_recut_parts)
    sort_inventory()
    try:
        os.rename(
            file_path,
            f'{file_path.replace(".json", "").replace("parts_batch_to_upload", "").replace("data", "parts batch to upload history")}{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json',
        )
    except FileExistsError:
        CustomPrint.print(
            "ERROR - Can't replace parts_batch_to_updoad.json file with an existing archive.",
            connected_clients=connected_clients,
        )
    CustomPrint.print(
        "INFO - Updated Inventory & archived batch",
        connected_clients=connected_clients,
    )
    signal_clients_for_changes(clients)


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
                    batch_data=batch_data,
                    part_name_to_update=part_to_add,
                    quantity=batch_data[part_to_add]["quantity"],
                )
                CustomPrint.print(
                    f"INFO - Added {batch_data[part_to_add]['quantity']} quantites to {part_to_add} from {category}",
                    connected_clients=connected_clients,
                )
                with contextlib.suppress(ValueError):
                    parts_updated.remove(part_to_add)
    for part_to_add_to_custom in parts_updated:
        add_part_to_inventory(category="Custom", part_to_add=part_to_add_to_custom, batch_data=batch_data)
        CustomPrint.print(f"INFO - Added {part_to_add_to_custom} to Custom", connected_clients=connected_clients)


def add_part_to_inventory(category, part_to_add, batch_data) -> None:
    """
    It adds a part to the inventory

    Args:
      category: The category of the part.
      part_to_add: The name of the part to add
      batch_data: This is the data that is being imported.
    """
    parts_in_inventory.add_item_in_object(category, part_to_add)
    batch_data[part_to_add]["modified_date"] = f'Added at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
    batch_data[part_to_add]["current_quantity"] = batch_data[part_to_add]["quantity"]
    batch_data[part_to_add]["unit_quantity"] = 1
    batch_data[part_to_add]["price"] = calculate_price(batch_data, part_to_add)
    parts_in_inventory.change_object_item(category, part_to_add, batch_data[part_to_add])


def update_quantity(batch_data: dict, part_name_to_update: str, quantity: int) -> None:
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
            current_quantity: int = parts_in_inventory.get_data()[category][part_name_to_update]["current_quantity"]
            batch_data[part_name_to_update]["current_quantity"] = current_quantity + quantity
            batch_data[part_name_to_update]["unit_quantity"] = parts_in_inventory.get_data()[category][part_name_to_update]["unit_quantity"]
            batch_data[part_name_to_update]["modified_date"] = f'{quantity} quantity added at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
            batch_data[part_name_to_update]["price"] = calculate_price(batch_data, part_name_to_update)
            parts_in_inventory.change_object_item(category, part_name_to_update, batch_data[part_name_to_update])


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
            recut_count = parts_in_inventory.get_data()["Recut"][recut_part]["recut_count"] + 1
            parts_in_inventory.change_object_in_object_item(
                "Recut",
                name,
                "recut_count",
                recut_count,
            )
            batch_data[recut_part]["recut_count"] = recut_count
            name = f"{recut_part} - (Recut {recut_count} time(s))"
        else:
            batch_data[recut_part]["recut_count"] = recut_count
        parts_in_inventory.add_item_in_object("Recut", name)
        batch_data[recut_part]["price"] = calculate_price(batch_data, recut_part)
        batch_data[recut_part]["modified_date"] = f'Added at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
        batch_data[recut_part]["current_quantity"] = batch_data[recut_part]["quantity"]
        batch_data[recut_part]["unit_quantity"] = 1
        parts_in_inventory.change_object_item("Recut", name, batch_data[recut_part])
        CustomPrint.print(f"INFO - Added {recut_part} to Recut", connected_clients=connected_clients)


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
    weight: float = batch_data[part_name]["weight"]
    machine_time: float = batch_data[part_name]["machine_time"]
    material: str = batch_data[part_name]["material"]
    price_per_pound: float = price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"]
    cost_for_laser: float = 250 if material in {"304 SS", "409 SS", "Aluminium"} else 150
    return float((machine_time * (cost_for_laser / 60)) + (weight * price_per_pound))


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


def remove_sheet_quantities(sheets_information) -> None:
    """
    This function removes sheet quantities from a dictionary of sheets information by calling another
    function to subtract the sheet count.

    Args:
      sheets_information: A dictionary containing information about the sheets, where the keys are the
    names of the sheets and the values are the quantities of each sheet.
    """
    for sheet in sheets_information:
        subtract_sheet_count(sheet_name_to_update=sheet, sheet_count=sheets_information[sheet])


def subtract_sheet_count(sheet_name_to_update: str, sheet_count: int) -> None:
    """
    It takes a sheet name and a sheet count, and subtracts the sheet count from the sheet name's current
    quantity

    Args:
      sheet_name_to_update (str): str = "Sheet Name"
      sheet_count (int): int = the number of sheets to subtract from the inventory
    """
    sheet_name_to_update = sheet_name_to_update.replace(" x ", "x")
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for sheet_name in list(category_data[category].keys()):
            if sheet_name_to_update == sheet_name:
                old_quantity: int = category_data[category][sheet_name]["current_quantity"]
                price_of_steel_inventory.change_object_in_object_item(category, sheet_name, "current_quantity", old_quantity - sheet_count)
                price_of_steel_inventory.change_object_in_object_item(
                    category,
                    sheet_name,
                    "latest_change_current_quantity",
                    f'Removed {sheet_count} at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}',
                )
                CustomPrint.print(f"INFO - Subtracted {sheet_count} quantities from {sheet_name_to_update}", connected_clients=connected_clients)


def get_sheet_information(batch_data: dict) -> dict:
    """
    The function takes in a dictionary of batch data and returns a dictionary of sheet information based
    on certain keys in the batch data.

    Args:
      batch_data (dict): A dictionary containing information about a batch of items, where each key
    represents an item and its value is a dictionary containing information about that item. The keys in
    the item dictionary include 'gauge', 'material', 'sheet_dim', and 'quantity_multiplier'.

    Returns:
      The function `get_sheet_information` returns a dictionary containing information about the sheets
    used in a batch of production. The keys of the dictionary are strings representing the sheet names,
    and the values are integers representing the total quantity of each sheet used in the batch.
    """
    sheet_information = {}
    for item in list(batch_data.keys()):
        if item[0] == "_":
            sheet_name = f"{batch_data[item]['gauge']} {batch_data[item]['material']} {batch_data[item]['sheet_dim']}"
            try:
                sheet_information[sheet_name] += batch_data[item]["quantity_multiplier"]
            except KeyError:
                sheet_information[sheet_name] = batch_data[item]["quantity_multiplier"]
    return sheet_information


def get_sheet_quantity(sheet_name: str) -> float:
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for _sheet_name in list(category_data[category].keys()):
            if sheet_name == _sheet_name:
                return category_data[category][sheet_name]["current_quantity"]


def set_sheet_quantity(sheet_name: str, new_quantity: float, clients) -> None:
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for _sheet_name in list(category_data[category].keys()):
            if sheet_name == _sheet_name:
                price_of_steel_inventory.change_object_in_object_item(
                    category,
                    sheet_name,
                    "current_quantity",
                    new_quantity,
                )
                price_of_steel_inventory.change_object_in_object_item(
                    category,
                    sheet_name,
                    "latest_change_current_quantity",
                    f'Set to {new_quantity} with QR code at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}',
                )
    signal_clients_for_changes(clients)

def sheet_exists(sheet_name: str) -> bool:
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for _sheet_name in list(category_data[category].keys()):
            if sheet_name == _sheet_name:
                return True
    return False

def sort_inventory() -> None:
    """
    This function sorts the parts in inventory by category and then by current quantity
    """
    for category in parts_in_inventory.get_data():
        parts_in_inventory.sort(category=category, item_name="current_quantity", ascending=True)
    CustomPrint.print("INFO - Sorted inventory", connected_clients=connected_clients)


def signal_clients_for_changes(connected_clients) -> None:
    CustomPrint.print(f"INFO - Signaling {len(connected_clients)} clients", connected_clients=connected_clients)
    for client in connected_clients:
        if client.ws_connection and client.ws_connection.stream.socket:
            client.write_message("download changes")
            CustomPrint.print(f"INFO - Signaling {client.request.remote_ip} to download changes", connected_clients=connected_clients)


if __name__ == "__main__":
    update_inventory(r"C:\Users\jared\Documents\Code\Inventory-Manager\server\utils\2023-04-28-10-16-09.json")
