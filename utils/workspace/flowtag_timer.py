from datetime import datetime
from typing import TypedDict, Union

from utils.workspace.flowtag import Flowtag
from utils.workspace.tag import Tag


class TagTimerDict(TypedDict):
    started: str
    finished: str | None


class FlowtagTimerDict(TypedDict):
    timer_data: list[TagTimerDict]


class TagTimer:
    def __init__(self, data: list[TagTimerDict]):
        self.timer_data: list[TagTimerDict] = []
        self.load_data(data)

    def start(self):
        self.timer_data.append({"started": datetime.now().isoformat(), "finished": None})

    def stop(self):
        try:
            self.timer_data[-1]["finished"] = datetime.now().isoformat()
        except IndexError:
            self.start()
            self.stop()

    def load_data(self, data: list[TagTimerDict]):
        self.timer_data.clear()
        self.timer_data = [] if isinstance(data, dict) else data

    def to_dict(self) -> list[TagTimerDict]:
        return self.timer_data


class FlowtagTimer:
    def __init__(self, data: dict[str, FlowtagTimerDict], flow_tag: Flowtag):
        self.recorded_data: dict[Tag, TagTimer] = {}
        self.flow_tag = flow_tag
        self.load_data(data)

    def load_data(self, data: dict[str, FlowtagTimerDict]):
        self.recorded_data.clear()
        for tag in self.flow_tag:
            self.recorded_data.update({tag: TagTimer(data.get(tag.name, []))})

    def start_timer(self):
        self.recorded_data[self.flow_tag.tags[0]].start()

    def has_started_timer(self) -> bool:
        return bool(self.recorded_data[self.flow_tag.tags[0]].timer_data)

    def start(self, tag_name: Union[Tag, str]):
        if isinstance(tag_name, str):
            for tag in self.recorded_data:
                if tag.name == tag_name:
                    self.recorded_data[tag].start()
                    break
        elif isinstance(tag_name, Tag):
            self.recorded_data[tag_name].start()

    def stop(self, tag_name: Union[Tag, str]):
        if isinstance(tag_name, str):
            for tag in self.recorded_data:
                if tag.name == tag_name:
                    self.recorded_data[tag].stop()
                    break
        elif isinstance(tag_name, Tag):
            self.recorded_data[tag_name].stop()

    def to_dict(self) -> dict[str, FlowtagTimerDict]:
        return {tag.name: tag_timer.to_dict() for tag, tag_timer in self.recorded_data.items()}
