from typing import TYPE_CHECKING, Union

from utils.inventory.coating_item import CoatingItem, CoatingTypes

if TYPE_CHECKING:
    from utils.inventory.paint_inventory import PaintInventory


class Powder(CoatingItem):
    def __init__(self, data: dict[str, str | float], paint_inventory):
        super().__init__(paint_inventory)
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
