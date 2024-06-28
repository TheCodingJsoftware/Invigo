from datetime import datetime

import ujson as json

from utils.components_inventory.components_inventory import ComponentsInventory
from utils.inventory.order import Order

def restore():
    with open(r"data\components_inventory - old orders.json", "r", encoding="utf-8") as file:
        old_components_inventory_data = json.load(file)
    print(f"loading start {datetime.now()}")
    components_inventory = ComponentsInventory()
    for component_name, component_data in old_components_inventory_data["components"].items():
        if component := components_inventory.get_component_by_name(component_name):
            if component_data["is_order_pending"]:
                new_order = Order({})
                new_order.quantity = component_data["order_pending_quantity"]
                new_order.expected_arrival_time = component_data["expected_arrival_time"]
                new_order.order_pending_date = component_data["order_pending_date"]
                component.add_order(new_order)
    print(f"loading done {datetime.now()}")
    print(f"saving start {datetime.now()}")
    components_inventory.save()
    print(f"saving done {datetime.now()}")

if __name__ == "__main__":
    restore()