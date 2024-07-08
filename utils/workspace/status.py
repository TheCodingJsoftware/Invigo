class Status:
    def __init__(self, name: str, data: dict[str, bool]) -> None:
        self.name = name
        self.completed: bool = False
        self.start_timer: bool = False
        self.next_flow_tag_message: str = ""
        self.load_data(data)

    def load_data(self, data: dict[str, bool]):
        self.completed = data.get("completed", False)
        self.start_timer = data.get("start_timer", False)
        self.next_flow_tag_message = data.get("next_flow_tag_message", "")

    def to_dict(self) -> dict[str, bool]:
        return {
            "completed": self.completed,
            "start_timer": self.start_timer,
            "next_flow_tag_message": self.next_flow_tag_message,
        }
