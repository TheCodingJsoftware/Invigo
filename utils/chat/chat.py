from datetime import datetime

from message import Message


class Chat:
    def __init__(self, id: str = None, name: str = "") -> None:
        self.id = id if id is not None else f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")} - {name}'
        self.display_name: str = name
        self.messages: list[Message] = []
        self.data: dict[str, str, str, list[Message]] = {
            "messages": self.messages,
            "chat_data": {"date_created": f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}', "display_name": self.display_name},
        }

    def set_display_name(self, chat_name: str):
        self.display_name = chat_name

    def set_chat_data(self, chat_data: dict):
        self.data["chat_data"] = chat_data

    def set_messages(self, message_data: list[dict[str, any]]):
        messages: list[Message] = []
        for message in message_data:
            user = message["user"]
            text = message["text"]
            date_created = message["date_created"]
            m = Message(user, text, date_created)
            messages.append(m)
        self.messages = messages

    def add_message(self, user: str, text: str):
        self.messages.append(Message(user, text))

    def to_dict(self) -> dict[str, list[dict[str, any]]]:
        data = {"messages": [], 'chat_data': self.data['chat_data']}
        messages_data = []
        for message in self.messages:
            messages_data.append(message.to_dict())
        data["messages"] = messages_data
        return data
