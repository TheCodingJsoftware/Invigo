import json
import os


class JsonFile:
    """
    Json data file handler
    """

    def __init__(self, file_name: str = "json_file"):
        self.data = None
        self.file_name: str = file_name.replace(".json", "")
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/"
        self.__create_file()
        self.__load_data()

    def __create_file(self) -> None:
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w") as json_file:
                json_file.write("{}")

    def __load_data(self) -> None:
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "r") as json_file:
            self.data = json.load(json_file)

    def __save_data(self):
        with open(
            f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w", encoding="utf-8"
        ) as json_file:
            json.dump(self.data, json_file, ensure_ascii=False, indent=4)

    def add_item(self, item_name: str, value) -> None:
        self.__load_data()
        self.data.update({item_name: value})
        self.__save_data()

    def change_item(self, item_name: str, new_value) -> None:
        self.__load_data()
        self.data.update({item_name: new_value})
        self.__save_data()

    def change_item(self, object_name: str, item_name: str, new_value) -> None:
        self.__load_data()
        self.data[object_name][item_name] = new_value
        self.__save_data()

    def remove_item(self, item_name) -> None:
        self.__load_data()
        self.data.pop(item_name)
        self.__save_data()

    def get_value(self, item_name: str) -> None:
        self.__load_data()
        try:
            return self.data[item_name]
        except KeyError:
            return None
