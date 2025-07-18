from typing import TypedDict

from utils.workspace.tag_attributes import TagAttributes, TagAttributesDict
from utils.workspace.tag_status import TagStatus, TagStatusDict


class TagDict(TypedDict):
    attribute: TagAttributesDict
    statuses: dict[str, TagStatusDict]


class Tag:
    def __init__(self, name, data: TagDict):
        self.name: str = name
        self.attributes: TagAttributes = None
        self.statuses: list[TagStatus] = []

        self.load_data(data)

    def add_status(self, status: TagStatus):
        self.statuses.append(status)

    def delete_status(self, status: TagStatus):
        self.statuses.remove(status)

    def load_data(self, data: TagDict):
        self.attributes = TagAttributes(data.get("attribute", {}))
        self.statuses.clear()
        for status_name, status_data in data.get("statuses", {}).items():
            status = TagStatus(status_name, status_data)
            self.statuses.append(status)

    def to_dict(self) -> TagDict:
        return {
            "attribute": self.attributes.to_dict(),
            "statuses": {status.name: status.to_dict() for status in self.statuses},
        }

    def __str__(self):
        return f"{self.name}"
