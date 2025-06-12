from typing import Union

import msgspec
from natsort import natsorted
from PyQt6.QtCore import QThread, pyqtSignal

from utils.inventory.category import Category
from utils.inventory.inventory import Inventory
from utils.inventory.sheet import Sheet
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.threads.sheets_inventory.add_sheet import AddSheetThread
from utils.threads.sheets_inventory.get_all_sheets import GetAllSheetsThread
from utils.threads.sheets_inventory.get_categories import \
    GetSheetCategoriesThread
from utils.threads.sheets_inventory.remove_sheets import RemoveSheetsThread
from utils.threads.sheets_inventory.update_sheet_thread import \
    UpdateSheetThread
from utils.threads.thread_chain import ThreadChain


class SheetsInventory(Inventory):
    def __init__(self, sheet_settings: SheetSettings):
        super().__init__("sheets_inventory")
        self.sheets: list[Sheet] = []
        self.sheet_settings = sheet_settings

        self.threads: list[QThread] = []

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

    def add_sheet(self, new_sheet: Sheet):
        add_sheet_thread = AddSheetThread(new_sheet)
        self.threads.append(add_sheet_thread)
        add_sheet_thread.signal.connect(self.add_sheet_thread_finished)
        add_sheet_thread.finished.connect(add_sheet_thread.deleteLater)
        add_sheet_thread.start()

    def add_sheet_thread_finished(self, response: dict, status_code: int, sheet: Sheet):
        if status_code == 200:
            self.sheets.append(sheet)
            # self.save_local_copy()

    def remove_sheets(self, sheets: list[Sheet], on_finished: callable = None):
        remove_sheet_thread = RemoveSheetsThread(sheets)
        self.threads.append(remove_sheet_thread)
        remove_sheet_thread.signal.connect(self.sheets_removed_responsed)
        if on_finished:
            remove_sheet_thread.finished.connect(on_finished)
        remove_sheet_thread.finished.connect(remove_sheet_thread.deleteLater)
        remove_sheet_thread.start()

    def remove_sheet(self, sheet: Sheet, on_finished: callable = None):
        remove_sheet_thread = RemoveSheetsThread([sheet])
        self.threads.append(remove_sheet_thread)
        remove_sheet_thread.signal.connect(self.sheets_removed_responsed)
        if on_finished:
            remove_sheet_thread.finished.connect(on_finished)
        remove_sheet_thread.finished.connect(remove_sheet_thread.deleteLater)
        remove_sheet_thread.start()

    def sheets_removed_responsed(self, response: dict, status_code: int, sheets: list[Sheet]):
        if status_code == 200:
            for sheet in sheets:
                self.sheets.remove(sheet)
            # self.save_local_copy()

    def save_sheet(self, sheet: Sheet):
        update_sheet_thread = UpdateSheetThread(sheet)
        self.threads.append(update_sheet_thread)
        # update_sheet_thread.signal.connect(self.save_sheet_response)
        update_sheet_thread.finished.connect(update_sheet_thread.deleteLater)
        update_sheet_thread.start()

    # def save_sheet_response(self, response: dict, status_code: int):
    #     if status_code == 200:
    #         self.save_local_copy()

    def update_sheet_data(self, sheet_id: int, data: dict) -> Sheet | None:
        for sheet in self.sheets:
            if sheet.id == sheet_id:
                sheet.load_data(data)
                return sheet
        return None

    def duplicate_category(
        self, category_to_duplicate: Category, new_category_name: str
    ) -> Category:
        new_category = Category(new_category_name)
        super().add_category(new_category)
        for sheet in self.get_sheets_by_category(category_to_duplicate):
            sheet.add_to_category(new_category)
            self.save_sheet(sheet)
        return new_category

    def delete_category(self, category: str | Category) -> Category:
        deleted_category = super().delete_category(category)
        for sheet in self.get_sheets_by_category(deleted_category):
            sheet.remove_from_category(deleted_category)
            self.save_sheet(sheet)
        return deleted_category

    def get_sheet_cost(self, sheet: Sheet) -> float:
        pounds_per_square_foot = self.sheet_settings.get_pounds_per_square_foot(
            sheet.material, sheet.thickness
        )
        pounds_per_sheet = ((sheet.length * sheet.width) / 144) * pounds_per_square_foot
        price_per_pound = self.sheet_settings.get_price_per_pound(sheet.material)
        return pounds_per_sheet * price_per_pound

    def get_category_stock_cost(self, category: Category) -> float:
        total = 0.0
        for sheet in self.get_sheets_by_category(category):
            total += self.get_sheet_cost(sheet) * sheet.quantity
        return total

    def get_sheet_by_name(self, sheet_name: str) -> Sheet:
        return next(
            (sheet for sheet in self.sheets if sheet.get_name() == sheet_name), None
        )

    def exists(self, other: Sheet) -> bool:
        return any(sheet.get_name() == other.get_name() for sheet in self.sheets)

    def sort_by_material(self) -> list[Sheet]:
        self.sheets = natsorted(self.sheets, key=lambda sheet: sheet.material)

    def sort_by_thickness(self) -> list[Sheet]:
        self.sheets = natsorted(self.sheets, key=lambda sheet: sheet.thickness)

    def save_local_copy(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self, on_loaded: callable = None):
        chain = ThreadChain()

        get_categories_thread = GetSheetCategoriesThread()
        get_all_sheets_thread = GetAllSheetsThread()

        chain.add(get_categories_thread, self.get_categories_response)
        chain.add(get_all_sheets_thread, self.get_all_sheets_response)

        if on_loaded:
            chain.finished.connect(on_loaded)

        self.threads.append(get_categories_thread)
        self.threads.append(get_all_sheets_thread)

        chain.start()

    def get_categories_response(self, response: list, status_code: int, next_step):
        if status_code == 200:
            self.categories.from_list(response)
        else:
            self.categories.clear()
        next_step()

    def get_all_sheets_response(self, response: dict, status_code: int, next_step):
        if status_code == 200:
            self.sheets.clear()
            for sheet_data in response:
                sheet = Sheet(sheet_data, self)
                self.sheets.append(sheet)
            self.save_local_copy()
        next_step()

    def to_dict(self) -> dict[str, Union[dict[str, object], list[object]]]:
        return {
            "categories": self.categories.to_dict(),
            "sheets": [sheet.to_dict() for sheet in self.sheets],
        }
