import os

import msgspec

from utils.chat.chat import Chat


class ChatFile:
    def __init__(self, file_name: str):
        self.file_name: str = file_name
        self.chats: list[Chat] = []
        self.chat_data: dict[str, Chat] = {}
        self.FOLDER_LOCATION: str = f"{os.getcwd()}/data"
        self.__create_file()
        self.load_data()

    def __create_file(self):
        if not os.path.exists(f"{self.FOLDER_LOCATION}/{self.file_name}.json"):
            with open(
                f"{self.FOLDER_LOCATION}/{self.file_name}.json", "w"
            ) as json_file:
                json_file.write("{}")

    def load_chat(self, chat_name: str, chat_data: dict[str, any]) -> Chat:
        chat = Chat(id=chat_name, name=chat_data["chat_data"]["display_name"])
        chat.set_messages(chat_data["messages"])
        chat.set_chat_data(chat_data["chat_data"])
        return chat

    def save(self):
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data(self):
        self.chats.clear()
        with open(f"{self.FOLDER_LOCATION}/{self.file_name}.json", "rb") as file:
            data = msgspec.json.decode(file.read())
        for chat_name in data:
            self.add_chat(self.load_chat(chat_name, data[chat_name]))

    def add_chat(self, chat: Chat):
        self.chats.append(chat)

    def to_dict(self) -> dict[str, dict[str, any]]:
        return {chat.id: chat.to_dict() for chat in self.chats}
