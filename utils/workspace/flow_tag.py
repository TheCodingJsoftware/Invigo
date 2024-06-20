from enum import Enum
from utils.workspace.tag import Tag

class Group(Enum):
    ASSEMBLY = 0
    LASER_CUT_PART = 1
    COMPONENT = 2

class FlowTag:
    def __init__(self, name: str, data: list[str], workspace_settings) -> None:
        from utils.workspace.workspace_settings import WorkspaceSettings

        self.name = name
        self.tags: list[Tag] = []
        self.group: Group = Group.LASER_CUT_PART
        self.workspace_settings: WorkspaceSettings = workspace_settings

        self.load_data(data)

    def get_name(self) -> str:
        tags = [tag.name for tag in self.tags]
        return " ➜ ".join(tags)

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
        return {"name": self.name, "group": self.group.value, "tags": [tag.name for tag in self.tags]}

    def to_list(self) -> list[str]:
        return [tag.name for tag in self.tags]
