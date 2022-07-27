import contextlib
import itertools
import os
import threading
from datetime import datetime

from PyQt5 import QtTest
from PyQt5.QtCore import QThread, pyqtSignal

from utils.json_file import JsonFile


class RemoveQuantityThread(QThread):
    """This class is a thread that removes a quantity of a product from the database."""

    signal = pyqtSignal(object)

    def __init__(
        self,
        inventory: JsonFile,
        category: str,
        inventory_prices_objects: dict,
        multiplier: int,
    ) -> None:
        """
        This function is a constructor for a class that inherits from QThread

        Args:
          inventory (JsonFile): JsonFile = The inventory object
          category (str): str = The category of the item.
          inventory_prices_objects (dict): A dictionary of objects that contain the prices of the items
        in the inventory.
          multiplier (int): int = multiplier
        """
        QThread.__init__(self)
        self.username = os.getlogin().title()
        self.category = category
        self.inventory_prices_objects = inventory_prices_objects
        self.completion_count: int = 0
        self.multiplier: int = multiplier
        self.max_item_count = inventory.get_sum_of_items()
        self.inventory = inventory

    def run(self) -> None:
        """
        It takes the current quantity of an item, subtracts the unit quantity of the item multiplied by
        the multiplier, and then sets the current quantity of the item to the result of the subtraction
        """
        self.signal.emit(f"{self.completion_count}, {self.max_item_count}")
        try:
            inventory = self.inventory.get_data()
            part_numbers = []
            for item, object_item in zip(
                list(inventory[self.category].keys()),
                list(self.inventory_prices_objects.keys()),
            ):
                unit_quantity: int = inventory[self.category][item]["unit_quantity"]
                current_quantity: int = inventory[self.category][item]["current_quantity"]
                part_numbers.append(inventory[self.category][item]["part_number"])
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
            for category in list(inventory.keys()):
                if category == self.category:
                    continue
                self.max_item_count += len(list(inventory[category].keys())) * len(
                    part_numbers
                )
                for item, part_number in itertools.product(
                    list(inventory[category].keys()), part_numbers
                ):
                    if part_number == inventory[category][item]["part_number"]:
                        unit_quantity: int = inventory[category][item]["unit_quantity"]
                        current_quantity: int = inventory[category][item][
                            "current_quantity"
                        ]
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
