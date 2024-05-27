import contextlib
from datetime import datetime

from utils.colors import Colors
from utils.custom_print import CustomPrint
from utils.send_email import send
from utils.sheets_inventory.sheets_inventory import Sheet, SheetsInventory

connected_clients = set()


def generate_sheet_report(clients) -> None:
    global connected_clients
    connected_clients = clients
    sheets_in_inventory = SheetsInventory(None)
    if datetime.now().strftime("%A") != "Monday":
        return
    sheets_low_in_quantity: int = 0
    message_to_send: str = '<div class="tg-wrap"><table style="font-family: sans-serif; table-layout: fixed; width: 633px; border-collapse: collapse; text-align: center; vertical-align: middle; background-color: #222; color: #EAE9FC;"><colgroup><col style="width: 200px"><col style="width: 270px"><col style="width: 146px"><col style="width: 340px"></colgroup><thead><tr><th>Sheet Name</th><th>Order Status</th><th>Current Quantity</th><th>Description</th></tr></thead><tbody>'

    for sheet in sheets_in_inventory.sheets:
        sheet_categories = [category.name for category in sheet.categories]
        if "Cutoff" in sheet_categories:
            continue
        if sheet.quantity <= sheet.red_quantity_limit or sheet.quantity <= sheet.yellow_quantity_limit:
            sheets_low_in_quantity += 1
            notes = sheet.notes
            if not notes:
                notes: str = "No notes provided"
            stylesheet = "border-bottom: 1px solid #222; color: #EAE9FC; background-color: #3F1E25;" if sheet.quantity <= sheet.red_quantity_limit else "border-bottom: 1px solid #222; color: #EAE9FC; background-color: #413C28;"
            order_pending: str = "No order is pending"
            if sheet.is_order_pending:
                order_pending = f"Order is pending since {sheet.order_pending_date} for {sheet.order_pending_quantity} sheets and expected to arrive at {sheet.expected_arrival_time}"
                stylesheet = "border-bottom: 1px solid #222; color: #EAE9FC; background-color: #24793c;"
            else:
                order_pending = "No order is pending"
            message_to_send += f'<tr style="border-bottom: 1px solid; {stylesheet}"><td>{sheet.get_name()}</td><td style="{"font-weight: bold;" if sheet.is_order_pending else ""}">{order_pending}</td><td>{sheet.quantity}</td><td>{notes}</td></tr>'
    message_to_send += '</tbody></table></div><br><p style="font-family: sans-serif;">Please remember to update the <b style="color: #3bba6d">"Order Pending"</b> status in the <b>"Sheet in Inventory"</b> tab after issuing a purchase order.<br>Wishing you a productive week ahead!</p>'
    CustomPrint.print("INFO - Sheet report generated", connected_clients=connected_clients)
    if sheets_low_in_quantity == 0:
        send(
            "Invigo - Weekly Report: Sheets in Inventory",
            "Nothing low in quantity, Wo-hoo! Have a marvelous week.",
            ["jaredgrozz@gmail.com", "lynden@pineymfg.com"],
            connected_clients,
        )
    else:
        send(
            "Invigo - Weekly Report: Sheets in Inventory",
            message_to_send,
            ["jaredgrozz@gmail.com", "lynden@pineymfg.com"],
            connected_clients,
        )
