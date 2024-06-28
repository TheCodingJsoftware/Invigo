from datetime import datetime

import ujson as json

from utils.sheet_settings.sheet_settings import SheetSettings
from utils.sheets_inventory.sheets_inventory import SheetsInventory
from utils.inventory.order import Order

def restore():
    sheet_settings = SheetSettings()
    with open(r"data\sheets_inventory - Copy.json", "r", encoding="utf-8") as file:
        old_sheets_inventory_data = json.load(file)
    print(f"loading start {datetime.now()}")
    sheets_inventory = SheetsInventory(sheet_settings)
    for sheet_name, sheet_data in old_sheets_inventory_data["sheets"].items():
        if component := sheets_inventory.get_sheet_by_name(sheet_name):
            if sheet_data["is_order_pending"]:
                new_order = Order({})
                new_order.quantity = sheet_data["order_pending_quantity"]
                new_order.expected_arrival_time = sheet_data["expected_arrival_time"]
                new_order.order_pending_date = sheet_data["order_pending_date"]
                component.add_order(new_order)
    print(f"loading done {datetime.now()}")
    print(f"saving start {datetime.now()}")
    sheets_inventory.save()
    print(f"saving done {datetime.now()}")

if __name__ == "__main__":
    restore()