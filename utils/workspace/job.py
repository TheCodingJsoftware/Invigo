from enum import Enum, auto
from typing import TYPE_CHECKING

from natsort import natsorted

from ui.icons import Icons
from ui.theme import theme_var
from utils.inventory.component import Component
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest
from utils.purchase_order.business_info import BusinessInfo
from utils.purchase_order.contact_info import ContactInfo
from utils.workspace.assembly import Assembly
from utils.workspace.job_flowtag_timeline import JobFlowtagTimeline
from utils.workspace.job_price_calculator import JobPriceCalculator
from utils.workspace.tag import Tag

if TYPE_CHECKING:
    from utils.workspace.job_manager import JobManager


class JobStatus(Enum):
    PLANNING = auto()
    QUOTING = auto()
    QUOTED = auto()
    QUOTE_CONFIRMED = auto()
    TEMPLATE = auto()
    WORKSPACE = auto()
    ARCHIVE = auto()


class JobIcon(Enum):
    PLANNING = JobStatus.PLANNING
    QUOTING = JobStatus.QUOTING
    QUOTED = JobStatus.QUOTED
    QUOTE_CONFIRMED = JobStatus.QUOTE_CONFIRMED
    TEMPLATE = JobStatus.TEMPLATE
    WORKSPACE = JobStatus.WORKSPACE
    ARCHIVE = JobStatus.ARCHIVE

    @classmethod
    def get_icon(cls, job_status: JobStatus):
        icon_map = {
            cls.PLANNING: Icons.job_planning_icon,
            cls.QUOTING: Icons.job_quoting_icon,
            cls.QUOTED: Icons.job_quoted_icon,
            cls.QUOTE_CONFIRMED: Icons.job_quote_confirmed_icon,
            cls.TEMPLATE: Icons.job_template_icon,
            cls.WORKSPACE: Icons.job_workspace_icon,
            cls.ARCHIVE: Icons.job_archive_icon,
        }
        return next(
            (icon_map.get(member) for member in cls if member.value == job_status),
            None,
        )


class JobColor(Enum):
    PLANNING = (theme_var("job-planning"), JobStatus.PLANNING)
    QUOTING = (theme_var("job-quoting"), JobStatus.QUOTING)
    QUOTED = (theme_var("job-quoted"), JobStatus.QUOTED)
    QUOTE_CONFIRMED = (theme_var("job-quote-confirmed"), JobStatus.QUOTE_CONFIRMED)
    TEMPLATE = (theme_var("job-template"), JobStatus.TEMPLATE)
    WORKSPACE = (theme_var("job-workspace"), JobStatus.WORKSPACE)
    ARCHIVE = (theme_var("job-archive"), JobStatus.ARCHIVE)

    @classmethod
    def get_color(cls, job_status: JobStatus):
        return next((color.value[0] for color in cls if color.value[1] == job_status), "red")


