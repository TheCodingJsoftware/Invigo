from enum import Enum
from typing import TYPE_CHECKING

from utils.workspace.tag import Tag


class Group(Enum):
    ASSEMBLY = 0
    LASER_CUT_PART = 1
    COMPONENT = 2


if TYPE_CHECKING:
    from utils.workspace.workspace_settings import WorkspaceSettings


class FlowTag:
    def __init__(self, name: str, data: list[str], workspace_settings) -> None:

        self.name = name
        self.tags: list[Tag] = []
        self.group: Group = Group.LASER_CUT_PART
        self.workspace_settings: WorkspaceSettings = workspace_settings

        self.load_data(data)

    def get_name(self) -> str:
        try:
            tags = [tag.name for tag in self.tags]
            return " ➜ ".join(tags)
        except AttributeError:  # Tag does not exist
            return "Tag name not found"

    def load_data(self, data: dict[str, str | list[str]]):
        if not data:
            return
        self.name = data.get("name", "")
        self.group = Group(data.get("group", 0))

        self.tags.clear()
        tags = data.get("tags", [])
        for tag in tags:
            tag = self.workspace_settings.get_tag(tag)
            self.add_tag(tag)

    def has_tag(self, tag_name: str) -> bool:
        return any(tag.name.lower() == tag_name.lower() for tag in self.tags)

    def add_tag(self, tag: Tag):
        self.tags.append(tag)

    def remove_tag(self, tag: Tag):
        self.tags.remove(tag)

    def __str__(self):
        return f"{self.name}: {self.get_name()}"

    def to_dict(self) -> dict[str]:
        try:
            return {
                "name": self.name,
                "group": self.group.value,
                "tags": [tag.name for tag in self.tags],
            }
        except AttributeError:  # no flow tag
            return {"name": "", "group": self.group.value, "tags": []}

    def to_list(self) -> list[str]:
        return [tag.name for tag in self.tags]
