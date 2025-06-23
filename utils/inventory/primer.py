from typing import TYPE_CHECKING, Union

from utils.inventory.coating_item import CoatingItem, CoatingTypes

if TYPE_CHECKING:
    from utils.inventory.paint_inventory import PaintInventory


class Primer(CoatingItem):
    def __init__(self, data: dict[str, str | float], paint_inventory):
        super().__init__(paint_inventory)
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
