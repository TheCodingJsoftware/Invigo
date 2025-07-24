from dataclasses import dataclass, field, fields
from typing import TypedDict, cast

import msgspec
from cryptography.fernet import Fernet

from config.environments import Environment


class ContactInfoDict(TypedDict):
    name: str
    phone: str
    email: str
    password: str


@dataclass
class ContactInfo:
    name: str = field(default_factory=str)
    phone: str = field(default_factory=str)
    email: str = field(default_factory=str)
    password: str = field(default_factory=str)

    def __init__(self, data: ContactInfoDict | None = None):
        if data:
            self.load_data(data)
        else:
            self.load_data_from_file()

    def _get_cipher(self) -> Fernet:
        with open(f"{Environment.DATA_PATH}/.contact_key", "rb") as f:
            key = f.read()
        return Fernet(key)

    def encrypt_password(self, plain: str) -> str:
        return self._get_cipher().encrypt(plain.encode()).decode()

    def decrypt_password(self, encrypted: str) -> str:
        return self._get_cipher().decrypt(encrypted.encode()).decode()

    def save_data(self):
        with open(f"{Environment.DATA_PATH}/contact_info.json", "wb") as file:
            file.write(msgspec.json.encode(self.to_dict()))

    def load_data_from_file(self):
        try:
            with open(f"{Environment.DATA_PATH}/contact_info.json", "rb") as file:
                data = msgspec.json.decode(file.read())
                self.load_data(data, encrypted=True)
        except FileNotFoundError:
            self.name = ""
            self.phone = ""
            self.email = ""
            self.password = ""

    def load_data(self, data: ContactInfoDict, *, encrypted: bool = False) -> None:
        self.name = data.get("name", "")
        self.phone = data.get("phone", "")
        self.email = data.get("email", "")
        raw_password = data.get("password", "")
        self.password = self.decrypt_password(raw_password) if encrypted and raw_password else raw_password

    def to_dict(self) -> ContactInfoDict:
        return {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "password": self.encrypt_password(self.password) if self.password else "",
        }
