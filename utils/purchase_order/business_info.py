from dataclasses import dataclass, field, fields
from typing import TypedDict, cast

import msgspec

from config.environments import Environment


class BusinessInfoDict(TypedDict):
    name: str
    email: str
    phone: str
    address: str
    pst_number: str
    gst_number: str
    pst_rate: float
    gst_rate: float
    business_number: str


@dataclass
class BusinessInfo:
    name: str = field(default_factory=str)
    email: str = field(default_factory=str)
    phone: str = field(default_factory=str)
    address: str = field(default_factory=str)
    pst_number: str = field(default_factory=str)
    gst_number: str = field(default_factory=str)
    pst_rate: float = field(default=7.0)
    gst_rate: float = field(default=5.0)
    business_number: str = field(default_factory=str)

    def __init__(self, data: BusinessInfoDict | None = None):
        if data:
            self.load_data(data)
        else:
            self.load_data_from_file()

    def save_data(self):
        with open(f"{Environment.DATA_PATH}/business_info.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data_from_file(self):
        try:
            with open(f"{Environment.DATA_PATH}/business_info.json", "rb") as file:
                data = msgspec.json.decode(file.read())
                self.load_data(data)
        except FileNotFoundError:
            self.set_default_values()

    def set_default_values(self):
        self.name = ""
        self.email = ""
        self.phone = ""
        self.address = ""
        self.business_number = ""
        self.pst_number = ""
        self.gst_number = ""
        self.pst_rate = 7.0
        self.gst_rate = 5.0

    def load_data(self, data: BusinessInfoDict) -> None:
        self.name = data.get("name", "")
        self.email = data.get("email", "")
        self.phone = data.get("phone", "")
        self.address = data.get("address", "")
        self.pst_number = data.get("pst_number", "")
        self.gst_number = data.get("gst_number", "")
        self.pst_rate = float(data.get("pst_rate", 7.0))
        self.gst_rate = float(data.get("gst_rate", 5.0))
        self.business_number = data.get("business_number", "")

    def to_dict(self) -> BusinessInfoDict:
        return cast(BusinessInfoDict, {f.name: getattr(self, f.name) for f in fields(self)})
