from utils.workspace.tag_attributes import TagAttributes
from utils.workspace.tag_status import TagStatus


class Tag:
    def __init__(self, name, data: dict[str, dict]):
        self.name: str = name
        self.attributes: TagAttributes = None
        self.statuses: list[TagStatus] = []

        self.load_data(data)

    def add_status(self, status: TagStatus):
        self.statuses.append(status)

    def delete_status(self, status: TagStatus):
        self.statuses.remove(status)

    def load_data(self, data: dict[str, dict]):
        self.attributes = TagAttributes(data.get("attribute", {}))
        self.statuses.clear()
        for status_name, status_data in data.get("statuses", {}).items():
            status = TagStatus(status_name, status_data)
            self.statuses.append(status)

    def to_dict(self) -> dict[str, dict[str, object]]:
        return {
            "attribute": self.attributes.to_dict(),
            "statuses": {status.name: status.to_dict() for status in self.statuses},
        }

    def __str__(self):
        return f"{self.name}"
