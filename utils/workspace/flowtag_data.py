from typing import TypedDict

from utils.workspace.flowtag import Flowtag
from utils.workspace.tag import Tag


class TagDataDict(TypedDict):
    expected_time_to_complete: float


FlowtagDataDict = dict[str, TagDataDict]


class FlowtagData:
    def __init__(self, flowtag: Flowtag):
        self.flowtag: Flowtag = flowtag
        self.workspace_settings = self.flowtag.workspace_settings
        self.tags_data: dict[Tag, TagDataDict] = {}

    def load_data(self, data: FlowtagDataDict):
        self.tags_data.clear()
        for tag in self.flowtag.tags:
            if workspace_tag := self.workspace_settings.get_tag(tag.name):
                tag_data = data.get(
                    tag.name,
                    {
                        "expected_time_to_complete": workspace_tag.attributes.expected_time_to_complete,
                    },
                )
                self.tags_data.update({tag: tag_data})

    def get_tag(self, tag_name: str) -> Tag | None:
        return next((tag for tag in self.tags_data if tag.name == tag_name), None)

    def set_tag_data(self, tag_name: Tag | str, key: str, value: float):
        if isinstance(tag_name, Tag):
            self.tags_data.setdefault(tag_name, {"expected_time_to_complete": 0.0})
            self.tags_data[tag_name][key] = value
        elif isinstance(tag_name, str):
            if tag := self.get_tag(tag_name):
                self.tags_data.setdefault(tag, {"expected_time_to_complete": 0.0})
                self.tags_data[tag][key] = value

    def get_tag_data(self, tag_name: Tag | str, key: str) -> float | None:
        if isinstance(tag_name, Tag):
            return self.tags_data[tag_name][key]
        elif isinstance(tag_name, str):
            if tag := self.get_tag(tag_name):
                return self.tags_data[tag][key]
        return None

    def to_dict(self) -> FlowtagDataDict:
        return {tag.name: tag_data for tag, tag_data in self.tags_data.items()}
