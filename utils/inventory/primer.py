from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Optional, TypedDict, Union, cast

from utils.inventory.coating_item import CoatingItem, CoatingTypes

if TYPE_CHECKING:
    from utils.inventory.paint_inventory import PaintInventory


class PrimerDataDict(TypedDict):
    uses_primer: bool
    primer_name: str
    primer_overspray: float


@dataclass
class PrimerData:
    uses_primer: bool = False
    primer_name: str = ""
    primer_item: Optional[CoatingItem] = None
    primer_overspray: float = 66.67

    def __init__(self, data: Optional[PrimerDataDict]):
        for f in fields(self.__class__):
            setattr(self, f.name, f.default)

        if data:
            for f in fields(self.__class__):
                if f.name in data:
                    setattr(self, f.name, data[f.name])

    def to_dict(self) -> PrimerDataDict:
        return {
            "uses_primer": self.uses_primer,
            "primer_name": self.primer_name,
            "primer_overspray": self.primer_overspray,
        }


class Primer(CoatingItem):
    def __init__(self, data: dict[str, str | float], paint_inventory):
        super().__init__(data, paint_inventory)
        self.paint_inventory: PaintInventory = paint_inventory
        self.COATING_TYPE = CoatingTypes.PRIMER
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
