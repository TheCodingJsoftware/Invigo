from typing import Union

import msgspec
from natsort import natsorted

from utils.inventory.category import Category
from utils.inventory.component import Component
from utils.inventory.inventory import Inventory


class ComponentsInventory(Inventory):
    def __init__(self):
        super().__init__("components_inventory")
        self.components: list[Component] = []
        self.load_data()

    def index(self, component: Component | str):
        if isinstance(component, Component):
            return self.components.index(component)
        elif isinstance(component, str):
            return self.components.index(self.get_component_by_name(component))

    def get_all_part_names(self) -> list[str]:
        return [component.part_name for component in self.components]

    def get_all_part_numbers(self) -> list[str]:
        return [component.name for component in self.components]

    def get_total_stock_cost(self) -> float:
        total = 0.0
        for component in self.components:
            total += component.get_total_cost_in_stock()
        return total

    def get_components_by_category(self, category: str | Category) -> list[Component]:
        if isinstance(category, str):
            category = self.get_category(category)
        return [
            component
            for component in self.components
            if category in component.categories
        ]

    def get_total_stock_cost_for_similar_categories(self, text: str) -> float:
        total = 0.0
        used_components: set[Component] = set()
        for category in self.get_categories():
            if text in category.name:
                for component in self.components:
                    if (
                        category in component.categories
                        and component not in used_components
                    ):
                        total += component.get_total_cost_in_stock()
                        used_components.add(component)
        return total

    def get_total_category_cost_in_stock(self, category: Category | str) -> float:
        total = 0.0
        if isinstance(category, str):
            category = self.get_category(category)
        for component in self.components:
            if category in component.categories:
                total += component.get_total_cost_in_stock()
        return total

    def get_total_category_unit_cost(self, category: Category | str) -> float:
        total = 0.0
        if isinstance(category, str):
            category = self.get_category(category)
        for component in self.components:
            if category in component.categories:
                total += component.get_total_unit_cost(category)
        return total

    def add_component(self, component: Component):
        self.components.append(component)

    def remove_component(self, component: Component):
        self.components.remove(component)

    def duplicate_category(
        self, category_to_duplicate: Category, new_category_name: str
    ) -> Category:
        new_category = Category(new_category_name)
        super().add_category(new_category)
        for component in self.get_components_by_category(category_to_duplicate):
            component.add_to_category(new_category)
        return new_category

    def delete_category(self, category: str | Category) -> Category:
        deleted_category = super().delete_category(category)
        for component in self.get_components_by_category(deleted_category):
            component.remove_from_category(deleted_category)
        return deleted_category

    def get_component_by_name(self, component_name: str) -> Component:
        return next(
            (
                component
                for component in self.components
                if component.name == component_name
            ),
            None,
        )

    def get_component_by_part_name(self, component_name: str) -> Component:
        return next(
            (
                component
                for component in self.components
                if component.part_name == component_name
            ),
            None,
        )

    def sort_by_quantity(self, ascending: bool) -> list[Component]:
        self.components = natsorted(
            self.components, key=lambda component: component.quantity, reverse=ascending
        )
        return self.components

    def sort_by_name(self, ascending: bool) -> list[Component]:
        self.components = natsorted(
            self.components,
            key=lambda component: component.part_name,
            reverse=ascending,
        )
        return self.compoennts

    def save(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self):
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "rb") as file:
                data: dict[str, Union[dict[str, object], list[object]]] = (
                    msgspec.json.decode(file.read())
                )
            self.categories.from_list(data["categories"])
            self.components.clear()

            for component_data in data["components"]:
                try:
                    component = Component(component_data, self)
                except AttributeError:  # Old inventory format
                    component = Component(data["components"][component_data], self)
                    component.part_number = component_data
                self.add_component(component)
        except KeyError:  # Inventory was just created
            return
        except msgspec.DecodeError:  # Inventory file got cleared
            self._reset_file()
            self.load_data()

    def to_dict(self) -> dict[str, Union[dict[str, object], list[object]]]:
        return {
            "categories": self.categories.to_dict(),
            "components": [component.to_dict() for component in self.components],
        }
