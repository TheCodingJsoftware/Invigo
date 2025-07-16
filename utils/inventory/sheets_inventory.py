from typing import Callable

import msgspec
from natsort import natsorted
from PyQt6.QtCore import QThread, QThreadPool

from utils.inventory.category import Category
from utils.inventory.inventory import Inventory
from utils.inventory.sheet import Sheet
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.workers.runnable_chain import RunnableChain
from utils.workers.sheets_inventory.add_sheet import AddSheetWorker
from utils.workers.sheets_inventory.get_all_sheets import GetAllSheetsWorker
from utils.workers.sheets_inventory.get_categories import GetSheetCategoriesWorker
from utils.workers.sheets_inventory.get_sheet import GetSheetWorker
from utils.workers.sheets_inventory.remove_sheets import RemoveSheetsWorker
from utils.workers.sheets_inventory.update_sheets import (
    UpdateSheetsWorker,
)


class SheetsInventory(Inventory):
    def __init__(self, sheet_settings: SheetSettings):
        super().__init__("sheets_inventory")
        self.sheets: list[Sheet] = []
        self.sheet_settings = sheet_settings

    def get_all_sheets_material(self, sheets: list[Sheet] | None = None) -> list[str]:
        materials: set[str] = set()
        if sheets:
            materials = {sheet.material for sheet in sheets}
        else:
            materials = {sheet.material for sheet in self.sheets}
        return list(materials)

    def get_sheets_by_category(self, category: str | Category) -> list[Sheet]:
        if isinstance(category, str):
            category = self.get_category(category)
        return [sheet for sheet in self.sheets if category in sheet.categories]

    def get_sheet_by_id(self, sheet_id: int) -> Sheet | None:
        return next((sheet for sheet in self.sheets if sheet.id == sheet_id), None)

    def add_sheet(self, new_sheet: Sheet, on_finished: Callable | None = None):
        worker = AddSheetWorker(new_sheet)
        worker.signals.success.connect(self.add_sheet_thread_response)
        if on_finished:
            worker.signals.finished.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def add_sheet_thread_response(self, response: tuple[dict, Sheet]):
        data, sheet = response
        sheet.id = data["id"]
        self.sheets.append(sheet)
        # self.save_local_copy()

    def remove_sheets(self, sheets: list[Sheet], on_finished: Callable | None = None):
        worker = RemoveSheetsWorker(sheets)
        worker.signals.success.connect(self.sheets_removed_responsed)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def remove_sheet(self, sheet: Sheet, on_finished: Callable | None = None):
        self.remove_sheets([sheet], on_finished)

    def sheets_removed_responsed(self, response: tuple[dict, list[Sheet]]):
        data, sheets = response
        for sheet in sheets:
            self.sheets.remove(sheet)
            # self.save_local_copy()

    def save_sheet(self, sheet: Sheet):
        self.save_sheets([sheet])

    def save_sheets(self, sheets: list[Sheet]):
        worker = UpdateSheetsWorker(sheets)
        worker.signals.success.connect(self.save_local_copy)
        QThreadPool.globalInstance().start(worker)

    def get_sheet(self, sheet_id: int | str, on_finished: Callable | None = None):
        worker = GetSheetWorker(sheet_id)
        worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def update_sheet_data(self, sheet_id: int, data: dict) -> Sheet | None:
        for sheet in self.sheets:
            if sheet.id == sheet_id:
                sheet.load_data(data)
                return sheet
        return None

    def duplicate_category(self, category_to_duplicate: Category, new_category_name: str) -> Category:
        new_category = Category(new_category_name)
        super().add_category(new_category)
        sheets_to_duplicate = self.get_sheets_by_category(category_to_duplicate)
        for sheet in sheets_to_duplicate:
            sheet.add_to_category(new_category)
        self.save_sheets(sheets_to_duplicate)
        return new_category

    def delete_category(self, category: str | Category) -> Category:
        deleted_category = super().delete_category(category)
        sheets_to_remove = self.get_sheets_by_category(deleted_category)
        for sheet in sheets_to_remove:
            sheet.remove_from_category(deleted_category)
        self.save_sheets(sheets_to_remove)
        return deleted_category

    def get_sheet_cost(self, sheet: Sheet) -> float:
        pounds_per_square_foot = self.sheet_settings.get_pounds_per_square_foot(sheet.material, sheet.thickness)
        pounds_per_sheet = ((sheet.length * sheet.width) / 144) * pounds_per_square_foot
        price_per_pound = self.sheet_settings.get_price_per_pound(sheet.material)
        price = pounds_per_sheet * price_per_pound
        sheet.price = price
        sheet.price_per_pound = price_per_pound
        sheet.pounds_per_square_foot = pounds_per_square_foot
        return price

    def get_category_stock_cost(self, category: Category) -> float:
        total = 0.0
        for sheet in self.get_sheets_by_category(category):
            total += self.get_sheet_cost(sheet) * sheet.quantity
        return total

    def get_sheet_by_name(self, sheet_name: str) -> Sheet | None:
        return next((sheet for sheet in self.sheets if sheet.get_name() == sheet_name), None)

    def exists(self, other: Sheet) -> bool:
        return any(sheet.get_name() == other.get_name() for sheet in self.sheets)

    def sort_by_material(self) -> list[Sheet]:
        self.sheets = natsorted(self.sheets, key=lambda sheet: sheet.material)
        return self.sheets

    def sort_by_thickness(self) -> list[Sheet]:
        self.sheets = natsorted(self.sheets, key=lambda sheet: sheet.thickness)
        return self.sheets

    def save_local_copy(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self, on_loaded: Callable | None = None):
        self.chain = RunnableChain()

        get_categories_worker = GetSheetCategoriesWorker()
        get_all_sheets_worker = GetAllSheetsWorker()

        self.chain.add(get_categories_worker, self.get_categories_response)
        self.chain.add(get_all_sheets_worker, self.get_all_sheets_response)

        if on_loaded:
            self.chain.finished.connect(on_loaded)

        self.chain.start()

    def get_categories_response(self, response: list, next_step: Callable):
        try:
            self.categories.from_list(response)
        except Exception:
            self.categories.clear()
        next_step()

    def get_all_sheets_response(self, response: dict, next_step: Callable):
        self.sheets.clear()
        for sheet_data in response:
            sheet = Sheet(sheet_data, self)
            self.sheets.append(sheet)
        self.save_local_copy()
        next_step()

    def to_dict(self) -> dict:
        return {
            "categories": self.categories.to_dict(),
            "sheets": [sheet.to_dict() for sheet in self.sheets],
        }
