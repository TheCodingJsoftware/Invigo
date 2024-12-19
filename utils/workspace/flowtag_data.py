from typing import Optional, Union

from utils.workspace.flowtag import Flowtag
from utils.workspace.tag import Tag


class FlowtagData:
    def __init__(self, flowtag: Flowtag):
        self.flowtag: Flowtag = flowtag
        self.workspace_settings = self.flowtag.workspace_settings

        self.tags_data: dict[Tag, dict[str, int]] = {}

    def load_data(self, data: dict[str, dict[str, str]]):
        self.tags_data.clear()
        for tag in self.flowtag.tags:
            tag_data = data.get(
                tag.name,
                {
                    "expected_time_to_complete": self.workspace_settings.get_tag(
                        tag.name
                    ).attributes.expected_time_to_complete
                },
            )
            self.tags_data.update({tag: tag_data})

    def get_tag(self, tag_name: str) -> Optional[Tag]:
        for tag in self.tags_data:
            if tag.name == tag_name:
                return tag
        return None

    def set_tag_data(self, tag_name: Union[Tag, str], key: str, value: float):
        if isinstance(tag_name, Tag):
            self.tags_data.setdefault(tag_name, {"expected_time_to_complete": 0})
            self.tags_data[tag_name][key] = value
        elif isinstance(tag_name, str):
            if tag := self.get_tag(tag_name):
                self.tags_data.setdefault(tag_name, {"expected_time_to_complete": 0})
                self.tags_data[tag][key] = value

    def get_tag_data(self, tag_name: Union[Tag, str], key: str) -> Optional[float]:
        if isinstance(tag_name, Tag):
            return self.tags_data[tag_name][key]
        elif isinstance(tag_name, str):
            if tag := self.get_tag(tag_name):
                return self.tags_data[tag][key]
        return None

    def to_dict(self) -> dict[str, dict[str, str]]:
        return {tag.name: tag_data for tag, tag_data in self.tags_data.items()}
