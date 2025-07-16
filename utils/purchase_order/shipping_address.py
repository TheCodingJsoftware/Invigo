from dataclasses import dataclass, field, fields
from typing import TypedDict, cast


class ShippingAddressDict(TypedDict):
    id: int
    name: str
    email: str
    phone: str
    address: str
    website: str
    notes: str


@dataclass
class ShippingAddress:
    id: int = field(default_factory=int)
    name: str = field(default_factory=str)
    email: str = field(default_factory=str)
    phone: str = field(default_factory=str)
    address: str = field(default_factory=str)
    website: str = field(default_factory=str)
    notes: str = field(default_factory=str)

    def __init__(self, data: ShippingAddressDict | None = None):
        if data:
            self.load_data(data)
        else:
            self.set_default_values()

    def set_default_values(self):
        self.id = 0
        self.name = ""
        self.email = ""
        self.phone = ""
        self.address = ""
        self.website = ""
        self.notes = ""

    def load_data(self, data: ShippingAddressDict) -> None:
        self.id = data.get("id", 0)
        self.name = data.get("name", "")
        self.email = data.get("email", "")
        self.phone = data.get("phone", "")
        self.address = data.get("address", "")
        self.website = data.get("website", "")
        self.notes = data.get("notes", "")

    def __str__(self) -> str:
        parts = []
        if self.name:
            parts.append(f"Name: {self.name}")
        if self.email:
            parts.append(f"Email: {self.email}")
        if self.phone:
            parts.append(f"Phone: {self.phone}")
        if self.address:
            parts.append(f"Address: {self.address}")
        if self.website:
            parts.append(f"Website: {self.website}")
        if self.notes:
            parts.append(f"Notes: {self.notes}")
        return "\n".join(parts)

    def to_dict(self) -> ShippingAddressDict:
        return cast(ShippingAddressDict, {f.name: getattr(self, f.name) for f in fields(self)})
