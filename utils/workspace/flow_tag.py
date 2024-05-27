from utils.workspace.attribute import Attribute
from utils.workspace.status import Status
from utils.workspace.tag import Tag


class FlowTag:
    def __init__(self, name: str, data: list[str], workspace_settings) -> None:
        self.name = name
        self.tags: list[Tag] = []
        self.workspace_settings = workspace_settings

        self.load_data(data)

    def get_name(self) -> str:
        tags = [tag.name for tag in self.tags]
        return " ➜ ".join(tags) if "flowtag" in self.name.lower() else self.name

    def load_data(self, data: list[str]):
        for tag in data:
            tag = self.workspace_settings.get_tag(tag)
            self.add_tag(tag)

    def add_tag(self, tag: Tag):
        self.tags.append(tag)

    def remove_tag(self, tag: Tag):
        self.tags.remove(tag)

    def to_dict(self) -> list[str]:
        return [tag.name for tag in self.tags]
