import os
import json
from datetime import datetime


class Settings:
    def __init__(self):
        self.data = {}
        self.file_name: str = "settings"
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/"
        self.__create_file()
        self.load_data()
        self.default_settings()

    def __create_file(self):
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
                json_file.write("{}")

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r", encoding="utf-8") as json_file:
                self.data = json.load(json_file)
        except json.decoder.JSONDecodeError as error:
            print(f"{self.file_name}.JsonFile.load_data: {error}")
            self.default_settings()

    def save_data(self):
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(self.data, json_file, ensure_ascii=False, indent=4, sort_keys=True)

    def get_value(self, setting_name: str) -> None | dict[str, dict[str, int]] | int | bool | str | float:
        try:
            return self.data[setting_name]
        except KeyError:
            return None

    def set_value(self, setting_name: str, setting_value: object):
        self.load_data()
        self.data[setting_name] = setting_value
        self.save_data()

    def default_settings(self):
        self.data.setdefault("tab_visibility", {
            "Chat": True,
            "Components": True,
            "Job Planner": True,
            "Job Quoter": True,
            "Laser Cut Inventory": True,
            "Quote Generator": True,
            "Sheet Settings": True,
            "Sheets in Inventory": True,
            "View Price Changes History": True,
            "View Removed Quantities History": True,
            "Workspace": True
        })
        self.data.setdefault("open_quote_when_generated", True)
        self.data.setdefault("open_workorder_when_generated", True)
        self.data.setdefault("open_packing_slip_when_generated", True)
        self.data.setdefault("exchange_rate", 1.0)
        self.data.setdefault("show_maximized", True)
        self.data.setdefault("sort_ascending", False)
        self.data.setdefault("sort_descending", True)
        self.data.setdefault("sort_quantity_in_stock", True)
        self.data.setdefault("sort_priority", False)
        self.data.setdefault("sort_alphabatical", False)
        self.data.setdefault("server_ip", "invi.go")
        self.data.setdefault("server_port", 80)
        self.data.setdefault("geometry", {"x": 200, "y": 200, "width": 1200, "height": 600})
        self.data.setdefault("last_opened", str(datetime.now()))
        self.data.setdefault("last_toolbox_tab", 0)
        self.data.setdefault("last_dock_location", 2)
        self.data.setdefault("quote_nest_directories", [])
        self.data.setdefault(
            "tables_font",
            {
                "family": "Segoe UI",
                "italic": False,
                "pointSize": 8,
                "weight": 400
            },
        )
        self.data.setdefault(
            "menu_tabs_order",
            [
                "Components",
                "Sheets in Inventory",
                "Laser Cut Inventory",
                "Quote Generator",
                "Job Planner",
                "Job Quoter",
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
        self.save_data()
