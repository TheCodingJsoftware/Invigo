import contextlib
import itertools
import os
import threading
from datetime import datetime

from PyQt5 import QtTest
from PyQt5.QtCore import QThread, pyqtSignal

from utils.json_file import JsonFile


class RemoveQuantityThread(QThread):
    signal = pyqtSignal(object)

    def __init__(
        self,
        inventory: JsonFile,
        category: str,
        inventory_prices_objects: dict,
        multiplier: int,
    ) -> None:
        QThread.__init__(self)
        self.username = os.getlogin().title()
        self.category = category
        self.inventory_prices_objects = inventory_prices_objects
        self.completion_count: int = 0
        self.multiplier: int = multiplier
        self.max_item_count = inventory.get_sum_of_items()
        self.inventory = inventory

    def run(self) -> None:
        try:
            category_data = self.inventory.get_value(item_name=self.category)
            inventory = self.inventory.get_data()
            part_numbers = []
            for item, object_item in zip(
                list(category_data.keys()), list(self.inventory_prices_objects.keys())
            ):
                unit_quantity: int = category_data[item]["unit_quantity"]
                current_quantity: int = category_data[item]["current_quantity"]
                part_numbers.append(category_data[item]["part_number"])
                spin_current_quantity = self.inventory_prices_objects[object_item][
                    "current_quantity"
                ]
                inventory[self.category][item]["current_quantity"] = current_quantity - (
                    unit_quantity * self.multiplier
                )
                inventory[self.category][item][
                    "latest_change_current_quantity"
                ] = f"Latest Change:\nfrom: {current_quantity}\nto: {current_quantity - (unit_quantity * self.multiplier)}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                spin_current_quantity.setValue(
                    int(current_quantity - (unit_quantity * self.multiplier))
                )
                self.completion_count += 1
                self.signal.emit(f"{self.completion_count}, {self.max_item_count}")
            part_numbers = list(set(part_numbers))
            data = self.inventory.get_data()
            for category in list(data.keys()):
                if category == self.category:
                    continue
                self.max_item_count += len(list(data[category].keys())) * len(
                    part_numbers
                )
                for item, part_number in itertools.product(
                    list(data[category].keys()), part_numbers
                ):
                    if part_number == data[category][item]["part_number"]:
                        unit_quantity: int = data[category][item]["unit_quantity"]
                        current_quantity: int = data[category][item]["current_quantity"]
                        inventory[category][item][
                            "current_quantity"
                        ] = current_quantity - (unit_quantity * self.multiplier)
                        inventory[category][item][
                            "latest_change_current_quantity"
                        ] = f"Latest Change:\nfrom: {current_quantity}\nto: {current_quantity - (unit_quantity * self.multiplier)}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                    self.completion_count += 1
                    self.signal.emit(f"{self.completion_count}, {self.max_item_count}")
            self.inventory.save_data(inventory)
            self.signal.emit("Done")
        except Exception as error:
            print(error)
            self.signal.emit(error)
