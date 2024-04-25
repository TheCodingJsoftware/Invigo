import contextlib
import json
import os
from datetime import datetime

from utils.colors import Colors
from utils.custom_print import CustomPrint
from utils.json_file import JsonFile
from utils.send_email import send
from utils.sheet_report import generate_single_sheet_report

# This is because of git, and having a test server.
with open("utils/inventory_file_to_use.txt", "r") as f:
    inventory_file_name: str = f.read()

inventory = JsonFile(file_name=f"data/{inventory_file_name}")
price_of_steel_inventory = JsonFile(file_name=f"data/{inventory_file_name} - Price of Steel")
parts_in_inventory = JsonFile(file_name=f"data/{inventory_file_name} - Parts in Inventory")

connected_clients = set()


def update_inventory(file_path: str, clients) -> None:
    global connected_clients
    connected_clients = clients
    CustomPrint.print("INFO - Updating inventory", connected_clients=connected_clients)
    parts_in_inventory.load_data()
    price_of_steel_inventory.load_data()
    with open(file_path) as json_file:
        quote_nest_information = json.load(json_file)

    # Need to combine duplicate items so inventory can be updated quicker and remove group names
    if "workorder" in file_path:
        new_laser_batch_data = {}
        for nest_name in list(quote_nest_information.keys()):
            if nest_name == "Components":
                continue
            if nest_name[0] == "_":
                new_laser_batch_data[nest_name] = quote_nest_information[nest_name]
            else:
                for item in quote_nest_information[nest_name]:
                    try:
                        new_laser_batch_data[item]["quantity"] += quote_nest_information[nest_name][item]["quantity"]
                    except KeyError:
                        new_laser_batch_data[item] = quote_nest_information[nest_name][item]
    else:
        # It is already in the combined format because its just an item
        new_laser_batch_data = quote_nest_information

    sheet_count_and_type: dict = get_sheet_information(batch_data=new_laser_batch_data)
    remove_sheet_quantities(sheets_information=sheet_count_and_type)
    recut_parts: list[str] = get_recut_parts(batch_data=new_laser_batch_data)
    add_recut_parts(batch_data=new_laser_batch_data, recut_parts=recut_parts)
    no_recut_parts: list[str] = get_no_recut_parts(batch_data=new_laser_batch_data)
    add_parts(batch_data=new_laser_batch_data, parts_to_add=no_recut_parts)
    sort_inventory()
    if "workorder" in file_path:
        os.rename(
            file_path,
            f'{file_path.replace(".json", "").replace("parts_batch_to_upload_workorder", "").replace("data", "parts batch to upload history")}Workrder {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json',
        )
        CustomPrint.print(
            "INFO - Updated Inventory & archived batch",
            connected_clients=connected_clients,
        )
    elif "part" in file_path:
        os.rename(
            file_path,
            f'{file_path.replace(".json", "").replace("parts_batch_to_upload_part", "").replace("", "").replace("data", "parts batch to upload history")}Part {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json',
        )
        CustomPrint.print(
            "INFO - Added part to inventory",
            connected_clients=connected_clients,
        )
    signal_clients_for_changes(clients)


def add_parts(batch_data: dict, parts_to_add: list[str]):
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
    parts_in_inventory.add_item_in_object(category, part_to_add)
    batch_data[part_to_add]["modified_date"] = f'Added at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
    batch_data[part_to_add]["current_quantity"] = batch_data[part_to_add]["quantity"]
    batch_data[part_to_add]["unit_quantity"] = 1
    batch_data[part_to_add]["price"] = calculate_price(batch_data, part_to_add)
    parts_in_inventory.change_object_item(category, part_to_add, batch_data[part_to_add])


def update_quantity(batch_data: dict, part_name_to_update: str, quantity: int) -> None:
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
    weight: float = batch_data[part_name]["weight"]
    machine_time: float = batch_data[part_name]["machine_time"]
    material: str = batch_data[part_name]["material"]
    price_per_pound: float = price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"]
    cost_for_laser: float = 250 if material in {"304 SS", "409 SS", "Aluminium"} else 150
    return float((machine_time * (cost_for_laser / 60)) + (weight * price_per_pound))


