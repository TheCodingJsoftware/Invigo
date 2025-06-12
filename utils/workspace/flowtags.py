from typing import Iterator

from utils.workspace.flowtag import Flowtag, Group


class Flowtags:
    def __init__(self, name: str):
        self.name = name
        self.group: Group = Group.LASER_CUT_PART
        self.flow_tags: list[Flowtag] = []

    def add_flow_tag(self, flow_tag: Flowtag):
        flow_tag.group = self.group
        self.flow_tags.append(flow_tag)

    def remove_flow_tag(self, flow_tag: Flowtag):
        self.flow_tags.remove(flow_tag)

    def clear(self):
        self.flow_tags.clear()

    def __iter__(self) -> Iterator[Flowtag]:
        return iter(self.flow_tags)
