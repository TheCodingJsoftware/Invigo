from dataclasses import dataclass
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from utils.purchase_order.purchase_order import PurchaseOrder


class OrderDict(TypedDict):
    purchase_order_id: int
    expected_arrival_time: str
    order_pending_quantity: float
    order_pending_date: str
    notes: str


@dataclass
class Order:
    purchase_order_id: int = -1
    expected_arrival_time: str = ""
    quantity: float = 0.0
    order_pending_date: str = ""
    notes: str = ""

    def __init__(self, data: OrderDict):
        self._purchase_order: "PurchaseOrder | None" = None
        self.load_data(data)

    def get_purchase_order(self) -> "PurchaseOrder | None":
        return self._purchase_order

    def set_purchase_order(self, purchase_order: "PurchaseOrder") -> None:
        self._purchase_order = purchase_order

    def load_data(self, data: OrderDict) -> None:
        self.purchase_order_id = data.get("purchase_order_id", -1)
        self.expected_arrival_time = data.get("expected_arrival_time", "")
        self.quantity = data.get("order_pending_quantity", 0.0)
        self.order_pending_date = data.get("order_pending_date", "")
        self.notes = data.get("notes", "No notes provided") or "No notes provided"

    def __str__(self) -> str:
        if self._purchase_order:
            po_str = f"Purchase Order: {self._purchase_order.meta_data.vendor.name} #{self._purchase_order.meta_data.purchase_order_number}\n"
            if self._purchase_order.components:
                po_str += f"Includes {len(self._purchase_order.components)} component(s)\n"
            if self._purchase_order.sheets:
                po_str += f"Includes {len(self._purchase_order.sheets)} sheet(s)\n"
        else:
            po_str = "Purchase Order: None\n"

        details = []
        if self.order_pending_date:
            details.append(f"Order pending since: {self.order_pending_date}")
        if self.quantity:
            details.append(f"Quantity ordered: {self.quantity}")
        if self.expected_arrival_time:
            details.append(f"Expected to arrive: {self.expected_arrival_time}")

        notes_str = f"Notes:\n{self.notes}" if self.notes else "Notes: None"

        return po_str + "\n".join(details) + f"\n{notes_str}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Order):
            return NotImplemented
        return (
            self.expected_arrival_time == other.expected_arrival_time
            and self.quantity == other.quantity
            and self.order_pending_date == other.order_pending_date
            and self.notes == other.notes
        )

    def to_dict(self) -> OrderDict:
        return {
            "purchase_order_id": self._purchase_order.id if self._purchase_order else -1,
            "expected_arrival_time": self.expected_arrival_time,
            "order_pending_quantity": self.quantity,
            "order_pending_date": self.order_pending_date,
            "notes": self.notes,
        }
