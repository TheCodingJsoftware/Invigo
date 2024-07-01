class Order:
    def __init__(self, data: dict[str, str | float]):
        self.expected_arrival_time: str = ""
        self.quantity: float = 0.0
        self.order_pending_date: str = ""
        self.notes: str = ""
        self.load_data(data)

    def load_data(self, data: dict[str, str | float]):
        self.expected_arrival_time = data.get("expected_arrival_time", "")
        self.quantity = data.get("order_pending_quantity", 0.0)
        self.order_pending_date = data.get("order_pending_date", "")
        self.notes = data.get("notes", "No notes provided") or "No notes provided"

    def __str__(self) -> str:
        return f"Order is pending since: {self.order_pending_date}\nQuantity ordered: {self.quantity}\nExpected to arrive at: {self.expected_arrival_time}\nNotes:\n{self.notes}"

    def __eq__(self, other: "Order") -> bool:
        if not isinstance(other, Order):
            return False
        return self.expected_arrival_time == other.expected_arrival_time and self.quantity == other.quantity and self.order_pending_date == other.order_pending_date and self.notes == other.notes

    def to_dict(self) -> dict:
        return {"expected_arrival_time": self.expected_arrival_time, "order_pending_quantity": self.quantity, "order_pending_date": self.order_pending_date, "notes": self.notes}