class Job:
    def __init__(self, data: dict, job_manager):
        self.id = -1
        self.name: str = ""
        self.order_number: float = 0.0
        self.PO_number: float = 0.0
        self.ship_to: str = ""
        self.starting_date: str = ""
        self.ending_date: str = ""
        self.assemblies: list[Assembly] = []
        self.nests: list[Nest] = []
        self.moved_job_to_workspace = False

        self.job_manager: JobManager = job_manager
        self.status = JobStatus.PLANNING
        self.color: str = JobColor.get_color(self.status)

        self.contact_info = ContactInfo()
        self.business_info = BusinessInfo()

        # NOTE Non serialized variables
        self.grouped_components: list[Component] = []
        self.grouped_laser_cut_parts: list[LaserCutPart] = []
        self.sheet_settings = self.job_manager.sheet_settings
        self.workspace_settings = self.job_manager.workspace_settings
        self.components_inventory = self.job_manager.components_inventory
        self.laser_cut_inventory = self.job_manager.laser_cut_inventory
        self.paint_inventory = self.job_manager.paint_inventory
        self.structural_steel_inventory = self.job_manager.structural_steel_inventory
        self.price_calculator = JobPriceCalculator(self, self.sheet_settings, self.paint_inventory, {})

        self.unsaved_changes = False
        self.downloaded_from_server = False

        # Because we need job_manager to be loaded first
        self.flowtag_timeline = JobFlowtagTimeline(self)

        self.load_data(data)

        if self.price_calculator.match_item_cogs_to_sheet:
            self.price_calculator.update_laser_cut_parts_to_sheet_price()

    def get_unique_parts_flowtag_tags(self) -> list[Tag]:
        tags: dict[str, Tag] = {}
        for laser_cut_part in self.get_all_laser_cut_parts():
            for tag in laser_cut_part.workspace_data.flowtag.tags:
                tags[tag.name] = tag
        for assembly in self.get_all_assemblies():
            for tag in assembly.workspace_data.flowtag.tags:
                tags[tag.name] = tag

        ordered_tags: list[Tag] = []
        ordered_tags.extend(tags[ordered_tag] for ordered_tag in self.workspace_settings.get_all_tags() if ordered_tag in tags)
        return ordered_tags

    def changes_made(self):
        self.unsaved_changes = True

    def add_assembly(self, assembly: Assembly):
        self.assemblies.append(assembly)

    def remove_assembly(self, assembly: Assembly):
        self.assemblies.remove(assembly)

    def add_nest(self, nest: Nest):
        self.nests.append(nest)

    def remove_nest(self, nest: Nest):
        self.nests.remove(nest)

    def group_laser_cut_parts(self):
        laser_cut_part_dict: dict[str, LaserCutPart] = {}
        for assembly in self.get_all_assemblies():
            for assembly_laser_cut_part in assembly.laser_cut_parts:
                unit_quantity = assembly_laser_cut_part.inventory_data.quantity
                new_laser_cut_part = LaserCutPart(assembly_laser_cut_part.to_dict(), self.laser_cut_inventory)
                new_laser_cut_part.inventory_data.quantity = unit_quantity * assembly.meta_data.quantity
                new_laser_cut_part.prices.matched_to_sheet_cost_price = assembly_laser_cut_part.prices.matched_to_sheet_cost_price

                if existing_component := laser_cut_part_dict.get(new_laser_cut_part.name):
                    existing_component.inventory_data.quantity += new_laser_cut_part.inventory_data.quantity
                else:
                    laser_cut_part_dict[new_laser_cut_part.name] = new_laser_cut_part
                # This is because we group the data, so all nest reference is lost.
                new_laser_cut_part.meta_data.quantity_on_sheet = None

        self.grouped_laser_cut_parts = laser_cut_part_dict.values()
        self.sort_laser_cut_parts()
        return self.grouped_laser_cut_parts

    def group_components(self):
        components_dict: dict[str, Component] = {}
        for assembly in self.get_all_assemblies():
            for assembly_component in assembly.components:
                unit_quantity = assembly_component.quantity
                new_component = Component(assembly_component.to_dict(), self.components_inventory)
                new_component.quantity = unit_quantity * assembly.meta_data.quantity
                if existing_component := components_dict.get(new_component.name):
                    existing_component.quantity += new_component.quantity
                else:
                    components_dict[new_component.name] = new_component

        self.grouped_components = components_dict.values()
        self.sort_components()
        return self.grouped_components

    def sort_nests(self):
        self.nests = natsorted(self.nests, key=lambda nest: nest.name)

    def sort_laser_cut_parts(self):
        self.grouped_laser_cut_parts = natsorted(self.grouped_laser_cut_parts, key=lambda laser_cut_part: laser_cut_part.name)

    def sort_components(self):
        self.grouped_components = natsorted(self.grouped_components, key=lambda laser_cut_part: laser_cut_part.name)

    def get_net_weight(self) -> float:
        total_weight = 0.0
        for assembly in self.get_all_assemblies():
            for laser_cut_part in assembly.laser_cut_parts:
                total_weight += laser_cut_part.meta_data.weight * laser_cut_part.inventory_data.quantity * assembly.meta_data.quantity
        return total_weight

    def get_all_assemblies(self) -> list[Assembly]:
        assemblies: list[Assembly] = []
        assemblies.extend(self.assemblies)
        for assembly in self.assemblies:
            assemblies.extend(assembly.get_all_sub_assemblies())
        return assemblies

    def get_all_laser_cut_parts(self) -> list[LaserCutPart]:
        """Laser cut parts in all assemblies."""
        laser_cut_parts: list[LaserCutPart] = []
        for assembly in self.get_all_assemblies():
            laser_cut_parts.extend(assembly.laser_cut_parts)
        return laser_cut_parts

    def get_all_nested_laser_cut_parts(self) -> list[LaserCutPart]:
        """Laser cut parts in nests excluding assembly laser cut parts."""
        laser_cut_parts: list[LaserCutPart] = []
        for nest in self.nests:
            laser_cut_parts.extend(nest.laser_cut_parts)
        return laser_cut_parts

    def get_grouped_laser_cut_parts(self) -> list[LaserCutPart]:
        """Used in printouts"""
        self.group_laser_cut_parts()
        return self.group_laser_cut_parts()

    def get_all_components(self) -> list[Component]:
        components: list[Component] = []
        for assembly in self.get_all_assemblies():
            components.extend(assembly.components)
        return components

    def get_grouped_components(self) -> list[Component]:
        return self.group_components()

    def get_workspace_name(self) -> str:
        return f"{self.id}. {self.name} #{self.order_number}: {self.starting_date} - {self.ending_date}"

    def load_settings(self, data):
        job_data = data.get("job_data", {})
        self.id = job_data.get("id", -1)
        self.name = job_data.get("name", "")
        self.order_number = job_data.get("order_number", 0)
        self.PO_number = job_data.get("PO_number", 0)
        self.ship_to = job_data.get("ship_to", "")
        self.starting_date = job_data.get("starting_date", "")
        self.ending_date = job_data.get("ending_date", "")
        self.status = JobStatus(int(job_data.get("type", 1)))  # We cast just in case, trust me
        self.color = JobColor.get_color(self.status)
        self.moved_job_to_workspace = job_data.get("moved_job_to_workspace", False)
        self.price_calculator.load_settings(job_data.get("price_settings", {}))

    def update_inventory_items_data(self):
        laser_cut_parts_to_update = []
        for laser_cut_part in self.get_all_laser_cut_parts():
            if inventory_laser_cut_part := self.laser_cut_inventory.get_laser_cut_part_by_name(laser_cut_part.name):
                inventory_laser_cut_part.meta_data.image_index = laser_cut_part.meta_data.image_index

                inventory_laser_cut_part.workspace_data.bending_files = laser_cut_part.workspace_data.bending_files
                inventory_laser_cut_part.workspace_data.welding_files = laser_cut_part.workspace_data.welding_files
                inventory_laser_cut_part.workspace_data.cnc_milling_files = laser_cut_part.workspace_data.cnc_milling_files
                inventory_laser_cut_part.workspace_data.flowtag = laser_cut_part.workspace_data.flowtag
                inventory_laser_cut_part.workspace_data.flowtag_data = laser_cut_part.workspace_data.flowtag_data

                inventory_laser_cut_part.primer_data.uses_primer = laser_cut_part.primer_data.uses_primer
                inventory_laser_cut_part.paint_data.uses_paint = laser_cut_part.paint_data.uses_paint
                inventory_laser_cut_part.powder_data.uses_powder = laser_cut_part.powder_data.uses_powder

                inventory_laser_cut_part.primer_data.primer_name = laser_cut_part.primer_data.primer_name
                inventory_laser_cut_part.paint_data.paint_name = laser_cut_part.paint_data.paint_name
                inventory_laser_cut_part.powder_data.powder_name = laser_cut_part.powder_data.powder_name

                inventory_laser_cut_part.primer_data.primer_overspray = laser_cut_part.primer_data.primer_overspray
                inventory_laser_cut_part.paint_data.paint_overspray = laser_cut_part.paint_data.paint_overspray
                inventory_laser_cut_part.powder_data.powder_transfer_efficiency = laser_cut_part.powder_data.powder_transfer_efficiency
                laser_cut_parts_to_update.append(inventory_laser_cut_part)

        self.laser_cut_inventory.save_laser_cut_parts(laser_cut_parts_to_update)

        components_to_save = []
        for component in self.get_all_components():
            if inventory_component := self.components_inventory.get_component_by_name(component.name):
                inventory_component.image_path = component.image_path
                components_to_save.append(inventory_component)
        # self.components_inventory.save_local_copy()
        self.components_inventory.save_components(components_to_save)

    def is_valid(self) -> tuple[bool, str]:
        for assembly in self.get_all_assemblies():
            if not assembly.workspace_data.flowtag:
                return (False, assembly.name)
        return next(
            ((False, laser_cut_part.name) for laser_cut_part in self.get_all_laser_cut_parts() if not laser_cut_part.workspace_data.flowtag.tags),
            (True, ""),
        )

    def is_job_finished(self) -> bool:
        return all(assembly.is_assembly_finished() for assembly in self.get_all_assemblies())

    def load_data(self, data: dict[str, dict[str, object]]):
        self.load_settings(data)

        nests_data = data.get("nests", [])

        self.nests.clear()
        for nest_data in nests_data:
            nest = Nest(nest_data, self.sheet_settings, self.laser_cut_inventory)
            self.add_nest(nest)

        assemblies_data = data.get("assemblies", [])

        self.assemblies.clear()
        for assembly_data in assemblies_data:
            assembly = Assembly(assembly_data, self)
            self.add_assembly(assembly)

        # Because we need laser cut parts
        self.flowtag_timeline.load_data(data.get("job_data", {}).get("flowtag_timeline", {}))

    def to_dict(self):
        self.unsaved_changes = False
        return {
            "job_data": {
                "id": self.id,
                "name": self.name,
                "type": self.status.value,
                "order_number": int(self.order_number),  # Just in case
                "PO_number": int(self.PO_number),
                "ship_to": self.ship_to,
                "starting_date": self.starting_date,
                "ending_date": self.ending_date,
                "color": JobColor.get_color(self.status),
                "price_settings": self.price_calculator.to_dict(),
                "flowtag_timeline": self.flowtag_timeline.to_dict(),
                "moved_job_to_workspace": self.moved_job_to_workspace,
                "contact_info": self.contact_info.to_dict(),
                "business_info": self.business_info.to_dict(),
            },
            "nests": [nest.to_dict() for nest in self.nests],
            "assemblies": [assembly.to_dict() for assembly in self.assemblies],
        }
