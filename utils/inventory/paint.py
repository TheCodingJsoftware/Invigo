from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Optional, TypedDict, Union, cast

from utils.inventory.coating_item import CoatingItem, CoatingTypes

if TYPE_CHECKING:
    from utils.inventory.paint_inventory import PaintInventory


class PaintDataDict(TypedDict):
    uses_paint: bool
    paint_name: str
    paint_overspray: float


@dataclass
class PaintData:
    uses_paint: bool = False
    paint_name: str = ""
    paint_item: Optional[CoatingItem] = None
    paint_overspray: float = 66.67

    def __init__(self, data: Optional[PaintDataDict]):
        for f in fields(self):
            setattr(self, f.name, f.default)

        if data:
            for f in fields(self):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> PaintDataDict:
        return {
            "uses_paint": self.uses_paint,
            "paint_name": self.paint_name,
            "paint_overspray": self.paint_overspray,
        }


class Paint(CoatingItem):
    def __init__(self, data: dict[str, str | float], paint_inventory):
        super().__init__(data, paint_inventory)
        self.paint_inventory: PaintInventory = paint_inventory
        self.COATING_TYPE = CoatingTypes.PAINT
        self.average_coverage: float = 300.0
        self.load_data(data)

    def load_data(self, data: dict[str, Union[str, int, float, bool]]):
        super().load_data(data)
        self.average_coverage = data.get("average_coverage", 300)

    def to_dict(self) -> dict[str, dict]:
        data = super().to_dict()
        data.update(
            {
                "average_coverage": self.average_coverage,
                "coating_type": self.COATING_TYPE.value,
            }
        )
        return data
