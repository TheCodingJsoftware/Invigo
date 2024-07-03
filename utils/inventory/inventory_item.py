from utils.inventory.category import Category


class InventoryItem:
    def __init__(self, name: str):
        self.name: str = name
        self.categories: list[Category] = []

    def print_categories(self) -> str:
        return "".join(
            f"{i + 1}. {category.name}\n" for i, category in enumerate(self.categories)
        )

    def rename(self, new_name: str):
        self.name = new_name

    def add_to_category(self, category: Category):
        self.categories.append(category)

    def remove_from_category(self, category: Category):
        self.categories.remove(category)
