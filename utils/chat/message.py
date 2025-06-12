from datetime import datetime


class Message:
    def __init__(self, user: str, text: str, date_created: str = None):
        self.user = user
        self.text = text
        self.date_created = (
            date_created
            if date_created is not None
            else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self.data = {
            "user": self.user,
            "text": self.text,
            "date_created": self.date_created,
        }

    def set_text(self, text: str):
        self.text = text

    def to_dict(self) -> dict[str, any]:
        return self.data
