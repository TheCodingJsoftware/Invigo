import copy
from typing import Any, Union


class Item:
    def __init__(self, **kwargs: Union[str, object]) -> None:
        self.name: str = kwargs.get("name")
        self.data: dict = kwargs.get("data")
        self.parent_assembly = None
        self.master_assembly = None

    def set_data(self, data: object) -> None:
        self.data = data

    def set_value(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get_value(self, key: str) -> Any:
        try:
            return self.data[key]
        except KeyError:
            return None

    def delete_value(self, key: str) -> Any:
        try:
            value_copy = self.data[key]
            del self.data[key]
            return value_copy
        except KeyError:
            return None

    def copy_data(self) -> dict:
        return copy.deepcopy(self.data)

    def rename(self, new_name: str) -> None:
        self.name = new_name

    def set_timer(self, flow_tag: str, time: object) -> None:
        self.data["timers"][flow_tag]["time_to_complete"] = time.value()

    def get_timer(self, flow_tag: str) -> float:
        self.data["timers"][flow_tag]['time_to_complete"']

    def to_dict(self) -> dict[str, object]:
        return self.data
