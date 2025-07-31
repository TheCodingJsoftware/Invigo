import json
import os
from datetime import datetime
from typing import TypedDict

from config.environments import Environment


class Geometry(TypedDict):
    x: int
    y: int
    width: int
    height: int


class TablesFont(TypedDict):
    family: str
    italic: bool
    pointSize: int
    weight: int


class UserWorkspaceSettings(TypedDict):
    view_parts: bool
    view_assemblies: bool
    visible_process_tags: list[str]


class TabVisibility(TypedDict):
    Components: bool
    JobPlanner: bool
    JobQuoter: bool
    LaserCutInventory: bool
    SheetSettings: bool
    SheetsInInventory: bool
    StructuralSteelInventory: bool
    StructuralSteelSettings: bool
    ViewPriceChangesHistory: bool
    ViewRemovedQuantitiesHistory: bool
    Workspace: bool


class CategoryTabsOrder(TypedDict):
    components_tab: list[str]
    sheets_in_inventory_tab: list[str]
    laser_cut_inventory_tab: list[str]


class ServerSettings(TypedDict):
    protocol: str
    ip: str
    port: int


class SortSettings(TypedDict):
    ascending: bool
    descending: bool
    quantity_in_stock: bool
    priority: bool
    alphabatical: bool


class SettingsDict(TypedDict, total=False):
    tab_visibility: TabVisibility
    user_workspace_settings: UserWorkspaceSettings
    open_workorder_when_generated: bool
    exchange_rate: float
    show_maximized: bool
    theme: str
    sort_ascending: bool
    sort_descending: bool
    sort_quantity_in_stock: bool
    sort_priority: bool
    sort_alphabatical: bool
    server: ServerSettings
    geometry: Geometry
    last_opened: str
    last_toolbox_tab: int
    quote_nest_directories: list[str]
    tables_font: TablesFont
    tabs_order: list[str]
    category_tabs_order: CategoryTabsOrder


DEFAULT_SETTINGS: SettingsDict = {
    "tab_visibility": {
        "Components": True,
        "JobPlanner": True,
        "JobQuoter": True,
        "LaserCutInventory": True,
        "SheetSettings": True,
        "SheetsInInventory": True,
        "StructuralSteelInventory": True,
        "StructuralSteelSettings": True,
        "ViewPriceChangesHistory": False,
        "ViewRemovedQuantitiesHistory": False,
        "Workspace": True,
    },
    "user_workspace_settings": {
        "view_parts": True,
        "view_assemblies": True,
        "visible_process_tags": ["Laser Cutting"],
    },
    "open_workorder_when_generated": True,
    "exchange_rate": 1.0,
    "show_maximized": True,
    "theme": "dark_theme",
    "sort_ascending": False,
    "sort_descending": True,
    "sort_quantity_in_stock": True,
    "sort_priority": False,
    "sort_alphabatical": False,
    "server": {
        "protocol": "http",
        "ip": "localhost",
        "port": 5057,
    },
    "geometry": {"x": 200, "y": 200, "width": 1200, "height": 600},
    "last_opened": str(datetime.now()),
    "last_toolbox_tab": 0,
    "quote_nest_directories": [],
    "tables_font": {"family": "Segoe UI", "italic": False, "pointSize": 8, "weight": 400},
    "tabs_order": [
        "Components",
        "Sheets In Inventory",
        "Laser Cut Inventory",
        "Sheet Settings",
        "Structural Steel Inventory",
        "Structural Steel Settings",
        "Job Planner",
        "Job Quoter",
        "Workspace",
    ],
    "category_tabs_order": {
        "components_tab": [],
        "sheets_in_inventory_tab": [],
        "laser_cut_inventory_tab": [],
    },
}


class Settings:
    def __init__(self):
        self.file_name = "settings"
        self.FOLDER_LOCATION = Environment.DATA_PATH
        self.file_path = os.path.join(self.FOLDER_LOCATION, f"{self.file_name}.json")
        self.data: SettingsDict = {}
        self.__create_file()
        self.load_data()
        self.default_settings()

    def __create_file(self):
        os.makedirs(self.FOLDER_LOCATION, exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def load_data(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"{self.file_name}.json failed to load: {e}")
            self.data = {}

    def save_data(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4, sort_keys=True)

    def get_value(self, setting_name: str):
        return self.data.get(setting_name)

    def set_value(self, setting_key: str, setting_value):
        self.load_data()
        self.data[setting_key] = setting_value
        self.save_data()

    def default_settings(self):
        for key, default_value in DEFAULT_SETTINGS.items():
            self.data.setdefault(key, default_value)
        self.save_data()
