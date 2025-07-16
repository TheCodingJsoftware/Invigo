from dataclasses import dataclass, field, fields
from typing import TypedDict, cast


class VendorDict(TypedDict):
    id: int
    name: str
    address: str
    phone: str
    email: str
    website: str
    notes: str


@dataclass
class Vendor:
    id: int = field(default_factory=int)
    name: str = field(default_factory=str)
    address: str = field(default_factory=str)
    phone: str = field(default_factory=str)
    email: str = field(default_factory=str)
    website: str = field(default_factory=str)
    notes: str = field(default_factory=str)

    def __init__(self, data: VendorDict | None = None):
        if data:
            self.load_data(data)
        else:
            self.id = 0
            self.name = ""
            self.address = ""
            self.phone = ""
            self.email = ""
            self.website = ""
            self.notes = ""

    def __str__(self) -> str:
        parts = []
        if self.name:
            parts.append(f"Name: {self.name}")
        if self.address:
            parts.append(f"Address: {self.address}")
        if self.phone:
            parts.append(f"Phone: {self.phone}")
        if self.email:
            parts.append(f"Email: {self.email}")
        if self.website:
            parts.append(f"Website: {self.website}")
        if self.notes:
            parts.append(f"Notes: {self.notes}")
        return "\n".join(parts)

    def load_data(self, data: VendorDict) -> None:
        self.id = data.get("id", 0)
        self.name = data.get("name", "")
        self.address = data.get("address", "")
        self.phone = data.get("phone", "")
        self.email = data.get("email", "")
        self.website = data.get("website", "")
        self.notes = data.get("notes", "")

    def to_dict(self) -> VendorDict:
        return cast(VendorDict, {f.name: getattr(self, f.name) for f in fields(self)})
