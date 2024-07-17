import msgspec
from natsort import natsorted
from typing import Union

from utils.inventory.category import Category
from utils.inventory.inventory import Inventory
from utils.inventory.sheet import Sheet
from utils.sheet_settings.sheet_settings import SheetSettings


class SheetsInventory(Inventory):
    def __init__(self, sheet_settings: SheetSettings):
        super().__init__("sheets_inventory")
        self.sheets: list[Sheet] = []
        self.sheet_settings = sheet_settings
        self.load_data()

    def get_all_sheets_material(self, sheets: list[Sheet] = None) -> list[str]:
        if sheets:
            materials: dict[str] = {sheet.material for sheet in sheets}
        else:
            materials: dict[str] = {sheet.material for sheet in self.sheets}
        return list(materials)

    def get_sheets_by_category(self, category: str | Category) -> list[Sheet]:
        if isinstance(category, str):
            category = self.get_category(category)
        return [sheet for sheet in self.sheets if category in sheet.categories]

    def add_sheet(self, sheet: Sheet):
        self.sheets.append(sheet)

    def remove_sheet(self, sheet: Sheet):
        self.sheets.remove(sheet)

    def duplicate_category(self, category_to_duplicate: Category, new_category_name: str) -> Category:
        new_category = Category(new_category_name)
        super().add_category(new_category)
        for sheet in self.get_sheets_by_category(category_to_duplicate):
            sheet.add_to_category(new_category)
        return new_category

    def delete_category(self, category: str | Category) -> Category:
        deleted_category = super().delete_category(category)
        for sheet in self.get_sheets_by_category(deleted_category):
            sheet.remove_from_category(deleted_category)
        return deleted_category

    def get_sheet_cost(self, sheet: Sheet) -> float:
        pounds_per_square_foot = self.sheet_settings.get_pounds_per_square_foot(sheet.material, sheet.thickness)
        pounds_per_sheet = ((sheet.length * sheet.width) / 144) * pounds_per_square_foot
        price_per_pound = self.sheet_settings.get_price_per_pound(sheet.material)
        return pounds_per_sheet * price_per_pound

    def get_category_stock_cost(self, category: Category) -> float:
        total = 0.0
        for sheet in self.get_sheets_by_category(category):
            total += self.get_sheet_cost(sheet) * sheet.quantity
        return total

    def get_sheet_by_name(self, sheet_name: str) -> Sheet:
        return next((sheet for sheet in self.sheets if sheet.get_name() == sheet_name), None)

    def exists(self, other: Sheet) -> bool:
        return any(sheet.get_name() == other.get_name() for sheet in self.sheets)

    def sort_by_material(self) -> list[Sheet]:
        self.sheets = natsorted(self.sheets, key=lambda sheet: sheet.material)

    def sort_by_thickness(self) -> list[Sheet]:
        self.sheets = natsorted(self.sheets, key=lambda sheet: sheet.thickness)

    def save(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "r", encoding="utf-8") as file:
                data: dict[str, dict[str, object]] = msgspec.json.decode(file.read())
            self.categories.from_dict(data["categories"])
            self.sheets.clear()
            for sheet_data in data["sheets"]:
                try:
                    sheet = Sheet(sheet_data, self)
                except AttributeError:
                    sheet = Sheet(data["sheets"][sheet_data], self)
                    sheet.name = sheet_data
                self.add_sheet(Sheet(sheet_data, self))
        except KeyError:  # Inventory was just created
            return
        except msgspec.DecodeError:  # Inventory file got cleared
            self._reset_file()
            self.load_data()

    def to_dict(self) -> dict[str, Union[dict[str, object], list[object]]]:
        return {
            "categories": self.categories.to_dict(),
            "sheets": [sheet.to_dict() for sheet in self.sheets],
        }
