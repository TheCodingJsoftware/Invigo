from datetime import datetime

import ujson as json

from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory


def restore():
    with open(r"data\inventory - Parts in Inventory.json", "r", encoding="utf-8") as file:
        old_components_inventory_data = json.load(file)
    print(f"loading start {datetime.now()}")
    laser_cut_inventory = LaserCutInventory(None)
    for category, category_data in old_components_inventory_data.items():
        for item, item_data in category_data.items():
            category_object = laser_cut_inventory.get_category(category)
            if laser_cut_part := laser_cut_inventory.get_laser_cut_part_by_name(item):
                laser_cut_part.set_category_quantity(category_object, item_data["unit_quantity"])
    print(f"loading done {datetime.now()}")
    print(f"saving start {datetime.now()}")
    laser_cut_inventory.save()
    print(f"saving done {datetime.now()}")


if __name__ == "__main__":
    restore()