def part_exists(category: str, part_name_to_find: str) -> bool:
    return part_name_to_find in list(parts_in_inventory.get_data()[category].keys())


def get_recut_parts(batch_data) -> list[str]:
    recut_parts: list[str] = []
    for part_name in list(batch_data.keys()):
        with contextlib.suppress(KeyError):
            if batch_data[part_name]["recut"] == True:
                recut_parts.append(part_name)
    return recut_parts


def get_no_recut_parts(batch_data) -> list[str]:
    no_recut_parts: list[str] = []
    for part_name in list(batch_data.keys()):
        with contextlib.suppress(KeyError):
            if batch_data[part_name]["recut"] == False:
                no_recut_parts.append(part_name)
    return no_recut_parts


def remove_sheet_quantities(sheets_information) -> None:
    for sheet in sheets_information:
        subtract_sheet_count(sheet_name_to_update=sheet, sheet_count=sheets_information[sheet])


def subtract_sheet_count(sheet_name_to_update: str, sheet_count: int) -> None:
    sheet_name_to_update = sheet_name_to_update.replace(" x ", "x")
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for sheet_name in list(category_data[category].keys()):
            if sheet_name_to_update == sheet_name:
                old_quantity: int = category_data[category][sheet_name]["current_quantity"]
                try:
                    notes: int = category_data[category][sheet_name]["notes"]
                except KeyError:
                    notes = "No notes to show..."
                try:
                    red_quantity_limit: int = category_data[category][sheet_name]["red_limit"]
                except KeyError:
                    red_quantity_limit: int = 4
                try:
                    is_order_pending: bool = category_data[category][sheet_name]["is_order_pending"]
                except KeyError:
                    is_order_pending: bool = False
                try:
                    has_sent_warning: bool = category_data[category][sheet_name]["has_sent_warning"]
                except KeyError:
                    has_sent_warning: bool = False
                price_of_steel_inventory.change_object_in_object_item(category, sheet_name, "current_quantity", old_quantity - sheet_count)
                price_of_steel_inventory.change_object_in_object_item(
                    category,
                    sheet_name,
                    "latest_change_current_quantity",
                    f'Removed {sheet_count} at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}',
                )
                CustomPrint.print(f"INFO - Subtracted {sheet_count} quantities from {sheet_name_to_update}", connected_clients=connected_clients)
                if (old_quantity - sheet_count) <= red_quantity_limit:
                    CustomPrint.print(f"INFO - {sheet_name_to_update} went into RED", connected_clients=connected_clients)
                    if category != "Cutoff" and is_order_pending == False and has_sent_warning == False:
                        generate_single_sheet_report(
                            sheet_name=sheet_name_to_update,
                            red_limit=red_quantity_limit,
                            old_quantity=old_quantity,
                            new_quantity=old_quantity-sheet_count,
                            notes=notes,
                            clients=connected_clients
                        )
                        price_of_steel_inventory.change_object_in_object_item(category, sheet_name_to_update, "has_sent_warning", True)

                if category == "Cutoff" and old_quantity - sheet_count == 0:
                    price_of_steel_inventory.remove_object_item(category, sheet_name)
                    CustomPrint.print(f"INFO - Removed {sheet_name} from Cutoff", connected_clients=connected_clients)


def get_cutoff_sheets() -> dict:
    price_of_steel_inventory.load_data()
    return price_of_steel_inventory.get_data()["Cutoff"]


