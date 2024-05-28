import os
from datetime import datetime

import ujson as json
from PyQt6.QtGui import QFont


class Settings:
    def __init__(self) -> None:
        self.data = {}
        self.file_name: str = "settings"
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/"
        self.__create_file()
        self.load_data()
        self.default_settings()

    def __create_file(self) -> None:
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
                json_file.write("{}")

    def load_data(self) -> None:
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r", encoding="utf-8") as json_file:
                self.data = json.load(json_file)
        except json.JSONDecodeError as error:
            print(f"{self.file_name}.JsonFile.load_data: {error}")
            self.default_settings()

    def save_data(self) -> None:
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(self.data, json_file, ensure_ascii=False, indent=4)

    def get_value(self, setting_name: str) -> None | dict[str, dict[str, int]] | int | bool | str | float:
        try:
            return self.data[setting_name]
        except KeyError:
            return None

    def set_value(self, setting_name: str, setting_value: object):
        self.load_data()
        self.data[setting_name] = setting_value
        self.save_data()

    def default_settings(self) -> None:
        self.data.setdefault("server_directory", r"C:\Users\Invigo\Inventory-Manager\server")
        self.data.setdefault("open_quote_when_generated", True)
        self.data.setdefault("open_workorder_when_generated", True)
        self.data.setdefault("open_packing_slip_when_generated", True)
        self.data.setdefault("exchange_rate", 1.0)
        self.data.setdefault("sort_ascending", False)
        self.data.setdefault("sort_descending", True)
        self.data.setdefault("sort_quantity_in_stock", True)
        self.data.setdefault("sort_priority", False)
        self.data.setdefault("sort_alphabatical", False)
        self.data.setdefault("server_ip", "invi.go")
        self.data.setdefault("server_port", 80)
        self.data.setdefault("geometry", {"x": 200, "y": 200, "width": 1200, "height": 600})
        self.data.setdefault("last_opened", str(datetime.now()))
        self.data.setdefault("last_category_tab", 0)
        self.data.setdefault("last_toolbox_tab", 0)
        self.data.setdefault("last_dock_location", 2)
        self.data.setdefault("change_quantities_by", "Category")
        self.data.setdefault("inventory_file_name", "inventory")
        self.data.setdefault("path_to_order_number", "order_number.json")
        self.data.setdefault(
            "trusted_users",
            ["lynden", "jared", "laserpc", "laser pc", "justin", "jordan"],
        )
        self.data.setdefault("quote_nest_directories", [])
        font = QFont("Segoe UI", 8, 400)
        self.data.setdefault(
            "tables_font",
            {
                "family": font.family(),
                "pointSize": font.pointSize(),
                "weight": font.weight(),
                "italic": font.italic(),
            },
        )
        self.data.setdefault(
            "menu_tabs_order",
            [
                "Components",
                "Sheets in Inventory",
                "Laser Cut Inventory",
                "Quote Generator",
                "Workspace",
                "Chat",
                "View Removed Quantities History",
                "View Price Changes History",
            ],
        )
        self.data.setdefault(
            "category_tabs_order",
            {
                "Components": [],
                "Sheets in Inventory": [],
                "Laser Cut Inventory": [],
                "Workspace": [],
            },
        )
        self.data.setdefault("price_history_file_name", str(datetime.now().strftime("%B %d %A %Y")))
        self.data.setdefault("days_until_new_price_history_assessment", 90)
        self.save_data()
