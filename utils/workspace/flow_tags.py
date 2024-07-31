from typing import Iterator

from utils.workspace.flow_tag import FlowTag, Group


class FlowTags:
    def __init__(self, name: str):
        self.name = name
        self.group: Group = Group.LASER_CUT_PART
        self.flow_tags: list[FlowTag] = []

    def add_flow_tag(self, flow_tag: FlowTag):
        flow_tag.group = self.group
        self.flow_tags.append(flow_tag)

    def remove_flow_tag(self, flow_tag: FlowTag):
        self.flow_tags.remove(flow_tag)

    def clear(self):
        self.flow_tags.clear()

    def __iter__(self) -> Iterator[FlowTag]:
        return iter(self.flow_tags)
