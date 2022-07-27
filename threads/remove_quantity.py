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
                self.value_change(
                    category=self.category,
                    item_name=item,
                    value_name="current_quantity",
                    new_value=current_quantity - (unit_quantity * self.multiplier),
                )
                spin_current_quantity.setValue(
                    int(current_quantity - (unit_quantity * self.multiplier))
                )
                self.completion_count += 1
                self.signal.emit(f"{self.completion_count}, {self.max_item_count}")
                QtTest.QTest.qWait(50)
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
                        self.value_change(
                            category=category,
                            item_name=item,
                            value_name="current_quantity",
                            new_value=current_quantity
                            - (unit_quantity * self.multiplier),
                        )
                    self.completion_count += 1
                    self.signal.emit(f"{self.completion_count}, {self.max_item_count}")
                    QtTest.QTest.qWait(50)

            self.signal.emit("Done")
        except Exception as error:
            self.signal.emit(error)

    def value_change(
        self, category: str, item_name: str, value_name: str, new_value
    ) -> None:
        """
        It changes the value of a value in a dictionary in a dictionary in a dictionary.

        Args:
          category (str): str = "category"
          item_name (str): str = the name of the item
          value_name (str): str = "current_quantity"
          new_value: str
        """

        # threading.Thread(
        #     target=self.inventory.change_object_in_object_item,
        #     args=(category, item_name, value_name, new_value),
        # ).start()
        self.inventory.change_object_in_object_item(
            object_name=category,
            item_name=item_name,
            value_name=value_name,
            new_value=new_value,
        )
        if value_name == "current_quantity":
            value_before = self.inventory.get_value(item_name=category)[item_name][
                "current_quantity"
            ]
            # threading.Thread(
            #     target=self.inventory.change_object_in_object_item,
            #     args=(
            #         category,
            #         item_name,
            #         "latest_change_current_quantity",
            #         f"Latest Change:\nfrom: {value_before}\nto: {new_value}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
            #     ),
            # ).start()
            self.inventory.change_object_in_object_item(
                category,
                item_name,
                "latest_change_current_quantity",
                f"Latest Change:\nfrom: {value_before}\nto: {new_value}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
            )
