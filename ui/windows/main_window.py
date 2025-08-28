import contextlib
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import traceback
import webbrowser
from collections import defaultdict
from datetime import datetime
from functools import partial
from tkinter import messagebox
from typing import Any, Callable, Optional, Union

import qtawesome as qta
import requests
from natsort import natsorted
from PyQt6.QtCore import (
    QEventLoop,
    QPoint,
    Qt,
    QThread,
    QThreadPool,
    QTimer,
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QDragEnterEvent,
    QDragLeaveEvent,
    QFont,
    QIcon,
)
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFontDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QToolBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.custom.job_tab import JobTab
from ui.custom_widgets import (
    ButtonManagerWidget,
    CustomTableWidget,
    MainTabButton,
    MultiToolBox,
    PdfTreeView,
    RichTextPushButton,
    ScrollPositionManager,
)
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.add_vendor_dialog import AddVendorDialog
from ui.dialogs.edit_business_dialog import EditBusinessInfoDialog
from ui.dialogs.edit_contact_dialog import EditContactInfoDialog
from ui.dialogs.edit_paint_inventory import EditPaintInventory
from ui.dialogs.edit_shipping_address_dialog import EditShippingAddressDialog
from ui.dialogs.edit_workspace_settings import EditWorkspaceSettings
from ui.dialogs.generate_workorder_dialog import GenerateWorkorderDialog
from ui.dialogs.job_generator import JobGeneratorDialog
from ui.dialogs.job_sorter_dialog import JobSorterDialog
from ui.dialogs.message_dialog import MessageDialog
from ui.dialogs.nest_editor_dialog import NestEditorDialog
from ui.dialogs.nest_sheet_verification import NestSheetVerification
from ui.dialogs.purchase_order_dialog import PurchaseOrderDialog
from ui.dialogs.select_item_dialog import SelectItemDialog
from ui.dialogs.send_jobs_to_workspace_dialog import SendJobsToWorkspaceDialog
from ui.dialogs.update_dialog import UpdateDialog
from ui.dialogs.view_removed_quantities_history_dialog import (
    ViewRemovedQuantitiesHistoryDialog,
)
from ui.icons import Icons
from ui.theme import theme_var
from ui.widgets.components_tab import ComponentsTab
from ui.widgets.job_widget import JobWidget
from ui.widgets.laser_cut_tab import LaserCutTab
from ui.widgets.saved_job_item import SavedPlanningJobItem
from ui.widgets.sheet_settings_tab import SheetSettingsTab
from ui.widgets.sheets_in_inventory_tab import SheetsInInventoryTab
from ui.widgets.structural_steel_settings_tab import StructuralSteelSettingsTab
from ui.widgets.structural_steel_tab import StructuralSteelInventoryTab

# from ui.widgets.workspace_tab_widget import WorkspaceTabWidget
from ui.windows.main_window_UI import Ui_MainWindow
from utils.colors import lighten_color, get_random_color
from utils.dialog_buttons import DialogButtons
from utils.inventory.category import Category
from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.nest import Nest
from utils.inventory.paint_inventory import PaintInventory
from utils.inventory.sheet import Sheet
from utils.inventory.sheets_inventory import SheetsInventory
from utils.inventory.structural_steel_inventory import StructuralSteelInventory
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.po import check_po_directories
from utils.purchase_order.purchase_order import PurchaseOrder
from utils.purchase_order.purchase_order_manager import PurchaseOrderManager
from utils.purchase_order.shipping_address import ShippingAddress
from utils.purchase_order.vendor import Vendor
from utils.settings import Settings
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.structural_steel_settings.structural_steel_settings import (
    StructuralSteelSettings,
)
from utils.threads.add_job_to_production_planner_thread import (
    AddJobToProductionPlannerThread,
)
from utils.threads.changes_thread import ChangesThread
from utils.threads.check_for_updates_thread import CheckForUpdatesThread
from utils.threads.download_thread import DownloadThread
from utils.threads.exchange_rate import ExchangeRate
from utils.threads.get_previous_quotes_thread import GetPreviousQuotesThread
from utils.threads.get_saved_quotes_thread import GetSavedQuotesThread
from utils.threads.load_nests_thread import LoadNestsThread
from utils.threads.send_email_thread import SendEmailThread
from utils.threads.send_sheet_report_thread import SendReportThread
from utils.workers.auth.connect import ConnectWorker
from utils.workers.auth.is_client_trusted import IsClientTrustedWorker
from utils.workers.jobs.delete_job import DeleteJobWorker
from utils.workers.jobs.get_all_jobs import GetAllJobsWorker
from utils.workers.jobs.job_loader_controller import JobLoaderController
from utils.workers.jobs.save_job import SaveJobWorker
from utils.workers.jobs.update_job_setting import UpdateJobSettingWorker
from utils.workers.runnable_chain import RunnableChain
from utils.workers.upload_files import UploadFilesWorker
from utils.workers.utils.get_order_number import GetOrderNumberWorker
from utils.workers.utils.set_order_number import SetOrderNumberWorker
from utils.workers.workspace.add_job_to_workspace import AddJobToWorkspaceWorker
from utils.workers.workspace.get_entries_by_name import (
    GetWorkspaceEntriesByNameWorker,
)
from utils.workers.workspace.get_workspace_entry import GetWorkspaceEntryWorker
from utils.workspace.job import Job, JobColor, JobIcon, JobStatus
from utils.workspace.job_manager import JobManager
from utils.workspace.job_preferences import JobPreferences
from utils.workspace.workorder import Workorder
from utils.workspace.workspace import Workspace
from utils.workspace.workspace_laser_cut_part_group import WorkspaceLaserCutPartGroup
from utils.workspace.workspace_settings import WorkspaceSettings

__version__: str = "v4.0.25"


def check_folders(folders: list[str]):
    for folder in folders:
        with contextlib.suppress(FileExistsError):
            if not os.path.exists(folder):
                os.mkdir(folder)


check_folders(
    folders=[
        "logs",
        "data",
        "data/jobs",
        "data/workspace",
        "images",
        "backups",
        "Price History Files",
        "excel files",
        "PO's",
        "PO's/templates",
    ]
)


def _play_celebrate_sound():
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound("sounds/sound.wav", winsound.SND_FILENAME)


def _play_boot_sound():
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound("sounds/boot.wav", winsound.SND_FILENAME)


logging.basicConfig(
    filename="logs/app.log",
    filemode="w",
    format="%(asctime)s [%(levelname)s] (Process: %(process)d | Thread: %(threadName)s) [%(filename)s:%(lineno)d - %(funcName)s] - %(message)s",
    datefmt="%B %d, %A %I:%M:%S %p",
    level=logging.INFO,
)


def excepthook(exc_type, exc_value, exc_traceback):
    logging.error(
        f"Unhandled exception traceback: {traceback.format_exc()}",
        exc_info=(exc_type, exc_value, exc_traceback),
    )
    threading.Thread(target=send_error_report).start()

    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    user_msg = (
        f"An unhandled exception has occurred and has been reported to jared@pinelandfarms.ca.\nIf it persists, please contact me with details.\n\nTechnical Info:\n{error_msg}"
    )

    # Use tkinter to show the error
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    messagebox.showerror("Unhandled Exception", user_msg)
    root.destroy()

    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def send_error_report():
    SERVER_IP: str = get_server_ip_address()
    SERVER_PORT: int = get_server_port()
    url = f"http://{SERVER_IP}:{SERVER_PORT}/send_error_report"

    try:
        with open("logs/app.log", "r", encoding="utf-8") as error_log:
            error_data = error_log.read()
        data = {"error_log": f"User: {os.getlogin().title()}\nVersion: {__version__}\n\n{error_data}"}
        with requests.Session() as session:
            response = session.post(url, data=data, headers={"X-Client-Name": os.getlogin()}, timeout=10)
            if response.status_code != 200:
                raise Exception("Failed to send report")

    except Exception as e:
        # Use tkinter to show fallback error
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning(
            "Report Failed",
            f"Failed to send error report. (This is bad)\nPlease notify Jared AS SOON AS POSSIBLE.\n\nReason: {e}",
        )
        root.destroy()


