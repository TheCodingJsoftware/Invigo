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
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w") as json_file:
                json_file.write("{}")

    def load_data(self) -> None:
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r", encoding="utf-8") as json_file:
                self.data = json.load(json_file)
        except Exception as error:
            print(f"{self.file_name}.JsonFile.load_data: {error}")
            self.default_settings()

    def save_data(self) -> None:
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(self.data, json_file, ensure_ascii=False, indent=4)

    def get_value(self, setting_name: str) -> None | dict[str, dict]:
        try:
            return self.data[setting_name]
        except KeyError:
            return None

    def set_value(self, setting_name: str, setting_value: object):
        self.data.update({setting_name: setting_value})
        self.save_data()

    def default_settings(self) -> None:
        self.check_setting(setting="open_quote_when_generated", default_value=True)
        self.check_setting(setting="open_workorder_when_generated", default_value=True)
        self.check_setting(setting="open_packing_slip_when_generated", default_value=True)
        self.check_setting(setting="exchange_rate", default_value=1.0)
        self.check_setting(setting="sort_ascending", default_value=False)
        self.check_setting(setting="sort_descending", default_value=True)
        self.check_setting(setting="sort_quantity_in_stock", default_value=True)
        self.check_setting(setting="sort_priority", default_value=False)
        self.check_setting(setting="sort_alphabatical", default_value=False)
        self.check_setting(setting="server_ip", default_value="10.0.0.9")
        self.check_setting(setting="server_port", default_value=8080)
        self.check_setting(
            setting="geometry",
            default_value={"x": 200, "y": 200, "width": 1200, "height": 600},
        )
        self.check_setting(
            setting="last_opened",
            default_value=str(datetime.now()),
        )
        self.check_setting(setting="last_category_tab", default_value=0)
        self.check_setting(setting="last_toolbox_tab", default_value=0)
        self.check_setting(setting="last_dock_location", default_value=2)
        self.check_setting(setting="change_quantities_by", default_value="Category")
        self.check_setting(setting="inventory_file_name", default_value="inventory")
        self.check_setting(setting="path_to_order_number", default_value="order_number.json")
        self.check_setting(
            setting="trusted_users",
            default_value=[
                "lynden",
                "jared",
                "laserpc",
                "laser pc",
                "justin",
                "jordan",
            ],
        )
        self.check_setting(setting="quote_nest_directories", default_value=[])
        font = QFont("Segoe UI", 8)
        font.setWeight(400)
        font_data = {
            "family": font.family(),
            "pointSize": font.pointSize(),
            "weight": font.weight(),
            "italic": font.italic(),
        }
        self.check_setting(setting="tables_font", default_value=font_data)
        self.check_setting(
            setting="menu_tabs_order",
            default_value=[
                "Edit Components",
                "Edit Sheets in Inventory",
                "Edit Laser Cut Inventory",
                "OmniGen",
                "Workspace",
                "Chat",
                "View Inventory (Read Only)",
                "View Removed Quantities History (Read Only)",
                "View Price Changes History (Read Only)",
            ],
        )
        self.check_setting(
            setting="category_tabs_order",
            default_value={
                "Edit Components": [],
                "Edit Sheets in Inventory": [],
                "Edit Laser Cut Inventory": [],
                "Workspace": [],
            },
        )
        self.check_setting(
            setting="price_history_file_name",
            default_value=str(datetime.now().strftime("%B %d %A %Y")),
        )
        self.check_setting(
            setting="days_until_new_price_history_assessment",
            default_value=90,
        )
        self.save_data()

    def check_setting(self, setting: str, default_value: object) -> None:
        try:
            if self.data[setting] is None:
                self.data[setting] = default_value
        except KeyError:  # Meaning the setting is not entered
            self.data[setting] = default_value
