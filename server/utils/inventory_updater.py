import json
from datetime import datetime

from utils.custom_print import CustomPrint
from utils.sheets_inventory.sheet import Sheet
from utils.sheets_inventory.sheets_inventory import SheetsInventory

sheets_inventory = SheetsInventory(None)

connected_clients = set()


def get_cutoff_sheets() -> list[Sheet]:
    sheets_inventory.load_data()
    return sheets_inventory.get_sheets_by_category("Cutoff")


def add_sheet(
    thickness: str,
    material: str,
    sheet_dim: str,
    sheet_count: float,
    _connected_clients,
) -> None:
    sheet_name: str = f"{thickness} {material} {sheet_dim}"
    sheets_inventory.load_data()
    length = float(sheet_dim.split("x")[0].strip())
    width = float(sheet_dim.split("x")[1].strip())
    new_sheet = Sheet(sheet_name, {"quantity": sheet_count, "thickness": thickness, "material": material, "length": length, "width": width, "categories": ["Cutoff"]}, sheets_inventory)
    new_sheet.latest_change_quantity = f"Item added at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')} via server"
    sheets_inventory.add_sheet(new_sheet)
    sheets_inventory.save()
    CustomPrint.print(f'INFO - Added "{sheet_name}" to Cutoff', connected_clients=_connected_clients)
    signal_clients_for_changes(_connected_clients, changed_files=["sheets_inventory.json"])


def remove_cutoff_sheet(sheet_name: str, _connected_clients):
    sheets_inventory.load_data()
    if sheet_to_delete := sheets_inventory.get_sheet_by_name(sheet_name):
        sheets_inventory.remove_sheet(sheet_to_delete)
    sheets_inventory.save()
    CustomPrint.print(
        f'INFO - Removed "{sheet_name}" from Cutoff',
        connected_clients=_connected_clients,
    )
    signal_clients_for_changes(_connected_clients, changed_files=["sheets_inventory.json"])


def get_sheet_pending_data(sheet_name: str) -> dict[str, str]:
    sheets_inventory.load_data()
    if sheet := sheets_inventory.get_sheet_by_name(sheet_name):
        return {
            "is_order_pending": sheet.is_order_pending,
            "expected_arrival_time": sheet.expected_arrival_time,
            "order_pending_date": sheet.order_pending_date,
            "order_pending_quantity": sheet.order_pending_quantity,
            "new_quantity": sheet.order_pending_quantity + sheet.quantity,
        }


def get_sheet_quantity(sheet_name: str) -> float:
    sheets_inventory.load_data()
    if sheet := sheets_inventory.get_sheet_by_name(sheet_name):
        return sheet.quantity


def set_sheet_quantity(sheet_name: str, new_quantity: float, clients) -> None:
    sheets_inventory.load_data()
    if sheet := sheets_inventory.get_sheet_by_name(sheet_name):
        sheet.quantity = new_quantity
        sheet.latest_change_quantity = f'Set to {new_quantity} with QR code at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
        if new_quantity >= sheet.red_quantity_limit:
            sheet.is_order_pending = False
            sheet.has_sent_warning = False
    sheets_inventory.save()
    signal_clients_for_changes(clients, changed_files=["sheets_inventory.json"])


def sheet_exists(sheet_name: str) -> bool:
    sheets_inventory.load_data()
    return bool(_ := sheets_inventory.get_sheet_by_name(sheet_name))


def signal_clients_for_changes(client_to_ignore, changed_files: list[str]) -> None:
    CustomPrint.print(
        f"INFO - Signaling {len(connected_clients)} clients",
        connected_clients=connected_clients,
    )
    for client in connected_clients:
        if client.request.remote_ip == client_to_ignore:
            CustomPrint.print(
                f"INFO - Ignoring {client.request.remote_ip} since it sent {changed_files}",
                connected_clients=connected_clients,
            )
            continue
        if client.ws_connection and client.ws_connection.stream.socket:
            message = json.dumps({"action": "download", "files": changed_files})
            client.write_message(message)
            CustomPrint.print(
                f"INFO - Signaling {client.request.remote_ip} to download {changed_files}",
                connected_clients=connected_clients,
            )
