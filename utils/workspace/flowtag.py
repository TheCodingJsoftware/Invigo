from enum import Enum
from typing import TYPE_CHECKING, Iterator, Union

from utils.workspace.tag import Tag


class Group(Enum):
    ASSEMBLY = 0
    LASER_CUT_PART = 1
    COMPONENT = 2


if TYPE_CHECKING:
    from utils.workspace.workspace_settings import WorkspaceSettings


class Flowtag:
    def __init__(self, name: str, data: list[str], workspace_settings):
        self.name = name
        self.tags: list[Tag] = []
        self.group: Group = Group.LASER_CUT_PART
        self.workspace_settings: WorkspaceSettings = workspace_settings
        self.add_quantity_tag: Tag = None
        self.remove_quantity_tag: Tag = None

        self.load_data(data)

    def get_name(self) -> str:
        try:
            tags = [tag.name for tag in self.tags]
            return " ➜ ".join(tags)
        except Exception:  # Tag does not exist
            return "Tag name not found"

    def load_data(self, data: dict[str, Union[str, list[str]]]):
        if not data:
            return
        self.name = data.get("name", "")
        self.group = Group(data.get("group", 0))

        self.add_quantity_tag = self.workspace_settings.get_tag(data.get("add_quantity_tag"))
        self.remove_quantity_tag = self.workspace_settings.get_tag(data.get("remove_quantity_tag"))

        self.tags.clear()
        tags = data.get("tags", [])
        for tag in tags:
            tag = self.workspace_settings.get_tag(tag)
            self.add_tag(tag)

    def has_tag(self, tag_name: str) -> bool:
        return any(tag.name.lower() == tag_name.lower() for tag in self.tags)

    def contains(self, texts: list[str]) -> bool:
        for text in texts:
            for tag in self.tags:
                if text.lower() in tag.name.lower():
                    return True
        return False

    def add_tag(self, tag: Tag):
        self.tags.append(tag)

    def remove_tag(self, tag: Tag):
        self.tags.remove(tag)

    def __str__(self):
        return f"{self.name}: {self.get_name()}"

    def __iter__(self) -> Iterator[Tag]:
        return iter(self.tags)

    def to_dict(self) -> dict[str]:
        try:
            return {
                "name": self.name,
                "group": self.group.value,
                "add_quantity_tag": self.add_quantity_tag.name if self.add_quantity_tag else None,
                "remove_quantity_tag": self.remove_quantity_tag.name if self.remove_quantity_tag else None,
                "tags": [tag.name for tag in self.tags],
            }
        except AttributeError:  # no flow tag
            return {
                "name": "",
                "group": self.group.value,
                "add_quantity_tag": self.add_quantity_tag.name if self.add_quantity_tag else None,
                "remove_quantity_tag": self.remove_quantity_tag.name if self.remove_quantity_tag else None,
                "tags": [],
            }

    def to_list(self) -> list[str]:
        return [tag.name for tag in self.tags]
