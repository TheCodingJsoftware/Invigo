from utils.inventory.category import Category


class InventoryItem:
    def __init__(self):
        self.id = -1
        self.name = ""
        self.categories: list[Category] = []

    def print_categories(self) -> str:
        return "".join(f"{i + 1}. {category.name}<br>" for i, category in enumerate(self.categories))

    def get_categories(self):
        return [category.name for category in self.categories]

    def rename(self, new_name: str):
        self.name = new_name

    def add_to_category(self, category: Category):
        self.categories.append(category)

    def remove_from_category(self, category: Category):
        self.categories.remove(category)
