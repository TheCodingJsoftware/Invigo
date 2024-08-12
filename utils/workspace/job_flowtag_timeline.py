import contextlib
from typing import TYPE_CHECKING
from datetime import datetime

from utils.workspace.tag import Tag

if TYPE_CHECKING:
    from utils.workspace.job import Job


class JobFlowtagTimeline:
    def __init__(self, job):
        self.tags_data: dict[Tag, dict[str, str]] = {}
        self.job: Job = job
        self.job_starting_date = self.job.starting_date
        self.job_ending_date = self.job.ending_date

    def get_job_range(self) -> int:
        with contextlib.suppress(ValueError): # Date not set yer
            start_date = datetime.strptime(self.job.starting_date, "%Y-%m-%d %I:%M %p")
            end_date = datetime.strptime(self.job.ending_date, "%Y-%m-%d %I:%M %p")
            return (end_date - start_date).days
        return 1

    def load_data(self, data: dict[str, dict[str, str]]):
        self.tags_data.clear()
        for tag in self.job.get_unique_parts_flowtag_tags():
            tag_data = data.get(tag.name, {"starting_date": self.job.starting_date, "ending_date": self.job.ending_date})
            self.tags_data.update({tag: tag_data})

    def to_dict(self) -> dict[str, dict[str, str]]:
        return {tag.name: tag_data for tag, tag_data in self.tags_data.items()}
