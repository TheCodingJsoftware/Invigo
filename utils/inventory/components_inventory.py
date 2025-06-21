from typing import Callable

import msgspec
from natsort import natsorted
from PyQt6.QtCore import QThreadPool

from utils.inventory.category import Category
from utils.inventory.component import Component
from utils.inventory.inventory import Inventory
from utils.workers.components_inventory.add_component import AddComponentWorker
from utils.workers.components_inventory.get_all_components import GetAllComponentsWorker
from utils.workers.components_inventory.get_categories import (
    GetComponentsCategoriesWorker,
)
from utils.workers.components_inventory.get_component import GetComponentWorker
from utils.workers.components_inventory.remove_components import RemoveComponentsWorker
from utils.workers.components_inventory.update_components import UpdateComponentsWorker
from utils.workers.runnable_chain import RunnableChain


class ComponentsInventory(Inventory):
    def __init__(self) -> None:
        super().__init__("components_inventory")
        self.components: list[Component] = []

    def index(self, component: Component | str) -> int:
        if isinstance(component, Component):
            return self.components.index(component)
        elif isinstance(component, str):
            if component_object := self.get_component_by_name(component):
                return self.components.index(component_object)
            else:
                return -1

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

    def add_component(self, component: Component, on_finished: Callable | None = None):
        worker = AddComponentWorker(component)
        worker.signals.success.connect(self.add_component_response)
        if on_finished:
            worker.signals.finished.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def add_component_response(self, response: tuple[dict, Component]):
        data, component = response
        component.id = data["id"]
        self.components.append(component)

    def remove_components(
        self, components: list[Component], on_finished: Callable | None = None
    ):
        worker = RemoveComponentsWorker(components)
        worker.signals.success.connect(self.components_removed_response)
        if on_finished:
            worker.signals.finished.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def remove_component(
        self, component: Component, on_finished: Callable | None = None
    ):
        self.remove_components([component], on_finished)

    def components_removed_response(self, response: tuple[dict, list[Component]]):
        data, components = response
        for component in components:
            self.components.remove(component)
        # self.save_local_copy()

    def save_component(self, component: Component):
        self.save_components([component])

    def save_components(self, components: list[Component]):
        worker = UpdateComponentsWorker(components)
        worker.signals.success.connect(self.save_local_copy)
        QThreadPool.globalInstance().start(worker)

    def get_component(
        self, component_id: int | str, on_finished: Callable | None = None
    ):
        worker = GetComponentWorker(component_id)
        worker.signals.success.connect(on_finished)
        QThreadPool.globalInstance().start(worker)

    def update_component_data(self, component_id: int, data: dict) -> Component | None:
        for component in self.components:
            if component.id == component_id:
                component.load_data(data)
                return component
        return None

    def duplicate_category(
        self, category_to_duplicate: Category, new_category_name: str
    ) -> Category:
        new_category = Category(new_category_name)
        super().add_category(new_category)
        for component in self.get_components_by_category(category_to_duplicate):
            component.add_to_category(new_category)
        self.save_components(self.get_components_by_category(category_to_duplicate))
        return new_category

    def delete_category(self, category: str | Category) -> Category:
        deleted_category = super().delete_category(category)
        for component in self.get_components_by_category(deleted_category):
            component.remove_from_category(deleted_category)
        self.save_components(self.get_components_by_category(deleted_category))
        return deleted_category

    def get_component_by_name(self, component_name: str) -> Component | None:
        return next(
            (
                component
                for component in self.components
                if component.name == component_name
            ),
            None,
        )

    def get_component_by_part_name(self, component_name: str) -> Component | None:
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
        return self.components

    def save_local_copy(self):
        with open(f"{self.FOLDER_LOCATION}/{self.filename}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self, on_loaded: Callable | None = None):
        self.chain = RunnableChain()

        get_categories_worker = GetComponentsCategoriesWorker()
        get_all_components_worker = GetAllComponentsWorker()

        self.chain.add(get_categories_worker, self.get_categories_response)
        self.chain.add(get_all_components_worker, self.get_all_components_response)

        if on_loaded:
            self.chain.finished.connect(on_loaded)

        self.chain.start()

    def get_categories_response(self, response: list, next_step: Callable):
        try:
            self.categories.from_list(response)
        except Exception:
            self.categories.clear()
        next_step()

    def get_all_components_response(self, response: dict, next_step: Callable):
        self.components.clear()
        for component_data in response:
            component = Component(component_data, self)
            self.components.append(component)
        self.save_local_copy()
        next_step()

    def to_dict(self) -> dict:
        return {
            "categories": self.categories.to_dict(),
            "components": [component.to_dict() for component in self.components],
        }
