from typing import TYPE_CHECKING

from utils.workspace.tag import Tag

if TYPE_CHECKING:
    from utils.workspace.job import Job


class FlowtagTimeline:
    def __init__(self, job):
        self.tags_data: dict[Tag, dict[str, str]] = {}
        self.job: Job = job

    def load_data(self, data: dict[str, dict[str, str]]):
        self.tags_data.clear()
        for tag in self.job.get_unique_parts_flowtag_tags():
            self.tags_data.update({tag: data[tag.name]})

    def to_dict(self) -> dict[str, dict[str, str]]:
        return {tag.name: self.tags_data[tag] for tag in self.job.get_unique_parts_flowtag_tags()}
