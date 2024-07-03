from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart


class WorkspaceItem:
    def __init__(
        self, inventory_item: Component | LaserCutPart | None, data: dict
    ) -> None:
        # NOTE NON serialized variables
        self.show: bool = True
        self.inventory_item = inventory_item

        # NOTE Serialized variables
        self.name: str = self.inventory_item.name
        self.parent_assembly = None
        self.master_assembly = None
        self.bending_files: list[str] = []
        self.welding_files: list[str] = []
        self.cnc_milling_files: list[str] = []
        self.thickness: str = ""
        self.material: str = ""
        self.parts_per: int = 0
        self.flow_tag: list[str] = []
        self.timers: dict[str, dict] = {}
        self.customer: str = ""
        self.ship_to: str = ""
        self.shelf_number: str = ""
        self.notes: str = ""

        # NOTE Used in user workspace
        self.current_flow_state: int = 0
        self.recoat: bool = False
        self.status: str = None
        self.recut: bool = False
        self.recut_count: int = 0
        self.completed: bool = False
        self.starting_date: str = ""
        self.ending_date: str = ""
        self.date_completed: str = ""

        self.load_data(data)

    def load_data(self, data: dict):
        self.bending_files: list[str] = data.get("bending_files", [])
        self.welding_files: list[str] = data.get("welding_files", [])
        self.cnc_milling_files: list[str] = data.get("cnc_milling_files", [])
        self.thickness: str = (
            self.inventory_item.gauge
            if isinstance(self.inventory_item, LaserCutPart)
            else data.get("thickness", "")
        )
        self.material: str = (
            self.inventory_item.material
            if isinstance(self.inventory_item, LaserCutPart)
            else data.get("material", "")
        )
        self.parts_per: int = data.get("parts_per", 0)
        self.flow_tag: list[str] = data.get("flow_tag", [])
        self.timers: dict[str, dict] = data.get("timers", {})
        self.customer: str = data.get("customer", "")
        self.ship_to: str = data.get("ship_to", "")
        self.shelf_number: str = (
            self.inventory_item.shelf_number
            if isinstance(self.inventory_item, LaserCutPart)
            else data.get("shelf_number", "")
        )
        self.notes: str = (
            self.inventory_item.notes
            if isinstance(self.inventory_item, Component)
            else data.get("notes", "")
        )
        # NOTE Used in user workspace
        self.current_flow_state: int = data.get("current_flow_state", 0)
        self.recoat: bool = data.get("recoat", False)
        self.status: str = data.get("status")
        self.recut: bool = data.get("recut", False)
        self.recut_count: int = data.get("recut_count", 0)
        self.completed: bool = data.get("completed", False)
        self.starting_date: str = data.get("starting_date", "")
        self.ending_date: str = data.get("ending_date", "")
        self.date_completed: str = data.get("date_completed", "")
        self.component: str = data.get("date_completed", "")
        self.date_completed: str = data.get("date_completed", "")

    def item_type(self) -> str | None:
        if isinstance(self.inventory_item, Component):
            return "component"
        elif isinstance(self.inventory_item, LaserCutPart):
            return "laser_cut_part"
        else:
            return None

    def get_all_files(self, file_category: str) -> list[str]:
        if file_category == "Bending Files":
            return self.bending_files
        elif file_category == "Welding Files":
            return self.welding_files
        elif file_category == "CNC/Milling Files":
            return self.cnc_milling_files
        return []

    def update_files(self, file_category: str, files: list[str]):
        if file_category == "Bending Files":
            self.bending_files = files
        elif file_category == "Welding Files":
            self.welding_files = files
        elif file_category == "CNC/Milling Files":
            self.cnc_milling_files = files

    def get_current_flow_state(self) -> str:
        return self.flow_tag[self.current_flow_state]

    def rename(self, new_name: str) -> None:
        self.name = new_name

    def set_timer(self, flow_tag: str, time: object) -> None:
        self.timers[flow_tag]["time_to_complete"] = time.value()

    def get_timer(self, flow_tag: str) -> float:
        return self.timers[flow_tag]['time_to_complete"']

    def get_paint_type(self) -> str:
        return self.inventory_item.paint_type.name

    def to_dict(self) -> dict[str, object]:
        return {
            "bending_files": self.bending_files,
            "welding_files": self.welding_files,
            "cnc_milling_files": self.cnc_milling_files,
            "thickness": self.thickness,
            "material": self.material,
            "parts_per": self.parts_per,
            "flow_tag": self.flow_tag,
            "timers": self.timers,
            "customer": self.customer,
            "ship_to": self.ship_to,
            "shelf_number": self.shelf_number,
            "notes": self.notes,
            "item_type": self.item_type(),
            # NOTE Used in user workspace
            "current_flow_state": self.current_flow_state,
            "recoat": self.recoat,
            "status": self.status,
            "recut": self.recut,
            "recut_count": self.recut_count,
            "completed": self.completed,
            "starting_date": self.starting_date,
            "ending_date": self.ending_date,
            "date_completed": self.date_completed,
        }
