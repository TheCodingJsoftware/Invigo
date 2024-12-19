from utils.inventory.category import Category


class Categories:
    def __init__(self):
        self.categories: list[Category] = []

    def get_category(self, category_name: str) -> Category:
        return next(
            (
                category
                for category in self.categories
                if category.name == category_name
            ),
            None,
        )

    def add_category(self, category: Category):
        self.categories.append(category)

    def delete_category(self, category: Category) -> Category:
        self.categories.remove(category)
        return category

    def clear(self):
        self.categories.clear()

    def to_dict(self) -> list[str]:
        data = {category.name for category in self.categories}
        return list(data)

    def from_dict(self, data: list[str]):
        self.categories.clear()
        for category_name in data:
            self.categories.append(Category(category_name))
