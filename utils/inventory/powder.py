from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Optional, TypedDict, Union, cast

from utils.inventory.coating_item import CoatingItem, CoatingTypes

if TYPE_CHECKING:
    from utils.inventory.paint_inventory import PaintInventory


class PowderDataDict(TypedDict):
    uses_powder: bool
    powder_name: str
    powder_transfer_efficiency: float


@dataclass
class PowderData:
    uses_powder: bool = False
    powder_name: str = ""
    powder_item: Optional[CoatingItem] = None
    powder_transfer_efficiency: float = 66.67

    def __init__(self, data: Optional[PowderDataDict]):
        for f in fields(self):
            setattr(self, f.name, f.default)

        if data:
            for f in fields(self):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> PowderDataDict:
        return {
            "uses_powder": self.uses_powder,
            "powder_name": self.powder_name,
            "powder_transfer_efficiency": self.powder_transfer_efficiency,
        }


class Powder(CoatingItem):
    def __init__(self, data: dict[str, str | float], paint_inventory):
        super().__init__(data, paint_inventory)
        self.paint_inventory: PaintInventory = paint_inventory
        self.COATING_TYPE = CoatingTypes.POWDER
        self.gravity: float = 2.0
        self.load_data(data)

    def load_data(self, data: dict[str, Union[str, int, float, bool]]):
        super().load_data(data)
        self.gravity = data.get("gravity", 2.0)

    def to_dict(self) -> dict[str, dict]:
        data = super().to_dict()
        data.update(
            {
                "gravity": self.gravity,
                "coating_type": self.COATING_TYPE.value,
            }
        )
        return data
