from typing import Iterator, Optional

import msgspec

from utils.inventory.laser_cut_part import LaserCutPart
from utils.workspace.tag import Tag


class WorkspaceLaserCutPartGroup:
    def __init__(self) -> None:
        self.laser_cut_parts: list[LaserCutPart] = []
        self.base_part: LaserCutPart | None = None

    def add_laser_cut_part(self, laser_cut_part: LaserCutPart):
        if not self.base_part:
            self.base_part = laser_cut_part
        self.laser_cut_parts.append(laser_cut_part)

    def get_files(self, file_type: str) -> list[str]:
        all_files: set[str] = set()
        for laser_cut_part in self:
            files = getattr(laser_cut_part, file_type)
            for file in files:
                all_files.add(file)
        return list(all_files)

    def get_all_files_with_ext(self, file_ext: str) -> list[str]:
        all_files: set[str] = set()
        for laser_cut_part in self:
            for bending_file in laser_cut_part.bending_files:
                if bending_file.lower().endswith(file_ext):
                    all_files.add(bending_file)
            for welding_file in laser_cut_part.welding_files:
                if welding_file.lower().endswith(file_ext):
                    all_files.add(welding_file)
            for cnc_milling_file in laser_cut_part.cnc_milling_files:
                if cnc_milling_file.lower().endswith(file_ext):
                    all_files.add(cnc_milling_file)
        return list(all_files)

    def get_all_files(self) -> list[str]:
        all_files: set[str] = set()
        for laser_cut_part in self:
            for bending_file in laser_cut_part.bending_files:
                all_files.add(bending_file)
            for welding_file in laser_cut_part.welding_files:
                all_files.add(welding_file)
            for cnc_milling_file in laser_cut_part.cnc_milling_files:
                all_files.add(cnc_milling_file)
        return list(all_files)

    def get_parts_list(self) -> str:
        text = ""
        for laser_cut_part in self:
            text += f"{laser_cut_part.name}: {laser_cut_part.flowtag.get_flow_string()}\n"
        return text

    def get_ids(self) -> str:
        return ",".join(str(laser_cut_part.id) for laser_cut_part in self)

    def update_entry(self, entry_data: dict) -> LaserCutPart | None:
        raw_data = entry_data["data"]
        if isinstance(raw_data, dict):
            json_data = raw_data
        elif isinstance(raw_data, (bytes, bytearray, str)):
            json_data = msgspec.json.decode(raw_data)
        else:
            raise TypeError(f"Unsupported data type for entry_data['data']: {type(raw_data)}")
        for laser_cut_part in self:
            if laser_cut_part.id == entry_data["id"]:
                laser_cut_part.load_data(json_data)
                return laser_cut_part
        return None

    def update_all_entries(self, entries_data: list[dict]) -> "WorkspaceLaserCutPartGroup":
        for entry_data in entries_data:
            self.update_entry(entry_data)
        return self

    def mark_as_recoat(self, quantity: Optional[int] = None):
        max_quantity = len(self.laser_cut_parts)
        if quantity is None or quantity > max_quantity:
            quantity = max_quantity

        for i in range(quantity):
            self.laser_cut_parts[i].timer.stop(self.get_current_tag())
            self.laser_cut_parts[i].current_flow_tag_index = self.laser_cut_parts[i].get_first_tag_index_with_similar_keyword(
                ["powder", "coating", "liquid", "paint", "gloss", "prime"]
            )
            self.laser_cut_parts[i].current_flow_tag_status_index = 0
            self.laser_cut_parts[i].recoat = True
            self.laser_cut_parts[i].recoat_count += 1

    def mark_as_recut(self, quantity: Optional[int] = None):
        max_quantity = len(self.laser_cut_parts)
        if quantity is None or quantity > max_quantity:
            quantity = max_quantity

        for i in range(quantity):
            self.laser_cut_parts[i].timer.stop(self.get_current_tag())
            self.laser_cut_parts[i].current_flow_tag_index = 0
            self.laser_cut_parts[i].current_flow_tag_status_index = 0
            self.laser_cut_parts[i].recut = True
            self.laser_cut_parts[i].recut_count += 1

    def unmark_as_recoat(self):
        for laser_cut_part in self:
            laser_cut_part.recoat = False
            self.move_to_next_process()

    def unmark_as_recut(self):
        for laser_cut_part in self:
            laser_cut_part.recut = False
            self.move_to_next_process()

    def get_current_tag(self) -> Optional[Tag]:
        if self.base_part:
            return self.base_part.get_current_tag()
        return None

    def set_flow_tag_status_index(self, status_index: int):
        for laser_cut_part in self:
            laser_cut_part.current_flow_tag_status_index = status_index

    def check_update_quantity_tags(self):
        if not self.base_part:
            return
        if current_tag := self.get_current_tag():
            if self.base_part.flowtag.add_quantity_tag and current_tag.name == self.base_part.flowtag.add_quantity_tag.name:
                self.base_part.laser_cut_inventory.add_or_update_laser_cut_parts(self.laser_cut_parts, f"workspace tag: {current_tag.name}")
            if self.base_part.flowtag.remove_quantity_tag and current_tag.name == self.base_part.flowtag.remove_quantity_tag.name:
                self.base_part.laser_cut_inventory.remove_laser_cut_parts_quantity(self.laser_cut_parts, f"workspace tag: {current_tag.name}")

    def move_to_next_process(self, quantity: Optional[int] = None):
        max_quantity = len(self.laser_cut_parts)
        if quantity is None or quantity > max_quantity:
            quantity = max_quantity

        for i in range(quantity):
            self.laser_cut_parts[i].move_to_next_process()
        self.check_update_quantity_tags()

    def get_process_status(self) -> str:
        try:
            if self.base_part.recut:
                return "Part is a Recut"
            elif self.base_part.recoat:
                return "Part is a Recoat"
            elif self.base_part.is_process_finished():
                return "Part is Finished"
            else:
                if self.get_current_tag().statuses:
                    return f"Part is currently in {self.get_current_tag().name}: {self.get_current_tag().statuses[self.base_part.current_flow_tag_status_index].name}"
                else:
                    return f"Part is currently in {self.get_current_tag().name}"
        except Exception as e:
            print(e)
            return ""

    def get_count(self) -> int:
        return len(self.laser_cut_parts)

    def get_quantity(self) -> int:
        quantity = 0
        for laser_cut_part in self:
            quantity += laser_cut_part.quantity
        return quantity

    def __iter__(self) -> Iterator[LaserCutPart]:
        return iter(self.laser_cut_parts)