sys.excepthook = excepthook


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.username = os.getlogin()
        self.trusted_user = False
        self.ignore_update = False

        self.setWindowTitle(f"Invigo - {__version__} - {self.username}")
        self.setWindowIcon(QIcon(Icons.invigo_icon))
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.threads: list[QThread] = []
        self.order_number: int = -1

        # Status
        self.status_button = RichTextPushButton(self)
        self.status_button.setObjectName("status_button")
        self.status_button.setFlat(True)
        self.status_button.setFixedHeight(25)
        self.status_button.setText("Downloading all files, please wait...", "yellow")
        self.verticalLayout_status.addWidget(self.status_button)

        check_po_directories()

        self.settings_file = Settings()
        # VARIABLES
        self.components_tab_widget_last_selected_tab_index = 0  # * Used inside components_tab.py
        self.sheets_inventory_tab_widget_last_selected_tab_index = 0  # * Used inside sheets_in_inventory_tab.py
        self.structural_steel_inventory_tab_widget_last_selected_tab_index = 0  # * Used inside sheets_in_inventory_tab.py
        self.laser_cut_tab_widget_last_selected_tab_index = 0  # * Used inside laser_cut_tab.py
        # self.workspace_tab_widget_last_selected_tab = ""

        self.should_update_components_in_inventory_tab = False
        self.should_update_laser_cut_inventory_tab = False
        self.should_update_sheets_in_inventory_tab = False
        self.should_update_sheet_settings_tab = False
        self.should_update_quote_generator_tab = False
        self.has_loaded_job_planner_tab = False
        self.has_loaded_job_quoter_tab = False
        self.should_update_workspace_tab = False

        self.is_sheets_inventory_ui_loaded = False
        self.is_components_inventory_ui_loaded = False
        self.is_laser_cut_parts_inventory_ui_loaded = False

        self.category: Category = None
        self.categories: list[Category] = []
        self.active_layout: QVBoxLayout = None
        self.downloading_changes = False
        self.finished_downloading_all_files = False
        self.finished_loading_tabs = False
        self.files_downloaded_count = 0
        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])
        self.tabs: dict[Category, CustomTableWidget] = {}
        self.parts_in_inventory_name_lookup: dict[str, int] = {}
        self.last_selected_menu_tab: str = self.settings_file.get_value("last_toolbox_tab")
        self.toolbox_job_nest_directories_list_widgets: dict[str, PdfTreeView] = {}
        self.toolbox_workspace_nest_directories_list_widgets: dict[str, PdfTreeView] = {}
        self.quote_nest_information = {}
        self.quote_components_information = {}

        self.stack_tab_buttons_data = {
            "Components": {
                "icon": "ph.package-fill",
                "object_name": "components_tab",
            },
            "Laser Cut Inventory": {
                "icon": "ph.package-fill",
                "object_name": "laser_cut_inventory_tab",
            },
            "Sheets In Inventory": {
                "icon": "ph.package-fill",
                "object_name": "sheets_in_inventory_tab",
            },
            "Sheet Settings": {
                "icon": "ri.list-settings-fill",
                "object_name": "sheet_settings_tab",
            },
            "Structural Steel Settings": {
                "icon": "ri.list-settings-fill",
                "object_name": "structural_steel_settings_tab",
            },
            "Structural Steel Inventory": {
                "icon": "ph.package-fill",
                "object_name": "structural_steel_tab",
            },
            "Job Planner": {
                "icon": "ph.calendar-blank-fill",
                "object_name": "job_planner_tab",
            },
            "Job Quoter": {
                "icon": "ph.calculator-fill",
                "object_name": "job_quoter_tab",
            },
            "Workspace": {
                "icon": "fa6s.network-wired",
                "object_name": "workspace_tab",
            },
        }
        self.stack_tab_buttons: list[MainTabButton] = []

        self.scroll_position_manager = ScrollPositionManager()
        self.saved_jobs: dict[str, dict[str, str]] = {}

        self.start_intilization_chain()

    def start_intilization_chain(self):
        self._initialize_chain = RunnableChain(self)

        connect_worker = ConnectWorker(__version__)
        is_client_trusted_worker = IsClientTrustedWorker()
        get_order_number_worker = GetOrderNumberWorker()

        self._initialize_chain.add(connect_worker, self.user_connected)
        self._initialize_chain.add(is_client_trusted_worker, self.handle_client_data)
        self._initialize_chain.add(get_order_number_worker, self.get_order_number_response)

        self._initialize_chain.finished.connect(self.load_inventories)

        self._initialize_chain.start()

    def user_connected(self, response, next_step: Callable):
        self.status_button.setText(response.get("message", "User data updated"), "lime")
        next_step()

    def handle_client_data(self, response: dict[str, bool], next_step: Callable):
        self.trusted_user = response.get("is_trusted", False)
        self.status_button.setText("User is trusted" if self.trusted_user else "User is not trusted", "lime")
        next_step()

    def get_order_number_response(self, response: dict[str, int], next_step: Callable):
        self.order_number = response.get("order_number", 0)
        self.status_button.setText(f"Order number: {self.order_number}", "lime")
        next_step()

    def load_inventories(self):
        self.sheet_settings = SheetSettings()
        self.structural_steel_settings = StructuralSteelSettings()
        self.workspace_settings = WorkspaceSettings()
        self.job_preferences = JobPreferences()

        self.sheets_inventory = SheetsInventory(self.sheet_settings)
        self.structural_steel_inventory = StructuralSteelInventory(self.structural_steel_settings,
                                                                   self.workspace_settings)
        self.components_inventory = ComponentsInventory()
        self.paint_inventory = PaintInventory(self.components_inventory)
        self.laser_cut_parts_inventory = LaserCutInventory(self.paint_inventory, self.workspace_settings,
                                                           self.sheet_settings)

        self.job_manager = JobManager(
            self.sheet_settings,
            self.sheets_inventory,
            self.workspace_settings,
            self.components_inventory,
            self.laser_cut_parts_inventory,
            self.paint_inventory,
            self.structural_steel_inventory,
            self,
        )
        self.purchase_order_manager = PurchaseOrderManager(self.components_inventory, self.sheets_inventory)
        self.workspace = Workspace(self.workspace_settings, self.job_manager)

        self.download_all_files()

        # --- Setup flags ---
        self._sheets_loaded = False
        self._components_loaded = False

        # --- Define shared checker function ---
        def check_and_load_po_menus():
            if self._sheets_loaded and self._components_loaded:
                self.load_po_menus()

        # --- Define on_loaded wrappers ---
        def sheets_loaded_wrapper():
            self.load_sheets_inventory_tab()
            self._sheets_loaded = True
            check_and_load_po_menus()

        def components_loaded_wrapper():
            self.load_components_inventory_tab()
            self._components_loaded = True
            check_and_load_po_menus()

        # --- Load inventories ---
        self.sheets_inventory.load_data(on_loaded=sheets_loaded_wrapper)
        self.components_inventory.load_data(on_loaded=components_loaded_wrapper)
        self.laser_cut_parts_inventory.load_data(on_loaded=self.load_laser_cut_inventory_tab)

    def setup_tab_buttons(self):
        self.menu_tab_manager = ButtonManagerWidget(self)
        self.menu_tab_manager.tabOrderChanged.connect(self.save_menu_tab_order)
        self.horizontalLayout_tab_buttons.addWidget(self.menu_tab_manager)
        saved_tab_order = self.settings_file.get_value("tabs_order")
        for tab in saved_tab_order:
            for tab_name, tab_data in self.stack_tab_buttons_data.items():
                if tab == tab_name:
                    object_name = tab_data["object_name"]
                    tab_button = MainTabButton(tab_name, self)
                    tab_button.setVisible(self.settings_file.get_value("tab_visibility").get(tab_name, False))
                    icon = qta.icon(
                        tab_data["icon"],
                        color_on=theme_var("primary"),
                        color_on_active=theme_var("primary"),
                        color_off=theme_var("on-surface"),
                        color_off_active=theme_var("on-surface"),
                    )
                    tab_button.setIcon(icon)
                    tab_button.clicked.connect(partial(self.tab_changed, tab_button, object_name))
                    self.stack_tab_buttons.append(tab_button)
                    self.menu_tab_manager.addButton(tab_button)
                    break

    def tab_changed(self, selected_button: MainTabButton, tab_name: str):
        for i, button in enumerate(self.stack_tab_buttons):
            button.setChecked(button is selected_button)
            if self.stackedWidget.widget(i).objectName() == tab_name:
                self.stackedWidget.setCurrentIndex(i)
        self.settings_file.set_value("last_toolbox_tab", selected_button.text())
        self.last_selected_menu_tab = selected_button.text()

    def tab_text(self, tab_index: int) -> str:
        return self.stackedWidget.widget(tab_index).objectName()

    def set_current_tab(self, tab_name: str):
        for button in self.stack_tab_buttons:
            if button.text() == tab_name:
                button.click()
                break

    def set_tab_visibility(self, tab_name: str, visible: bool):
        if tab_name.endswith("_tab"):
            tab_name = tab_name.replace("_tab", "").replace("_", " ").title()
        for button in self.stack_tab_buttons:
            if button.text() == tab_name:
                button.setVisible(visible)
                break

    def toggle_tab_visibility(self, action: QAction):
        tab_name = action.text()
        self.settings_file.load_data()
        self.settings_file.get_value("tab_visibility")[tab_name] = action.isChecked()
        self.settings_file.save_data()
        self.set_tab_visibility(tab_name, action.isChecked())

    def __load_ui(self):
        self.splitter.setStretchFactor(0, 1)  # Job Planner
        self.splitter.setStretchFactor(1, 0)  # Job Planner

        self.splitter_2.setStretchFactor(0, 1)  # Job Quoter
        self.splitter_2.setStretchFactor(1, 0)  # Job Quoter

        # self.splitter_4.setSizes([1, 0])
        self.splitter_4.setStretchFactor(0, 1)
        self.splitter_4.setStretchFactor(1, 0)

        # self.components_inventory.load_data()
        # self.sheets_inventory.load_data()
        # self.laser_cut_parts_inventory.load_data()

        self.sheet_settings.load_data()
        self.structural_steel_settings.load_data()
        self.workspace_settings.load_data()
        # self.workspace.load_data()

        self.setup_tab_buttons()

        if not self.trusted_user:
            self.set_tab_visibility("Components", False)
            self.set_tab_visibility("Sheets In Inventory", False)
            self.set_tab_visibility("Laser Cut Inventory", False)
            self.set_tab_visibility("Structural Steel Inventory", False)
            self.set_tab_visibility("Sheet Settings", False)
            self.set_tab_visibility("Structural Steel Settings", False)
            self.set_tab_visibility("Job Planner", False)
            self.set_tab_visibility("Job Quoter", False)

            self.menuHistory.setEnabled(False)
            self.menuJobSorter.setEnabled(False)
            self.menuProduction_Planner.setEnabled(False)
            self.menuPaint_Inventory.setEnabled(False)
            self.menuQuote_Generator.setEnabled(False)
            self.menuPurchase_Orders.setEnabled(False)
            self.menuSort.setEnabled(False)

            self.action_Set_User_Workspace.setEnabled(False)
            self.actionSet_Order_Number.setEnabled(False)
            self.actionEditTags.setEnabled(False)
            self.actionComponents.setEnabled(False)
            self.actionSheets_in_Inventory.setEnabled(False)
            self.actionStructural_Steel_Settings.setEnabled(False)
            self.actionStructural_Steel_Inventory.setEnabled(False)
            self.actionLaser_Cut_Inventory.setEnabled(False)
            self.actionSheet_Settings.setEnabled(False)
            self.actionJob_Planner.setEnabled(False)
            self.actionJob_Quoter.setEnabled(False)
            self.actionWorkspace.setEnabled(False)
            for tab in self.settings_file.get_value("tabs_order"):
                if tab == "workspace_tab":
                    self.set_tab_visibility(tab, True)
                    self.settings_file.get_value("tab_visibility")["Workspace"] = True
                    self.last_selected_menu_tab = "workspace_tab"
                    continue
                self.set_tab_visibility(tab, False)
                self.settings_file.get_value("tab_visibility")[tab] = False
            self.settings_file.save_data()

        if self.trusted_user:
            try:
                self.set_current_tab(self.last_selected_menu_tab)
            except IndexError:
                self.stackedWidget.setCurrentIndex(0)
        else:
            self.set_current_tab("workspace_tab")

        self.load_job_planning_tab()
        self.load_job_quoting_tab()

        self.clear_layout(self.sheet_settings_layout)
        self.sheet_settings_tab_widget = SheetSettingsTab(self)
        self.sheet_settings_layout.addWidget(self.sheet_settings_tab_widget)

        self.clear_layout(self.structural_steel_settings_layout)
        self.structural_steel_settings_tab_widget = StructuralSteelSettingsTab(self)
        self.structural_steel_settings_layout.addWidget(self.structural_steel_settings_tab_widget)

        self.clear_layout(self.structural_steel_layout)
        self.structural_steel_tab_widget = StructuralSteelInventoryTab(self)
        self.structural_steel_layout.addWidget(self.structural_steel_tab_widget)

        # self.clear_layout(self.workspace_layout)
        # self.workspace_tab_widget = WorkspaceTabWidget(self)
        # self.workspace_tab_widget_last_selected_tab = self.workspace_tab_widget.tag_buttons[0].text()
        # self.workspace_tab_widget.get_all_workspace_jobs_thread()

        # with contextlib.suppress(AttributeError):  # There are no visible process tags
        # self.workspace_tab_changed(self.workspace_tab_widget_last_selected_tab)
        # self.workspace_tab_widget.tabChanged.connect(self.workspace_tab_changed)
        # self.workspace_layout.addWidget(self.workspace_tab_widget)

        # Tool Box
        self.stackedWidget.currentChanged.connect(self.tool_box_menu_changed)

        # WORKSPACE
        self.treeWidget_cutoff_sheets.doubleClicked.connect(self.tree_widget_cutoff_sheet_double_clicked)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_toggle_cutoff, self.cutoff_widget)
        self.cutoff_widget.setHidden(True)

        self.apply_stylesheet_to_toggle_buttons(self.pushButton_toggle_cutoff_2, self.cutoff_widget_2)
        self.cutoff_widget_2.setHidden(True)

        # QUOTE GENERATOR
        # self.cutoff_widget = MultiToolBox(self)
        # self.verticalLayout_cutoff.addWidget(self.cutoff_widget)
        # cutoff_items = QListWidget(self)
        # cutoff_items.doubleClicked.connect(
        #     partial(self.cutoff_sheet_double_clicked, cutoff_items)
        # )
        # self.cutoff_widget.addItem(cutoff_items, "Cutoff Sheets")
        # self.cutoff_widget.close_all()

        # NEST RELATED
        # self.pushButton_generate_quote.clicked.connect(self.generate_printout)

        self.pushButton_load_nests_2.clicked.connect(self.process_selected_nests_to_job)
        self.pushButton_load_nests_2.setIcon(Icons.import_icon)
        self.pushButton_load_nests_3.clicked.connect(self.workspace_process_selected_nests)
        self.pushButton_load_nests_3.setIcon(Icons.import_icon)

        self.pushButton_clear_selections_2.clicked.connect(self.clear_job_quote_selections)
        self.pushButton_clear_selections_2.setIcon(Icons.clear_icon)
        self.pushButton_clear_selections_3.clicked.connect(self.clear_workspace_nest_selections)
        self.pushButton_clear_selections_3.setIcon(Icons.clear_icon)

        self.pushButton_refresh_directories_2.clicked.connect(self.refresh_nest_directories)
        self.pushButton_refresh_directories_2.setIcon(Icons.refresh_icon)
        self.pushButton_refresh_directories_3.clicked.connect(self.refresh_nest_directories)
        self.pushButton_refresh_directories_3.setIcon(Icons.refresh_icon)

        # Jobs
        # self.tabWidget_3.setCornerWidget(self.pushButton_job_generator, Qt.Corner.TopRightCorner)
        self.pushButton_job_generator.clicked.connect(self.job_generator)
        self.pushButton_job_generator.setIcon(Icons.merge_icon)

        self.pushButton_refresh_jobs.clicked.connect(self.load_jobs_worker)
        self.pushButton_refresh_jobs.setIcon(Icons.refresh_icon)
        self.pushButton_refresh_jobs_2.clicked.connect(self.load_jobs_worker)
        self.pushButton_refresh_jobs_2.setIcon(Icons.refresh_icon)

        self.pushButton_save_job.clicked.connect(partial(self.save_job, None))
        self.pushButton_save_job.setIcon(Icons.save_icon)

        self.pushButton_save_job_2.clicked.connect(partial(self.save_job, None))
        self.pushButton_save_job_2.setIcon(Icons.save_icon)

        self.pushButton_save_as_job.setHidden(True)
        self.pushButton_save_as_job_2.setHidden(True)
        self.pushButton_save_as_job_2.setIcon(Icons.save_as_icon)

        self.pushButton_send_to_production_planner.clicked.connect(self.send_job_to_production_planner)
        self.pushButton_send_to_production_planner.setIcon(Icons.calendar_icon)
        self.pushButton_send_to_production_planner_2.clicked.connect(self.send_job_to_production_planner)
        self.pushButton_send_to_production_planner_2.setIcon(Icons.calendar_icon)

        self.pushButton_send_to_workspace.clicked.connect(self.send_job_to_workspace)
        self.pushButton_send_to_workspace.setIcon(Icons.workspace_icon)
        self.pushButton_send_to_workspace_2.clicked.connect(self.send_job_to_workspace)
        self.pushButton_send_to_workspace_2.setIcon(Icons.workspace_icon)

        self.saved_planning_jobs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.saved_jobs_multitoolbox = MultiToolBox(self)
        self.saved_planning_jobs_layout.addWidget(self.saved_jobs_multitoolbox)
        self.saved_planning_job_items_last_opened: dict[int, bool] = {}

        self.template_jobs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.templates_jobs_multitoolbox = MultiToolBox(self)
        self.template_jobs_layout.addWidget(self.templates_jobs_multitoolbox)
        self.templates_job_items_last_opened: dict[int, bool] = {}

        self.saved_planning_jobs_layout_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.saved_jobs_multitoolbox_2 = MultiToolBox(self)
        self.saved_planning_jobs_layout_2.addWidget(self.saved_jobs_multitoolbox_2)
        self.saved_planning_job_items_last_opened_2: dict[int, bool] = {}

        self.template_jobs_layout_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.templates_jobs_multitoolbox_2 = MultiToolBox(self)
        self.template_jobs_layout_2.addWidget(self.templates_jobs_multitoolbox_2)
        self.templates_job_items_last_opened_2: dict[int, bool] = {}

        # Tab widget
        # self.pushButton_add_new_sheet.clicked.connect(self.add_sheet_item)

        # Action events
        # HELP
        self.actionAbout_Qt.triggered.connect(QApplication.aboutQt)
        self.actionAbout_Qt.setIcon(Icons.info_icon)
        self.actionCheck_for_Updates.triggered.connect(self.check_for_updates)
        self.actionCheck_for_Updates.setIcon(Icons.update_icon)
        self.actionInvi_go.triggered.connect(self.open_invigo)
        self.actionInvi_go.setIcon(Icons.website_icon)
        self.actionAbout.triggered.connect(self.show_about_dialog)
        self.actionAbout.setIcon(Icons.info_icon)
        self.actionServer_log.triggered.connect(self.open_server_log)
        self.actionServer_log.setIcon(Icons.website_icon)
        self.actionServer_logs.triggered.connect(self.open_server_logs)
        self.actionServer_logs.setIcon(Icons.website_icon)
        self.actionInventory.triggered.connect(self.open_inventory)
        self.actionInventory.setIcon(Icons.website_icon)
        self.actionQR_Codes.triggered.connect(self.open_qr_codes)
        self.actionQR_Codes.setIcon(Icons.website_icon)
        self.actionWay_Back_Machine.triggered.connect(self.open_way_back_machine)
        self.actionWay_Back_Machine.setIcon(Icons.website_icon)
        self.actionInvigo_Help.triggered.connect(self.open_wiki)
        self.actionInvigo_Help.setIcon(Icons.question_icon)
        self.actionOpen_production_planner.triggered.connect(self.open_production_planner)
        self.actionOpen_production_planner.setIcon(Icons.website_icon)
        # PRINT

        # SETTINGS
        self.actionChange_tables_font.triggered.connect(self.change_tables_font)
        self.actionChange_tables_font.setIcon(Icons.font_icon)
        self.actionSet_Order_Number.triggered.connect(self.set_order_number)
        self.actionSet_Order_Number.setIcon(Icons.edit_icon)
        # self.action_Set_User_Workspace.triggered.connect(self.open_edit_user_workspace_settings)
        # self.action_Set_User_Workspace.setIcon(Icons.edit_user_icon)

        self.menuVisible_Tabs.setIcon(Icons.eye_icon)
        self.actionComponents.triggered.connect(partial(self.toggle_tab_visibility, self.actionComponents))
        self.actionComponents.setChecked(self.settings_file.get_value("tab_visibility").get("Components", True))
        self.actionComponents.setIcon(Icons.inventory_icon)
        self.actionSheets_in_Inventory.triggered.connect(
            partial(self.toggle_tab_visibility, self.actionSheets_in_Inventory))
        self.actionSheets_in_Inventory.setChecked(
            self.settings_file.get_value("tab_visibility").get("Sheets In Inventory", True))
        self.actionSheets_in_Inventory.setIcon(Icons.inventory_icon)
        self.actionLaser_Cut_Inventory.triggered.connect(
            partial(self.toggle_tab_visibility, self.actionLaser_Cut_Inventory))
        self.actionLaser_Cut_Inventory.setChecked(
            self.settings_file.get_value("tab_visibility").get("Laser Cut Inventory", True))
        self.actionLaser_Cut_Inventory.setIcon(Icons.inventory_icon)
        self.actionStructural_Steel_Inventory.triggered.connect(
            partial(self.toggle_tab_visibility, self.actionStructural_Steel_Inventory))
        self.actionStructural_Steel_Inventory.setChecked(
            self.settings_file.get_value("tab_visibility").get("Structural Steel Inventory", True))
        self.actionStructural_Steel_Inventory.setIcon(Icons.inventory_icon)
        self.actionStructural_Steel_Settings.triggered.connect(
            partial(
                self.toggle_tab_visibility,
                self.actionStructural_Steel_Settings,
            )
        )
        self.actionStructural_Steel_Settings.setChecked(
            self.settings_file.get_value("tab_visibility").get("Structural Steel Settings", True))
        self.actionStructural_Steel_Settings.setIcon(Icons.sheet_settings_icon)
        self.actionSheet_Settings.triggered.connect(partial(self.toggle_tab_visibility, self.actionSheet_Settings))
        self.actionSheet_Settings.setChecked(self.settings_file.get_value("tab_visibility").get("Sheet Settings", True))
        self.actionSheet_Settings.setIcon(Icons.sheet_settings_icon)
        self.actionJob_Planner.triggered.connect(partial(self.toggle_tab_visibility, self.actionJob_Planner))
        self.actionJob_Planner.setChecked(self.settings_file.get_value("tab_visibility").get("Job Planner", True))
        self.actionJob_Planner.setIcon(Icons.job_planner_icon)
        self.actionJob_Quoter.triggered.connect(partial(self.toggle_tab_visibility, self.actionJob_Quoter))
        self.actionJob_Quoter.setChecked(self.settings_file.get_value("tab_visibility").get("Job Quoter", True))
        self.actionJob_Quoter.setIcon(Icons.calculator_icon)
        self.actionWorkspace.triggered.connect(partial(self.toggle_tab_visibility, self.actionWorkspace))
        self.actionWorkspace.setChecked(self.settings_file.get_value("tab_visibility").get("Workspace", True))
        self.actionWorkspace.setIcon(Icons.action_workspace_icon)

        self.menuTheme.setIcon(Icons.paint_icon)
        self.actionLight.triggered.connect(partial(self.set_color_theme, "light_theme"))
        self.actionLight.setIcon(Icons.sun_icon)

        self.actionDark.triggered.connect(partial(self.set_color_theme, "dark_theme"))
        self.actionDark.setIcon(Icons.moon_icon)

        self.actionStart_Maximized.triggered.connect(partial(self.toggle_maximized, self.actionStart_Maximized))
        self.actionStart_Maximized.setChecked(self.settings_file.get_value("show_maximized"))
        self.actionStart_Maximized.setIcon(Icons.maximized_icon)

        # SORT BY
        self.actionAlphabatical.triggered.connect(
            partial(
                self.action_group,
                "sorting",
                [
                    self.actionQuantity_in_Stock,
                    self.actionAlphabatical,
                ],
            )
        )
        self.actionAlphabatical.setChecked(self.settings_file.get_value(setting_name="sort_alphabatical"))
        self.actionAlphabatical.setEnabled(not self.settings_file.get_value(setting_name="sort_alphabatical"))
        self.actionQuantity_in_Stock.triggered.connect(
            partial(
                self.action_group,
                "sorting",
                [
                    self.actionQuantity_in_Stock,
                    self.actionAlphabatical,
                ],
            )
        )
        self.actionQuantity_in_Stock.setChecked(self.settings_file.get_value(setting_name="sort_quantity_in_stock"))
        self.actionQuantity_in_Stock.setEnabled(not self.settings_file.get_value(setting_name="sort_quantity_in_stock"))
        self.actionAscending.setChecked(self.settings_file.get_value(setting_name="sort_ascending"))
        self.actionAscending.setEnabled(not self.settings_file.get_value(setting_name="sort_ascending"))
        self.actionAscending.triggered.connect(
            partial(
                self.action_group,
                "order",
                [self.actionAscending, self.actionDescending],
            )
        )
        self.actionDescending.setChecked(self.settings_file.get_value(setting_name="sort_descending"))
        self.actionDescending.setEnabled(not self.settings_file.get_value(setting_name="sort_descending"))
        self.actionDescending.triggered.connect(
            partial(
                self.action_group,
                "order",
                [self.actionAscending, self.actionDescending],
            )
        )
        self.actionSort.triggered.connect(self.apply_sort)
        self.actionSort.setIcon(Icons.sort_icon)
        self.update_sorting_status_text()

        # PURCHASE ORDERS
        self.actionCreate_New_Purchase_Order.triggered.connect(self.create_purchase_order)
        self.actionCreate_New_Purchase_Order.setIcon(Icons.add_file_icon)
        self.actionOpen_Latest_Purchase_Order.triggered.connect(self.open_latest_purchase_order)
        self.menuPurchase_Orders_2.setIcon(Icons.action_history_icon)

        self.actionAdd_New_Vendor.triggered.connect(self.add_new_vendor)
        self.actionAdd_New_Vendor.setIcon(Icons.add_file_icon)

        self.actionDelete_Vendor.triggered.connect(self.delete_vendor)
        self.actionDelete_Vendor.setIcon(Icons.remove_file_icon)
        self.menuEdit_Vendors.setIcon(QIcon(Icons.edit_icon))

        self.actionAdd_New_Shipping_Address.triggered.connect(self.add_new_shipping_address)
        self.actionAdd_New_Shipping_Address.setIcon(Icons.add_file_icon)

        self.actionDelete_Shipping_Address.triggered.connect(self.delete_shipping_address)
        self.actionDelete_Shipping_Address.setIcon(Icons.remove_file_icon)
        self.menuEdit_Shiping_Addresses.setIcon(QIcon(Icons.edit_icon))

        self.actionEdit_Contact_Info.triggered.connect(self.edit_contact_info)
        self.actionEdit_Contact_Info.setIcon(Icons.edit_icon)

        self.actionEdit_Business_Info.triggered.connect(self.edit_business_info)
        self.actionEdit_Business_Info.setIcon(Icons.edit_icon)
        # self.actionAdd_Purchase_Order.triggered.connect(
        #     partial(self.add_po_templates, [], True)
        # )
        # self.actionAdd_Purchase_Order.setIcon(Icons.add_file_icon)
        # self.actionRemove_Purchase_Order.triggered.connect(self.delete_po)
        # self.actionRemove_Purchase_Order.setIcon(Icons.remove_file_icon)
        # self.actionOpen_Purchase_Order.triggered.connect(partial(self.open_po, None))
        # self.actionOpen_Purchase_Order.setIcon(Icons.generate_file_icon)
        # self.actionOpen_Folder.triggered.connect(partial(self.open_folder, "PO's"))
        # self.actionOpen_Folder.setIcon(Icons.open_folder_icon)

        # QUOTE GENERATOR
        self.actionAdd_Nest_Directory.triggered.connect(self.add_nest_directory)
        self.actionAdd_Nest_Directory.setIcon(Icons.add_folder_icon)
        self.actionRemove_Nest_Directory.triggered.connect(self.remove_nest_directory)
        self.actionRemove_Nest_Directory.setIcon(Icons.remove_folder_icon)

        # PAINT INVENTORY
        self.actionEdit_Paint_in_Inventory.triggered.connect(self.edit_paint_inventory)
        self.actionEdit_Paint_in_Inventory.setIcon(Icons.paint_brush_icon)

        # JOB SORTER
        self.actionOpenMenu.triggered.connect(self.open_job_sorter)
        self.actionOpenMenu.setIcon(Icons.open_window_icon)

        # WORKSPACE
        self.actionEditTags.triggered.connect(self.open_tag_editor)
        self.actionEditTags.setIcon(Icons.edit_workspace_settings_icon)

        # FILE
        self.actionOpen_Item_History.triggered.connect(self.open_item_history)
        self.actionOpen_Item_History.setIcon(Icons.generate_file_icon)
        self.actionRemoved_Component_Quantity_History.triggered.connect(self.view_removed_component_quantity_history)
        self.actionRemoved_Component_Quantity_History.setIcon(Icons.action_history_icon)

        self.actionExit.triggered.connect(self.close)
        self.actionExit.setIcon(Icons.quit_icon)
        # self.actionExit.setIcon(QIcon("icons/tab_close.png"))

    def load_job_planning_tab(self):
        if self.has_loaded_job_planner_tab:
            return

        self.clear_layout(self.job_planner_layout)
        self.job_planner_widget = JobTab(self.stack_tab_buttons_data["Job Planner"], self)
        self.job_planner_widget.default_job_status = JobStatus.PLANNING
        self.job_planner_widget.saveJob.connect(self.save_job)
        self.job_planner_widget.printJob.connect(self.print_job)
        self.job_planner_widget.reloadJob.connect(self.reload_job)
        self.job_planner_widget.add_job()
        self.job_planner_layout.addWidget(self.job_planner_widget)
        self.has_loaded_job_planner_tab = True

    def load_job_quoting_tab(self):
        if self.has_loaded_job_quoter_tab:
            return

        self.clear_layout(self.quote_generator_layout)
        self.job_quote_widget = JobTab(self.stack_tab_buttons_data["Job Quoter"], self)
        self.job_quote_widget.default_job_status = JobStatus.QUOTING
        self.job_quote_widget.saveJob.connect(self.save_job)
        self.job_quote_widget.printJob.connect(self.print_job)
        self.job_quote_widget.reloadJob.connect(self.reload_job)
        self.job_quote_widget.add_job()
        self.quote_generator_layout.addWidget(self.job_quote_widget)
        self.has_loaded_job_quoter_tab = True

    def load_paint_inventory_tab(self):
        # Nothing needs to be done
        pass

    def load_sheets_inventory_tab(self):
        current_tab = self.tab_text(self.stackedWidget.currentIndex())
        self.clear_layout(self.sheets_inventory_layout)
        self.sheets_inventory_tab_widget = SheetsInInventoryTab(self)
        self.sheets_inventory_layout.addWidget(self.sheets_inventory_tab_widget)
        if current_tab == "sheets_in_inventory_tab":
            self.update_sheets_inventory_tab()
        self.is_sheets_inventory_ui_loaded = True
        self.should_update_sheets_in_inventory_tab = False

    def update_sheets_inventory_tab(self):
        if not self.should_update_sheets_in_inventory_tab:
            return
        if self.tab_text(self.stackedWidget.currentIndex()) == "sheets_in_inventory_tab":
            self.sheets_inventory_tab_widget.block_table_signals()
            self.sheets_inventory_tab_widget.load_categories()
            self.sheets_inventory.sort_by_thickness()
            self.sheets_inventory_tab_widget.restore_last_selected_tab()
            self.sheets_inventory_tab_widget.update_stock_costs()
            self.sheets_inventory_tab_widget.unblock_table_signals()
            self.should_update_sheets_in_inventory_tab = False

    def load_components_inventory_tab(self):
        self.paint_inventory.load_data(
            on_loaded=self.load_paint_inventory_tab)  # Paint inventory is depdendent on components inventory
        # We load these because components tab is depended on them, they might be loaded ahead of time or they might not be
        self.load_job_planning_tab()
        self.load_job_quoting_tab()
        self.clear_layout(self.components_layout)
        self.components_tab_widget = ComponentsTab(self)
        self.components_layout.addWidget(self.components_tab_widget)
        if self.tab_text(self.stackedWidget.currentIndex()) == "components_tab":
            self.update_components_inventory_tab()
        self.is_components_inventory_ui_loaded = True
        self.should_update_components_in_inventory_tab = False

    def update_components_inventory_tab(self):
        if not self.should_update_components_in_inventory_tab:
            return
        if self.tab_text(self.stackedWidget.currentIndex()) == "components_tab":
            self.components_tab_widget.block_table_signals()
            self.components_tab_widget.load_categories()
            self.components_tab_widget.sort_components()
            self.components_tab_widget.unblock_table_signals()
            self.should_update_components_in_inventory_tab = False

    def load_laser_cut_inventory_tab(self):
        self.load_job_planning_tab()
        self.load_job_quoting_tab()
        self.clear_layout(self.laser_cut_layout)
        self.laser_cut_parts_tab_widget = LaserCutTab(self)
        self.laser_cut_layout.addWidget(self.laser_cut_parts_tab_widget)
        if self.tab_text(self.stackedWidget.currentIndex()) == "laser_cut_tab":
            self.update_laser_cut_inventory_tab()
        self.is_laser_cut_parts_inventory_ui_loaded = True
        self.should_update_laser_cut_inventory_tab = False

    def update_laser_cut_inventory_tab(self):
        if not self.should_update_laser_cut_inventory_tab:
            return
        if self.tab_text(self.stackedWidget.currentIndex()) == "laser_cut_tab":
            self.laser_cut_parts_tab_widget.block_table_signals()
            self.laser_cut_parts_tab_widget.load_categories()
            self.laser_cut_parts_tab_widget.sort_laser_cut_parts()
            self.laser_cut_parts_tab_widget.unblock_table_signals()
            self.should_update_laser_cut_inventory_tab = False

    def load_inventory_vendors(self):
        self.components_tab_widget.load_inventory_vendors()
        self.sheets_inventory_tab_widget.load_inventory_vendors()

    # * \/ SLOTS & SIGNALS \/
    def tool_box_menu_changed(self):
        if self.last_selected_menu_tab == "Job Planner" and self.job_planner_widget.get_active_job().unsaved_changes:
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "Unsaved changes",
                f"There are unsaved changes in Job Planner, {self.job_planner_widget.get_active_job().name}.",
            )
            msg.exec()
        if self.last_selected_menu_tab == "Job Quoter" and self.job_quote_widget.get_active_job().unsaved_changes:
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "Unsaved changes",
                f"There are unsaved changes in Job Quoter, {self.job_quote_widget.get_active_job().name}.",
            )
            msg.exec()

        current_tab = self.tab_text(self.stackedWidget.currentIndex())

        if current_tab == "components_tab" and self.is_components_inventory_ui_loaded:
            self.menuSort.setEnabled(True)
            self.update_components_inventory_tab()
        elif current_tab == "sheets_in_inventory_tab" and self.is_sheets_inventory_ui_loaded:
            self.menuSort.setEnabled(True)
            self.update_sheets_inventory_tab()
        elif current_tab == "laser_cut_inventory_tab" and self.is_laser_cut_parts_inventory_ui_loaded:
            self.menuSort.setEnabled(True)
            self.update_laser_cut_inventory_tab()
        elif current_tab == "sheet_settings_tab":
            self.sheet_settings_tab_widget.load_tabs()
        elif current_tab == "structural_steel_settings_tab":
            self.structural_steel_settings_tab_widget.load_tabs()
        elif current_tab == "quote_generator_tab":
            self.load_cuttoff_drop_down()
            self.load_saved_quoted_thread()
            self.load_previous_quotes_thread()
            self.refresh_nest_directories()
            for quote_widget in self.quote_generator_tab_widget.quotes:
                quote_widget.update_sheet_statuses()
        elif current_tab == "job_quoter_tab":
            self.load_tree_widget_cuttoff_drop_down(self.treeWidget_cutoff_sheets)
            self.refresh_nest_directories()
            self.load_jobs_worker()
            self.job_quote_widget.update_tables()
        elif current_tab == "job_planner_tab":
            self.load_jobs_worker()
            self.job_planner_widget.update_tables()
        elif current_tab == "workspace_tab":
            self.load_tree_widget_cuttoff_drop_down(self.treeWidget_cutoff_sheets_2)
            self.refresh_nest_directories()
            if self.should_update_workspace_tab:
                # self.workspace_tab_widget.load_tags()
                # self.workspace_tab_widget.load_menu_buttons()
                # self.workspace_tab_widget.load_sort_button()
                self.should_update_workspace_tab = False

        # self.loading_screen.hide()

    def apply_sort(self):
        # Because each of these gets deleted when not in view
        with contextlib.suppress(AttributeError, RuntimeError):
            if self.tab_text(self.stackedWidget.currentIndex()) == "components_tab":
                self.status_button.setText("Sorted Components", "lime")
                self.components_tab_widget.sort_components()
            elif self.tab_text(self.stackedWidget.currentIndex()) == "sheets_in_inventory_tab":
                self.status_button.setText("Sorted Sheets", "lime")
                self.sheets_inventory_tab_widget.sort_sheets()
            elif self.tab_text(self.stackedWidget.currentIndex()) == "laser_cut_inventory_tab":
                self.laser_cut_parts_tab_widget.sort_laser_cut_parts()
                self.status_button.setText("Sorted Laser Cut Parts", "lime")

    def action_group(self, group_name: str, actions: list[QAction]):
        self.settings_file.load_data()
        if group_name == "order":
            if self.settings_file.get_value(setting_name="sort_descending"):
                actions[1].setChecked(False)
                actions[0].setEnabled(False)
                actions[1].setEnabled(True)
            elif self.settings_file.get_value(setting_name="sort_ascending"):
                actions[0].setChecked(False)
                actions[1].setEnabled(False)
                actions[0].setEnabled(True)
        elif group_name == "sorting":
            if self.settings_file.get_value(setting_name="sort_alphabatical"):
                actions[1].setChecked(False)
                actions[0].setEnabled(False)
                actions[1].setEnabled(True)
            elif self.settings_file.get_value(setting_name="sort_quantity_in_stock"):
                actions[0].setChecked(False)
                actions[0].setEnabled(True)
                actions[1].setEnabled(False)

        self.settings_file.set_value(
            "sort_quantity_in_stock",
            self.actionQuantity_in_Stock.isChecked(),
        )
        self.settings_file.set_value(
            "sort_alphabatical",
            self.actionAlphabatical.isChecked(),
        )
        self.settings_file.set_value(
            "sort_ascending",
            self.actionAscending.isChecked(),
        )
        self.settings_file.set_value(
            "sort_descending",
            self.actionDescending.isChecked(),
        )
        self.update_sorting_status_text()

    def edit_paint_inventory(self):
        dialog = EditPaintInventory(self.paint_inventory, self)
        dialog.show()

    def process_selected_nests(self):
        if self.quote_generator_tab_widget.current_quote.downloaded_from_server:
            msg = QMessageBox(
                QMessageBox.Icon.Question,
                "Overwrite changes",
                f"You are about to overwrite this quote from your view. This action will not change the quote from the server. It will only be changed from your current session.\n\nAre you sure you want to overwrite {self.quote_generator_tab_widget.current_quote.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                self,
            )
            response = msg.exec()
            if response in [
                QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Cancel,
            ]:
                return
        if selected_items := self.get_all_selected_nests():
            self.generate_quote_thread(selected_items)

    def process_selected_nests_to_job(self):
        current_job = self.job_planner_widget.current_job
        if current_job.downloaded_from_server and current_job.unsaved_changes:
            msg = QMessageBox(
                QMessageBox.Icon.Question,
                "Overwrite Nests",
                f"You are about to overwrite this jobs nests. This action will not change the job from the server. It will only be changed from your current session until you save it.\n\nAre you sure you want to overwrite {current_job.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                self,
            )
            response = msg.exec()
            if response in [
                QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Cancel,
            ]:
                return
        if selected_items := self.get_all_selected_job_quotes():
            self.load_nests_for_job_thread(selected_items)

    def workspace_process_selected_nests(self):
        if selected_items := self.get_all_selected_workspace_nests():
            self.load_nests_for_workspace_thread(selected_items)

    # def cutoff_sheet_double_clicked(self, cutoff_items: QListWidget):
    #     cutoff_sheets = self.sheets_inventory.get_sheets_by_category("Cutoff")
    #     item_pressed: QListWidgetItem = cutoff_items.selectedItems()[0]
    #     for sheet in cutoff_sheets:
    #         if item_pressed.text() == sheet.get_name():
    #             self.quote_generator_tab_widget.quotes[
    #                 self.quote_generator_tab_widget.tab_widget.currentIndex()
    #             ].comboBox_global_sheet_material_2.setCurrentText(sheet.material)
    #             self.quote_generator_tab_widget.quotes[
    #                 self.quote_generator_tab_widget.tab_widget.currentIndex()
    #             ].comboBox_global_sheet_thickness_2.setCurrentText(sheet.thickness)
    #             self.quote_generator_tab_widget.quotes[
    #                 self.quote_generator_tab_widget.tab_widget.currentIndex()
    #             ].doubleSpinBox_global_sheet_length_2.setValue(sheet.length)
    #             self.quote_generator_tab_widget.quotes[
    #                 self.quote_generator_tab_widget.tab_widget.currentIndex()
    #             ].doubleSpinBox_global_sheet_width_2.setValue(sheet.width)
    #             self.quote_generator_tab_widget.quotes[
    #                 self.quote_generator_tab_widget.tab_widget.currentIndex()
    #             ].global_sheet_materials_changed()
    #             self.quote_generator_tab_widget.quotes[
    #                 self.quote_generator_tab_widget.tab_widget.currentIndex()
    #             ].global_sheet_materials_changed()
    #             self.quote_generator_tab_widget.quotes[
    #                 self.quote_generator_tab_widget.tab_widget.currentIndex()
    #             ].global_sheet_dimension_changed()
    #             self.quote_generator_tab_widget.quotes[
    #                 self.quote_generator_tab_widget.tab_widget.currentIndex()
    #             ].update_sheet_statuses()
    #             return

    def tree_widget_cutoff_sheet_double_clicked(self):
        cutoff_sheets = self.sheets_inventory.get_sheets_by_category("Cutoff")
        item_pressed = self.treeWidget_cutoff_sheets.selectedItems()[0]
        for sheet in cutoff_sheets:
            if item_pressed.text(0) == sheet.get_name():
                self.status_button.setText(
                    f"Applying cutoff sheet ({sheet.get_name()}) settings to nests...",
                    "yellow",
                )
                active_job_widget = self.job_quote_widget.get_active_job_widget()
                active_job_widget.comboBox_materials.setCurrentText(sheet.material)
                active_job_widget.comboBox_thicknesses.setCurrentText(sheet.thickness)
                active_job_widget.doubleSpinBox_length.setValue(sheet.length)
                active_job_widget.doubleSpinBox_width.setValue(sheet.width)
                for nest_Widget in active_job_widget.nest_widgets:
                    nest_Widget.sheet_changed()
                self.status_button.setText(
                    f"Applied cutoff sheet ({sheet.get_name()}) settings to nests",
                    "lime",
                )
                return

    # def workspace_tab_changed(self, tab_name: str):
    #     # self.workspace_tab_widget_last_selected_tab = tab_name
    #     if any(keyword in tab_name.lower() for keyword in ["laser"]):
    #         self.splitter_4.setSizes([1, 1])
    #         # # self.workspace_tab_widget.workspace_widget.get_all_recut_parts_thread()
    #     else:
    #         self.splitter_4.setSizes([1, 0])

    # * /\ SLOTS & SIGNALS /\

    # * \/ UPDATE UI ELEMENTS \/
    def load_po_menus(self):
        def load_purchase_order_menu():
            self.menuPurchase_Orders_2.clear()
            organized_purchase_orders = self.purchase_order_manager.get_organized_purchase_orders()
            for vendor_name, purchase_orders in organized_purchase_orders.items():
                has_po_as_draft = False
                vendor_menu = QMenu(vendor_name, self.menuPurchase_Orders_2)
                vendor = self.purchase_order_manager.get_vendor_by_name(vendor_name)
                create_purchase_order_action = QAction("Create Purchase Order", self.menuPurchase_Orders_2)
                create_purchase_order_action.setIcon(QIcon(Icons.add_file_icon))
                create_purchase_order_action.triggered.connect(partial(self.create_purchase_order, vendor))
                vendor_menu.addAction(create_purchase_order_action)
                for purchase_order in purchase_orders:
                    action = QAction(purchase_order.get_name(), self.menuPurchase_Orders_2)
                    if purchase_order.meta_data.is_draft:
                        has_po_as_draft = True
                        action.setIcon(QIcon(Icons.purchase_order_draft_icon))
                    else:
                        action.setIcon(QIcon(Icons.edit_icon))
                    action.triggered.connect(partial(self.open_purchase_order, purchase_order))
                    vendor_menu.addAction(action)
                if has_po_as_draft:
                    vendor_menu.setIcon(QIcon(Icons.purchase_order_draft_icon))
                self.menuPurchase_Orders_2.addMenu(vendor_menu)

        def load_vendors_menu():
            self.menuEdit_Vendors.clear()
            for vendor in self.purchase_order_manager.vendors:
                action = QAction(vendor.name, self.menuEdit_Vendors)
                action.setIcon(QIcon(Icons.edit_icon))
                action.triggered.connect(partial(self.edit_vendor, vendor))
                self.menuEdit_Vendors.addAction(action)

        def load_shipping_addresses_menu():
            self.menuEdit_Shiping_Addresses.clear()
            for shipping_address in self.purchase_order_manager.shipping_addresses:
                action = QAction(shipping_address.name, self.menuEdit_Shiping_Addresses)
                action.setIcon(QIcon(Icons.edit_icon))
                action.triggered.connect(partial(self.edit_shipping_address, shipping_address))
                self.menuEdit_Shiping_Addresses.addAction(action)

        def after_load():
            load_purchase_order_menu()
            load_vendors_menu()
            load_shipping_addresses_menu()
            QTimer.singleShot(250, self.load_inventory_vendors)

        self.purchase_order_manager.load_data(on_finished=after_load)

    def set_color_theme(self, theme: str):
        self.settings_file.set_value("theme", theme)

        msg = QMessageBox(
            QMessageBox.Icon.Information,
            "Restart Invigo",
            "You need to restart Invigo for the theme to take effect.",
            QMessageBox.StandardButton.Ok,
            self,
        )
        msg.exec()

    def toggle_maximized(self, action: QAction):
        if action.isChecked():
            self.showMaximized()

        self.settings_file.load_data()
        self.settings_file.set_value("show_maximized", action.isChecked())
        self.settings_file.save_data()

    def change_tables_font(self):
        font, ok = QFontDialog.getFont()
        if ok:
            font_data = {
                "family": font.family(),
                "pointSize": font.pointSize(),
                "weight": font.weight(),
                "italic": font.italic(),
            }
            self.tables_font.setFamily(font.family())
            self.tables_font.setPointSize(font.pointSize())
            self.tables_font.setWeight(font.weight())
            self.tables_font.setItalic(font.italic())
            self.settings_file.set_value("tables_font", font_data)

    def update_sorting_status_text(self):
        sorting_from_alphabet: str = "A"
        sorting_to_alphabet: str = "Z"

        sorting_from_number: str = "0"
        sorting_to_number: str = "9"

        if self.actionAscending.isChecked():
            self.actionAlphabatical.setStatusTip(f"Sort from {sorting_from_alphabet} to {sorting_to_alphabet}")
            self.actionQuantity_in_Stock.setStatusTip(f"Sort from {sorting_from_number} to {sorting_to_number}")
        else:
            self.actionAlphabatical.setStatusTip(f"Sort from {sorting_to_alphabet} to {sorting_from_alphabet}")
            self.actionQuantity_in_Stock.setStatusTip(f"Sort from {sorting_to_number} to {sorting_from_number}")

        if self.actionAlphabatical.isChecked():
            if self.actionAscending.isChecked():
                self.actionSort.setStatusTip(f"Sort from {sorting_from_alphabet} to {sorting_to_alphabet}")
            else:
                self.actionSort.setStatusTip(f"Sort from {sorting_to_alphabet} to {sorting_from_alphabet}")
            self.actionAscending.setStatusTip(f"Sort from {sorting_from_alphabet} to {sorting_to_alphabet}")
            self.actionDescending.setStatusTip(f"Sort from {sorting_to_alphabet} to {sorting_from_alphabet}")
        elif self.actionQuantity_in_Stock.isChecked():
            if self.actionAscending.isChecked():
                self.actionSort.setStatusTip(f"Sort from {sorting_from_number} to {sorting_to_number}")
            else:
                self.actionSort.setStatusTip(f"Sort from {sorting_to_number} to {sorting_from_number}")
            self.actionAscending.setStatusTip(f"Sort from {sorting_from_number} to {sorting_to_number}")
            self.actionDescending.setStatusTip(f"Sort from {sorting_to_number} to {sorting_from_number}")

    def set_table_row_color(self, table, row_index, color):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def set_table_row_text_color(self, table, row_index, color):
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setForeground(QColor(color))

    def clear_job_quote_selections(self):
        for tree_view in self.toolbox_job_nest_directories_list_widgets.values():
            tree_view.clearSelection()

    def clear_workspace_nest_selections(self):
        for tree_view in self.toolbox_workspace_nest_directories_list_widgets.values():
            tree_view.clearSelection()

    def job_quote_directory_item_selected(self):
        # self.process_selected_nests()
        selected_nests = len(self.get_all_selected_job_quotes())
        if selected_nests == 0:
            self.pushButton_load_nests_2.setEnabled(False)
        else:
            self.pushButton_load_nests_2.setEnabled(True)
        self.pushButton_load_nests_2.setText(f"Import {selected_nests} Nest{'' if selected_nests == 1 else 's'}")

    def workspace_directory_item_selected(self):
        selected_nests = len(self.get_all_selected_workspace_nests())
        if selected_nests == 0:
            self.pushButton_load_nests_3.setEnabled(False)
        else:
            self.pushButton_load_nests_3.setEnabled(True)
        self.pushButton_load_nests_3.setText(f"Load {selected_nests} Nest{'' if selected_nests == 1 else 's'}")

    def save_scroll_position(self, category: Category, table: CustomTableWidget):
        self.scroll_position_manager.save_scroll_position(
            f"{self.tab_text(self.stackedWidget.currentIndex())} - {category.name}",
            table,
        )

    def get_scroll_position(self, category: Category) -> QPoint:
        return self.scroll_position_manager.get_scroll_position(
            f"{self.tab_text(self.stackedWidget.currentIndex())} - {category.name}")

    # * /\ UPDATE UI ELEMENTS /\
    # * \/ GETTERS \/

    def get_exchange_rate(self) -> float:
        return self.settings_file.get_value(setting_name="exchange_rate")

    def get_all_selected_job_quotes(self) -> list[str]:
        selected_nests = []
        for tree_view in self.toolbox_job_nest_directories_list_widgets.values():
            selected_nests.extend(tree_view.full_paths)
        return list(set(selected_nests))

    def get_all_selected_workspace_nests(self) -> list[str]:
        selected_nests = []
        for tree_view in self.toolbox_workspace_nest_directories_list_widgets.values():
            selected_nests.extend(tree_view.full_paths)
        return list(set(selected_nests))

    def get_menu_tab_order(self) -> list[str]:
        return [widget.text() for widget in self.menu_tab_manager.findChildren(QPushButton)]

    def get_tab_from_name(self, name: str) -> int:
        return next(
            (i for i in range(self.stackedWidget.count()) if self.stackedWidget.widget(i).objectName() == name),
            -1,
        )

    def get_all_selected_parts(self, tab: CustomTableWidget) -> list[str]:
        selected_rows = tab.selectedItems()
        all_items = list(self.parts_in_inventory_name_lookup.keys())

        selected_items: list[str] = [item.text() for item in selected_rows if
                                     item.text() in all_items and item.column() == 0]
        return selected_items

    # * /\ GETTERS /\
    def job_generator(self):
        job_generator_dialog = JobGeneratorDialog(self)
        if job_generator_dialog.exec():
            if job := job_generator_dialog.merge():
                self.job_planner_widget.load_job(job)

    def save_geometry(self):
        geometry = self.settings_file.get_value("geometry")
        geometry["x"] = max(self.pos().x(), 0)
        geometry["y"] = max(self.pos().y(), 0)
        geometry["width"] = self.size().width()
        geometry["height"] = self.size().height()
        self.settings_file.set_value("geometry", geometry)

    def save_menu_tab_order(self):
        self.settings_file.set_value("tabs_order", self.get_menu_tab_order())

    # * \/ Dialogs \/
    def edit_contact_info(self):
        self.contact_info_dialog = EditContactInfoDialog(self)
        self.contact_info_dialog.show()

    def edit_business_info(self):
        self.business_info_dialog = EditBusinessInfoDialog(self)
        self.business_info_dialog.show()

    def open_purchase_order(self, purchase_order: PurchaseOrder):
        self.purchase_order_dialog = PurchaseOrderDialog(self, self.purchase_order_manager, purchase_order)
        self.purchase_order_dialog.closed.connect(self.components_tab_widget.sort_components)
        self.purchase_order_dialog.closed.connect(self.sheets_inventory_tab_widget.sort_sheets)
        self.purchase_order_dialog.closed.connect(self.load_po_menus)
        self.purchase_order_dialog.show()

    def add_components_to_purchase_order(self, components: list[Component]):
        if not hasattr(self, "purchase_order_dialog"):
            self.create_purchase_order()
        if self.purchase_order_dialog:
            for component in components:
                self.purchase_order_dialog.purchase_order.set_component_order_quantity(component, 0)
            self.purchase_order_dialog.purchase_order.components.extend(components)
            self.purchase_order_dialog.load_components_table()
        else:
            self.create_purchase_order()
            for component in components:
                self.purchase_order_dialog.purchase_order.set_component_order_quantity(component, 0)
            self.purchase_order_dialog.purchase_order.components.extend(components)
            self.purchase_order_dialog.load_components_table()

    def add_sheets_to_purchase_order(self, sheets: list[Sheet]):
        if not hasattr(self, "purchase_order_dialog"):
            self.create_purchase_order()
        if self.purchase_order_dialog:
            for sheet in sheets:
                self.purchase_order_dialog.purchase_order.set_sheet_order_quantity(sheet, 0)
            self.purchase_order_dialog.purchase_order.sheets.extend(sheets)
            self.purchase_order_dialog.load_sheets_table()
        else:
            self.create_purchase_order()
            for sheet in sheets:
                self.purchase_order_dialog.purchase_order.set_sheet_order_quantity(sheet, 0)
            self.purchase_order_dialog.purchase_order.sheets.extend(sheets)
            self.purchase_order_dialog.load_sheets_table()

    def create_purchase_order(self, vendor: Vendor | None = None):
        new_purchase_order = PurchaseOrder(self.components_inventory, self.sheets_inventory)
        if vendor:
            new_purchase_order.meta_data.vendor = vendor
        self.purchase_order_dialog = PurchaseOrderDialog(self, self.purchase_order_manager, new_purchase_order)
        self.purchase_order_dialog.closed.connect(self.components_tab_widget.sort_components)
        self.purchase_order_dialog.closed.connect(self.sheets_inventory_tab_widget.sort_sheets)
        self.purchase_order_dialog.closed.connect(self.load_po_menus)
        self.purchase_order_dialog.show()

    def open_latest_purchase_order(self):
        if getattr(self, "purchase_order_dialog", None):
            self.purchase_order_dialog.show()
        else:
            self.create_purchase_order()

    def add_new_vendor(self):
        new_vendor_dialog = AddVendorDialog(self)
        if new_vendor_dialog.exec():
            self.purchase_order_manager.add_vendor(new_vendor_dialog.get_vendor(), on_finished=self.load_po_menus)

    def edit_vendor(self, vendor: Vendor):
        edit_vendor_dialog = AddVendorDialog(self, vendor)
        if edit_vendor_dialog.exec():
            self.purchase_order_manager.save_vendor(edit_vendor_dialog.get_vendor(), on_finished=self.load_po_menus)

    def delete_vendor(self):
        vendor_to_remove, ok = QInputDialog.getItem(
            self,
            "Delete Vendor",
            "Select the vendor to delete:",
            [f"{vendor.name} (id: {vendor.id})" for vendor in self.purchase_order_manager.vendors],
            0,
            False,
        )
        if vendor_to_remove and ok:
            for vendor in self.purchase_order_manager.vendors:
                name = f"{vendor.name} (id: {vendor.id})"
                if vendor_to_remove == name:
                    self.purchase_order_manager.delete_vendor(vendor, on_finished=self.load_po_menus)
                    break

    def add_new_shipping_address(self):
        new_shipping_address_dialog = EditShippingAddressDialog(self)
        if new_shipping_address_dialog.exec():
            self.purchase_order_manager.add_shipping_address(new_shipping_address_dialog.get_shipping_address(),
                                                             on_finished=self.load_po_menus)

    def edit_shipping_address(self, shipping_address: ShippingAddress):
        edit_shipping_address_dialog = EditShippingAddressDialog(self, shipping_address)
        if edit_shipping_address_dialog.exec():
            self.purchase_order_manager.save_shipping_address(edit_shipping_address_dialog.get_shipping_address(),
                                                              on_finished=self.load_po_menus)

    def delete_shipping_address(self):
        shipping_address_to_remove, ok = QInputDialog.getItem(
            self,
            "Delete Shipping Address",
            "Select the shipping address to delete:",
            [f"{shipping_address.name} (id: {shipping_address.id})" for shipping_address in
             self.purchase_order_manager.shipping_addresses],
            0,
            False,
        )
        if shipping_address_to_remove and ok:
            for shipping_address in self.purchase_order_manager.shipping_addresses:
                name = f"{shipping_address.name} (id: {shipping_address.id})"
                if shipping_address_to_remove == name:
                    self.purchase_order_manager.delete_shipping_address(shipping_address,
                                                                        on_finished=self.load_po_menus)
                    break

    # def open_edit_user_workspace_settings(self):
    #     edit_user_workspace_dialog = EditUserWorkspaceSettingsDialog(self.workspace_settings, self)
    #     if edit_user_workspace_dialog.exec():
    #         with contextlib.suppress(AttributeError):
    #             self.workspace_tab_widget.user_workspace_settings_changed()

    def show_about_dialog(self):
        dialog = AboutDialog(
            self,
            __version__,
            "https://github.com/TheCodingJsoftware/Invigo",
        )
        dialog.show()

    def open_group_menu(self, menu: QMenu):
        menu.exec(QCursor.pos())

    def add_nest_directory(self):
        nest_directories: list[str] = self.settings_file.get_value("quote_nest_directories")
        if new_nest_directory := QFileDialog.getExistingDirectory(self, "Open directory", "/"):
            nest_directories.append(new_nest_directory)
            self.settings_file.set_value("quote_nest_directories", nest_directories)
            self.refresh_nest_directories()

    def remove_nest_directory(self):
        nest_directories: list[str] = self.settings_file.get_value("quote_nest_directories")
        select_item_dialog = SelectItemDialog(
            DialogButtons.discard_cancel,
            "Remove Nest Directory",
            "Select a nest directory to delete. (from gui. not system)\n\nThis action is permanent and cannot be undone.",
            nest_directories,
            self,
        )

        if select_item_dialog.exec():
            response = select_item_dialog.get_response()
            if response == DialogButtons.discard:
                try:
                    nest_directories.remove(select_item_dialog.get_selected_item())
                except ValueError:  # No Item was selected
                    return
                self.settings_file.set_value("quote_nest_directories", nest_directories)
                self.refresh_nest_directories()
            elif response == DialogButtons.cancel:
                return

    def reload_job(self, job_widget: JobWidget):
        job = job_widget.job
        self.reload_job_worker(job.id)

    def get_active_job(self) -> Job | None:
        if self.tab_text(self.stackedWidget.currentIndex()) == "job_planner_tab":
            return self.job_planner_widget.get_active_job()
        elif self.tab_text(self.stackedWidget.currentIndex()) == "job_quoter_tab":
            return self.job_quote_widget.get_active_job()
        return None

    def save_job(self, job: Job | None):
        if job is None:
            job = self.get_active_job()
        if job is None:
            msg = QMessageBox(
                QMessageBox.Icon.Critical,
                "Critical",
                "Active job could not be found. Aborted.\n\nHow did this happen?",
            )
            msg.exec()
            return

        self.save_job_worker(job)
        job.unsaved_changes = False
        self.job_planner_widget.update_job_save_status(job)
        self.status_button.setText(f"Saved {job.name}", "lime")

    def print_job(self, job: Job | None):
        if job is None:
            job = self.get_active_job()
        if job is None:
            msg = QMessageBox(
                QMessageBox.Icon.Critical,
                "Critical",
                "Active job could not be found. Aborted.\n\nHow did this happen?",
            )
            msg.exec()
            return

        self.print_job_worker(job)
        job.unsaved_changes = False
        self.job_planner_widget.update_job_save_status(job)
        self.status_button.setText(f"Saved {job.name}", "lime")

    def add_job_to_production_plan(
            self,
            job_widget: JobTab,
            jobs_data: dict[str, int],
            should_update_components: bool,
    ):
        job_name, job_quantity = jobs_data
        if not (job := job_widget.get_job(job_name)):
            msg = QMessageBox(
                QMessageBox.Icon.Question,
                "Could not find job?",
                f"{job_name} not found. How did this happen?\n\nOperation aborted. Start panic.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return
        is_job_valid, response = job.is_valid()
        if not is_job_valid:
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "Flow tags missing",
                f"{job.name} is not properly set up.\n\nCheck: {response}\n\nOperation aborted.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return
        if job.unsaved_changes:
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "Ensure job is Saved",
                f"Save {job.name} before adding it to the production plan.\n\nOperation aborted.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return

        job_path = f"saved_jobs/{job.status.name.lower()}/{job.name}"

        for _ in range(job_quantity):  # Add job x amount of times
            if should_update_components:
                self.subtract_component_quantity_from_job(job)
            self.add_job_to_production_planner_thread(job_path)

    def send_job_to_production_planner(self):
        active_jobs_in_planning = {}
        for job_widget in self.job_planner_widget.job_widgets:
            job = job_widget.job
            active_jobs_in_planning[job.name] = {
                "job": job,
                "type": job.status.value,
                "modified_date": "Currently open",
                "order_number": job.order_number,
            }
        active_jobs_in_quoting = {}
        for job_widget in self.job_quote_widget.job_widgets:
            job = job_widget.job
            active_jobs_in_quoting[job.name] = {
                "job": job,
                "type": job.status.value,
                "modified_date": "Currently open",
                "order_number": job.order_number,
            }
        if not (active_jobs_in_planning or active_jobs_in_quoting):
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "No jobs loaded",
                "You have no jobs currently loaded.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return

        send_to_workspace_dialog = SendJobsToWorkspaceDialog(
            active_jobs_in_planning,
            active_jobs_in_quoting,
            "Production Planner",
            self.tab_text(self.stackedWidget.currentIndex()),
            self,
        )

        if send_to_workspace_dialog.exec():
            selected_jobs = send_to_workspace_dialog.get_selected_jobs()
            for selected_job_data in selected_jobs.get("planning", []):
                self.add_job_to_production_plan(
                    self.job_planner_widget,
                    selected_job_data,
                    send_to_workspace_dialog.should_update_components(),
                )
            for selected_job_data in selected_jobs.get("quoting", []):
                self.add_job_to_production_plan(
                    self.job_quote_widget,
                    selected_job_data,
                    send_to_workspace_dialog.should_update_components(),
                )

            # self.components_inventory.save_local_copy()
            # self.upload_files([f"{self.components_inventory.filename}.json"])

    def add_job_to_workspace(
            self,
            job_widget: JobTab,
            jobs_data: dict[str, int],
            should_update_components: bool,
    ):
        job_name, job_quantity = jobs_data
        if not (job := job_widget.get_job(job_name)):
            msg = QMessageBox(
                QMessageBox.Icon.Question,
                "Could not find job?",
                f"{job_name} not found. How did this happen?\n\nOperation aborted. Start panic.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return
        is_job_valid, response = job.is_valid()
        if not is_job_valid:
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "Flow tags missing",
                f"{job.name} is not properly set up.\n\nCheck: {response}\n\nOperation aborted.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return
        for _ in range(job_quantity):  # Add job x amount of times
            if should_update_components:
                self.subtract_component_quantity_from_job(job)
            new_job = self.workspace.deep_split_job_copy(job)
            new_job.color = get_random_color()
            new_job.status = JobStatus.WORKSPACE
            # for laser_cut_part in new_job.get_all_laser_cut_parts():
            #     laser_cut_part.timer.start_timer()
            self.add_job_to_workspace_thread(new_job)

    def send_job_to_workspace(self):
        active_jobs_in_planning = {}
        for job_widget in self.job_planner_widget.job_widgets:
            job = job_widget.job
            active_jobs_in_planning[job.name] = {
                "job": job,
                "type": job.status.value,
                "modified_date": "Currently open",
                "order_number": job.order_number,
            }
        active_jobs_in_quoting = {}
        for job_widget in self.job_quote_widget.job_widgets:
            job = job_widget.job
            active_jobs_in_quoting[job.name] = {
                "job": job,
                "type": job.status.value,
                "modified_date": "Currently open",
                "order_number": job.order_number,
            }
        if not (active_jobs_in_planning or active_jobs_in_quoting):
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "No jobs loaded",
                "You have no jobs currently loaded.",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return

        send_to_workspace_dialog = SendJobsToWorkspaceDialog(
            active_jobs_in_planning,
            active_jobs_in_quoting,
            "Workspace",
            self.tab_text(self.stackedWidget.currentIndex()),
            self,
        )

        if send_to_workspace_dialog.exec():
            selected_jobs = send_to_workspace_dialog.get_selected_jobs()
            # self.workspace.load_data()
            for selected_job_data in selected_jobs.get("planning", []):
                self.add_job_to_workspace(
                    self.job_planner_widget,
                    selected_job_data,
                    send_to_workspace_dialog.should_update_components(),
                )
            for selected_job_data in selected_jobs.get("quoting", []):
                self.add_job_to_workspace(
                    self.job_quote_widget,
                    selected_job_data,
                    send_to_workspace_dialog.should_update_components(),
                )

            # for assembly in self.workspace.get_all_assemblies():
            #     if assembly.all_laser_cut_parts_complete() and not assembly.timer.has_started_timer():
            #         assembly.timer.start_timer()

            # self.workspace.save()
            # self.components_inventory.save_local_copy()
            # self.laser_cut_parts_inventory.save_local_copy()
            # self.upload_files(
            #     [
            #         # f"{self.workspace.filename}.json",
            #         # f"{self.components_inventory.filename}.json",
            #         # f"{self.laser_cut_parts_inventory.filename}.json",
            #     ]
            # )
            # self.workspace_tab_widget.load_tags()
            # self.workspace_tab_widget.get_all_workspace_jobs_thread()
            # self.workspace_tab_widget.set_current_tab(self.workspace_tab_widget_last_selected_tab)

    def set_order_number(self):
        self.get_order_number_thread()
        loop = QEventLoop()
        QTimer.singleShot(200, loop.quit)
        loop.exec()
        input_number, ok = QInputDialog.getDouble(self, "Set Order Number", "Enter a Order Number:", self.order_number)
        if input_number and ok:
            self.set_order_number_thread(input_number)

    def open_job_sorter(self):
        job_sorter_menu = JobSorterDialog(
            self,
        )
        job_sorter_menu.show()

    def open_tag_editor(self):
        self.workspace_settings.load_data()
        tag_editor = EditWorkspaceSettings(self.workspace_settings, self)

        def upload_workspace_settings():
            self.status_button.setText("Synching", "lime")
            self.upload_files(
                ["workspace_settings.json"],
            )

        if tag_editor.exec():
            upload_workspace_settings()
            if self.job_planner_widget:
                self.job_planner_widget.workspace_settings_changed()
            if self.job_quote_widget:
                self.job_quote_widget.workspace_settings_changed()
            # if self.workspace_tab_widget:
            # self.workspace_tab_widget.workspace_settings_changed()

    # * /\ Dialogs /\

    # * \/ Load UI \/
    def load_cuttoff_drop_down(self):
        cutoff_items: QListWidget = self.cutoff_widget.widgets[0]
        cutoff_items.clear()
        cutoff_sheets = self.sheets_inventory.get_sheets_by_category("Cutoff")
        for group in self.sheets_inventory.get_all_sheets_material(cutoff_sheets):
            cutoff_items.addItem(f"\t             {group}")
            for sheet in cutoff_sheets:
                if group != sheet.material:
                    continue
                cutoff_items.addItem(sheet.get_name())

    def load_tree_widget_cuttoff_drop_down(self, tree_widget: QTreeWidget):
        tree_widget.clear()
        tree_widget.setColumnCount(0)
        tree_widget.setHeaderLabels(["Sheets"])
        cutoff_sheets = self.sheets_inventory.get_sheets_by_category("Cutoff")
        for group in self.sheets_inventory.get_all_sheets_material(cutoff_sheets):
            parent_item = QTreeWidgetItem()
            parent_item.setText(0, group)
            for sheet in cutoff_sheets:
                if group != sheet.material:
                    continue
                sheet_item = QTreeWidgetItem(parent_item)
                sheet_item.setText(0, sheet.get_name())
                parent_item.addChild(sheet_item)
            tree_widget.addTopLevelItem(parent_item)
        tree_widget.expandAll()

    def load_planning_jobs(self, data: list[dict[str, dict[str, Any]]]):
        self.saved_planning_job_items_last_opened = self.saved_jobs_multitoolbox.get_widget_visibility()
        self.templates_job_items_last_opened = self.templates_jobs_multitoolbox.get_widget_visibility()

        self.templates_jobs_multitoolbox.clear()
        self.saved_jobs_multitoolbox.clear()
        sorted_data = natsorted(data, key=lambda x: (x["job_data"]["type"], -x["job_data"]["order_number"]))

        for job_data in sorted_data:
            job_item = SavedPlanningJobItem(job_data, self)
            job_id = job_data.get("id", -1)
            job_type = job_data.get("job_data", {}).get("type", 1)
            job_name = job_data.get("name")
            job_order_number = int(job_data.get("job_data", {}).get("order_number"))
            job_item.load_job.connect(partial(self.load_job_worker, job_id))
            job_item.delete_job.connect(partial(self.delete_job_worker, job_id))
            job_item.open_webpage.connect(partial(self.open_job, job_id))
            job_item.pushButton_open_in_browser.setToolTip(
                f"{job_item.pushButton_open_in_browser.toolTip()}\n\nhttp://{get_server_ip_address()}:{get_server_port()}/jobs/load_job/{job_id}"
            )
            job_item.job_type_changed.connect(
                partial(
                    self.update_job_settings_worker,
                    job_id,
                    "type",
                    job_item.comboBox_job_status,
                )
            )
            if job_type != JobStatus.TEMPLATE.value:
                self.saved_jobs_multitoolbox.addItem(
                    job_item,
                    f"{job_name} #{job_order_number}",
                    JobColor.get_color(JobStatus(job_type)),
                    icon=JobIcon.get_icon(JobStatus(job_type)),
                )
            elif job_type == JobStatus.TEMPLATE.value:
                self.templates_jobs_multitoolbox.addItem(
                    job_item,
                    f"{job_name} #{job_order_number}",
                    JobColor.get_color(JobStatus(job_type)),
                    icon=JobIcon.get_icon(JobStatus(job_type)),
                )
        self.saved_jobs_multitoolbox.close_all()
        self.templates_jobs_multitoolbox.close_all()
        self.saved_jobs_multitoolbox.set_widgets_visibility(self.saved_planning_job_items_last_opened)
        self.templates_jobs_multitoolbox.set_widgets_visibility(self.templates_job_items_last_opened)

    def load_quoting_jobs(self, data: list[dict]):
        self.saved_planning_job_items_last_opened_2 = self.saved_jobs_multitoolbox_2.get_widget_visibility()
        self.templates_job_items_last_opened_2 = self.templates_jobs_multitoolbox_2.get_widget_visibility()

        self.templates_jobs_multitoolbox_2.clear()
        self.saved_jobs_multitoolbox_2.clear()
        sorted_data = natsorted(data, key=lambda x: (x["job_data"]["type"], -x["job_data"]["order_number"]))
        for job_data in sorted_data:
            job_item = SavedPlanningJobItem(job_data, self)
            job_id = job_data.get("id", -1)
            job_type = job_data.get("job_data", {}).get("type", 1)
            job_name = job_data.get("name")
            job_order_number = int(job_data.get("job_data", {}).get("order_number"))
            job_item.load_job.connect(partial(self.load_job_worker, job_id))
            job_item.delete_job.connect(partial(self.delete_job_worker, job_id))
            job_item.open_webpage.connect(partial(self.open_job, job_id))
            job_item.pushButton_open_in_browser.setToolTip(
                f"{job_item.pushButton_open_in_browser.toolTip()}\n\nhttp://{get_server_ip_address()}:{get_server_port()}/jobs/load_job/{job_id}"
            )
            job_item.job_type_changed.connect(
                partial(
                    self.update_job_settings_worker,
                    job_id,
                    "type",
                    job_item.comboBox_job_status,
                )
            )
            if job_type != JobStatus.TEMPLATE.value:
                self.saved_jobs_multitoolbox_2.addItem(
                    job_item,
                    f"{job_name} #{job_order_number}",
                    JobColor.get_color(JobStatus(job_type)),
                    icon=JobIcon.get_icon(JobStatus(job_type)),
                )
            elif job_type == JobStatus.TEMPLATE.value:
                self.templates_jobs_multitoolbox_2.addItem(
                    job_item,
                    f"{job_name} #{job_order_number}",
                    JobColor.get_color(JobStatus(job_type)),
                    icon=JobIcon.get_icon(JobStatus(job_type)),
                )
        self.saved_jobs_multitoolbox_2.close_all()
        self.templates_jobs_multitoolbox_2.close_all()
        self.saved_jobs_multitoolbox_2.set_widgets_visibility(self.saved_planning_job_items_last_opened_2)
        self.templates_jobs_multitoolbox_2.set_widgets_visibility(self.templates_job_items_last_opened_2)

    def refresh_nest_directories(self):
        self.clear_layout(self.verticalLayout_33)
        self.clear_layout(self.verticalLayout_37)
        self.toolbox_job_nest_directories_list_widgets.clear()
        self.toolbox_workspace_nest_directories_list_widgets.clear()
        self.settings_file.load_data()
        nest_directories: list[str] = self.settings_file.get_value("quote_nest_directories")
        toolbox_2 = QToolBox(self)
        toolbox_2.setLineWidth(0)
        toolbox_2.layout().setSpacing(0)
        toolbox_3 = QToolBox(self)
        toolbox_3.setLineWidth(0)
        toolbox_3.layout().setSpacing(0)
        self.verticalLayout_33.addWidget(toolbox_2)  # Job Quoter
        self.verticalLayout_37.addWidget(toolbox_3)
        for i, nest_directory in enumerate(nest_directories):
            nest_directory_name: str = nest_directory.split("/")[-1]
            tree_view_2 = PdfTreeView(nest_directory, self)
            tree_view_2.selectionModel().selectionChanged.connect(self.job_quote_directory_item_selected)
            tree_view_3 = PdfTreeView(nest_directory, self)
            tree_view_3.selectionModel().selectionChanged.connect(self.workspace_directory_item_selected)
            self.toolbox_job_nest_directories_list_widgets[nest_directory] = tree_view_2
            self.toolbox_workspace_nest_directories_list_widgets[nest_directory] = tree_view_3
            toolbox_2.addItem(tree_view_2, nest_directory_name)
            toolbox_2.setItemIcon(i, Icons.folder_icon)
            toolbox_3.addItem(tree_view_3, nest_directory_name)
            toolbox_3.setItemIcon(i, Icons.folder_icon)
        self.job_quote_directory_item_selected()
        self.workspace_directory_item_selected()

    # * \/ CHECKERS \/
    def check_for_updates(self, on_start_up: bool = False):
        try:
            try:
                response = requests.get("http://10.0.0.10:5051/version", timeout=5)
            except ConnectionError:
                return
            if response.status_code == 200:
                version = response.text
                if version != __version__:
                    subprocess.Popen("start update.exe", shell=True)
                elif not on_start_up:
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Information)
                    msg.setWindowTitle("No updates")
                    msg.setText("There are currently no updates available")
                    msg.exec()
        except Exception as e:
            if not on_start_up:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Update error")
                msg.setText(f"{e}")
                msg.exec()

    # * /\ CHECKERS /\

    def copy_file_with_overwrite(self, source: str, target: str, retry_interval=1, max_retries=10):
        source = source.replace("/", "\\")
        target = target.replace("/", "\\")
        if target in source:
            return
        retries = 0
        while retries < max_retries:
            try:
                if os.path.exists(target) and os.path.samefile(source, target):
                    os.remove(target)
                shutil.copyfile(source, target)
                return
            except shutil.SameFileError:
                if os.path.samefile(source, target):
                    os.remove(target)
                    shutil.copyfile(source, target)
                    return
            except PermissionError as e:
                if e.winerror == 32:  # File in use error
                    retries += 1
                    time.sleep(retry_interval)
                else:
                    raise
        raise PermissionError(f"Failed to copy file {source} to {target} after {max_retries} retries.")

    # * \/ External Actions \/
    def open_print_selected_parts(self):
        webbrowser.open("print_selected_parts.html", new=0)

    def open_invigo(self):
        webbrowser.open(f"http://{get_server_ip_address()}:{get_server_port()}", new=0)

    def open_server_log(self):
        webbrowser.open(f"http://{get_server_ip_address()}:{get_server_port()}/server_log", new=0)

    def open_server_logs(self):
        webbrowser.open(f"http://{get_server_ip_address()}:{get_server_port()}/logs", new=0)

    def open_inventory(self):
        webbrowser.open(f"http://{get_server_ip_address()}:{get_server_port()}/inventory", new=0)

    def open_way_back_machine(self):
        webbrowser.open(
            f"http://{get_server_ip_address()}:{get_server_port()}/way_back_machine",
            new=0,
        )

    def open_production_planner(self):
        webbrowser.open(
            f"http://{get_server_ip_address()}:{get_server_port()}/production_planner",
            new=0,
        )

    def open_wiki(self):
        webbrowser.open("https://github.com/TheCodingJsoftware/Invigo/wiki", new=0)

    def open_qr_codes(self):
        webbrowser.open(
            f"http://{get_server_ip_address()}:{get_server_port()}/sheet_qr_codes",
            new=0,
        )

    def open_job(self, job_id: int):
        webbrowser.open(
            f"http://{get_server_ip_address()}:{get_server_port()}/jobs/view?id={job_id}",
            new=0,
        )

    def open_workorder(self, workorder_id: int):
        webbrowser.open(
            f"http://{get_server_ip_address()}:{get_server_port()}/workorders/view?id={workorder_id}",
            new=0,
        )

    def open_item_history(self):
        os.startfile(f"{os.path.dirname(os.path.realpath(sys.argv[0]))}/data/inventory history.xlsx")

    def view_removed_component_quantity_history(self):
        dialog = ViewRemovedQuantitiesHistoryDialog(self)
        dialog.show()

    def open_folder(self, path: str):
        try:
            os.startfile(path)
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Error opening folder")
            msg.setText(f"{e}")
            msg.exec()

    def play_celebrate_sound(self):
        threading.Thread(target=_play_celebrate_sound).start()

    def play_boot_sound(self):
        threading.Thread(target=_play_boot_sound).start()

    # * /\ External Actions /\
    # * \/ THREADS \/
    def sync_changes(self, tab_name: Optional[str] = None):
        if not tab_name:  # Ideal if were not poping out a widget
            tab_name = self.tab_text(self.stackedWidget.currentIndex())

        self.status_button.setText(f"Synching {tab_name}", "lime")

        # if tab_name == "components_tab":
        #     self.upload_files(
        #         [
        #             f"{self.components_inventory.filename}.json",
        #         ],
        #     )
        # if tab_name in [
        #     "laser_cut_inventory_tab",
        #     "quote_generator_tab",
        #     "job_quoter_tab",
        #     "job_planner_tab",
        #     "nest_editor",
        # ]:
        #     self.upload_files(
        #         [
        #             f"{self.laser_cut_parts_inventory.filename}.json",
        #         ],
        #     )
        # if tab_name in [
        #     "sheets_in_inventory_tab",
        #     "quote_generator_tab",
        #     "job_quoter_tab",
        #     "nest_editor",
        # ]:
        #     self.upload_files(
        #         [
        #             f"{self.sheets_inventory.filename}.json",
        #         ],
        #     )

        if tab_name in ["structural_steel_inventory_tab"]:
            self.upload_files(
                [
                    f"{self.structural_steel_inventory.filename}.json",
                ],
            )
        if tab_name == "sheet_settings_tab":
            self.upload_files(
                [
                    f"{self.sheet_settings.filename}.json",
                ],
            )
        if tab_name == "structural_steel_settings_tab":
            self.upload_files(
                [
                    f"{self.structural_steel_settings.filename}.json",
                ],
            )
        if tab_name == "workspace_tab":
            self.upload_files(
                [
                    f"{self.laser_cut_parts_inventory.filename}.json",  # Because of add/remove quantity flow tags
                    # f"{self.workspace.filename}.json",
                ],
            )

    def add_job_to_production_planner_thread(self, job_path: str):
        thread = AddJobToProductionPlannerThread(job_path)
        self.threads.append(thread)
        thread.signal.connect(self.add_job_to_production_planner_response)
        thread.start()
        thread.wait()

    def add_job_to_production_planner_response(self, response: str, job_path: str, status_code: int):
        if status_code == 200:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Job added")
            msg.setText(f"{response['message']}")
            msg.exec()
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Job not added")
            msg.setText(f"{response}")
            msg.exec()

    def add_job_to_workspace_thread(self, job: Job):
        add_job_to_workspace_thread = AddJobToWorkspaceWorker(job)
        add_job_to_workspace_thread.signals.success.connect(self.add_job_to_workspace_response)
        QThreadPool.globalInstance().start(add_job_to_workspace_thread)

    def add_job_to_workspace_response(self, response: dict):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Job added")
        msg.setText("Successfully added job to workspace")
        msg.exec()

    def add_laser_cut_part_to_inventory(self, laser_cut_part_to_add: LaserCutPart, from_where: str):
        if laser_cut_part_to_add.recut:
            new_recut_part = LaserCutPart(
                laser_cut_part_to_add.to_dict(),
                self.laser_cut_parts_inventory,
            )
            new_recut_part.add_to_category(self.laser_cut_parts_inventory.get_category("Recut"))
            if existing_recut_part := self.laser_cut_parts_inventory.get_recut_part_by_name(laser_cut_part_to_add.name):
                existing_recut_part.recut_count += 1
                new_recut_part.recut_count = existing_recut_part.recut_count
                new_recut_part.name = f"{new_recut_part.name} - (Recut count: {new_recut_part.recut_count})"
            new_recut_part.meta_data.modified_date = f"{os.getlogin().title()} - Part added from {from_where} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.laser_cut_parts_inventory.add_recut_part(new_recut_part)
        elif existing_laser_cut_part := self.laser_cut_parts_inventory.get_laser_cut_part_by_name(
                laser_cut_part_to_add.name):
            existing_laser_cut_part.inventory_data.quantity += laser_cut_part_to_add.inventory_data.quantity
            existing_laser_cut_part.meta_data.material = laser_cut_part_to_add.meta_data.material
            existing_laser_cut_part.meta_data.gauge = laser_cut_part_to_add.meta_data.gauge
            existing_laser_cut_part.primer_data.uses_primer = laser_cut_part_to_add.primer_data.uses_primer
            existing_laser_cut_part.primer_data.primer_name = laser_cut_part_to_add.primer_data.primer_name
            existing_laser_cut_part.paint_data.uses_paint = laser_cut_part_to_add.paint_data.uses_paint
            existing_laser_cut_part.paint_data.paint_name = laser_cut_part_to_add.paint_data.paint_name
            existing_laser_cut_part.powder_data.uses_powder = laser_cut_part_to_add.powder_data.uses_powder
            existing_laser_cut_part.powder_data.powder_name = laser_cut_part_to_add.powder_data.powder_name
            existing_laser_cut_part.primer_data.primer_overspray = laser_cut_part_to_add.primer_data.primer_overspray
            existing_laser_cut_part.paint_data.paint_overspray = laser_cut_part_to_add.paint_data.paint_overspray
            existing_laser_cut_part.meta_data.modified_date = f"{os.getlogin().title()} - Added {laser_cut_part_to_add.inventory_data.quantity} quantities from {from_where} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
        else:
            if not (category := self.laser_cut_parts_inventory.get_category("Uncategorized")):
                category = Category("Uncategorized")
                self.laser_cut_parts_inventory.add_category(category)
            laser_cut_part_to_add.add_to_category(category)
            # laser_cut_part_to_add.quantity = 1
            laser_cut_part_to_add.meta_data.modified_date = f"{os.getlogin().title()} - Part added from {from_where} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.laser_cut_parts_inventory.add_laser_cut_part(laser_cut_part_to_add)

    def remove_sheet_quantities_from_nests(self, nests: list[Nest]):
        grouped_sheet_counts: dict[str, int] = defaultdict(int)

        # Group total quantity used per sheet name
        for nest in nests:
            name = nest.sheet.get_name()
            grouped_sheet_counts[name] += nest.sheet_count

        sheets_to_save: list[Sheet] = []
        for sheet_name, total_count in grouped_sheet_counts.items():
            sheet = self.sheets_inventory.get_sheet_by_name(sheet_name)
            if not sheet:
                continue

            old_quantity = sheet.quantity
            sheet.quantity -= total_count
            sheet.latest_change_quantity = f"{os.getlogin().title()} - Removed {total_count} sheets from workorder at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"

            if sheet.quantity <= sheet.red_quantity_limit and not sheet.has_sent_warning and "Cutoff" not in sheet.get_categories():
                sheet.has_sent_warning = True
                self.generate_single_sheet_report(sheet, old_quantity)

            if "Cutoff" in sheet.get_categories() and sheet.quantity <= 0:
                self.sheets_inventory.remove_sheet(sheet)
            else:
                sheets_to_save.append(sheet)

        self.sheets_inventory.save_sheets(sheets_to_save)

    def subtract_component_quantity_from_job(self, job: Job):
        for assembly in job.get_all_assemblies():
            components_to_save = []
            for component_from_job in assembly.components:
                if not (component_from_inventory := self.components_inventory.get_component_by_part_name(
                        component_from_job.part_name)):
                    continue
                component_from_inventory.quantity -= component_from_job.quantity * assembly.meta_data.quantity
                component_from_inventory.latest_change_quantity = f"{os.getlogin().title()} removed {component_from_job.quantity * assembly.meta_data.quantity} quantity from sending {job.name} to workspace at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                components_to_save.append(component_from_inventory)
            self.components_inventory.save_components(components_to_save)
        # self.components_inventory.save_local_copy()

    def generate_single_sheet_report(self, sheet: Sheet, old_quantity: int):
        notes = sheet.notes
        if not sheet.notes:
            notes = "No notes provided"
        message_to_send = f"""<body style="font-family: sans-serif;">
            <p><b>Important Sheets Inventory Update</b></p>
            <p style>Please be advised that the quantity in stock for <b>"{sheet.get_name()}"</b> has reached a critical low. The current quantity has fallen to {sheet.quantity} sheets, which is <b style="color: lightpink">below the designated minimum threshold of {sheet.red_quantity_limit} sheets.</b></p>
            <p><b>Details:</b></p>
            <ul>
                <li><b>Previous Quantity: </b> {old_quantity}</li>
                <li><b>Current Quantity: </b> {sheet.quantity}</li>
                <li><b>Notes: </b>{notes}</li>
            </ul>
            <p><b>Action Required:</b></p>
            <ul>
                <p>Please review this situation at your earliest convenience and initiate a purchase order. Once you have dispatched the order, please ensure to update the status to <b style="color: #3bba6d">"Order Pending"</b> in the <b>"Sheet in Inventory"</b> tab to reflect this action.</p>
            </ul>
            <br>
            <p>Have a fabulous day!</p>
        </body>
        """
        self.send_email_thread(
            f"Alert: Low Sheet Inventory Notice for: {sheet.get_name()}",
            message_to_send,
            ["jaredgrozz@gmail.com", "lynden@pineymfg.com"],
        )

    def download_required_images_thread(self, required_images: list[str]):
        download_thread = Download(required_images)
        download_thread.signal.connect(self.download_required_images_response)
        self.threads.append(download_thread)
        download_thread.start()

    def download_required_images_response(self, response: str):
        if not response:
            self.status_button.setText("Warning: No images found", "yellow")
        elif response == "Successfully downloaded":
            with contextlib.suppress(AttributeError):
                self.status_button.setText(
                    f"Successfully loaded {len(self.get_all_selected_parts(self.tabs[self.category.name]))} images",
                    "lime",
                )
        else:
            self.status_button.setText(f"Error: {response}", "red")

    def upload_nest_images(self, nests: list[Nest]):
        images_to_upload: list[str] = []
        for nest in nests:
            images_to_upload.extend(laser_cut_part.meta_data.image_index for laser_cut_part in nest.laser_cut_parts)
            images_to_upload.extend(nest.image_path for nest in nests)

        images = set(images_to_upload)
        self.upload_files(list(images))

    def changes_response(self, responses: str | list[str]):
        logging.info(f"changes_response: {responses}")

        def extract_last(path: str) -> str:
            """Helper to extract last part of path."""
            return path.split("/")[-1]

        def extract_job_id_and_name(path: str):
            """Helper to extract job_id and entry_name from path."""
            parts = path.split("/")
            return int(parts[-2]), parts[-1]

        def set_status(text: str, color: str = "lime"):
            self.status_button.setText(text, color)

        tab_name = self.tab_text(self.stackedWidget.currentIndex())

        # Handle if responses is a single string, log as error
        if isinstance(responses, str):
            logging.error(f"Syncing Error: {responses}")
            set_status(f"Syncing Error: {responses}", "red")
            return

        # Defensive: Empty list check
        if not responses:
            logging.error(f"Syncing Error: empty responses list: {responses}")
            set_status("Syncing Error: Empty responses", "red")
            return

        self.status_button.setText("Syncing", "yellow")
        self.downloading_changes = True

        first_resp = responses[0]

        # Dispatch map for single endpoint cases
        dispatch_single = {
            "reload_saved_quotes": self.load_saved_quoted_thread,
            "reload_saved_jobs": self.load_jobs_worker,
        }

        # Check simple reload keywords first
        if first_resp in dispatch_single:
            dispatch_single[first_resp]()
            set_status(f"Synced: {first_resp}")
            logging.info(f"Synced: {first_resp}")
            return

        # Endpoint-specific checks
        if any(key in first_resp for key in
               ("vendors/get_all", "purchase_orders/get_all", "shipping_addresses/get_all")):
            self.load_po_menus()

        elif "jobs/get_all" in first_resp:
            self.load_jobs_worker()

        elif "workspace/get_entry" in first_resp and tab_name == "workspace_tab":
            entry_id = extract_last(first_resp)
            worker = GetWorkspaceEntryWorker(entry_id)
            # worker.signals.success.connect(self.get_workspace_entry_response)
            QThreadPool.globalInstance().start(worker)

        elif "sheets_inventory/get_sheet" in first_resp:
            for resp in responses:
                sheet_id = extract_last(resp)
                self.sheets_inventory.get_sheet(sheet_id, on_finished=self.get_sheet_response)

        elif "sheets_inventory/get_all" in first_resp:
            self.should_update_sheets_in_inventory_tab = True
            self.sheets_inventory.load_data(on_loaded=self.update_sheets_inventory_tab)

        elif "components_inventory/get_component" in first_resp:
            for resp in responses:
                comp_id = extract_last(resp)
                self.components_inventory.get_component(comp_id, on_finished=self.get_component_response)

        elif "components_inventory/get_all" in first_resp:
            self.should_update_components_in_inventory_tab = True
            self.components_inventory.load_data(on_loaded=self.update_components_inventory_tab)

        elif "laser_cut_parts_inventory/get_laser_cut_part" in first_resp:
            for resp in responses:
                part_id = extract_last(resp)
                self.laser_cut_parts_inventory.get_laser_cut_part(part_id, on_finished=self.get_laser_cut_part_response)

        elif "laser_cut_parts_inventory/get_all" in first_resp:
            self.should_update_laser_cut_inventory_tab = True
            self.laser_cut_parts_inventory.load_data(on_loaded=self.update_laser_cut_inventory_tab)

        elif "workspace/get_entries_by_name" in first_resp:
            for resp in responses:
                job_id, entry_name = extract_job_id_and_name(resp)
                worker = GetWorkspaceEntriesByNameWorker(job_id, entry_name)
                # worker.signals.success.connect(self.get_workspace_entries_response)
                QThreadPool.globalInstance().start(worker)

        else:
            self.download_files(responses)

        set_status(f"Synced: {first_resp}")
        logging.info(f"Synced: {responses}")

    # def get_workspace_entry_response(self, entry_data: dict, status_code: int):
    #     if status_code == 200:
    #         # self.workspace_tab_widget.update_entry(entry_data)

    #         # if "laser" in self.workspace_tab_widget.workspace_filter.current_tag.lower():
    #             # self.workspace_tab_widget.get_all_recut_parts_thread()
    #     else:
    #         self.status_button.setText(f"Error: {entry_data}", "red")

    # def get_workspace_entries_response(self, entries_data: list[dict]):
    # self.workspace_tab_widget.update_entries(entries_data)

    def get_sheet_response(self, sheet_data: dict):
        try:
            self.should_update_sheets_in_inventory_tab = True
            self.sheets_inventory_tab_widget.block_table_signals()
            self.sheets_inventory_tab_widget.update_sheet(sheet_data)
            self.sheets_inventory_tab_widget.unblock_table_signals()
        except Exception:
            self.status_button.setText(f"Error: {sheet_data}", "red")

    def get_component_response(self, component_data: dict):
        try:
            self.should_update_components_in_inventory_tab = True
            self.components_tab_widget.block_table_signals()
            self.components_tab_widget.update_component(component_data)
            self.components_tab_widget.unblock_table_signals()
        except Exception as e:
            self.status_button.setText(f"Error: {e}", "red")
            print(e)

    def get_laser_cut_part_response(self, laser_cut_part_data):
        try:
            self.should_update_laser_cut_parts_in_inventory_tab = True
            self.laser_cut_parts_tab_widget.block_table_signals()
            self.laser_cut_parts_tab_widget.update_laser_cut_part(laser_cut_part_data)
            self.laser_cut_parts_tab_widget.unblock_table_signals()
        except Exception as e:
            self.status_button.setText(f"Error: {e}", "red")
            print(e)

    def data_received(self, data):
        if "timed out" in str(data).lower() or "fail" in str(data).lower():
            self.status_button.setText("Server error", "red")
            self.centralwidget.setEnabled(False)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Server error")
            msg.setText(
                f"The server is either offline or your device is not connected to the internet. Please ensure that any VPNs are disabled, then try again. If the problem persists, contact your server or network administrator for assistance.\n\nThread response:\n{str(data)}"
            )
            msg.exec()
        # QApplication.restoreOverrideCursor()

    def start_changes_thread(self):
        changes_thread = ChangesThread(self)  # 5 minutes
        changes_thread.signal.connect(self.changes_response)
        self.threads.append(changes_thread)
        changes_thread.start()

    def start_exchange_rate_thread(self):
        exchange_rate_thread = ExchangeRate()
        exchange_rate_thread.signal.connect(self.exchange_rate_received)
        self.threads.append(exchange_rate_thread)
        exchange_rate_thread.start()

    def exchange_rate_received(self, exchange_rate: float):
        try:
            self.components_tab_widget.label_exchange_price.setText(f"1.00 USD: {exchange_rate} CAD")
            self.settings_file.set_value("exchange_rate", exchange_rate)
        except (
                AttributeError,
                RuntimeError,
        ) as e:  # It might be the case that ComponentsTab is not loaded
            self.status_button.setText(f"{e}", "red")

    def send_sheet_report(self):
        thread = SendReportThread()
        self.threads.append(thread)
        thread.start()

    def upload_files(self, files_to_upload: list[str]):
        self.upload_thread = UploadFilesWorker(files_to_upload)
        self.upload_thread.signals.success.connect(self.upload_thread_response)
        QThreadPool.globalInstance().start(self.upload_thread)

    def upload_thread_response(self, response: dict):
        # print("upload_thread_response", response, files_uploaded)
        if response["status"] == "success":
            self.status_button.setText("Synched", "lime")

    def download_files(self, files_to_download: list[str]):
        download_thread = DownloadThread(files_to_download)
        download_thread.signal.connect(self.download_thread_response)
        self.threads.append(download_thread)
        download_thread.start()

    def download_thread_response(self, response: dict):
        print("download_thread_response", response)

        if not self.finished_downloading_all_files:
            self.download_all_files_finished()
        elif self.downloading_changes and response["status"] == "success":
            # Update relevant files
            if f"{self.sheet_settings.filename}.json" in response["successful_files"]:
                self.sheet_settings.load_data()
                self.sheet_settings_tab_widget.load_tabs()
            if f"{self.structural_steel_settings.filename}.json" in response["successful_files"]:
                self.structural_steel_settings.load_data()
                self.structural_steel_settings_tab_widget.load_tabs()
            if f"{self.workspace_settings.filename}.json" in response["successful_files"]:
                self.workspace_settings.load_data()
                # self.workspace.load_data()
                with contextlib.suppress(AttributeError):
                    self.job_planner_widget.workspace_settings_changed()
                with contextlib.suppress(AttributeError):
                    self.job_quote_widget.workspace_settings_changed()
                # with contextlib.suppress(AttributeError):
                # self.workspace_tab_widget.workspace_settings_changed()

            # if (
            #     f"{self.components_inventory.filename}.json"
            #     in response["successful_files"]
            # ):
            #     self.components_inventory.load_data()
            #     self.should_update_components_tab = True

            # if f"{self.sheets_inventory.filename}.json" in response["successful_files"]:
            #     self.sheets_inventory.load_data()
            # self.should_update_sheets_in_inventory_tab = True

            # if (
            #     f"{self.laser_cut_inventory.filename}.json"
            #     in response["successful_files"]
            # ):
            #     self.laser_cut_inventory.load_data()
            #     self.should_update_laser_cut_inventory_tab = True

            if f"{self.workspace.filename}.json" in response["successful_files"]:
                # self.workspace.load_data()
                self.should_update_workspace_tab = True

            # if f"{self.paint_inventory.filename}.json" in response["successful_files"]:
            #     self.paint_inventory.load_data()

            # Update relevant tabs
            # if (
            #     self.tab_text(self.stackedWidget.currentIndex())
            #     == "laser_cut_inventory_tab"
            #     or self.should_update_laser_cut_inventory_tab
            # ):
            #     self.laser_cut_tab_widget.load_categories()
            #     self.laser_cut_inventory.sort_by_quantity()
            #     self.laser_cut_tab_widget.restore_last_selected_tab()
            #     self.should_update_laser_cut_inventory_tab = False
            # elif (
            #     self.tab_text(self.stackedWidget.currentIndex())
            #     == "sheets_in_inventory_tab"
            #     or self.should_update_sheets_in_inventory_tab
            # ):
            #     self.sheets_inventory_tab_widget.load_categories()
            #     self.sheets_inventory.sort_by_thickness()
            #     self.sheets_inventory_tab_widget.restore_last_selected_tab()
            #     self.should_update_sheets_in_inventory_tab = False
            # elif (
            #     self.tab_text(self.stackedWidget.currentIndex()) == "components_tab"
            #     or self.should_update_components_tab
            # ):
            #     self.components_tab_widget.load_categories()
            #     self.components_tab_widget.sort_component_inventory()
            #     self.components_tab_widget.restore_last_selected_tab()
            #     self.should_update_components_tab = False
            if self.tab_text(self.stackedWidget.currentIndex()) == "quote_generator_tab":
                self.load_saved_quoted_thread()
                self.load_cuttoff_drop_down()
            elif self.tab_text(
                    self.stackedWidget.currentIndex()) == "workspace_tab" or self.should_update_workspace_tab:
                # self.workspace_tab_widget.load_tags()
                # self.workspace_tab_widget.set_current_tab(self.workspace_tab_widget_last_selected_tab)
                self.should_update_workspace_tab = False
            self.downloading_changes = False

    def download_all_files_finished(self):
        self.finished_downloading_all_files = True
        self.status_button.setText("Downloaded all files", "lime")
        self.centralwidget.setEnabled(True)
        self.downloading_changes = False

        self.start_changes_thread()
        self.start_exchange_rate_thread()
        self.start_check_for_updates_thread()
        self.__load_ui()
        self.tool_box_menu_changed()
        if self.settings_file.get_value("show_maximized"):
            self.showMaximized()

    def download_all_files(self):
        print("download_all_files")
        self.download_files(
            [
                f"{self.sheet_settings.filename}.json",
                f"{self.structural_steel_settings.filename}.json",
                f"{self.workspace_settings.filename}.json",
                f"{self.structural_steel_inventory.filename}.json",
                f"{self.paint_inventory.filename}.json",
                # f"{self.laser_cut_inventory.filename}.json",
                # f"{self.sheets_inventory.filename}.json",
                # f"{self.components_inventory.filename}.json",
                # f"{self.workspace.filename}.json",
            ]
        )

    def load_nests_for_job_thread(self, nests: list[str]):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.status_button.setText("Processing nests", "yellow")
        self.pushButton_load_nests_2.setEnabled(False)
        load_nest_thread = LoadNestsThread(
            self,
            nests,
            self.components_inventory,
            self.laser_cut_parts_inventory,
            self.sheet_settings,
        )
        self.threads.append(load_nest_thread)
        load_nest_thread.signal.connect(self.load_nests_for_job_response)
        load_nest_thread.start()

    # TODO: Update existing LCP's with the ones in the nest
    def load_nests_for_job_response(self, nests: Union[list[Nest], str]):
        if isinstance(nests, str):
            self.status_button.setText(f"Encountered error processing nests: {nests}", "red")
            self.pushButton_load_nests_2.setEnabled(True)
            QApplication.restoreOverrideCursor()
            msg = QMessageBox(
                QMessageBox.Icon.Critical,
                "PDF error",
                f"{nests}",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.exec()
            return

        self.pushButton_load_nests_2.setEnabled(True)

        self.upload_nest_images(nests)

        QApplication.restoreOverrideCursor()

        settings_text = "".join(
            f"  {i + 1}. {nest.name}: {nest.sheet.thickness} {nest.sheet.material}\n" for i, nest in enumerate(nests))
        select_item_dialog = NestSheetVerification(
            f"The nests sheet settings from PDF are:\n{settings_text}",
            nests[0].sheet.thickness,
            nests[0].sheet.material,
            self.sheet_settings,
            self,
        )

        if select_item_dialog.exec():
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.status_button.setText("Loading nests", "yellow")
            current_job_widget = self.job_quote_widget.get_active_job_widget()
            current_job = current_job_widget.job
            if select_item_dialog.response == DialogButtons.set:
                material = select_item_dialog.get_selected_material()
                thickness = select_item_dialog.get_selected_thickness()
                for nest in nests:
                    nest.sheet.material = material
                    nest.sheet.thickness = thickness
                    for laser_cut_part in nest.laser_cut_parts:
                        laser_cut_part.meta_data.material = material
                        laser_cut_part.meta_data.gauge = thickness

            QApplication.restoreOverrideCursor()
            nest_editor_dialog = NestEditorDialog(nests, self)
            if not nest_editor_dialog.exec():
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

            current_job.nests = nests
            parts_to_update = {part.name for part in current_job.get_all_nested_laser_cut_parts()}
            for nest_laser_cut_part in current_job.get_all_nested_laser_cut_parts():
                for laser_cut_part in current_job.get_all_laser_cut_parts():
                    if laser_cut_part.name == nest_laser_cut_part.name:
                        laser_cut_part.load_part_data(nest_laser_cut_part.to_dict().get("meta_data", {}))
                        parts_to_update.discard(nest_laser_cut_part.name)
                        break
            if not_updated_parts := list(parts_to_update):
                message = f"The following parts were not found in {current_job.name}:\n"
                for i, part in enumerate(not_updated_parts):
                    message += f"{i + 1}. {part}\n"
                message += "\nBe sure to review these parts."
                QMessageBox(
                    QMessageBox.Icon.Information,
                    "Parts to update",
                    message,
                    QMessageBox.StandardButton.Ok,
                    self,
                ).exec()
            current_job_widget.load_nests()
            current_job_widget.update_nest_summary()
            current_job_widget.update_tables()
            current_job.unsaved_changes = True
            self.job_quote_widget.job_changed(current_job)
            # self.job_quote_widget.update_nests()
            # self.job_quote_widget.update_tables()
            self.status_button.setText(f"Nests loaded into {current_job.name}", "lime")
        else:
            self.status_button.setText("Loading nests aborted", "lime")
        QApplication.restoreOverrideCursor()

    def load_nests_for_workspace_thread(self, nests: list[str]):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.status_button.setText("Processing nests", "yellow")
        self.pushButton_load_nests_3.setEnabled(False)
        load_nest_thread = LoadNestsThread(
            self,
            nests,
            self.components_inventory,
            self.laser_cut_parts_inventory,
            self.sheet_settings,
        )
        self.threads.append(load_nest_thread)
        load_nest_thread.signal.connect(self.load_nests_for_workspace_response)
        load_nest_thread.start()
        load_nest_thread.wait()

    def load_nests_for_workspace_response(self, nests: Union[list[Nest], str]):
        if isinstance(nests, str):
            self.handle_load_nest_pdf_error(nests)
            return

        self.pushButton_load_nests_3.setEnabled(True)
        self.upload_nest_images(nests)
        QApplication.restoreOverrideCursor()

        if not (sheet_dialog := self.verify_nest_sheet_settings(nests)):
            return

        if not sheet_dialog.exec():
            return

        if sheet_dialog.response == DialogButtons.set:
            self.update_nest_material_and_thickness(
                sheet_dialog.get_selected_material(),
                sheet_dialog.get_selected_thickness(),
                nests,
            )

        nest_editor_dialog = NestEditorDialog(nests, self)
        if not nest_editor_dialog.exec():
            return

        self.process_generate_workorder_dialog(nests)

        QApplication.restoreOverrideCursor()

    def handle_load_nest_pdf_error(self, error_message: str):
        self.status_button.setText(f"Encountered error processing nests: {error_message}", "red")
        self.pushButton_load_nests_3.setEnabled(True)
        QApplication.restoreOverrideCursor()
        msg = QMessageBox(
            QMessageBox.Icon.Critical,
            "PDF error",
            error_message,
            QMessageBox.StandardButton.Ok,
            self,
        )
        msg.exec()

    def verify_nest_sheet_settings(self, nests: list[Nest]) -> NestSheetVerification:
        settings_text = "".join(
            f"  {i + 1}. {nest.name}: {nest.sheet.thickness} {nest.sheet.material}\n" for i, nest in enumerate(nests))
        return NestSheetVerification(
            f"The nests sheet settings from PDF are:\n{settings_text}",
            nests[0].sheet.thickness,
            nests[0].sheet.material,
            self.sheet_settings,
            self,
        )

    def get_nested_laser_cut_parts(self, nests: list[Nest]) -> list[LaserCutPart]:
        part_dict: dict[str, LaserCutPart] = {}

        for nest in nests:
            for laser_cut_part in nest.laser_cut_parts:
                part_name = laser_cut_part.name
                if part_name not in part_dict:
                    new_part = LaserCutPart(laser_cut_part.to_dict(), self.laser_cut_parts_inventory)
                    new_part.inventory_data.quantity = laser_cut_part.meta_data.quantity_on_sheet * nest.sheet_count
                    part_dict[part_name] = new_part
                else:
                    part_dict[
                        part_name].inventory_data.quantity += laser_cut_part.meta_data.quantity_on_sheet * nest.sheet_count

        return natsorted(part_dict.values(), key=lambda part: part.name)

    def update_nest_material_and_thickness(self, new_material: str, new_thickness: str, nests: list[Nest]):
        for nest in nests:
            nest.sheet.material = new_material
            nest.sheet.thickness = new_thickness
            for laser_cut_part in nest.laser_cut_parts:
                laser_cut_part.meta_data.material = new_material
                laser_cut_part.meta_data.gauge = new_thickness

    def get_nested_parts_not_in_workspace(
            self,
            nested_laser_cut_parts: list[LaserCutPart],
            workspace_laser_cut_part_groups: list[WorkspaceLaserCutPartGroup],
    ) -> list[LaserCutPart]:
        workspace_part_names = set()
        for group in workspace_laser_cut_part_groups:
            for part in group:
                workspace_part_names.add(part.name)

        return [part for part in nested_laser_cut_parts if part.name not in workspace_part_names]

    def get_nested_parts_in_workspace(
            self,
            nested_laser_cut_parts: list[LaserCutPart],
            workspace_laser_cut_part_groups: list[WorkspaceLaserCutPartGroup],
    ) -> list[LaserCutPart]:
        workspace_parts_dict: dict[str, LaserCutPart] = {}
        for group in workspace_laser_cut_part_groups:
            for part in group:
                workspace_parts_dict[part.name] = part

        updated_parts = []
        for part in nested_laser_cut_parts:
            if part.name in workspace_parts_dict:
                workspace_part = workspace_parts_dict[part.name]
                part.workspace_data.flowtag = workspace_part.workspace_data.flowtag
                updated_parts.append(part)

        return updated_parts

    def show_nested_parts_not_in_workspace_dialog(self, nested_parts_not_in_workspace: list[LaserCutPart]) -> int:
        headers = ["No.", "Part Name", "Quantity", "Destination"]
        table_rows = "".join(
            f"""
            <tr>
                <td>{i + 1}</td>
                <td>{part.name}</td>
                <td>{part.inventory_data.quantity}</td>
                <td>Laser Cut Inventory</td>
            </tr>
            """
            for i, part in enumerate(nested_parts_not_in_workspace)
        )
        message = f"""
        <html>
            <head>
                <style>
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    th, td {{
                        border-bottom: 1px solid white;
                        padding: 8px;
                        text-align: left;
                    }}
                </style>
            </head>
            <body>
                <p>The following parts were NOT found in Workspace and will be added to laser cut inventory:</p>
                <table>
                    <tr>
                        <th>{headers[0]}</th>
                        <th>{headers[1]}</th>
                        <th>{headers[2]}</th>
                        <th>{headers[3]}</th>
                    </tr>
                    {table_rows}
                </table>
                <p>Be sure to review these parts.</p>
            </body>
        </html>
        """

        message_dialog = MessageDialog("Parts NOT found in Workspace", message, self)
        return message_dialog.exec()

    def show_nested_parts_in_workspace_dialog(self, nested_parts_in_workspace: list[LaserCutPart]) -> int:
        headers = ["No.", "Part Name", "Quantity", "Next Process", "Entire Process"]
        table_rows = ""

        for i, part in enumerate(nested_parts_in_workspace):
            next_process = part.get_next_tag_name()
            table_rows += f"""
            <tr>
                <td>{i + 1}</td>
                <td>{part.name}</td>
                <td>{part.inventory_data.quantity}</td>
                <td>{next_process}</td>
                <td>{part.workspace_data.flowtag.get_flow_string()}</td>
            </tr>
            """

        message = f"""
        <html>
            <head>
                <style>
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                    }}
                    th, td {{
                        border-bottom: 1px solid white;
                        padding: 8px;
                        text-align: left;
                    }}
                </style>
            </head>
            <body>
                <p>The following parts were found in Workspace and their process will be updated:</p>
                <table>
                    <tr>
                        <th>{headers[0]}</th>
                        <th>{headers[1]}</th>
                        <th>{headers[2]}</th>
                        <th>{headers[3]}</th>
                        <th>{headers[4]}</th>
                    </tr>
                    {table_rows}
                </table>
            </body>
        </html>
        """

        message_dialog = MessageDialog("Parts found in Workspace", message, self)
        return message_dialog.exec()

    def process_generate_workorder_dialog(self, nests: list[Nest]):
        generate_workorder_dialog = GenerateWorkorderDialog(self)
        if generate_workorder_dialog.exec():
            all_nested_laser_cut_parts = self.get_nested_laser_cut_parts(nests)
            all_workspace_laser_part_groups = self.workspace.get_grouped_laser_cut_parts(
                self.workspace.get_all_laser_cut_parts_with_similar_tag("laser"))

            self.workorder_update_nest_parts_data(nests, all_workspace_laser_part_groups)

            nested_parts_not_in_workspace = self.get_nested_parts_not_in_workspace(all_nested_laser_cut_parts,
                                                                                   all_workspace_laser_part_groups)
            nested_parts_in_workspace = self.get_nested_parts_in_workspace(all_nested_laser_cut_parts,
                                                                           all_workspace_laser_part_groups)

            if nested_parts_not_in_workspace and generate_workorder_dialog.should_add_overflow_parts():
                if self.show_nested_parts_not_in_workspace_dialog(nested_parts_not_in_workspace):
                    laser_cut_parts_to_update: list[LaserCutPart] = []
                    for nest in nests:
                        for nest_laser_cut_part in nest.laser_cut_parts:
                            for nested_laser_cut_part_not_in_workspace in nested_parts_not_in_workspace:
                                if nest_laser_cut_part.name == nested_laser_cut_part_not_in_workspace.name:
                                    new_part = LaserCutPart(
                                        nested_laser_cut_part_not_in_workspace.to_dict(),
                                        self.laser_cut_parts_inventory,
                                    )
                                    new_part.inventory_data.quantity = nested_laser_cut_part_not_in_workspace.meta_data.quantity_on_sheet * nest.sheet_count
                                    laser_cut_parts_to_update.append(new_part)
                                    break

                    self.laser_cut_parts_inventory.add_or_update_laser_cut_parts(laser_cut_parts_to_update,
                                                                                 "workorder nest overflow")
                    # self.laser_cut_parts_inventory.save_local_copy()
                    # self.upload_files(
                    #     [f"{self.laser_cut_parts_inventory.filename}.json"]
                    # )
                    msg = QMessageBox(
                        QMessageBox.Icon.Information,
                        "Updated",
                        "Parts were added to laser cut inventory.",
                        QMessageBox.StandardButton.Ok,
                        self,
                    )
                    msg.exec()
                else:
                    msg = QMessageBox(
                        QMessageBox.Icon.Information,
                        "Aborted",
                        "Process aborted.",
                        QMessageBox.StandardButton.Ok,
                        self,
                    )
                    msg.exec()
                    return

            if generate_workorder_dialog.should_remove_sheet_quantity():
                self.remove_sheet_quantities_from_nests(nests)
                msg = QMessageBox(
                    QMessageBox.Icon.Information,
                    "Updated",
                    "Sheets quantity was updated.",
                    QMessageBox.StandardButton.Ok,
                    self,
                )
                msg.exec()

            # if generate_workorder_dialog.should_update_inventory() and nested_parts_in_workspace:
            #     if not self.show_nested_parts_in_workspace_dialog(nested_parts_in_workspace):
            #         # self.laser_cut_parts_inventory.save_local_copy()
            #         # self.workspace.save()
            #         # self.upload_files(
            #         #     [
            #         #         f"{self.workspace.filename}.json",
            #         #         f"{self.laser_cut_parts_inventory.filename}.json",
            #         #     ],
            #         # )
            #         msg = QMessageBox(
            #             QMessageBox.Icon.Information,
            #             "Aborted",
            #             "Process aborted.",
            #             QMessageBox.StandardButton.Ok,
            #             self,
            #         )
            #         msg.exec()
            #         return
            #     self.workorder_move_to_next_process(
            #         nests,
            #         all_workspace_laser_part_groups,
            #         generate_workorder_dialog.should_add_remaining_parts(),
            #     )
            # self.laser_cut_parts_inventory.save_local_copy()
            # self.workspace.save()
            # self.upload_files(
            #     [
            #         f"{self.workspace.filename}.json",
            #         f"{self.laser_cut_parts_inventory.filename}.json",
            #     ],
            # )

            if generate_workorder_dialog.should_generate_printout():
                workorder = Workorder(nests, self.sheet_settings, self.laser_cut_parts_inventory)

                if generate_workorder_dialog.should_open_printout():
                    def workorder_saved(response: dict):
                        self.open_workorder(response["id"])

                    workorder.open_workorder(on_finished=workorder_saved)

            # self.workspace_tab_widget.workspace_widget.get_all_workspace_jobs_thread()
            # # self.workspace_tab_widget.workspace_widget.load_parts_table()
            # # self.workspace_tab_widget.workspace_widget.load_parts_tree()
            # # self.workspace_tab_widget.workspace_widget.load_assembly_tree()

    def workorder_update_nest_parts_data(
            self,
            nests: list[Nest],
            all_workspace_laser_part_groups: list[WorkspaceLaserCutPartGroup],
    ):
        for nest in nests:
            for nest_laser_cut_part in nest.laser_cut_parts:
                for workspace_laser_cut_part_group in all_workspace_laser_part_groups:
                    if workspace_laser_cut_part_group.base_part.name == nest_laser_cut_part.name:
                        nest_laser_cut_part.workspace_data.flowtag = workspace_laser_cut_part_group.base_part.workspace_data.flowtag

                        nest_laser_cut_part.meta_data.shelf_number = workspace_laser_cut_part_group.base_part.meta_data.shelf_number

                        nest_laser_cut_part.primer_data.uses_primer = workspace_laser_cut_part_group.base_part.primer_data.uses_primer
                        nest_laser_cut_part.primer_data.primer_item = workspace_laser_cut_part_group.base_part.primer_data.primer_item
                        nest_laser_cut_part.primer_data.primer_name = workspace_laser_cut_part_group.base_part.primer_data.primer_name
                        nest_laser_cut_part.paint_data.uses_paint = workspace_laser_cut_part_group.base_part.paint_data.uses_paint
                        nest_laser_cut_part.paint_data.paint_name = workspace_laser_cut_part_group.base_part.paint_data.paint_name
                        nest_laser_cut_part.paint_data.paint_item = workspace_laser_cut_part_group.base_part.paint_data.paint_item
                        nest_laser_cut_part.powder_data.uses_powder = workspace_laser_cut_part_group.base_part.powder_data.uses_powder
                        nest_laser_cut_part.powder_data.powder_name = workspace_laser_cut_part_group.base_part.powder_data.powder_name
                        nest_laser_cut_part.powder_data.powder_item = workspace_laser_cut_part_group.base_part.powder_data.powder_item
                        break

    def set_order_number_thread(self, order_number: float):
        self.order_number = order_number
        set_order_number_worker = SetOrderNumberWorker(order_number)
        QThreadPool.globalInstance().start(set_order_number_worker)

    def get_order_number_thread(self):
        get_order_number_worker = GetOrderNumberWorker()
        get_order_number_worker.signals.success.connect(self.get_order_number_thread_response)
        QThreadPool.globalInstance().start(get_order_number_worker)

    def get_order_number_thread_response(self, order_number: dict[str, int]):
        print(order_number)
        try:
            self.order_number = order_number.get("order_number", 0)
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Order number error")
            msg.setText(f"{e}")
            msg.exec()

    def load_previous_quotes_thread(self):
        get_previous_quotes_thread = GetPreviousQuotesThread()
        self.threads.append(get_previous_quotes_thread)
        get_previous_quotes_thread.signal.connect(self.load_previous_quotes_response)
        get_previous_quotes_thread.start()

    def load_previous_quotes_response(self, data: dict):
        if isinstance(data, dict):
            self.load_previous_quotes(data)
        else:
            self.status_button.setText(f"Error: {data}'", "red")

    def save_job_worker(self, job: Job):
        upload_job_worker = SaveJobWorker(job)
        upload_job_worker.signals.success.connect(self.save_job_response)
        self.status_button.setText(f"Uploading {job.name}", "yellow")
        self.job_planner_widget.update_job_save_status(job)
        QThreadPool.globalInstance().start(upload_job_worker)

    def save_job_response(self, response: str):
        if job := self.get_active_job():
            job.id = response["id"]
        self.status_button.setText("Job was sent successfully", "lime")
        self.load_jobs_worker()

    def print_job_worker(self, job: Job):
        upload_job_worker = SaveJobWorker(job)
        upload_job_worker.signals.success.connect(self.save_job_response)
        upload_job_worker.signals.success.connect(self.print_job_response)
        self.status_button.setText(f"Uploading {job.name}", "yellow")
        self.job_planner_widget.update_job_save_status(job)
        QThreadPool.globalInstance().start(upload_job_worker)

    def print_job_response(self, response: dict):
        self.open_job(response["id"])

    def load_jobs_worker(self):
        get_all_jobs_worker = GetAllJobsWorker()
        get_all_jobs_worker.signals.success.connect(self.load_jobs_response)
        QThreadPool.globalInstance().start(get_all_jobs_worker)

    def load_jobs_response(self, data: list[dict]):
        self.saved_jobs = data
        self.status_button.setText("Fetched all jobs", "lime")
        if self.tab_text(self.stackedWidget.currentIndex()) == "job_planner_tab":
            self.load_planning_jobs(data)
        elif self.tab_text(self.stackedWidget.currentIndex()) == "job_quoter_tab":
            self.load_quoting_jobs(data)
        # More will be added here such as quoting, workspace, archive...

    def load_saved_quoted_thread(self):
        get_saved_quotes_thread = GetSavedQuotesThread()
        self.threads.append(get_saved_quotes_thread)
        get_saved_quotes_thread.signal.connect(self.load_saved_quotes_response)
        get_saved_quotes_thread.start()

    def load_saved_quotes_response(self, data: dict):
        if isinstance(data, dict):
            self.load_saved_quotes(data)
        else:
            self.status_button.setText(f"Error: {data}'", "red")

    def reload_job_worker(self, job_id: int):
        self.status_button.setText(f"Reloading job (ID: {job_id}) data...", "yellow")
        job_loader_controller = JobLoaderController(self.job_manager, job_id)
        job_loader_controller.finished.connect(self.reload_job_response)
        self.threads.append(job_loader_controller)
        job_loader_controller.start()

    def reload_job_response(self, job: Job | None):
        if job:
            self.status_button.setText(f"{job.name} reloaded successfully!", "lime")
            if self.tab_text(self.stackedWidget.currentIndex()) == "job_planner_tab":
                self.job_planner_widget.reload_job(job)
            elif self.tab_text(self.stackedWidget.currentIndex()) == "job_quoter_tab":
                self.job_quote_widget.reload_job(job)
        else:
            self.status_button.setText(
                "Failed to load job: reload_job_worker.JobLoaderController: Job is None",
                "red",
            )

    def load_job_worker(self, job_id: int):
        self.status_button.setText(f"Loading job (ID: {job_id}) data...", "yellow")
        job_loader_thread = JobLoaderController(self.job_manager, job_id)
        job_loader_thread.finished.connect(self.load_job_response)
        self.threads.append(job_loader_thread)
        job_loader_thread.start()

    def load_job_response(self, job: Job | None):
        print(job)
        if job:
            self.status_button.setText(f"{job.name} loaded successfully!", "lime")
            if self.tab_text(self.stackedWidget.currentIndex()) == "job_planner_tab":
                self.job_planner_widget.load_job(job)
            elif self.tab_text(self.stackedWidget.currentIndex()) == "job_quoter_tab":
                self.job_quote_widget.load_job(job)
        else:
            print(f"Failed to load job: {job}")
            self.status_button.setText(
                "Failed to load job: load_job_worker.JobLoaderController: Job is None",
                "red",
            )

    def update_job_settings_worker(self, job_id: str, job_setting_key: str, setting: QComboBox):
        setting.setEnabled(False)
        update_job_settings_worker = UpdateJobSettingWorker(job_id, job_setting_key, setting.currentIndex() + 1)
        update_job_settings_worker.signals.success.connect(self.update_job_settings_response)
        QThreadPool.globalInstance().start(update_job_settings_worker)

    def update_job_settings_response(self, response: dict):
        self.status_button.setText(
            f"Successfully updated job (ID: {response}) settings",
            "lime",
        )
        self.load_jobs_worker()

    def delete_job_worker(self, job_id: int):
        are_you_sure = QMessageBox(
            QMessageBox.Icon.Question,
            "Are you sure?",
            "Are you sure you want to delete this job?\n\nThis is permanent and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            self,
        )
        if are_you_sure.exec() == QMessageBox.StandardButton.Yes:
            self.status_button.setText(f"Deleting {job_id}", "yellow")
            delete_job_worker = DeleteJobWorker(job_id)
            delete_job_worker.signals.success.connect(self.delete_job_response)
            QThreadPool.globalInstance().start(delete_job_worker)

    def delete_job_response(self, response: dict):
        self.status_button.setText(
            "Successfully deleted!",
            "lime",
        )
        self.load_jobs_worker()

    def send_email_thread(self, title: str, message: str, emails: list[str], notify: bool = False):
        self.status_button.setText("Loading quote data", "yellow")
        send_email_thread = SendEmailThread(title, message, emails)
        self.threads.append(send_email_thread)
        if notify:
            send_email_thread.signal.connect(self.send_email_response)
        send_email_thread.start()

    def send_email_response(self, response: str):
        self.status_button.setText(response, "lime")

    def start_check_for_updates_thread(self):
        check_for_updates_thread = CheckForUpdatesThread(self, __version__)
        check_for_updates_thread.signal.connect(self.update_available_thread_response)
        self.threads.append(check_for_updates_thread)
        check_for_updates_thread.start()

    def update_available_thread_response(self, new_version: str, update_message: str):
        if not self.ignore_update:
            self.ignore_update = True
            msg = UpdateDialog(self, __version__, new_version, update_message)
            if msg.exec():
                subprocess.Popen("start update.exe", shell=True)

    # * /\ THREADS /\

    def clear_layout(self, layout: QVBoxLayout | QHBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = theme_var("primary")
        hover_color: str = lighten_color(base_color)
        inverted_color = theme_var("on-primary")
        button.setObjectName("tool_box_button")
        button.setStyleSheet(
            f"""
            QPushButton#tool_box_button {{
                border: 1px solid {theme_var("surface")};
                background-color: {theme_var("surface")};
                border-radius: {theme_var("border-radius")};
                color: {theme_var("on-surface")};
                text-align: left;
            }}

            /* CLOSED */
            QPushButton:!checked#tool_box_button {{
                color: {theme_var("on-surface")};
                border: 1px solid {theme_var("outline")};
            }}

            QPushButton:!checked:hover#tool_box_button {{
                background-color: {theme_var("outline-variant")};
            }}
            QPushButton:!checked:pressed#tool_box_button {{
                background-color: {theme_var("surface")};
            }}
            /* OPENED */
            QPushButton:checked#tool_box_button {{
                color: %(inverted_color)s;
                border-color: %(base_color)s;
                background-color: %(base_color)s;
                border-top-left-radius: {theme_var("border-radius")};
                border-top-right-radius: {theme_var("border-radius")};
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}

            QPushButton:checked:hover#tool_box_button {{
                background-color: %(hover_color)s;
            }}

            QPushButton:checked:pressed#tool_box_button {{
                background-color: %(pressed_color)s;
            }}"""
            % {
                "base_color": base_color,
                "hover_color": hover_color,
                "pressed_color": base_color,
                "inverted_color": inverted_color,
            }
        )
        widget.setObjectName("assembly_widget_drop_menu")
        widget.setStyleSheet(
            """QWidget#assembly_widget_drop_menu{
            border: 1px solid %(base_color)s;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            };
            """
            % {"base_color": base_color}
        )

    # * \/ OVERIDDEN UI EVENTS \/
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        pass

    def closeEvent(self, event):
        self.save_geometry()
        self.save_menu_tab_order()
        super().closeEvent(event)

    # * /\ OVERIDDEN UI EVENTS /
