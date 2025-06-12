class TagAttributes:
    def __init__(self, data: dict[str, float | str]):
        self.expected_time_to_complete = 0.0
        self.next_flow_tag_message = ""
        self.load_data(data)

    def load_data(self, data: dict[str, float | str]):
        self.expected_time_to_complete = data.get("expected_time_to_complete", 0.0)
        self.next_flow_tag_message = data.get("next_flow_tag_message", "")

    def to_dict(self) -> dict[str, float | str]:
        return {
            "expected_time_to_complete": self.expected_time_to_complete,
            "next_flow_tag_message": self.next_flow_tag_message,
        }
