import contextlib
import math
import os

import ujson as json


class JsonFile:
    def __init__(self, file_name: str = "json_file"):
        self.data = None
        self.file_name: str = file_name.replace(".json", "")
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/"
        self.__create_file()
        self.load_data()

    def __create_file(self) -> None:
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w") as json_file:
                json_file.write("{}")

    def load_data(self) -> None:
        try:
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r", encoding="utf-8") as json_file:
                self.data = json.load(json_file)
        except Exception as error:
            print(f'{self.file_name}.JsonFile.load_data: {error}')

    def __save_data(self) -> None:
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(self.data, json_file, ensure_ascii=False, indent=4)

    def save_data(self, data: dict) -> None:
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    def add_item(self, item_name: str, value) -> None:
        self.data.update({item_name: value})
        self.__save_data()

    def add_item_in_object(self, object_name: str, item_name: str) -> None:
        self.data[object_name].update({item_name: {}})
        self.__save_data()

    def add_group_to_category(self, category: str, group_name: str) -> None:
        self.data[category].update({group_name: {"group": True}})
        self.__save_data()

    def change_key_name(self, key_name: str, new_name: str) -> None:
        self.data[new_name] = self.data[key_name]
        del self.data[key_name]
        self.__save_data()

    def clone_key(self, key_name) -> None:
        clonded_data = self.data
        clonded_data[f"Clone from: {key_name} Double click me rename me"] = clonded_data[key_name]
        self.data.update(clonded_data)
        self.__save_data()

    def change_item_name(self, object_name: str, item_name: str, new_name: str) -> None:
        self.data[object_name][new_name] = self.data[object_name][item_name]
        del self.data[object_name][item_name]
        self.__save_data()

    def change_item(self, item_name: str, new_value) -> None:
        self.data.update({item_name: new_value})
        self.__save_data()

    def change_object_item(self, object_name: str, item_name: str, new_value) -> None:
        self.data[object_name][item_name] = new_value
        self.__save_data()

    def change_object_in_object_item(self, object_name: str, item_name: str, value_name: str, new_value) -> None:
        self.data[object_name][item_name][value_name] = new_value
        self.__save_data()

    def remove_item(self, item_name) -> None:
        self.data.pop(item_name)
        self.__save_data()

    def remove_object_item(self, object_name: str, item_name: str) -> None:
        del self.data[object_name][item_name]
        self.__save_data()

    def get_data(self) -> dict:
        return self.data

    def get_keys(self) -> list[str]:
        return list(self.data.keys())

    def get_value(self, item_name: str) -> None | dict[str, dict]:
        try:
            return self.data[item_name]
        except KeyError:
            return None

    def get_sum_of_items(self) -> int:
        return sum(len(self.data[category].keys()) for category in list(self.data.keys()))

    def get_total_count(self, category: str, key_name: str) -> int:
        try:
            return sum(self.data[category][item][key_name] for item in list(self.data[category].keys()))
        except Exception as error:
            return 1

    def get_exact_total_unit_count(self, category: str) -> float:
        try:
            total_count: float = math.inf
            for item in list(self.data[category].keys()):
                if self.data[category][item]["current_quantity"] / self.data[category][item]["unit_quantity"] < total_count:
                    total_count = self.data[category][item]["current_quantity"] / self.data[category][item]["unit_quantity"]
            return total_count
        except Exception as error:
            return 1

    def get_total_unit_cost(self, category: str, last_exchange_rate: float) -> float:
        total_cost: float = 0
        with contextlib.suppress(KeyError):
            for item in self.data[category]:
                use_exchange_rate: bool = self.data[category][item]["use_exchange_rate"]
                exchange_rate: float = last_exchange_rate if use_exchange_rate else 1
                price: float = self.data[category][item]["price"]
                unit_quantity: int = self.data[category][item]["unit_quantity"]
                price = max(price * unit_quantity * exchange_rate, 0)
                total_cost += price
        return total_cost

    def get_total_stock_cost(self, last_exchange_rate: float) -> float:
        total_stock_cost: float = 0.0
        all_items = {}
        for category in self.get_keys():
            for item in self.data[category]:
                all_items[self.data[category][item]["part_number"]] = {}
                all_items[self.data[category][item]["part_number"]].update(
                    {
                        "price": self.data[category][item]["price"],
                        "quantity": self.data[category][item]["current_quantity"],
                        "use_exchange_rate": self.data[category][item]["use_exchange_rate"],
                    },
                )

        for item in all_items:
            exchange_rate: float = last_exchange_rate if all_items[item]["use_exchange_rate"] else 1
            price: float = max(all_items[item]["price"] * all_items[item]["quantity"] * exchange_rate, 0)
            total_stock_cost += price
        return total_stock_cost

    def get_total_stock_cost_for_similar_categories(self, category_name: str) -> float:
        total_stock_cost: float = 0.0
        all_items = {}
        for category in self.get_keys():
            if category_name in category:
                for item in self.data[category]:
                    all_items[self.data[category][item]["part_number"]] = {}
                    all_items[self.data[category][item]["part_number"]].update(
                        {
                            "price": self.data[category][item]["price"],
                            "quantity": self.data[category][item]["current_quantity"],
                        },
                    )

        for item in all_items:
            price: float = all_items[item]["price"] * all_items[item]["quantity"]
            price = max(price, 0)
            total_stock_cost += price
        return total_stock_cost

    def check_if_value_exists_less_then(self, category: str, value_to_check: int) -> bool:
        with contextlib.suppress(KeyError):
            for item in self.data[category]:
                if self.data[category][item]["current_quantity"] <= value_to_check:
                    return True
        return False

    def sort_by_groups(self, category: dict, groups_id: str) -> dict:
        grouped_category: dict = {}

        for key, value in category.items():
            if group_name := value.get(groups_id, ""):
                grouped_category.setdefault(group_name, {})
                grouped_category[group_name][key] = value

        return grouped_category

    def sort_by_multiple_tags(self, category: dict, tags_ids: list[str]) -> dict:
        grouped_category: dict = {}

        for key, value in category.items():
            group_name = ""
            for tag_id in tags_ids:
                group_name += value.get(tag_id, "") + ";"
            grouped_category.setdefault(group_name, {})
            grouped_category[group_name][key] = value

        return grouped_category

    def sort(self, category: str, item_name: str, ascending: bool) -> None:
        if item_name == "alphabet":
            sorted_data = dict(
                sorted(
                    self.data[category].items(),
                    key=lambda x: x[0],
                    reverse=ascending,
                )
            )
        else:
            sorted_data = dict(
                sorted(
                    self.data[category].items(),
                    key=lambda x: x[1][item_name],
                    reverse=ascending,
                )
            )

        self.data[category] = sorted_data
        self.__save_data()
