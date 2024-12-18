import os

from utils.inventory.categories import Categories
from utils.inventory.category import Category


class Inventory:
    def __init__(self, filename: str):
        self.categories: Categories = Categories()
        self.filename: str = filename.replace(".json", "")
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"
        self.__create_file()

    def __create_file(self):
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.filename}.json"):
            self._reset_file()

    def _reset_file(self):
        with open(
            f"{self.FOLDER_LOCATION}/{self.filename}.json", "w", encoding="utf-8"
        ) as file:
            file.write("{}")

    def get_categories(self) -> list[Category]:
        return self.categories.categories

    def get_category(self, category_name: str) -> Category:
        return self.categories.get_category(category_name)

    def add_category(self, category: str | Category):
        if isinstance(category, str):
            self.categories.add_category(Category(category))
        elif isinstance(category, Category):
            self.categories.add_category(category)

    def delete_category(self, category: str | Category) -> Category:
        if isinstance(category, str):
            return self.categories.delete_category(self.get_category(category))
        elif isinstance(category, Category):
            return self.categories.delete_category(category)
