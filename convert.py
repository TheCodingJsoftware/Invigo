import contextlib
from datetime import datetime

import ujson as json

from utils.components_inventory.component import Component
from utils.components_inventory.components_inventory import ComponentsInventory
from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.sheets_inventory.sheet import Sheet
from utils.sheets_inventory.sheets_inventory import SheetsInventory

sheet_settings = SheetSettings()


def convert_legacy_database():
    # ! LASER CUT PARTS
    with open(r"data\inventory - Parts in Inventory.json", "r", encoding="utf-8") as file:
        laser_cut_inventory_data = json.load(file)
    print(f"loading start {datetime.now()}")
    laser_cut_inventory = LaserCutInventory(None)
    for category, category_data in laser_cut_inventory_data.items():
        laser_cut_inventory.add_category(category)
    for category, category_data in laser_cut_inventory_data.items():
        laser_cut_category = laser_cut_inventory.get_category(category)
        for laser_part_name, laser_part_data in category_data.items():
            if category == "Recut":
                recut_part = LaserCutPart(laser_part_name, laser_part_data, laser_cut_inventory)
                with contextlib.suppress(AttributeError):
                    recut_part.bend_cost = float(recut_part.bend_cost.replace("$", ""))
                with contextlib.suppress(AttributeError):
                    recut_part.labor_cost = float(recut_part.labor_cost.replace("$", ""))
                recut_part.add_to_category(laser_cut_category)
                recut_part.recut = True
                laser_cut_inventory.add_recut_part(recut_part)
                continue
            if laser_cut_part := laser_cut_inventory.get_laser_cut_part_by_name(laser_part_name):
                laser_cut_part.add_to_category(laser_cut_category)
            else:
                laser_cut_part = LaserCutPart(laser_part_name, laser_part_data, laser_cut_inventory)
                with contextlib.suppress(AttributeError):
                    laser_cut_part.bend_cost = float(laser_cut_part.bend_cost.replace("$", ""))
                with contextlib.suppress(AttributeError):
                    laser_cut_part.labor_cost = float(laser_cut_part.labor_cost.replace("$", ""))
                laser_cut_part.add_to_category(laser_cut_category)
                if laser_cut_part.recut:
                    laser_cut_inventory.add_recut_part(laser_cut_part)
                else:
                    laser_cut_inventory.add_laser_cut_part(laser_cut_part)
    print(f"loading done {datetime.now()}")
    print(f"saving start {datetime.now()}")
    laser_cut_inventory.save()
    print(f"saving done {datetime.now()}")
    # ! SHEETS INVENTORY
    with open(r"data\inventory - Price of Steel.json", "r", encoding="utf-8") as file:
        sheets_inventory_data = json.load(file)
    print(f"loading start {datetime.now()}")
    sheets_inventory = SheetsInventory(sheet_settings)
    for category, category_data in sheets_inventory_data.items():
        if category == "Price Per Pound":
            continue
        sheets_inventory.add_category(category)
    for category, category_data in sheets_inventory_data.items():
        if category == "Price Per Pound":
            continue
        sheets_category = sheets_inventory.get_category(category)
        for sheet_name, sheet_data in category_data.items():
            if sheet := sheets_inventory.get_sheet_by_name(sheet_name):
                sheet.add_to_category(sheets_category)
            else:
                sheet = Sheet(sheet_name, sheet_data, sheets_inventory)
                sheet.length = float(sheet_data["sheet_dimension"].split("x")[0])
                sheet.width = float(sheet_data["sheet_dimension"].split("x")[1])
                sheet.quantity = sheet_data["current_quantity"]
                with contextlib.suppress(KeyError):
                    sheet.red_quantity_limit = sheet_data["red_limit"]
                with contextlib.suppress(KeyError):
                    sheet.yellow_quantity_limit = sheet_data["yellow_limit"]
                sheet.latest_change_quantity = sheet_data["latest_change_current_quantity"]
                sheet.add_to_category(sheets_category)
                sheets_inventory.add_sheet(sheet)
    print(f"loading done {datetime.now()}")
    print(f"saving start {datetime.now()}")
    sheets_inventory.save()
    print(f"saving done {datetime.now()}")
    # ! COMPONENTS
    with open(r"data\inventory.json", "r", encoding="utf-8") as file:
        components_inventory_data = json.load(file)
    print(f"loading start {datetime.now()}")
    components_inventory = ComponentsInventory()
    for category, category_data in components_inventory_data.items():
        components_inventory.add_category(category)
    for category, category_data in components_inventory_data.items():
        components_category = components_inventory.get_category(category)
        for component_name, component_data in category_data.items():
            if component := components_inventory.get_component_by_name(component_data["part_number"]):
                component.add_to_category(components_category)
            else:
                component = Component(component_data["part_number"], component_data, components_inventory)
                component.part_name = component_name
                component.quantity = component_data["current_quantity"]
                with contextlib.suppress(KeyError):
                    component.red_quantity_limit = component_data["red_limit"]
                with contextlib.suppress(KeyError):
                    component.yellow_quantity_limit = component_data["yellow_limit"]
                component.add_to_category(components_category)
                components_inventory.add_component(component)
    print(f"loading done {datetime.now()}")
    print(f"saving start {datetime.now()}")
    components_inventory.save()
    print(f"saving done {datetime.now()}")


convert_legacy_database()
