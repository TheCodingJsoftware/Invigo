from typing import TYPE_CHECKING

from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.paint_inventory import PaintInventory
from utils.inventory.sheets_inventory import SheetsInventory
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.workspace.workspace_settings import WorkspaceSettings

if TYPE_CHECKING:
    from main import MainWindow


class JobManager:
    def __init__(self, parent):
        self.parent: MainWindow = parent

        self.sheet_settings: SheetSettings = self.parent.sheet_settings
        self.sheets_inventory: SheetsInventory = self.parent.sheets_inventory
        self.workspace_settings: WorkspaceSettings = self.parent.workspace_settings
        self.components_inventory: ComponentsInventory = self.parent.components_inventory
        self.laser_cut_inventory: LaserCutInventory = self.parent.laser_cut_inventory
        self.paint_inventory: PaintInventory = self.parent.paint_inventory

    def sync_changes(self):
        self.parent.sync_changes()
