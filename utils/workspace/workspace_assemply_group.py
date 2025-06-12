from typing import Iterator, Optional

import msgspec

from utils.workspace.assembly import Assembly
from utils.workspace.tag import Tag


class WorkspaceAssemblyGroup:
    def __init__(self):
        self.assemblies: list[Assembly] = []
        self.base_assembly: Assembly = None

    def add_assembly(self, assembly: Assembly):
        if not self.base_assembly:
            self.base_assembly = assembly
        self.assemblies.append(assembly)

    def get_files(self, file_ext: str) -> list[str]:
        all_files: set[str] = set()
        for file in self.get_all_files():
            if file.endswith(file_ext):
                all_files.add(file)
        return list(all_files)

    def get_all_files(self) -> list[str]:
        all_files: set[str] = set()
        for assembly in self:
            for file in assembly.assembly_files:
                all_files.add(file)
        return list(all_files)

    def get_ids(self) -> str:
        return ",".join(str(assembly.id) for assembly in self)

    def update_entry(self, entry_data: dict) -> Optional[Assembly]:
        raw_data = entry_data["data"]
        if isinstance(raw_data, dict):
            json_data = raw_data
        elif isinstance(raw_data, (bytes, bytearray, str)):
            json_data = msgspec.json.decode(raw_data)
        else:
            raise TypeError(
                f"Unsupported data type for entry_data['data']: {type(raw_data)}"
            )
        for assembly in self:
            if assembly.id == entry_data["id"]:
                assembly.load_data(json_data)
                return assembly
        return None

    def get_current_tag(self) -> Optional[Tag]:
        return self.base_assembly.get_current_tag()

    def set_flow_tag_status_index(self, status_index: int):
        for assembly in self:
            assembly.current_flow_tag_status_index = status_index

    def move_to_next_process(self, quantity: Optional[int] = None):
        max_quantity = len(self.assemblies)
        if quantity is None or quantity > max_quantity:
            quantity = max_quantity

        for i in range(quantity):
            self.assemblies[i].move_to_next_process()

    def get_quantity(self) -> int:
        return len(self.assemblies)

    def __iter__(self) -> Iterator[Assembly]:
        return iter(self.assemblies)
