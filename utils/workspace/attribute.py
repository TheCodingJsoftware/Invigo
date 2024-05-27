class Attribute:
    def __init__(self, data: dict[str, bool | str]) -> None:
        self.show_all_items: bool = False
        self.is_timer_enabled: bool = False
        self.next_flow_tag_message: str = ""
        self.load_data(data)

    def load_data(self, data: dict[str, bool | str]):
        self.show_all_items = data.get("show_all_items", False)
        self.is_timer_enabled = data.get("is_timer_enabled", False)
        self.next_flow_tag_message = data.get("next_flow_tag_message", "")

    def to_dict(self) -> dict[str, bool | str]:
        return {
            "show_all_items": self.show_all_items,
            "is_timer_enabled": self.is_timer_enabled,
            "next_flow_tag_message": self.next_flow_tag_message,
        }
