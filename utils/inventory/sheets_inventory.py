from typing import Union

import msgspec
from natsort import natsorted
from PyQt6.QtCore import QThread, QThreadPool

from utils.inventory.category import Category
from utils.inventory.inventory import Inventory
from utils.inventory.sheet import Sheet
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.threads.runnable_chain import RunnableChain
from utils.threads.sheets_inventory.add_sheet import AddSheetWorker
from utils.threads.sheets_inventory.get_all_sheets import GetAllSheetsWorker
from utils.threads.sheets_inventory.get_categories import GetSheetCategoriesWorker
from utils.threads.sheets_inventory.get_sheet import GetSheetWorker
from utils.threads.sheets_inventory.remove_sheets import RemoveSheetsWorker
from utils.threads.sheets_inventory.update_sheet_thread import (
    UpdateSheetWorker,
)


class SheetsInventory(Inventory):
    def __init__(self, sheet_settings: SheetSettings):
        super().__init__("sheets_inventory")
        self.sheets: list[Sheet] = []
        self.sheet_settings = sheet_settings
        self.threads: list[QThread] = []

    def get_all_sheets_material(self, sheets: list[Sheet] | None = None) -> list[str]:
        if sheets:
            materials: dict[str] = {sheet.material for sheet in sheets}
        else:
            materials: dict[str] = {sheet.material for sheet in self.sheets}
        return list(materials)

    def get_sheets_by_category(self, category: str | Category) -> list[Sheet]:
        if isinstance(category, str):
            category = self.get_category(category)
        return [sheet for sheet in self.sheets if category in sheet.categories]

    def add_sheet(self, new_sheet: Sheet, on_finished: callable = None):
        worker = AddSheetWorker(new_sheet)
        worker.signals.success.connect(self.add_sheet_thread_finished)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def add_sheet_thread_finished(self, response: dict, status_code: int, sheet: Sheet):
        if status_code == 200:
            self.sheets.append(sheet)
            # self.save_local_copy()

    def remove_sheets(self, sheets: list[Sheet], on_finished: callable = None):
        worker = RemoveSheetsWorker(sheets)
        worker.signals.success.connect(self.sheets_removed_responsed)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def remove_sheet(self, sheet: Sheet, on_finished: callable = None):
        worker = RemoveSheetsWorker([sheet])
        worker.signals.success.connect(self.sheets_removed_responsed)
        if on_finished:
            worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def sheets_removed_responsed(
        self, response: dict, status_code: int, sheets: list[Sheet]
    ):
        if status_code == 200:
            for sheet in sheets:
                self.sheets.remove(sheet)
            # self.save_local_copy()

    def save_sheet(self, sheet: Sheet):
        worker = UpdateSheetWorker(sheet)
        worker.signals.success.connect(self.save_sheet_response)
        QThreadPool.globalInstance().start(worker)

    def get_sheet(self, sheet_id: int | str, on_finished: callable = None):
        worker = GetSheetWorker(sheet_id)
        worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def save_sheet_response(self, response: dict):
        self.save_local_copy()

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

    def get_sheet_by_name(self, sheet_name: str) -> Sheet | None:
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
        chain = RunnableChain()

        get_categories_worker = GetSheetCategoriesWorker()
        get_all_sheets_worker = GetAllSheetsWorker()

        chain.add(get_categories_worker, self.get_categories_response)
        chain.add(get_all_sheets_worker, self.get_all_sheets_response)

        if on_loaded:
            chain.finished.connect(on_loaded)

        chain.start()

    def get_categories_response(self, response: list, next_step):
        try:
            self.categories.from_list(response)
        except Exception:
            self.categories.clear()
        next_step()

    def get_all_sheets_response(self, response: dict, next_step):
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
