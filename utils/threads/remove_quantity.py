import itertools
import os
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal

from utils.json_file import JsonFile


class RemoveQuantityThread(QThread):
    """This class is a thread that removes a quantity of a product from the database."""

    signal = pyqtSignal(object)

    def __init__(
        self,
        inventory: JsonFile,
        category: str,
        multiplier: int,
    ):
        QThread.__init__(self)
        self.username = os.getlogin().title()
        self.category = category
        self.completion_count: int = 0
        self.multiplier: int = multiplier
        self.max_item_count = inventory.get_sum_of_items()
        self.inventory = inventory

    def run(self):
        print("thread running")
        self.signal.emit(f"{self.completion_count}, {self.max_item_count}")
        try:
            inventory = self.inventory.get_data()
            part_numbers = []
            for item in list(inventory[self.category].keys()):
                unit_quantity: int = inventory[self.category][item]["unit_quantity"]
                current_quantity: int = inventory[self.category][item]["current_quantity"]
                part_numbers.append(inventory[self.category][item]["part_number"])
                inventory[self.category][item]["current_quantity"] = current_quantity - (unit_quantity * self.multiplier)
                inventory[self.category][item]["latest_change_current_quantity"] = f"{self.username} - Changed from {current_quantity} to {current_quantity - (unit_quantity * self.multiplier)} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                self.completion_count += 1
                # self.signal.emit(f"{self.completion_count}, {self.max_item_count}")
            part_numbers = list(set(part_numbers))
            for category in self.inventory.get_keys():
                if category == self.category:
                    continue
                self.max_item_count += len(list(inventory[category].keys())) * len(part_numbers)
            for category in self.inventory.get_keys():
                if category == self.category:
                    continue
                for item, part_number in itertools.product(list(inventory[category].keys()), part_numbers):
                    if part_number == inventory[category][item]["part_number"]:
                        unit_quantity: int = inventory[category][item]["unit_quantity"]
                        current_quantity: int = inventory[category][item]["current_quantity"]
                        inventory[category][item]["current_quantity"] = current_quantity - (unit_quantity * self.multiplier)
                        inventory[category][item]["latest_change_current_quantity"] = f"{self.username} - Changed from {current_quantity} to {current_quantity - (unit_quantity * self.multiplier)} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                    self.completion_count += 1
                    # self.signal.emit(f"{self.completion_count}, {self.max_item_count}")
            self.inventory.save_data(inventory)
            self.signal.emit("Done")
            print("thread done")
        except Exception as error:
            print(error)
            self.signal.emit(error)
