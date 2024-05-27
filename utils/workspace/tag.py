from utils.workspace.attribute import Attribute
from utils.workspace.status import Status


class Tag:
    def __init__(self, name, data: dict[str, dict]) -> None:
        self.name: str = name
        self.attribute: Attribute = None
        self.statuses: list[Status] = []

        self.load_data(data)

    def add_status(self, status: Status):
        self.statuses.append(status)

    def delete_status(self, status: Status):
        self.statuses.remove(status)

    def load_data(self, data: dict[str, dict]):
        self.attribute = Attribute(data.get("attribute", {}))
        self.statuses.clear()
        for status_name, status_data in data.get("statuses", {}).items():
            status = Status(status_name, status_data)
            self.statuses.append(status)

    def to_dict(self) -> dict[str, dict[str, object]]:
        return {
            "attribute": self.attribute.to_dict(),
            "statuses": {status.name: status.to_dict() for status in self.statuses},
        }
