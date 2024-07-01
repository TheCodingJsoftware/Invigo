from datetime import datetime

import ujson as json

from utils.components_inventory.components_inventory import ComponentsInventory


def restore():
    with open(r"data\inventory.json", "r", encoding="utf-8") as file:
        old_components_inventory_data = json.load(file)
    print(f"loading start {datetime.now()}")
    components_inventory = ComponentsInventory()
    for category, category_data in old_components_inventory_data.items():
        for item, item_data in category_data.items():
            category_object = components_inventory.get_category(category)
            if component := components_inventory.get_component_by_part_name(item):
                component.set_category_quantity(category_object, item_data["unit_quantity"])
                if not component.latest_change_quantity or component.latest_change_quantity == "Nothing recorded":
                    component.latest_change_quantity = item_data["latest_change_current_quantity"]
    print(f"loading done {datetime.now()}")
    print(f"saving start {datetime.now()}")
    components_inventory.save()
    print(f"saving done {datetime.now()}")


if __name__ == "__main__":
    restore()