def add_sheet(thickness: str, material: str, sheet_dim: str, sheet_count: float, _connected_clients) -> None:
    sheet_name: str = f'{thickness} {material} {sheet_dim}'
    category_name: str = "Cutoff"
    price_of_steel_inventory.load_data()
    price_of_steel_inventory.add_item_in_object(category_name, sheet_name)
    price_of_steel_inventory.change_object_in_object_item(category_name, sheet_name, "current_quantity", sheet_count)
    price_of_steel_inventory.change_object_in_object_item(category_name, sheet_name, "sheet_dimension", sheet_dim)
    price_of_steel_inventory.change_object_in_object_item(category_name, sheet_name, "thickness", thickness)
    price_of_steel_inventory.change_object_in_object_item(category_name, sheet_name, "material", material)
    price_of_steel_inventory.change_object_in_object_item(category_name, sheet_name, "group", material)
    price_of_steel_inventory.change_object_in_object_item(
        category_name,
        sheet_name,
        "latest_change_current_quantity",
        f"Item added at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')} via server",
    )
    CustomPrint.print(f'INFO - Adding "{sheet_name}" to Cutoff', connected_clients=_connected_clients)
    signal_clients_for_changes(connected_clients=_connected_clients)


def remove_cutoff_sheet(sheet_name: str, _connected_clients):
    price_of_steel_inventory.load_data()
    if sheet_exists(sheet_name):
        price_of_steel_inventory.remove_object_item("Cutoff", sheet_name)
    CustomPrint.print(f'INFO - Removed "{sheet_name}" from Cutoff', connected_clients=_connected_clients)
    signal_clients_for_changes(connected_clients=_connected_clients)


def get_sheet_information(batch_data: dict) -> dict:
    sheet_information = {}
    for item in list(batch_data.keys()):
        if item == "Components":
            continue
        if item[0] == "_":
            sheet_name = f"{batch_data[item]['gauge']} {batch_data[item]['material']} {batch_data[item]['sheet_dim']}"
            try:
                sheet_information[sheet_name] += batch_data[item]["quantity_multiplier"]
            except KeyError:
                sheet_information[sheet_name] = batch_data[item]["quantity_multiplier"]
    return sheet_information

def get_sheet_pending_data(sheet_name: str) -> dict[str, str]:
    price_of_steel_inventory.load_data()
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for _sheet_name in list(category_data[category].keys()):
            if sheet_name == _sheet_name:
                try:
                    pending_data = {
                        "is_order_pending": category_data[category][sheet_name]["is_order_pending"],
                        "expected_arrival_time": category_data[category][sheet_name]["expected_arrival_time"],
                        "order_pending_date": category_data[category][sheet_name]["order_pending_date"],
                        "order_pending_quantity": category_data[category][sheet_name]["order_pending_quantity"],
                        "new_quantity": category_data[category][sheet_name]["order_pending_quantity"] + category_data[category][sheet_name]["current_quantity"]
                    }
                except KeyError:
                    pending_data = {
                        "is_order_pending": False,
                        "expected_arrival_time": None,
                        "order_pending_date": None,
                        "order_pending_quantity": None,
                        "new_quantity": 0
                    }
                return pending_data


def get_sheet_quantity(sheet_name: str) -> float:
    price_of_steel_inventory.load_data()
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for _sheet_name in list(category_data[category].keys()):
            if sheet_name == _sheet_name:
                return category_data[category][sheet_name]["current_quantity"]


def set_sheet_quantity(sheet_name: str, new_quantity: float, clients) -> None:
    price_of_steel_inventory.load_data()
    category_data = price_of_steel_inventory.get_data()
    for category in list(category_data.keys()):
        if category == "Price Per Pound":
            continue
        for _sheet_name in list(category_data[category].keys()):
            if sheet_name == _sheet_name:
                try:
                    red_quantity_limit: int = category_data[category][sheet_name]["red_limit"]
                except KeyError:
                    red_quantity_limit: int = 4
                if red_quantity_limit >= new_quantity:
                    price_of_steel_inventory.change_object_in_object_item(category, sheet_name, "has_sent_warning", False)
                price_of_steel_inventory.change_object_in_object_item(
                    category,
                    sheet_name,
                    "current_quantity",
                    new_quantity,
                )
                price_of_steel_inventory.change_object_in_object_item(
                    category,
                    sheet_name,
                    "is_order_pending",
                    False,
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
