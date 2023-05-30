
import contextlib
from datetime import datetime

from utils.colors import Colors
from utils.custom_print import CustomPrint
from utils.inventory_updater import update_inventory
from utils.json_file import JsonFile
from utils.send_email import send

sheets_in_inventory = JsonFile(file_name="data/inventory - Price of Steel")
connected_clients = set()

def generate_sheet_report(clients) -> None:
    """
    This function generates a report of sheets low in quantity and sends it as an email.
    """
    global connected_clients
    connected_clients = clients
    sheets_low_in_quantity: int = 0
    message_to_send: str = '<div class="tg-wrap"><table style="font-family: sans-serif; table-layout: fixed; width: 633px; border-collapse: collapse; text-align: center; vertical-align: middle; background-color: #222; color: white;"><colgroup><col style="width: 187px"><col style="width: 146px"><col style="width: 146px"><col style="width: 340px"></colgroup><thead><tr><th>Sheet Name</th><th>Order Status</th><th>Current Quantity</th><th>Description</th></tr></thead><tbody>'
    data = sheets_in_inventory.get_data()

    for material in list(data.keys()):
        if material in ["Price Per Pound", "Cutoff"]:
            continue
        for sheet_name in list(data[material].keys()):
            try:
                red_limit: int = data[material][sheet_name]["red_limit"]
                yellow_limit: int = data[material][sheet_name]["yellow_limit"]
            except Exception:
                # Default values
                red_limit: int = 4
                yellow_limit: int = 10
            current_quantity: int = data[material][sheet_name]["current_quantity"]
            if current_quantity <= red_limit or current_quantity <= yellow_limit:
                sheets_low_in_quantity += 1
                notes: str = "Nothing here"
                with contextlib.suppress(Exception):
                    notes: str = data[material][sheet_name]["notes"]
                is_order_pending: bool = False
                with contextlib.suppress(KeyError):
                    is_order_pending = data[material][sheet_name]["is_order_pending"]
                stylesheet = (
                    "border: 1px solid #222; color: lightpink; background-color: #3F1E25;"
                    if current_quantity <= red_limit
                    else "border: 1px solid #222; color: #ffffe0; background-color: #413C28;"
                )
                order_pending: str = "No order pending"
                if is_order_pending:
                    order_pending = "Order is pending"
                    stylesheet = "border: 1px solid #222; color: #cef4d9; background-color: #24793c;"
                else:
                    order_pending = "No order is pending"
                message_to_send += f'<tr style="border: 1px solid; {stylesheet}"><td>{sheet_name}</td><td style="{"font-weight: bold;" if is_order_pending else ""}">{order_pending}</td><td>{current_quantity}</td><td>{notes}</td></tr>'
    message_to_send += '</tbody></table></div><br><p style="font-family: sans-serif;">Don\'t forget to update the pending status button in the Sheet Inventory tab when you sent a purchase order.<br>Have a fabulous week!</p>'
    CustomPrint.print(f'INFO - Sheet report generated', connected_clients=connected_clients)
    if sheets_low_in_quantity == 0:
        send(
            "Nothing low in quantity, Whew! Have a marvelous week.",
            email_addresses=["jaredgrozz@gmail.com"], 
            connected_clients=connected_clients,
        )
    else:
        send(message_to_send, 
             email_addresses=["jaredgrozz@gmail.com"], 
             connected_clients=connected_clients
        )