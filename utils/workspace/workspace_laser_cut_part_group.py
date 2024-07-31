from typing import Optional, Iterator

from utils.inventory.laser_cut_part import LaserCutPart
from utils.workspace.tag import Tag


class WorkspaceLaserCutPartGroup:
    def __init__(self):
        self.laser_cut_parts: list[LaserCutPart] = []
        self.base_part: LaserCutPart = None

    def add_laser_cut_part(self, laser_cut_part: LaserCutPart):
        if not self.base_part:
            self.base_part = laser_cut_part
        self.laser_cut_parts.append(laser_cut_part)

    def get_parts_list(self) -> str:
        text = ""
        for laser_cut_part in self:
            text += f"{laser_cut_part.name}: {laser_cut_part.flow_tag.get_name()}\n"
        return text

    def unmark_as_recut(self):
        for laser_cut_part in self:
            laser_cut_part.recut = False
            self.move_to_next_process()

    def get_current_tag(self) -> Optional[Tag]:
        return self.base_part.get_current_tag()

    def set_flow_tag_status_index(self, status_index: int):
        for laser_cut_part in self:
            laser_cut_part.current_flow_tag_status_index = status_index

    def move_to_next_process(self, quantity: Optional[int]=None):
        max_quantity = len(self.laser_cut_parts)
        if quantity is None or quantity > max_quantity:
            quantity = max_quantity

        for i in range(quantity):
            self.laser_cut_parts[i].move_to_next_process()

    def get_quantity(self) -> int:
        return len(self.laser_cut_parts)

    def __iter__(self) -> Iterator[LaserCutPart]:
        return iter(self.laser_cut_parts)
