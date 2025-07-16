from dataclasses import dataclass, field, fields
from typing import TypedDict, cast

import msgspec

from config.environments import Environment


class ContactInfoDict(TypedDict):
    name: str
    phone: str
    email: str


@dataclass
class ContactInfo:
    name: str = field(default_factory=str)
    phone: str = field(default_factory=str)
    email: str = field(default_factory=str)

    def __init__(self, data: ContactInfoDict | None = None):
        if data:
            self.load_data(data)
        else:
            self.load_data_from_file()

    def save_data(self):
        with open(f"{Environment.DATA_PATH}/contact_info.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data_from_file(self):
        try:
            with open(f"{Environment.DATA_PATH}/contact_info.json", "rb") as file:
                data = msgspec.json.decode(file.read())
                self.load_data(data)
        except FileNotFoundError:
            self.name = ""
            self.phone = ""
            self.email = ""

    def load_data(self, data: ContactInfoDict) -> None:
        self.name = data.get("name", "")
        self.phone = data.get("phone", "")
        self.email = data.get("email", "")

    def to_dict(self) -> ContactInfoDict:
        return cast(ContactInfoDict, {f.name: getattr(self, f.name) for f in fields(self)})
