class Item:
    def __init__(self, name: str) -> None:
        self.name = name
        self.data = {}

    def set_data(self, data: object) -> None:
        self.data = data

    def rename(self, new_name: str) -> None:
        self.name = new_name

    def to_dict(self) -> dict:
        return self.data
