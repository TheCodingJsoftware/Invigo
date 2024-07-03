import contextlib
import logging
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
import winsound
from datetime import datetime
from functools import partial
from typing import Any

import requests
import win32api  # pywin32
from natsort import natsorted, ns
from PyQt6 import uic
from PyQt6.QtCore import QEventLoop, QPoint, Qt, QThread, QTimer
from PyQt6.QtGui import QAction, QColor, QCursor, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QFont, QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QApplication, QComboBox, QCompleter, QFileDialog, QFileIconProvider, QFontDialog, QGridLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPushButton, QScrollArea, QTableWidgetItem, QTabWidget, QToolBox, QTreeView, QTreeWidget, QVBoxLayout, QWidget

from ui.about_dialog import AboutDialog
from ui.components_tab import ComponentsTab
from ui.custom.job_tab import JobTab
from ui.custom.job_widget import JobWidget
from ui.custom.saved_job_item import SavedPlanningJobItem
from ui.custom_widgets import CustomTableWidget, MultiToolBox, PdfTreeView, PreviousQuoteItem, RichTextPushButton, SavedQuoteItem, ScrollPositionManager, ViewTree, set_default_dialog_button_stylesheet
from ui.edit_paint_inventory import EditPaintInventory
from ui.edit_workspace_settings import EditWorkspaceSettings
from ui.generate_quote_dialog import GenerateQuoteDialog
from ui.job_sorter_dialog import JobSorterDialog
from ui.laser_cut_tab import LaserCutTab
from ui.nest_sheet_verification import NestSheetVerification
from ui.quote_generator_tab import QuoteGeneratorTab
from ui.save_quote_dialog import SaveQuoteDialog
from ui.select_item_dialog import SelectItemDialog
from ui.sheet_settings_tab import SheetSettingsTab
from ui.sheets_in_inventory_tab import SheetsInInventoryTab
from ui.workspace_tab import WorkspaceTab
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.history_file import HistoryFile
from utils.inventory.category import Category
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.inventory.paint_inventory import PaintInventory
from utils.inventory.sheet import Sheet
from utils.inventory.sheets_inventory import SheetsInventory
from utils.inventory_excel_file import ExcelFile
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.json_file import JsonFile
from utils.po import check_po_directories, get_all_po
from utils.po_template import POTemplate
from utils.price_history_file import PriceHistoryFile
from utils.quote.generate_printout import GeneratePrintout
from utils.quote.nest import Nest
from utils.quote.quote import Quote
from utils.settings import Settings
from utils.sheet_settings.sheet_settings import SheetSettings
from utils.threads.changes_thread import ChangesThread
from utils.threads.check_for_updates_thread import CheckForUpdatesThread
from utils.threads.delete_job_thread import DeleteJobThread
from utils.threads.delete_quote_thread import DeleteQuoteThread
from utils.threads.download_images_thread import DownloadImagesThread
from utils.threads.download_job_thread import DownloadJobThread
from utils.threads.download_quote_thread import DownloadQuoteThread
from utils.threads.download_thread import DownloadThread
from utils.threads.exchange_rate import ExchangeRate
from utils.threads.generate_quote_thread import GenerateQuoteThread
from utils.threads.get_jobs_thread import GetJobsThread
from utils.threads.get_order_number_thread import GetOrderNumberThread
from utils.threads.get_previous_quotes_thread import GetPreviousQuotesThread
from utils.threads.get_saved_quotes_thread import GetSavedQuotesThread
from utils.threads.job_loader_thread import JobLoaderThread
from utils.threads.load_nests_thread import LoadNestsThread
from utils.threads.send_email_thread import SendEmailThread
from utils.threads.send_sheet_report_thread import SendReportThread
from utils.threads.set_order_number_thread import SetOrderNumberThread
from utils.threads.update_job_setting import UpdateJobSetting
from utils.threads.update_quote_settings import UpdateQuoteSettings
from utils.threads.upload_job_thread import UploadJobThread
from utils.threads.upload_quote import UploadQuote
from utils.threads.upload_thread import UploadThread
from utils.trusted_users import get_trusted_users
from utils.workspace.generate_printout import JobPlannerPrintout
from utils.workspace.job import Job, JobColor, JobStatus
from utils.workspace.job_manager import JobManager
from utils.workspace.job_preferences import JobPreferences
from utils.workspace.workspace import Workspace
from utils.workspace.workspace_settings import WorkspaceSettings

__version__: str = "v3.0.39"
__updated__: str = "2024-07-02 19:54:56"


def check_folders(folders: list[str]) -> None:
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


def _play_celebrate_sound() -> None:
    winsound.PlaySound("sounds/sound.wav", winsound.SND_FILENAME)


def _play_boot_sound() -> None:
    winsound.PlaySound("sounds/boot.wav", winsound.SND_FILENAME)


logging.basicConfig(
    filename="logs/app.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)


def excepthook(exc_type, exc_value, exc_traceback):
    logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
    threading.Thread(target=send_error_report).start()
    win32api.MessageBox(
        0,
        f"We've encountered an unexpected issue. The details of this glitch have been automatically reported to Jared, and a notification has been sent to jared@pinelandfarms.ca for immediate attention. Rest assured, Jared is on the case and will likely have this resolved with the next update. Your patience and understanding are greatly appreciated. If this problem persists, please don't hesitate to reach out directly to Jared for further assistance.\n\nTechnical details for reference:\n - Exception Type: {exc_type}\n - Error Message: {exc_value}\n - Traceback Information: {exc_traceback}",
        "Unhandled exception - excepthook detected",
        0x40,
    )  # 0x40 for OK button


def send_error_report():
    SERVER_IP: str = get_server_ip_address()
    SERVER_PORT: int = get_server_port()
    url = f"http://{SERVER_IP}:{SERVER_PORT}/send_error_report"
    with open("logs/app.log", "r", encoding="utf-8") as error_log:
        error_data = error_log.read()
    data = {"error_log": f"User: {os.getlogin().title()}\nVersion: {__version__}\n\n{error_data}"}
    response = requests.post(url, data=data, timeout=5)
    if response.status_code != 200:
        win32api.MessageBox(
            0,
            f"Failed to send email. Kindly notify Jared about the issue you just encountered!",
            "Failed to send email",
            0x40,
        )


sys.excepthook = excepthook


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("ui/main_window.ui", self)
        self.threads: list[QThread] = []
        self.order_number: int = -1
        self.get_order_number_thread()

        self.settings_file = Settings()
        self.sheet_settings = SheetSettings()
        self.workspace_settings = WorkspaceSettings()
        self.job_preferences = JobPreferences()

        self.sheets_inventory = SheetsInventory(self)
        self.components_inventory = ComponentsInventory()
        self.paint_inventory = PaintInventory(self)
        self.laser_cut_inventory = LaserCutInventory(self)
        self.job_manager = JobManager(self)

        self.quote_generator_tab_widget = QuoteGeneratorTab(self)
        self.quote_generator_tab_widget.add_quote(Quote("Quote0", None, self.components_inventory, self.laser_cut_inventory, self.sheet_settings))
        self.quote_generator_tab_widget.save_quote.connect(self.save_quote)
        self.quote_generator_tab_widget.save_quote_as.connect(self.save_quote_as)
        self.clear_layout(self.omnigen_layout)
        self.omnigen_layout.addWidget(self.quote_generator_tab_widget)

        self.job_planner_widget = JobTab(self)
        self.job_planner_widget.savJob.connect(self.save_job)
        self.job_planner_widget.saveJobAs.connect(self.save_job_as)
        self.job_planner_widget.reloadJob.connect(self.reload_job)
        template_job = Job("Enter Job Name0", {}, self.job_manager)
        template_job.order_number = self.order_number
        self.job_planner_widget.load_job(template_job)
        self.clear_layout(self.job_planner_layout)
        self.job_planner_layout.addWidget(self.job_planner_widget)

        self.job_quote_widget = JobTab(self)
        self.job_quote_widget.savJob.connect(self.save_job)
        self.job_quote_widget.saveJobAs.connect(self.save_job_as)
        self.job_quote_widget.reloadJob.connect(self.reload_job)
        template_job = Job("Enter Job Name0", {}, self.job_manager)
        template_job.job_status = JobStatus.QUOTING
        template_job.order_number = self.order_number
        self.job_quote_widget.load_job(template_job)

        # self.quote_planner_tab_widget.add_job(Job("Job0", None))
        self.clear_layout(self.quote_generator_layout)
        self.quote_generator_layout.addWidget(self.job_quote_widget)

        self.components_tab_widget: ComponentsTab = None
        self.components_tab_widget_last_selected_tab_index: int = 0  # * Used inside components_tab.py

        self.sheets_inventory_tab_widget: SheetsInInventoryTab = None
        self.sheets_inventory_tab_widget_last_selected_tab_index: int = 0  # * Used inside sheets_in_inventory_tab.py

        self.laser_cut_tab_widget: LaserCutTab = None
        self.laser_cut_tab_widget_last_selected_tab_index: int = 0  # * Used inside laser_cut_tab.py

        self.sheet_settings_tab_widget: SheetSettingsTab = None

        self.workspace_tab_widget: WorkspaceTab = None

        self.username = os.getlogin().title()
        self.trusted_user: bool = False
        self.setWindowTitle(f"Invigo - {__version__} - {self.username}")
        self.setWindowIcon(QIcon(Icons.icon))

        check_po_directories()
        # self.check_for_updates(on_start_up=True)

        history_file_date = datetime.strptime(self.settings_file.get_value("price_history_file_name"), "%B %d %A %Y")
        days_from_last_price_history_assessment: int = int((datetime.now() - history_file_date).total_seconds() / 60 / 60 / 24)
        if days_from_last_price_history_assessment > self.settings_file.get_value("days_until_new_price_history_assessment"):
            self.settings_file.set_value("price_history_file_name", str(datetime.now().strftime("%B %d %A %Y")))
            msg = QMessageBox(QMessageBox.Icon.Information, "Price Assessment", f"It has been {self.settings_file.get_value('days_until_new_price_history_assessment')} days until the last price assessment. A new price history file has been created in the 'Price History Files' directory.")
            msg.exec()

        # VARIABLES
        self.category: Category = None
        self.categories: list[Category] = []
        self.active_layout: QVBoxLayout = None
        self.downloading_changes: bool = False
        self.finished_downloading_all_files: bool = False
        self.finished_loading_tabs: bool = False
        self.files_downloaded_count: int = 0
        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])
        self.tabs: dict[Category, CustomTableWidget] = {}
        self.parts_in_inventory_name_lookup: dict[str, int] = {}
        self.last_selected_menu_tab: str = self.settings_file.get_value("menu_tabs_order")[self.settings_file.get_value("last_toolbox_tab")]
        self.quote_nest_directories_list_widgets: dict[str, PdfTreeView] = {}
        self.quote_job_directories_list_widgets: dict[str, PdfTreeView] = {}
        self.quote_nest_information = {}
        self.quote_components_information = {}
        self.tabWidget: QTabWidget = self.findChild(QTabWidget, "tabWidget")
        self.scroll_position_manager = ScrollPositionManager()

        self.ignore_update: bool = False

        self.check_trusted_user()
        self.__load_ui()
        self.download_all_files()
        self.start_check_for_updates_thread()

        self.splitter_3.setStretchFactor(3, 3)  # Quote Generator
        self.splitter.setStretchFactor(10, 11)  # Job Planner
        self.splitter_2.setStretchFactor(10, 11)  # Quote Generator 2

    def __load_ui(self) -> None:
        menu_tabs_order: list[str] = self.settings_file.get_value(setting_name="menu_tabs_order")
        for tab_name in menu_tabs_order:
            index = self.get_tab_from_name(tab_name)
            if index != -1:
                self.tabWidget.tabBar().moveTab(index, menu_tabs_order.index(tab_name))

        # Tool Box
        self.tabWidget.setCurrentIndex(self.settings_file.get_value(setting_name="last_toolbox_tab"))
        self.tabWidget.currentChanged.connect(self.tool_box_menu_changed)

        # Load Nests
        self.saved_quotes_tool_box = MultiToolBox(self)
        self.saved_quotes_tool_box_opened_menus: dict[int, bool] = {0: False, 1: False, 2: False}
        self.verticalLayout_4.addWidget(self.saved_quotes_tool_box)
        self.pushButton_refresh_saved_nests.clicked.connect(self.load_saved_quoted_thread)

        self.previous_quotes_tool_box = MultiToolBox(self)
        self.previous_quotes_tool_box_opened_menus: dict[int, bool] = {0: False, 1: False, 2: False}
        self.verticalLayout_28.addWidget(self.previous_quotes_tool_box)
        self.pushButton_refresh_previous_nests.clicked.connect(self.load_previous_quotes_thread)

        self.cutoff_widget = MultiToolBox(self)
        self.verticalLayout_cutoff.addWidget(self.cutoff_widget)
        cutoff_items = QListWidget(self)
        cutoff_items.doubleClicked.connect(partial(self.cutoff_sheet_double_clicked, cutoff_items))
        self.cutoff_widget.addItem(cutoff_items, "Cutoff Sheets")
        self.cutoff_widget.close_all()

        self.pushButton_load_nests.clicked.connect(self.process_selected_nests)
        self.pushButton_clear_selections.clicked.connect(self.clear_nest_selections)
        self.pushButton_refresh_directories.clicked.connect(self.refresh_nest_directories)
        self.pushButton_generate_quote.clicked.connect(self.generate_printout)

        self.pushButton_load_nests_2.clicked.connect(self.process_selected_nests_to_job)
        self.pushButton_clear_selections_2.clicked.connect(self.clear_job_quote_selections)
        self.pushButton_refresh_directories_2.clicked.connect(self.refresh_nest_directories)

        self.pushButton_refresh_jobs.clicked.connect(self.load_jobs_thread)

        self.pushButton_save.clicked.connect(partial(self.save_quote, None))
        self.pushButton_save_as.clicked.connect(partial(self.save_quote_as, None))

        self.pushButton_save_job.clicked.connect(partial(self.save_job, None))
        self.pushButton_save_as_job.setHidden(True)

        self.saved_planning_jobs_layout = self.findChild(QVBoxLayout, "saved_planning_jobs_layout")
        self.saved_planning_jobs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.saved_jobs_multitoolbox = MultiToolBox(self)
        self.saved_planning_jobs_layout.addWidget(self.saved_jobs_multitoolbox)
        self.saved_planning_job_items_last_opened: dict[int, bool] = {}

        self.templates_jobs_layout = self.findChild(QVBoxLayout, "template_jobs_layout")
        self.templates_jobs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.templates_jobs_multitoolbox = MultiToolBox(self)
        self.templates_jobs_layout.addWidget(self.templates_jobs_multitoolbox)
        self.templates_job_items_last_opened: dict[int, bool] = {}

        self.saved_planning_jobs_layout_2 = self.findChild(QVBoxLayout, "saved_planning_jobs_layout_2")
        self.saved_planning_jobs_layout_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.saved_jobs_multitoolbox_2 = MultiToolBox(self)
        self.saved_planning_jobs_layout_2.addWidget(self.saved_jobs_multitoolbox_2)
        self.saved_planning_job_items_last_opened_2: dict[int, bool] = {}

        self.templates_jobs_layout_2 = self.findChild(QVBoxLayout, "template_jobs_layout_2")
        self.templates_jobs_layout_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.templates_jobs_multitoolbox_2 = MultiToolBox(self)
        self.templates_jobs_layout_2.addWidget(self.templates_jobs_multitoolbox_2)
        self.templates_job_items_last_opened_2: dict[int, bool] = {}

        # Status
        self.status_button = RichTextPushButton(self)
        self.status_button.setText("Downloading all files, please wait...", "yellow")
        self.status_button.setObjectName("status_button")
        self.status_button.setFlat(True)
        self.status_button.setFixedHeight(25)
        self.verticalLayout_status.addWidget(self.status_button)

        # Tab widget
        # self.pushButton_add_new_sheet.clicked.connect(self.add_sheet_item)

        # Action events
        # HELP
        self.actionAbout_Qt.triggered.connect(QApplication.aboutQt)
        self.actionCheck_for_Updates.triggered.connect(self.check_for_updates)
        self.actionAbout.triggered.connect(self.show_about_dialog)
        self.actionServer_logs.triggered.connect(self.open_server_logs)
        self.actionInventory.triggered.connect(self.open_inventory)
        self.actionQr_Codes.triggered.connect(self.open_qr_codes)
        # PRINT
        self.actionPrint_Inventory.triggered.connect(self.print_inventory)

        # SETTINGS
        self.actionChange_tables_font.triggered.connect(self.change_tables_font)
        self.actionSet_Order_Number.triggered.connect(self.set_order_number)

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
        self.update_sorting_status_text()

        # PURCHASE ORDERS
        self.actionAdd_Purchase_Order.triggered.connect(partial(self.add_po_templates, [], True))
        self.actionRemove_Purchase_Order.triggered.connect(self.delete_po)
        self.actionOpen_Purchase_Order.triggered.connect(partial(self.open_po, None))
        self.actionOpen_Folder.triggered.connect(partial(self.open_folder, "PO's"))

        # QUOTE GENERATOR
        self.actionAdd_Nest_Directory.triggered.connect(self.add_nest_directory)
        self.actionRemove_Nest_Directory.triggered.connect(self.remove_nest_directory)
        self.actionEdit_Paint_in_Inventory.triggered.connect(self.edit_paint_inventory)

        # JOB SORTER
        self.actionOpenMenu.triggered.connect(self.open_job_sorter)

        # WORKSPACE
        self.actionEditTags.triggered.connect(self.open_tag_editor)

        # FILE

        self.actionOpen_Item_History.triggered.connect(self.open_item_history)

        self.actionExit.triggered.connect(self.close)
        # self.actionExit.setIcon(QIcon("icons/tab_close.png"))

        if not self.trusted_user:
            self.tabWidget.setTabVisible(
                self.settings_file.get_value("menu_tabs_order").index("Components"),
                False,
            )
            self.tabWidget.setTabVisible(
                self.settings_file.get_value("menu_tabs_order").index("View Price Changes History"),
                False,
            )
            self.tabWidget.setTabVisible(
                self.settings_file.get_value("menu_tabs_order").index("View Removed Quantities History"),
                False,
            )

    # * \/ SLOTS & SIGNALS \/
    def tool_box_menu_changed(self) -> None:
        # self.loading_screen.show()
        self.components_inventory.load_data()
        self.sheets_inventory.load_data()
        self.laser_cut_inventory.load_data()
        self.sheet_settings.load_data()
        self.workspace_settings.load_data()

        self.clear_layout(self.sheet_settings_layout)
        self.sheet_settings_layout.addWidget(QLabel("Loading...", self))
        self.clear_layout(self.laser_cut_layout)
        self.laser_cut_layout.addWidget(QLabel("Loading...", self))
        self.clear_layout(self.sheets_inventory_layout)
        self.sheets_inventory_layout.addWidget(QLabel("Loading...", self))
        self.clear_layout(self.components_layout)
        self.components_layout.addWidget(QLabel("Loading...", self))
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Components":
            if not self.trusted_user:
                self.show_not_trusted_user()
                return
            self.menuSort.setEnabled(True)
            self.clear_layout(self.components_layout)
            self.components_tab_widget = ComponentsTab(self)
            self.components_layout.addWidget(self.components_tab_widget)
            self.components_tab_widget.restore_scroll_position()
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
            self.menuSort.setEnabled(True)
            self.clear_layout(self.sheets_inventory_layout)
            self.sheets_inventory_tab_widget = SheetsInInventoryTab(self)
            self.sheets_inventory_layout.addWidget(self.sheets_inventory_tab_widget)
            self.sheets_inventory_tab_widget.restore_scroll_position()
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Laser Cut Inventory":
            self.menuSort.setEnabled(True)
            self.clear_layout(self.laser_cut_layout)
            self.laser_cut_tab_widget = LaserCutTab(self)
            self.laser_cut_layout.addWidget(self.laser_cut_tab_widget)
            self.laser_cut_tab_widget.restore_scroll_position()
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheet Settings":
            self.clear_layout(self.sheet_settings_layout)
            self.sheet_settings_tab_widget = SheetSettingsTab(self)
            self.sheet_settings_layout.addWidget(self.sheet_settings_tab_widget)
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Quote Generator":
            self.load_cuttoff_drop_down()
            self.load_saved_quoted_thread()
            self.load_previous_quotes_thread()
            self.refresh_nest_directories()
            for quote_widget in self.quote_generator_tab_widget.quotes:
                quote_widget.update_sheet_statuses()
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Quote Generator 2":
            self.load_jobs_thread()
            self.refresh_nest_directories()
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Job Planner":  # TODO Load server jobs
            self.load_jobs_thread()
            self.job_planner_widget.update_tables()
            # pass
            # self.clear_layout(self.job_planner_layout)
            # self.quote_planner_tab_widget = QuotePlannerTab(self)
            # self.job_planner_layout.addWidget(self.quote_planner_tab_widget)
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "View Removed Quantities History":  # View Removed Quantities History
            self.menuSort.setEnabled(False)
            if not self.trusted_user:
                self.show_not_trusted_user()
                return
            self.load_history_view()
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "View Price Changes History":  # View Price Changes History
            self.menuSort.setEnabled(False)
            if not self.trusted_user:
                self.show_not_trusted_user()
                return
            self.load_price_history_view()
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            msg = QMessageBox(QMessageBox.Icon.Warning, "In development", "Workspace is not available at the moment.", QMessageBox.StandardButton.Ok, self)
            msg.exec()
            return
            self.menuSort.setEnabled(False)
            self.clear_layout(self.workspace_layout)
            self.workspace_tab_widget = WorkspaceTab(self.admin_workspace, self.user_workspace, self.history_workspace, self.workspace_settings, self.components_inventory, self.laser_cut_inventory, self.paint_inventory, self)
            self.workspace_layout.addWidget(self.workspace_tab_widget)
        self.settings_file.set_value("last_toolbox_tab", self.tabWidget.currentIndex())
        self.last_selected_menu_tab = self.tabWidget.tabText(self.tabWidget.currentIndex())

        # self.loading_screen.hide()

    def apply_sort(self):
        # Because each of these gets deleted when not in view
        with contextlib.suppress(AttributeError, RuntimeError):
            if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Components":
                self.status_button.setText("Sorted Components", "lime")
                self.components_tab_widget.sort_components()
            elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
                self.status_button.setText("Sorted Sheets", "lime")
                self.sheets_inventory_tab_widget.sort_sheets()
            elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Laser Cut Inventory":
                self.laser_cut_tab_widget.sort_laser_cut_parts()
                self.status_button.setText("Sorted Laser Cut Parts", "lime")

    def action_group(self, group_name: str, actions: list[QAction]) -> None:
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

    def process_selected_nests(self) -> None:
        if self.quote_generator_tab_widget.current_quote.downloaded_from_server:
            msg = QMessageBox(
                QMessageBox.Icon.Question,
                "Overwrite changes",
                f"You are about to overwrite this quote from your view. This action will not change the quote from the server. It will only be changed from your current session.\n\nAre you sure you want to overwrite {self.quote_generator_tab_widget.current_quote.name}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                self,
            )
            response = msg.exec()
            if response in [QMessageBox.StandardButton.No, QMessageBox.StandardButton.Cancel]:
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
            if response in [QMessageBox.StandardButton.No, QMessageBox.StandardButton.Cancel]:
                return
        if selected_items := self.get_all_selected_job_quotes():
            self.load_nests_for_job_thread(selected_items)

    def cutoff_sheet_double_clicked(self, cutoff_items: QListWidget):
        cutoff_sheets = self.sheets_inventory.get_sheets_by_category("Cutoff")
        item_pressed: QListWidgetItem = cutoff_items.selectedItems()[0]
        for sheet in cutoff_sheets:
            if item_pressed.text() == sheet.get_name():
                self.quote_generator_tab_widget.quotes[self.quote_generator_tab_widget.tab_widget.currentIndex()].comboBox_global_sheet_material_2.setCurrentText(sheet.material)
                self.quote_generator_tab_widget.quotes[self.quote_generator_tab_widget.tab_widget.currentIndex()].comboBox_global_sheet_thickness_2.setCurrentText(sheet.thickness)
                self.quote_generator_tab_widget.quotes[self.quote_generator_tab_widget.tab_widget.currentIndex()].doubleSpinBox_global_sheet_length_2.setValue(sheet.length)
                self.quote_generator_tab_widget.quotes[self.quote_generator_tab_widget.tab_widget.currentIndex()].doubleSpinBox_global_sheet_width_2.setValue(sheet.width)
                self.quote_generator_tab_widget.quotes[self.quote_generator_tab_widget.tab_widget.currentIndex()].global_sheet_materials_changed()
                self.quote_generator_tab_widget.quotes[self.quote_generator_tab_widget.tab_widget.currentIndex()].global_sheet_materials_changed()
                self.quote_generator_tab_widget.quotes[self.quote_generator_tab_widget.tab_widget.currentIndex()].global_sheet_dimension_changed()
                self.quote_generator_tab_widget.quotes[self.quote_generator_tab_widget.tab_widget.currentIndex()].update_sheet_statuses()
                return

    # * /\ SLOTS & SIGNALS /\

    # * \/ UPDATE UI ELEMENTS \/
    def change_tables_font(self) -> None:
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

    def update_sorting_status_text(self) -> None:
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

    def clear_nest_selections(self) -> None:
        for tree_view in self.quote_nest_directories_list_widgets.values():
            tree_view.clearSelection()

    def clear_job_quote_selections(self) -> None:
        for tree_view in self.quote_job_directories_list_widgets.values():
            tree_view.clearSelection()

    def nest_directory_item_selected(self) -> None:
        # self.process_selected_nests()
        selected_nests = len(self.get_all_selected_nests())
        if selected_nests == 0:
            self.pushButton_load_nests.setEnabled(False)
        else:
            self.pushButton_load_nests.setEnabled(True)
        self.pushButton_load_nests.setText(f"Load {selected_nests} Nest{'' if selected_nests == 1 else 's'}")

    def job_quote_directory_item_selected(self) -> None:
        # self.process_selected_nests()
        selected_nests = len(self.get_all_selected_job_quotes())
        if selected_nests == 0:
            self.pushButton_load_nests_2.setEnabled(False)
        else:
            self.pushButton_load_nests_2.setEnabled(True)
        self.pushButton_load_nests_2.setText(f"Load {selected_nests} Nest{'' if selected_nests == 1 else 's'}")

    def save_scroll_position(self, category: Category, table: CustomTableWidget):
        self.scroll_position_manager.save_scroll_position(f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} - {category.name}", table)

    def get_scroll_position(self, category: Category) -> QPoint:
        return self.scroll_position_manager.get_scroll_position(f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} - {category.name}")

    # * /\ UPDATE UI ELEMENTS /\
    # * \/ GETTERS \/

    def get_exchange_rate(self) -> float:
        return self.settings_file.get_value(setting_name="exchange_rate")

    def get_all_selected_nests(self) -> list[str]:
        selected_nests = []
        for tree_view in self.quote_nest_directories_list_widgets.values():
            selected_nests.extend(tree_view.full_paths)
        return list(set(selected_nests))

    def get_all_selected_job_quotes(self) -> list[str]:
        selected_nests = []
        for tree_view in self.quote_job_directories_list_widgets.values():
            selected_nests.extend(tree_view.full_paths)
        return list(set(selected_nests))

    def get_menu_tab_order(self) -> list[str]:
        return [self.tabWidget.tabText(i) for i in range(self.tabWidget.count())]

    def get_tab_from_name(self, name: str) -> int:
        return next(
            (i for i in range(self.tabWidget.count()) if self.tabWidget.tabText(i) == name),
            -1,
        )

    def get_all_selected_parts(self, tab: CustomTableWidget) -> list[str]:
        selected_rows = tab.selectedItems()
        all_items = list(self.parts_in_inventory_name_lookup.keys())

        selected_items: list[str] = [item.text() for item in selected_rows if item.text() in all_items and item.column() == 0]
        return selected_items

    # * /\ GETTERS /\
    def save_geometry(self) -> None:
        geometry = self.settings_file.get_value("geometry")
        geometry["x"] = max(self.pos().x(), 0)
        geometry["y"] = max(self.pos().y(), 0)
        geometry["width"] = self.size().width()
        geometry["height"] = self.size().height()
        self.settings_file.set_value("geometry", geometry)

    def save_menu_tab_order(self) -> None:
        self.settings_file.set_value("menu_tabs_order", self.get_menu_tab_order())

    # * \/ Dialogs \/
    def show_about_dialog(self) -> None:
        dialog = AboutDialog(
            self,
            __version__,
            __updated__,
            "https://github.com/TheCodingJsoftware/Inventory-Manager",
        )
        dialog.show()

    def show_not_trusted_user(self) -> None:
        self.tabWidget.setCurrentIndex(self.settings_file.get_value("menu_tabs_order").index(self.last_selected_menu_tab))
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Permission error")
        msg.setText("You don't have permission to change inventory items.")
        msg.exec()

    def open_group_menu(self, menu: QMenu) -> None:
        menu.exec(QCursor.pos())

    def add_nest_directory(self) -> None:
        nest_directories: list[str] = self.settings_file.get_value("quote_nest_directories")
        if new_nest_directory := QFileDialog.getExistingDirectory(self, "Open directory", "/"):
            nest_directories.append(new_nest_directory)
            self.settings_file.set_value("quote_nest_directories", nest_directories)
            self.refresh_nest_directories()

    def remove_nest_directory(self) -> None:
        nest_directories: list[str] = self.settings_file.get_value("quote_nest_directories")
        select_item_dialog = SelectItemDialog(DialogButtons.discard_cancel, "Remove Nest Directory", "Select a nest directory to delete. (from gui. not system)\n\nThis action is permanent and cannot be undone.", nest_directories, self)

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
        folder_path = f"saved_jobs\\{job.job_status.name.lower()}\\{job.name}"
        self.reload_job_thread(folder_path)

    def save_job(self, job: Job):
        if job is None:
            job = self.job_planner_widget.current_job
        job_plan_printout = JobPlannerPrintout(job)
        html = job_plan_printout.generate()
        self.upload_job_thread(f"saved_jobs/{job.job_status.name.lower()}/{job.name}", job, html)
        job.unsaved_changes = False
        self.job_planner_widget.update_job_save_status(job)
        self.status_button.setText(f"Saved {job.name}", "lime")
        self.upload_file(
            [
                "components_inventory.json",
                "laser_cut_inventory.json",
            ],
        )

    def save_job_as(self, job: Job):  # Todo
        return
        job_plan_printout = JobPlannerPrintout(job)
        html = job_plan_printout.generate()
        self.upload_job_thread(f"saved_jobs/{job.job_status.name.lower()}/{job.name}", job, html)
        self.status_button.setText(f"Saved {job.name}", "lime")
        self.upload_file(
            [
                "components_inventory.json",
                "laser_cut_inventory.json",
            ],
        )

    def save_quote(self, quote: Quote):
        if quote is None:
            quote = self.quote_generator_tab_widget.current_quote
        if not quote.downloaded_from_server:
            self.save_quote_as(quote)
            return
        quote.group_laser_cut_parts()
        generate_quote = GeneratePrintout("Quote", quote)
        html_file = generate_quote.generate()

        folder = f"saved_quotes/quotes/{quote.name}"
        self.upload_nest_images(quote)
        self.upload_quote_thread(folder, quote, html_file)
        self.status_button.setText(f"Saved {quote.name}", "lime")
        quote.unsaved_changes = False
        self.quote_generator_tab_widget.update_quote_save_status(quote)

    def save_quote_as(self, quote: Quote):
        if quote is None:
            quote = self.quote_generator_tab_widget.current_quote
        dialog = SaveQuoteDialog(quote, self)
        if dialog.exec():
            quote.name = dialog.get_name()
            quote.status = dialog.get_status()
            quote.order_number = dialog.get_order_number()
            quote.date_shipped = dialog.get_date_shipped()
            quote.date_expected = dialog.get_date_expected()
            quote.ship_to = dialog.get_ship_to()

            quote_type = dialog.get_type()

            quote.group_laser_cut_parts()
            generate_quote = GeneratePrintout(quote_type, quote)
            html_file = generate_quote.generate()
            folder = f"saved_quotes/{quote_type.lower().replace(' ', '_')}s/{quote.name}"
            self.upload_nest_images(quote)
            self.upload_quote_thread(folder, quote, html_file)
            self.status_button.setText(f"Saved {quote.name}", "lime")
            quote.unsaved_changes = False
            quote.downloaded_from_server = True
            self.quote_generator_tab_widget.update_quote_save_status(quote)

    # TODO
    def generate_printout(self) -> None:
        select_item_dialog = GenerateQuoteDialog(self)
        if select_item_dialog.exec():
            should_generate_quote, should_generate_workorder, should_update_inventory, should_generate_packing_slip, should_group_items, should_remove_sheet_quantities = select_item_dialog.get_selected_item()

            quote = self.quote_generator_tab_widget.current_quote

            # TODO if not should_group_items:
            quote.group_laser_cut_parts()

            self.settings_file.load_data()

            if should_generate_quote:
                self.generate_quote(
                    "Quote",
                    quote,
                    "previous_quotes/quotes/",
                    "open_quote_when_generated",
                )
            if should_generate_workorder:
                self.generate_quote(
                    "Workorder",
                    quote,
                    "previous_quotes/workorders/",
                    "open_workorder_when_generated",
                )
            if should_generate_packing_slip:
                self.generate_packing_slip(quote)
            self.status_button.setText("Generated printouts", "lime")

            if should_update_inventory:
                self.add_quantities_to_laser_cut_inventory(quote)

            if should_remove_sheet_quantities:
                self.remove_sheet_quantities(quote)

            self.load_previous_quotes_thread()
            self.quote_generator_tab_widget.quotes[self.quote_generator_tab_widget.tab_widget.currentIndex()].update_sheet_statuses()

    def generate_packing_slip(self, quote: Quote):
        self.get_order_number_thread()
        loop = QEventLoop()
        QTimer.singleShot(200, loop.quit)
        loop.exec()
        self.set_order_number_thread(self.order_number + 1)
        self.generate_quote(
            "Packing Slip",
            quote,
            "previous_quotes/packing_slips/",
            "open_workorder_when_generated",
        )

    def generate_quote(self, quote_type: str, quote: Quote, folder: str, open_file_settings: str):
        generate_quote = GeneratePrintout(quote_type, quote)
        html_file = generate_quote.generate()
        folder = f"{folder}{quote.name} - {datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.upload_quote_thread(folder, quote, html_file)
        if self.settings_file.get_value(open_file_settings):
            self.open_quote(folder)

    def set_order_number(self) -> None:
        self.get_order_number_thread()
        loop = QEventLoop()
        QTimer.singleShot(200, loop.quit)
        loop.exec()
        input_number, ok = QInputDialog.getDouble(self, "Set Order Number", "Enter a Order Number:", self.order_number)
        if input_number and ok:
            self.set_order_number_thread(input_number)

    def open_job_sorter(self) -> None:
        job_sorter_menu = JobSorterDialog(
            self,
        )
        job_sorter_menu.show()

    def open_tag_editor(self) -> None:
        self.workspace_settings.load_data()
        tag_editor = EditWorkspaceSettings(self.workspace_settings, self)

        def upload_workspace_settings():
            self.status_button.setText("Synching", "lime")
            self.upload_file(
                ["workspace_settings.json"],
            )

        if tag_editor.exec():
            upload_workspace_settings()
            self.job_planner_widget.workspace_settings_changed()

    # * /\ Dialogs /\

    # * \/ Load UI \/
    def load_history_view(self) -> None:
        # CATEOGRY HISTORY
        self.categoryHistoryTable.clear()
        self.categoryHistoryTable.setRowCount(0)
        self.categoryHistoryTable.setHorizontalHeaderLabels(("Date;Description;").split(";"))
        self.categoryHistoryTable.setColumnWidth(0, 270)
        self.categoryHistoryTable.setColumnWidth(1, 600)
        history_file = HistoryFile()
        for i, date, description in zip(
            range(len(history_file.get_data_from_category()["Date"])),
            history_file.get_data_from_category()["Date"],
            history_file.get_data_from_category()["Description"],
        ):
            self.categoryHistoryTable.insertRow(self.categoryHistoryTable.rowCount())
            self.categoryHistoryTable.setItem(i, 0, QTableWidgetItem(date))
            self.categoryHistoryTable.setItem(i, 1, QTableWidgetItem(description))
        # SINGLE ITEM HISTORY
        self.singleItemHistoryTable.clear()
        self.singleItemHistoryTable.setRowCount(0)
        self.singleItemHistoryTable.setHorizontalHeaderLabels(("Date;Description;").split(";"))
        self.singleItemHistoryTable.setColumnWidth(0, 270)
        self.singleItemHistoryTable.setColumnWidth(1, 600)
        for i, date, description in zip(
            range(len(history_file.get_data_from_single_item()["Date"])),
            history_file.get_data_from_single_item()["Date"],
            history_file.get_data_from_single_item()["Description"],
        ):
            self.singleItemHistoryTable.insertRow(self.singleItemHistoryTable.rowCount())
            self.singleItemHistoryTable.setItem(i, 0, QTableWidgetItem(date))
            self.singleItemHistoryTable.setItem(i, 1, QTableWidgetItem(description))

    def load_price_history_view(self) -> None:
        # CATEOGRY HISTORY
        self.priceHistoryTable.clear()
        self.priceHistoryTable.setRowCount(0)
        self.priceHistoryTable.setHorizontalHeaderLabels(("Date;Part Name;Part #;Old Price;New Price").split(";"))
        self.priceHistoryTable.setColumnWidth(0, 270)
        self.priceHistoryTable.setColumnWidth(1, 600)
        price_history_file = PriceHistoryFile(file_name=f"{self.settings_file.get_value(setting_name='price_history_file_name')}.xlsx")
        for i, date, part_name, part_number, old_price, new_price in zip(
            range(len(price_history_file.get_data_from_category()["Date"])),
            price_history_file.get_data_from_category()["Date"],
            price_history_file.get_data_from_category()["Part Name"],
            price_history_file.get_data_from_category()["Part Number"],
            price_history_file.get_data_from_category()["Old Price"],
            price_history_file.get_data_from_category()["New Price"],
        ):
            if i == 0:
                continue
            self.priceHistoryTable.insertRow(self.priceHistoryTable.rowCount())
            self.priceHistoryTable.setItem(i - 1, 0, QTableWidgetItem(str(date)))
            self.priceHistoryTable.setItem(i - 1, 1, QTableWidgetItem(str(part_name)))
            self.priceHistoryTable.setItem(i - 1, 2, QTableWidgetItem(str(part_number)))
            self.priceHistoryTable.setItem(i - 1, 3, QTableWidgetItem(str(old_price)))
            self.priceHistoryTable.setItem(i - 1, 4, QTableWidgetItem(str(new_price)))

    def load_tree_view(self, inventory_file: JsonFile):
        self.clear_layout(self.search_layout)
        tree_view = ViewTree(data=inventory_file.get_data())
        self.search_layout.addWidget(tree_view, 0, 0)

    def load_cuttoff_drop_down(self) -> None:
        cutoff_items: QListWidget = self.cutoff_widget.widgets[0]
        cutoff_items.clear()
        cutoff_sheets = self.sheets_inventory.get_sheets_by_category("Cutoff")
        for group in self.sheets_inventory.get_all_sheets_material(cutoff_sheets):
            cutoff_items.addItem(f"\t             {group}")
            for sheet in cutoff_sheets:
                if group != sheet.material:
                    continue
                cutoff_items.addItem(sheet.get_name())

    def load_previous_quotes(self, data: dict[str, dict[str, Any]]) -> None:
        sorted_data = dict(natsorted(data.items(), key=lambda item: item[1]["modified_date"], reverse=True, alg=ns.FLOAT))
        with contextlib.suppress(IndexError):  # Not loaded yet
            self.previous_quotes_tool_box_opened_menus[0] = not self.previous_quotes_tool_box.buttons[0].isChecked()
            self.previous_quotes_tool_box_opened_menus[1] = not self.previous_quotes_tool_box.buttons[1].isChecked()
            self.previous_quotes_tool_box_opened_menus[2] = not self.previous_quotes_tool_box.buttons[2].isChecked()

        self.previous_quotes_tool_box.clear()

        quote_widget = QWidget(self.previous_quotes_tool_box)
        quote_layout = QVBoxLayout(quote_widget)
        self.previous_quotes_tool_box.addItem(quote_widget, "Quotes")

        workorders_widget = QWidget(self.previous_quotes_tool_box)
        workorders_layout = QVBoxLayout(workorders_widget)
        self.previous_quotes_tool_box.addItem(workorders_widget, "Workorders")

        packing_slips_widget = QWidget(self.previous_quotes_tool_box)
        packing_slips_layout = QVBoxLayout(packing_slips_widget)
        self.previous_quotes_tool_box.addItem(packing_slips_widget, "Packing Slips")
        self.previous_quotes_tool_box.close_all()
        self.previous_quotes_tool_box.set_widgets_visibility(self.previous_quotes_tool_box_opened_menus)

        for folder_path, file_info in sorted_data.items():
            folder_path = folder_path.replace("\\", "/")
            folder_name = folder_path.split("/")[0]
            if folder_name == "quotes":
                quote_item = PreviousQuoteItem(file_info, quote_widget)
                quote_item.load_quote.connect(partial(self.download_quote_data_thread, f"previous_quotes/{folder_path}"))
                quote_item.open_webpage.connect(partial(self.open_quote, f"previous_quotes/{folder_path}"))
                quote_item.delete_quote.connect(partial(self.delete_quote_thread, f"previous_quotes/{folder_path}"))
                quote_layout.addWidget(quote_item)
            elif folder_name == "workorders":
                quote_item = PreviousQuoteItem(file_info, workorders_widget)
                quote_item.load_quote.connect(partial(self.download_quote_data_thread, f"previous_quotes/{folder_path}"))
                quote_item.open_webpage.connect(partial(self.open_quote, f"previous_quotes/{folder_path}"))
                quote_item.delete_quote.connect(partial(self.delete_quote_thread, f"previous_quotes/{folder_path}"))
                workorders_layout.addWidget(quote_item)
            elif folder_name == "packing_slips":
                quote_item = PreviousQuoteItem(file_info, packing_slips_widget)
                quote_item.load_quote.connect(partial(self.download_quote_data_thread, f"previous_quotes/{folder_path}"))
                quote_item.open_webpage.connect(partial(self.open_quote, f"previous_quotes/{folder_path}"))
                quote_item.delete_quote.connect(partial(self.delete_quote_thread, f"previous_quotes/{folder_path}"))
                packing_slips_layout.addWidget(quote_item)
        self.status_button.setText("Refreshed", "lime")

    def load_planning_jobs(self, data: dict[str, dict[str, Any]]):
        self.saved_planning_job_items_last_opened = self.saved_jobs_multitoolbox.get_widget_visibility()
        self.templates_job_items_last_opened = self.templates_jobs_multitoolbox.get_widget_visibility()

        self.templates_jobs_multitoolbox.clear()
        self.saved_jobs_multitoolbox.clear()
        sorted_data = dict(natsorted(data.items(), key=lambda x: x[1]["name"], reverse=True))
        for folder_path, file_info in sorted_data.items():
            job_item = SavedPlanningJobItem(file_info, self)
            job_item.load_job.connect(partial(self.load_job_thread, f"saved_jobs/{folder_path}"))
            job_item.delete_job.connect(partial(self.delete_job_thread, f"saved_jobs/{folder_path}"))
            job_item.open_webpage.connect(partial(self.open_job, f"saved_jobs/{folder_path}"))
            job_item.pushButton_open_in_browser.setToolTip(f"{job_item.pushButton_open_in_browser.toolTip()}\n\nhttp://{get_server_ip_address()}:{get_server_port()}/load_job/saved_jobs/{folder_path}")
            job_item.job_type_changed.connect(partial(self.change_job_thread, f"saved_jobs/{folder_path}", "type", job_item.comboBox_job_status))
            if file_info["type"] == JobStatus.PLANNING.value:
                self.saved_jobs_multitoolbox.addItem(job_item, file_info.get("name"), JobColor.get_color(JobStatus(file_info.get("type", 1))))
            elif file_info["type"] == JobStatus.TEMPLATE.value:
                self.templates_jobs_multitoolbox.addItem(job_item, file_info.get("name"), JobColor.get_color(JobStatus(file_info.get("type", 1))))
        self.saved_jobs_multitoolbox.close_all()
        self.templates_jobs_multitoolbox.close_all()
        self.saved_jobs_multitoolbox.set_widgets_visibility(self.saved_planning_job_items_last_opened)
        self.templates_jobs_multitoolbox.set_widgets_visibility(self.templates_job_items_last_opened)

    def load_quoting_jobs(self, data: dict[str, dict[str, Any]]):
        self.saved_planning_job_items_last_opened_2 = self.saved_jobs_multitoolbox_2.get_widget_visibility()
        self.templates_job_items_last_opened_2 = self.templates_jobs_multitoolbox_2.get_widget_visibility()

        self.templates_jobs_multitoolbox_2.clear()
        self.saved_jobs_multitoolbox_2.clear()
        sorted_data = dict(natsorted(data.items(), key=lambda x: x[1]["name"], reverse=True))
        for folder_path, file_info in sorted_data.items():
            job_item = SavedPlanningJobItem(file_info, self)
            job_item.load_job.connect(partial(self.load_job_thread, f"saved_jobs/{folder_path}"))
            job_item.delete_job.connect(partial(self.delete_job_thread, f"saved_jobs/{folder_path}"))
            job_item.open_webpage.connect(partial(self.open_job, f"saved_jobs/{folder_path}"))
            job_item.pushButton_open_in_browser.setToolTip(f"{job_item.pushButton_open_in_browser.toolTip()}\n\nhttp://{get_server_ip_address()}:{get_server_port()}/load_job/saved_jobs/{folder_path}")
            job_item.job_type_changed.connect(partial(self.change_job_thread, f"saved_jobs/{folder_path}", "type", job_item.comboBox_job_status))
            if file_info["type"] in [JobStatus.PLANNING.value, JobStatus.QUOTED.value, JobStatus.QUOTING.value]:
                self.saved_jobs_multitoolbox_2.addItem(job_item, file_info.get("name"), JobColor.get_color(JobStatus(file_info.get("type", 1))))
            elif file_info["type"] == JobStatus.TEMPLATE.value:
                self.templates_jobs_multitoolbox_2.addItem(job_item, file_info.get("name"), JobColor.get_color(JobStatus(file_info.get("type", 1))))
        self.saved_jobs_multitoolbox_2.close_all()
        self.templates_jobs_multitoolbox_2.close_all()
        self.saved_jobs_multitoolbox_2.set_widgets_visibility(self.saved_planning_job_items_last_opened_2)
        self.templates_jobs_multitoolbox_2.set_widgets_visibility(self.templates_job_items_last_opened_2)

    def load_saved_quotes(self, data: dict[str, dict[str, Any]]) -> None:
        sorted_data = dict(natsorted(data.items(), key=lambda x: x[1]["order_number"], alg=ns.FLOAT, reverse=True))

        with contextlib.suppress(IndexError):  # Not loaded yet
            self.saved_quotes_tool_box_opened_menus[0] = not self.saved_quotes_tool_box.buttons[0].isChecked()
            self.saved_quotes_tool_box_opened_menus[1] = not self.saved_quotes_tool_box.buttons[1].isChecked()
            self.saved_quotes_tool_box_opened_menus[2] = not self.saved_quotes_tool_box.buttons[2].isChecked()

        self.saved_quotes_tool_box.clear()

        quote_widget = QWidget(self.saved_quotes_tool_box)
        quote_layout = QVBoxLayout(quote_widget)
        self.saved_quotes_tool_box.addItem(quote_widget, "Quotes")

        workorders_widget = QWidget(self.saved_quotes_tool_box)
        workorders_layout = QVBoxLayout(workorders_widget)
        self.saved_quotes_tool_box.addItem(workorders_widget, "Workorders")

        packing_slips_widget = QWidget(self.saved_quotes_tool_box)
        packing_slips_layout = QVBoxLayout(packing_slips_widget)
        self.saved_quotes_tool_box.addItem(packing_slips_widget, "Packing Slips")
        self.saved_quotes_tool_box.close_all()
        self.saved_quotes_tool_box.set_widgets_visibility(self.saved_quotes_tool_box_opened_menus)

        for folder_path, file_info in sorted_data.items():
            folder_path = folder_path.replace("\\", "/")
            folder_name = folder_path.split("/")[0]
            if folder_name == "quotes":
                quote_item = SavedQuoteItem(file_info, quote_widget)
                quote_item.load_quote.connect(partial(self.download_quote_data_thread, f"saved_quotes/{folder_path}"))
                quote_item.open_webpage.connect(partial(self.open_quote, f"saved_quotes/{folder_path}"))
                quote_item.delete_quote.connect(partial(self.delete_quote_thread, f"saved_quotes/{folder_path}"))
                quote_item.status_changed.connect(partial(self.change_quote_thread, f"saved_quotes/{folder_path}", "status", quote_item.status_combobox))
                quote_layout.addWidget(quote_item)
            elif folder_name == "workorders":
                quote_item = SavedQuoteItem(file_info, workorders_widget)
                quote_item.load_quote.connect(partial(self.download_quote_data_thread, f"saved_quotes/{folder_path}"))
                quote_item.open_webpage.connect(partial(self.open_quote, f"saved_quotes/{folder_path}"))
                quote_item.delete_quote.connect(partial(self.delete_quote_thread, f"saved_quotes/{folder_path}"))
                quote_item.status_changed.connect(partial(self.change_quote_thread, f"saved_quotes/{folder_path}", "status", quote_item.status_combobox))
                workorders_layout.addWidget(quote_item)
            elif folder_name == "packing_slips":
                quote_item = SavedQuoteItem(file_info, packing_slips_widget)
                quote_item.load_quote.connect(partial(self.download_quote_data_thread, f"saved_quotes/{folder_path}"))
                quote_item.open_webpage.connect(partial(self.open_quote, f"saved_quotes/{folder_path}"))
                quote_item.delete_quote.connect(partial(self.delete_quote_thread, f"saved_quotes/{folder_path}"))
                quote_item.status_changed.connect(partial(self.change_quote_thread, f"saved_quotes/{folder_path}", "status", quote_item.status_combobox))
                packing_slips_layout.addWidget(quote_item)
        self.status_button.setText("Refreshed", "lime")

    def refresh_nest_directories(self) -> None:
        self.clear_layout(self.verticalLayout_24)
        self.clear_layout(self.verticalLayout_33)
        self.quote_nest_directories_list_widgets.clear()
        self.quote_job_directories_list_widgets.clear()
        self.settings_file.load_data()
        nest_directories: list[str] = self.settings_file.get_value("quote_nest_directories")
        toolbox_1 = QToolBox(self)
        toolbox_1.setLineWidth(0)
        toolbox_1.layout().setSpacing(0)
        toolbox_2 = QToolBox(self)
        toolbox_2.setLineWidth(0)
        toolbox_2.layout().setSpacing(0)
        self.verticalLayout_24.addWidget(toolbox_1)  # Quote Generator
        self.verticalLayout_33.addWidget(toolbox_2)  # Quote Generator 2
        for i, nest_directory in enumerate(nest_directories):
            nest_directory_name: str = nest_directory.split("/")[-1]
            tree_view_1 = PdfTreeView(nest_directory, self)
            tree_view_1.selectionModel().selectionChanged.connect(self.nest_directory_item_selected)
            tree_view_2 = PdfTreeView(nest_directory, self)
            tree_view_2.selectionModel().selectionChanged.connect(self.job_quote_directory_item_selected)
            self.quote_nest_directories_list_widgets[nest_directory] = tree_view_1
            self.quote_job_directories_list_widgets[nest_directory] = tree_view_2
            toolbox_1.addItem(tree_view_1, nest_directory_name)
            toolbox_1.setItemIcon(i, QIcon("icons/folder.png"))
            toolbox_2.addItem(tree_view_2, nest_directory_name)
            toolbox_2.setItemIcon(i, QIcon("icons/folder.png"))
        self.nest_directory_item_selected()
        self.job_quote_directory_item_selected()

    # * \/ CHECKERS \/
    def check_for_updates(self, on_start_up: bool = False) -> None:
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

    def check_trusted_user(self) -> None:
        trusted_users = get_trusted_users()
        check_trusted_user = (user for user in trusted_users if not self.trusted_user)
        for user in check_trusted_user:
            self.trusted_user = self.username.lower() == user.lower()

        # if not self.trusted_user:
        # self.menuSort.setEnabled(False)

    # * /\ CHECKERS /\

    # * \/ Purchase Order \/
    def open_po(self, po_name: str = None) -> None:
        if po_name is None:
            input_dialog = SelectItemDialog(DialogButtons.open_cancel, "Open PO", "Select a PO to open", get_all_po(), self)
            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.open:
                    try:
                        po_template = POTemplate(f"{os.path.abspath(os.getcwd())}/PO's/templates/{input_dialog.get_selected_item()}.xlsx")
                        po_template.generate()
                        os.startfile(po_template.get_output_path())
                    except AttributeError:
                        return
                elif response == DialogButtons.cancel:
                    return
        else:
            po_template = POTemplate(f"{os.path.abspath(os.getcwd())}/PO's/templates/{po_name}.xlsx")
            po_template.generate()
            os.startfile(po_template.get_output_path())

    def delete_po(self) -> None:
        input_dialog = SelectItemDialog(DialogButtons.discard_cancel, "Delete PO", "Select a PO to delete.\n\nThis cannot be undone.", get_all_po(), self)
        if input_dialog.exec():
            response = input_dialog.get_response()
            if response == DialogButtons.discard:
                try:
                    os.remove(f"PO's/templates/{input_dialog.get_selected_item()}.xlsx")
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Information)
                    msg.setWindowTitle("Success")
                    msg.setText("Successfully removed template.")
                    msg.exec()
                except AttributeError:
                    return
            elif response == DialogButtons.cancel:
                return

    def add_po_templates(self, po_file_paths: list[str], open_select_file_dialog: bool = False) -> None:
        if open_select_file_dialog:
            po_file_paths, check = QFileDialog.getOpenFileNames(None, "Add Purchase Order Template", "", "Excel Files (*.xlsx)")
            if not po_file_paths:
                return
            for po_file_path in po_file_paths:
                try:
                    po_file: POTemplate = POTemplate(po_file_path)
                except Exception as error:
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Critical)
                    msg.setWindowTitle("Error")
                    msg.setText(f"An error occurred while parsing the Excel file you provided. Kindly verify that the order number and vendor cell positions are accurate. Alternatively, please forward the Excel file to me for further review.\n\nError Details: {error}\n\nPO File Path:{po_file_path}")
                    msg.exec()
                    return
                new_file_path = f"PO's/templates/{po_file.get_vendor().replace('.','')}.xlsx"
                shutil.copyfile(po_file_path, new_file_path)
            check_po_directories()
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Success")
            msg.setText("Successfully added new Purchase Order template.")
            msg.exec()
        if not open_select_file_dialog:
            for po_file_path in po_file_paths:
                try:
                    po_file: POTemplate = POTemplate(po_file_path)
                except Exception as error:
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Icon.Critical)
                    msg.setWindowTitle("Error")
                    msg.setText(f"An error occurred while parsing the Excel file you provided. Kindly verify that the order number and vendor cell positions are accurate. Alternatively, please forward the Excel file to me for further review.\n\nError Details: {error}")
                    msg.exec()
                    return
                new_file_path = f"PO's/templates/{po_file.get_vendor().replace('.','')}.xlsx"
                shutil.copyfile(po_file_path, new_file_path)
            check_po_directories()
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Success")
            msg.setText(f"Successfully added new Purchase Order template.")
            msg.exec()

        self.reload_po_menu()

    def reload_po_menu(self) -> None:
        with contextlib.suppress(Exception, RuntimeError):
            for po_button in self.components_tab_widget.po_buttons:
                po_menu = QMenu(self)
                for po in get_all_po():
                    po_menu.addAction(po, partial(self.open_po, po))
                po_button.setMenu(po_menu)

    # * /\ Purchase Order /\
    def print_inventory(self) -> None:
        try:
            file_name = f"excel files/{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            excel_file = ExcelFile(self.components_inventory, f"{file_name}.xlsx")
            excel_file.generate()
            excel_file.save()

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Finished.")
            msg.setText("Would you love to open it?")
            msg.setStandardButtons(QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            response = msg.exec()
            if response == QMessageBox.StandardButton.Yes:
                try:
                    os.startfile(f"{os.path.dirname(os.path.realpath(sys.argv[0]))}/{file_name}.xlsx")
                except AttributeError:
                    return
        except Exception as error:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"{error}")
            msg.exec()

    # * \/ External Actions \/
    def open_print_selected_parts(self):
        webbrowser.open(f"print_selected_parts.html", new=0)

    def open_server_logs(self) -> None:
        webbrowser.open(f"http://{get_server_ip_address()}:{get_server_port()}", new=0)

    def open_inventory(self) -> None:
        webbrowser.open(f"http://{get_server_ip_address()}:{get_server_port()}/inventory", new=0)

    def open_qr_codes(self) -> None:
        webbrowser.open(f"http://{get_server_ip_address()}:{get_server_port()}/sheet_qr_codes", new=0)

    def open_job(self, folder: str):
        webbrowser.open(f"http://{get_server_ip_address()}:{get_server_port()}/load_job/{folder}", new=0)

    def open_quote(self, folder: str):
        webbrowser.open(f"http://{get_server_ip_address()}:{get_server_port()}/load_quote/{folder}", new=0)

    def open_item_history(self) -> None:
        os.startfile(f"{os.path.dirname(os.path.realpath(sys.argv[0]))}/data/inventory history.xlsx")

    def open_folder(self, path: str) -> None:
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Error opening folder")
            msg.setText(f"{e}")
            msg.exec()

    def play_celebrate_sound(self) -> None:
        threading.Thread(target=_play_celebrate_sound).start()

    def play_boot_sound(self) -> None:
        threading.Thread(target=_play_boot_sound).start()

    # * /\ External Actions /\
    # * \/ THREADS \/
    def sync_changes(self) -> None:
        self.status_button.setText(f"Synching {self.tabWidget.tabText(self.tabWidget.currentIndex())}", "lime")
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Components":
            self.upload_file(
                [
                    "components_inventory.json",
                ],
            )
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) in [
            "Laser Cut Inventory",
            "Quote Generator",
        ]:
            self.upload_file(
                [
                    "laser_cut_inventory.json",
                ],
            )
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) in [
            "Sheets in Inventory",
            "Quote Generator",
        ]:
            self.upload_file(
                [
                    "sheets_inventory.json",
                ],
            )
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheet Settings":
            self.upload_file(
                [
                    "sheet_settings.json",
                ],
            )
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            if self.category.name == "Staging":
                self.upload_file(
                    [
                        "admin_workspace.json",
                    ],
                )
            else:
                self.upload_file(
                    [
                        "user_workspace.json",
                        "history_workspace.json",
                    ],
                )

    def add_laser_cut_part_to_inventory(self, laser_cut_part_to_add: LaserCutPart, quote_name: str):
        laser_cut_part_to_add.quantity_in_nest = None
        if laser_cut_part_to_add.recut:
            new_recut_part = LaserCutPart(laser_cut_part_to_add.name, laser_cut_part_to_add.to_dict(), self.laser_cut_inventory)
            new_recut_part.add_to_category(self.laser_cut_inventory.get_category("Recut"))
            if existing_recut_part := self.laser_cut_inventory.get_recut_part_by_name(laser_cut_part_to_add.name):
                existing_recut_part.recut_count += 1
                new_recut_part.recut_count = existing_recut_part.recut_count
                new_recut_part.name = f"{new_recut_part.name} - (Recut count: {new_recut_part.recut_count})"
            new_recut_part.modified_date = f"{os.getlogin().title()} - Part added from {quote_name} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.laser_cut_inventory.add_recut_part(new_recut_part)
        elif existing_laser_cut_part := self.laser_cut_inventory.get_laser_cut_part_by_name(laser_cut_part_to_add.name):
            existing_laser_cut_part.quantity += laser_cut_part_to_add.quantity
            existing_laser_cut_part.uses_primer = laser_cut_part_to_add.uses_primer
            existing_laser_cut_part.primer_name = laser_cut_part_to_add.primer_name
            existing_laser_cut_part.uses_paint = laser_cut_part_to_add.uses_paint
            existing_laser_cut_part.paint_name = laser_cut_part_to_add.paint_name
            existing_laser_cut_part.uses_powder = laser_cut_part_to_add.uses_powder
            existing_laser_cut_part.powder_name = laser_cut_part_to_add.powder_name
            existing_laser_cut_part.primer_overspray = laser_cut_part_to_add.primer_overspray
            existing_laser_cut_part.paint_overspray = laser_cut_part_to_add.paint_overspray
            existing_laser_cut_part.modified_date = f"{os.getlogin().title()} - Added {laser_cut_part_to_add.quantity} quantities from {quote_name} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
        else:
            if not (category := self.laser_cut_inventory.get_category("Uncategorized")):
                category = Category("Uncategorized")
                self.laser_cut_inventory.add_category(category)
            laser_cut_part_to_add.add_to_category(category)
            laser_cut_part_to_add.modified_date = f"{os.getlogin().title()} - Part added from {quote_name} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            self.laser_cut_inventory.add_laser_cut_part(laser_cut_part_to_add)

    def add_quantities_to_laser_cut_inventory(self, quote: Quote):
        quote.group_laser_cut_parts()
        for laser_cut_part in quote.grouped_laser_cut_parts:
            self.add_laser_cut_part_to_inventory(laser_cut_part, quote.name)
        self.laser_cut_inventory.save()
        self.sync_changes()

    def remove_sheet_quantities(self, quote: Quote):
        for nest in quote.nests:
            if sheet := self.sheets_inventory.get_sheet_by_name(nest.sheet.get_name()):
                old_quantity = sheet.quantity
                sheet.quantity -= nest.sheet_count
                sheet.latest_change_quantity = f"{os.getlogin().title()} - Removed {nest.sheet_count} sheets from {quote.name} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
                if sheet.quantity <= sheet.red_quantity_limit and not sheet.has_sent_warning and "Cutoff" not in sheet.get_categories():
                    sheet.has_sent_warning = True
                    self.generate_single_sheet_report(sheet, old_quantity)
                if "Cutoff" in sheet.get_categories() and sheet.quantity <= 0:
                    self.sheets_inventory.remove_sheet(sheet)
        self.sheets_inventory.save()
        self.sync_changes()

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

    def download_required_images_thread(self, required_images: list[str]) -> None:
        download_thread = DownloadImagesThread(required_images)
        download_thread.signal.connect(self.download_required_images_response)
        self.threads.append(download_thread)
        download_thread.start()

    def download_required_images_response(self, response: str) -> None:
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

    def upload_nest_images(self, data: Quote | list[Nest]) -> None:
        images_to_upload = []
        if isinstance(data, Quote):
            data.group_laser_cut_parts()
            images_to_upload.extend(laser_cut_part.image_index for laser_cut_part in data.grouped_laser_cut_parts)
            images_to_upload.extend(component.image_path for component in data.components)
            images_to_upload.extend(nest.image_path for nest in data.nests)
        elif isinstance(data, list):
            for nest in data:
                images_to_upload.extend(laser_cut_part.image_index for laser_cut_part in nest.laser_cut_parts)
                images_to_upload.extend(nest.image_path for nest in data)

        images = set(images_to_upload)
        self.upload_file(list(images))

    def changes_response(self, response: str | list[str]) -> None:
        if isinstance(response, list):
            self.status_button.setText("Syncing", "yellow")
            self.downloading_changes = True
            if response[0] == "reload_saved_quotes":
                self.load_saved_quoted_thread()
            elif response[0] == "reload_saved_jobs":
                self.load_jobs_thread()
            else:
                self.download_files(response)
            self.status_button.setText("Synched", "lime")
        else:
            self.status_button.setText(f"Syncing Error: {response}", "red")

    def data_received(self, data) -> None:
        print(data)

        if "timed out" in str(data).lower() or "fail" in str(data).lower():
            self.status_button.setText("Server error", "red")
            self.centralwidget.setEnabled(False)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Server error")
            msg.setText(f"The server is either offline or your device is not connected to the internet. Please ensure that any VPNs are disabled, then try again. If the problem persists, contact your server or network administrator for assistance.\n\nThread response:\n{str(data)}")
            msg.exec()
        # QApplication.restoreOverrideCursor()

    def start_changes_thread(self) -> None:
        changes_thread = ChangesThread(self)  # 5 minutes
        changes_thread.signal.connect(self.changes_response)
        self.threads.append(changes_thread)
        changes_thread.start()

    def start_exchange_rate_thread(self) -> None:
        exchange_rate_thread = ExchangeRate()
        exchange_rate_thread.signal.connect(self.exchange_rate_received)
        self.threads.append(exchange_rate_thread)
        exchange_rate_thread.start()

    def exchange_rate_received(self, exchange_rate: float) -> None:
        with contextlib.suppress(AttributeError, RuntimeError):  # It might be the case that ComponentsTab is not loaded
            self.components_tab_widget.label_exchange_price.setText(f"1.00 USD: {exchange_rate} CAD")
            self.settings_file.load_data()
            self.settings_file.set_value("exchange_rate", exchange_rate)

    def send_sheet_report(self) -> None:
        thread = SendReportThread()
        self.threads.append(thread)
        thread.start()

    def upload_file(self, files_to_upload: list[str]) -> None:
        upload_thread = UploadThread(files_to_upload)
        self.threads.append(upload_thread)
        upload_thread.signal.connect(self.upload_thread_response)
        upload_thread.start()

    def upload_thread_response(self, response: dict, files_uploaded: list[str]):
        print(response, files_uploaded)
        if response["status"] == "success":
            self.status_button.setText("Synched", "lime")

    def download_files(self, files_to_download: list[str]) -> None:
        download_thread = DownloadThread(files_to_download)
        self.threads.append(download_thread)
        download_thread.signal.connect(self.download_thread_response)
        download_thread.start()

    def download_thread_response(self, response: dict, files_uploaded: list[str]):
        if not self.finished_downloading_all_files:
            self.finished_downloading_all_files = True
            self.tool_box_menu_changed()
            self.status_button.setText("Downloaded all files", "lime")
            self.centralwidget.setEnabled(True)
            # ON STARTUP
            self.downloading_changes = False
            self.start_changes_thread()
            self.start_exchange_rate_thread()
            if self.username != "Jared":  # Because I can
                self.showMaximized()
        else:
            if self.downloading_changes and response["status"] == "success":
                if "sheet_settings.json" in response["successful_files"]:
                    self.sheet_settings.load_data()
                if "workspace_settings.json" in response["successful_files"]:
                    self.workspace_settings.load_data()
                    self.job_planner_widget.workspace_settings_changed()
                if "components_inventory.json" in response["successful_files"]:
                    self.components_inventory.load_data()
                if "sheets_inventory.json" in response["successful_files"]:
                    self.sheets_inventory.load_data()
                if "laser_cut_inventory.json" in response["successful_files"]:
                    self.laser_cut_inventory.load_data()

                if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Laser Cut Inventory":
                    self.laser_cut_tab_widget.load_categories()
                    self.laser_cut_tab_widget.restore_last_selected_tab()
                elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
                    self.sheets_inventory_tab_widget.load_categories()
                    self.sheets_inventory_tab_widget.restore_last_selected_tab()
                elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Components":
                    self.components_tab_widget.load_categories()
                    self.components_tab_widget.restore_last_selected_tab()
                elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Quote Generator":
                    self.load_saved_quoted_thread()
                    self.load_cuttoff_drop_down()
                self.downloading_changes = False

    def download_all_files(self) -> None:
        self.download_files(
            [
                "laser_cut_inventory.json",
                "sheets_inventory.json",
                "components_inventory.json",
                "workspace_settings.json",
                "sheet_settings.json",
            ]
        )

    def load_nests_for_job_thread(self, nests: list[str]) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.status_button.setText("Processing nests", "yellow")
        self.pushButton_load_nests_2.setEnabled(False)
        load_nest_thread = LoadNestsThread(self, nests, self.components_inventory, self.laser_cut_inventory, self.sheet_settings)
        self.threads.append(load_nest_thread)
        load_nest_thread.signal.connect(self.load_nests_for_job_response)
        load_nest_thread.start()

    def load_nests_for_job_response(self, data: list[Nest] | str) -> None:
        if isinstance(data, str):
            self.status_button.setText(f"Encountered error processing nests: {data}", "red")
            self.pushButton_load_nests_2.setEnabled(True)
            QApplication.restoreOverrideCursor()
            msg = QMessageBox(QMessageBox.Icon.Critical, "PDF error", f"{data}", QMessageBox.StandardButton.Ok, self)
            msg.exec()
            return
        self.pushButton_load_nests_2.setEnabled(True)

        self.upload_nest_images(data)

        QApplication.restoreOverrideCursor()

        settings_text = "".join(f"  {i + 1}. {nest.name}: {nest.sheet.thickness} {nest.sheet.material}\n" for i, nest in enumerate(data))
        select_item_dialog = NestSheetVerification(f"The nests sheet settings from pdf are:\n{settings_text}", data[0].sheet.thickness, data[0].sheet.material, self.sheet_settings, self)

        if select_item_dialog.exec():
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.status_button.setText("Loading quote", "yellow")
            if select_item_dialog.response == DialogButtons.set:
                for nest in data:
                    nest.sheet.material = select_item_dialog.get_selected_material()
                    nest.sheet.thickness = select_item_dialog.get_selected_thickness()
                    for laser_cut_part in nest.laser_cut_parts:
                        laser_cut_part.material = select_item_dialog.get_selected_material()
                        laser_cut_part.gauge = select_item_dialog.get_selected_thickness()
            current_job = self.job_quote_widget.current_job
            current_job.nests = data
            current_job.unsaved_changes = True
            self.job_quote_widget.job_changed(current_job)
            self.job_quote_widget.update_tables()
            self.status_button.setText(f"Nests loaded into {current_job.name}", "lime")
        else:
            self.status_button.setText("Loading nests aborted", "lime")
        QApplication.restoreOverrideCursor()

    def generate_quote_thread(self, nests: list[str]) -> None:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.status_button.setText("Processing nests", "yellow")
        self.pushButton_load_nests.setEnabled(False)
        load_nest_thread = GenerateQuoteThread(self, nests, self.components_inventory, self.laser_cut_inventory, self.sheet_settings)
        self.threads.append(load_nest_thread)
        load_nest_thread.signal.connect(self.generate_quote_response)
        load_nest_thread.start()

    def generate_quote_response(self, data: Quote | str) -> None:
        if isinstance(data, str):
            self.status_button.setText("Encountered error processing nests", "red")
            self.pushButton_load_nests.setEnabled(True)
            QApplication.restoreOverrideCursor()
            msg = QMessageBox(QMessageBox.Icon.Critical, "PDF error", f"{data}", QMessageBox.StandardButton.Ok, self)
            msg.exec()
            return
        self.pushButton_load_nests.setEnabled(True)

        self.upload_nest_images(data)

        QApplication.restoreOverrideCursor()

        settings_text = "".join(f"  {i + 1}. {nest.name}: {nest.sheet.thickness} {nest.sheet.material}\n" for i, nest in enumerate(data.nests))
        select_item_dialog = NestSheetVerification(f"The nests sheet settings from pdf are:\n{settings_text}", data.nests[0].sheet.thickness, data.nests[0].sheet.material, self.sheet_settings, self)

        if select_item_dialog.exec():
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self.status_button.setText("Loading quote", "yellow")
            if select_item_dialog.response == DialogButtons.set:
                for nest in data.nests:
                    nest.sheet.material = select_item_dialog.get_selected_material()
                    nest.sheet.thickness = select_item_dialog.get_selected_thickness()
                    for laser_cut_part in nest.laser_cut_parts:
                        laser_cut_part.material = select_item_dialog.get_selected_material()
                        laser_cut_part.gauge = select_item_dialog.get_selected_thickness()

            current_tab_index = self.quote_generator_tab_widget.tab_widget.currentIndex()
            self.quote_generator_tab_widget.set_quote(current_tab_index, data)
            current_quote_widget = self.quote_generator_tab_widget.quotes[current_tab_index]
            current_quote_widget.comboBox_global_sheet_material_2.blockSignals(True)
            current_quote_widget.comboBox_global_sheet_material_2.setCurrentText(select_item_dialog.get_selected_material())
            current_quote_widget.comboBox_global_sheet_material_2.blockSignals(False)
            current_quote_widget.comboBox_global_sheet_thickness_2.blockSignals(True)
            current_quote_widget.comboBox_global_sheet_thickness_2.setCurrentText(select_item_dialog.get_selected_thickness())
            current_quote_widget.comboBox_global_sheet_thickness_2.blockSignals(False)
            self.status_button.setText(
                f"Successfully loaded {len(self.get_all_selected_nests())} nests into {self.quote_generator_tab_widget.tab_widget.tabText(current_tab_index)}",
                "lime",
            )
        else:
            self.status_button.setText("Loading nests aborted", "lime")
        QApplication.restoreOverrideCursor()

    def upload_quote_thread(self, folder: str, quote: Quote, html_file_contents: str) -> None:
        upload_batch = UploadQuote(folder, quote, html_file_contents)
        upload_batch.signal.connect(self.upload_quote_response)
        self.threads.append(upload_batch)
        self.status_button.setText(f"Uploading {quote.name}", "yellow")
        upload_batch.start()

    def upload_quote_response(self, response: str) -> None:
        if response == "Quote sent successfully":
            self.status_button.setText("Quote was sent successfully", "lime")
            self.load_saved_quoted_thread()
        else:
            self.status_button.setText("Quote failed to send", "red")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Upload error")
            msg.setText(f"{response}")
            msg.exec()

    def set_order_number_thread(self, order_number: float) -> None:
        self.order_number = order_number
        set_order_number_thread = SetOrderNumberThread(order_number)
        set_order_number_thread.signal.connect(self.set_order_number_thread_response)
        self.threads.append(set_order_number_thread)
        set_order_number_thread.start()

    def get_order_number_thread(self) -> None:
        get_order_number_thread = GetOrderNumberThread()
        get_order_number_thread.signal.connect(self.get_order_number_thread_response)
        self.threads.append(get_order_number_thread)
        get_order_number_thread.start()

    def set_order_number_thread_response(self, response) -> None:
        if response != "success":
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Order number error")
            msg.setText(f"Encountered error when setting order number.\n\n{response}")
            msg.exec()

    def get_order_number_thread_response(self, order_number: int) -> None:
        try:
            self.order_number = order_number
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Order number error")
            msg.setText(f"{e}")
            msg.exec()

    def load_previous_quotes_thread(self) -> None:
        get_previous_quotes_thread = GetPreviousQuotesThread()
        self.threads.append(get_previous_quotes_thread)
        get_previous_quotes_thread.signal.connect(self.load_previous_quotes_response)
        get_previous_quotes_thread.start()

    def load_previous_quotes_response(self, data: dict) -> None:
        if isinstance(data, dict):
            self.load_previous_quotes(data)
        else:
            self.status_button.setText(f"Error: {data}'", "red")

    def upload_job_thread(self, folder: str, job: Job, html_file_contents: str) -> None:
        upload_batch = UploadJobThread(folder, job, html_file_contents)
        upload_batch.signal.connect(self.upload_job_response)
        self.threads.append(upload_batch)
        self.status_button.setText(f"Uploading {job.name}", "yellow")
        self.job_planner_widget.update_job_save_status(job)
        upload_batch.start()

    def upload_job_response(self, response: str) -> None:
        if response == "Job sent successfully":
            self.status_button.setText("Job was sent successfully", "lime")
            self.load_jobs_thread()
        else:
            self.status_button.setText("Job failed to send", "red")
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Upload error")
            msg.setText(f"{response}")
            msg.exec()

    def load_jobs_thread(self) -> None:
        get_saved_quotes_thread = GetJobsThread()
        self.threads.append(get_saved_quotes_thread)
        get_saved_quotes_thread.signal.connect(self.load_jobs_response)
        get_saved_quotes_thread.start()

    def load_jobs_response(self, data: dict) -> None:
        if isinstance(data, dict):
            self.status_button.setText("Fetched all jobs", "lime")
            if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Job Planner":
                self.load_planning_jobs(data)
            elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Quote Generator 2":
                self.load_quoting_jobs(data)
            # More will be added here such as quoting, workspace, archive...
        else:
            self.status_button.setText(f"Error: {data}'", "red")

    def load_saved_quoted_thread(self) -> None:
        get_saved_quotes_thread = GetSavedQuotesThread()
        self.threads.append(get_saved_quotes_thread)
        get_saved_quotes_thread.signal.connect(self.load_saved_quotes_response)
        get_saved_quotes_thread.start()

    def load_saved_quotes_response(self, data: dict) -> None:
        if isinstance(data, dict):
            self.load_saved_quotes(data)
        else:
            self.status_button.setText(f"Error: {data}'", "red")

    def reload_job_thread(self, folder_name: str):
        self.status_button.setText(f"Fetching {folder_name} data...", "yellow")
        job_loader_thread = JobLoaderThread(self.job_manager, folder_name)
        self.threads.append(job_loader_thread)
        job_loader_thread.signal.connect(self.reload_job_response)
        job_loader_thread.start()
        job_loader_thread.wait()

    def reload_job_response(self, job: Job | None):
        if job:
            self.status_button.setText(f"{job.name} reloaded successfully!", "lime")
            self.job_planner_widget.reload_job(job)
        else:
            self.status_button.setText("Failed to load job.", "red")

    def load_job_thread(self, folder_name: str):
        self.status_button.setText(f"Fetching {folder_name} data...", "yellow")
        job_loader_thread = JobLoaderThread(self.job_manager, folder_name)
        self.threads.append(job_loader_thread)
        job_loader_thread.signal.connect(self.load_job_response)
        job_loader_thread.start()
        job_loader_thread.wait()

    def load_job_response(self, job: Job | None):
        if job:
            self.status_button.setText(f"{job.name} loaded successfully!", "lime")
            if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Job Planner":
                self.job_planner_widget.load_job(job)
            elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Quote Generator 2":
                self.job_quote_widget.load_job(job)
        else:
            self.status_button.setText("Failed to load job.", "red")

    def download_job_data_thread(self, folder_name: str) -> None:
        self.status_button.setText("Fetching job data", "lime")
        download_quote_thread = DownloadJobThread(folder_name)
        self.threads.append(download_quote_thread)
        download_quote_thread.signal.connect(self.download_job_data_response)
        download_quote_thread.start()

    def download_job_data_response(self, data: dict[str, dict[str, Any]], folder_name: str) -> None:
        if isinstance(data, dict):
            job_name = folder_name.split("\\")[-1]
            job = Job(job_name, data, self.job_manager)

            # required_images = [laser_cut_part.image_index for laser_cut_part in job.grouped_laser_cut_parts]
            # required_images.extend(nest.image_path for nest in job.nests)

            # self.download_required_images_thread(required_images)

            job.downloaded_from_server = True
            self.job_planner_widget.load_job(job)
            self.status_button.setText(
                f"Successfully fetched {folder_name} data",
                "lime",
            )
        else:
            self.status_button.setText(f"Error - {data}", "red")

    def change_job_thread(self, job_path: str, job_setting_key: str, setting: QComboBox):
        setting.setEnabled(False)
        update_job_thread = UpdateJobSetting(job_path, job_setting_key, setting.currentIndex() + 1)
        self.threads.append(update_job_thread)
        update_job_thread.signal.connect(self.change_job_response)
        update_job_thread.start()

    def change_job_response(self, response: dict | str, folder_name: str):
        if isinstance(response, dict):
            self.status_button.setText(
                f"Successfully updated {folder_name}",
                "lime",
            )
        else:
            self.status_button.setText(f"Error: {response} - {folder_name}", "red")
        self.load_jobs_thread()

    def delete_job_thread(self, folder_path: str):
        self.status_button.setText(f"Deleting {folder_path}", "yellow")
        delete_job_thread = DeleteJobThread(folder_path)
        self.threads.append(delete_job_thread)
        delete_job_thread.signal.connect(self.delete_job_response)
        delete_job_thread.start()

    def delete_job_response(self, response: dict | str, folder_name: str) -> None:
        if isinstance(response, dict):
            self.status_button.setText(
                f"Successfully deleted {folder_name}",
                "lime",
            )
            self.load_jobs_thread()
        else:
            self.status_button.setText(f"Error: {response}", "red")

    def change_quote_thread(self, quote_path: str, quote_setting_key: str, setting: QComboBox):
        setting.setEnabled(False)
        update_quote_thread = UpdateQuoteSettings(quote_path, quote_setting_key, setting.currentText())
        self.threads.append(update_quote_thread)
        update_quote_thread.signal.connect(self.change_quote_response)
        update_quote_thread.start()

    def change_quote_response(self, response: dict | str, folder_name: str):
        if isinstance(response, dict):
            self.status_button.setText(
                f"Successfully updated {folder_name}",
                "lime",
            )
        else:
            self.status_button.setText(f"Error: {response} - {folder_name}", "red")
        self.load_saved_quoted_thread()

    def download_quote_data_thread(self, folder_name: str) -> None:
        self.status_button.setText("Fetching quote data", "lime")
        download_quote_thread = DownloadQuoteThread(folder_name)
        self.threads.append(download_quote_thread)
        download_quote_thread.signal.connect(self.download_quote_data_response)
        download_quote_thread.start()

    def download_quote_data_response(self, data: dict[str, dict[str, Any]], folder_name: str) -> None:
        if isinstance(data, dict):
            quote_name = folder_name.split("/")[-1]
            quote = Quote(quote_name, data, self.components_inventory, self.laser_cut_inventory, self.sheet_settings)

            required_images = [laser_cut_part.image_index for laser_cut_part in quote.grouped_laser_cut_parts]
            required_images.extend(component.image_path for component in quote.components)
            required_images.extend(nest.image_path for nest in quote.nests)

            self.download_required_images_thread(required_images)

            quote.downloaded_from_server = True
            self.quote_generator_tab_widget.add_tab(quote)
            self.status_button.setText(
                f"Successfully fetched {folder_name} data",
                "lime",
            )
        else:
            self.status_button.setText(f"Error - {data}", "red")

    def delete_quote_thread(self, folder_path: str):
        self.status_button.setText("Fetching quote data", "yellow")
        delete_quote_thread = DeleteQuoteThread(folder_path)
        self.threads.append(delete_quote_thread)
        delete_quote_thread.signal.connect(self.delete_quote_response)
        delete_quote_thread.start()

    def delete_quote_response(self, response: dict | str, folder_name: str) -> None:
        if isinstance(response, dict):
            self.status_button.setText(
                f"Successfully deleted {folder_name}",
                "lime",
            )
            if "saved_quotes" in folder_name:
                self.load_saved_quoted_thread()
            elif "previous_quotes" in folder_name:
                self.load_previous_quotes_thread()
        else:
            self.status_button.setText(f"Error: {response}", "red")

    def send_email_thread(self, title: str, message: str, emails: list[str], notify: bool = False):
        self.status_button.setText("Fetching quote data", "yellow")
        send_email_thread = SendEmailThread(title, message, emails)
        self.threads.append(send_email_thread)
        if notify:
            send_email_thread.signal.connect(self.send_email_response)
        send_email_thread.start()

    def send_email_response(self, response: str):
        self.status_button.setText(response, "lime")

    def start_check_for_updates_thread(self) -> None:
        check_for_updates_thread = CheckForUpdatesThread(self, __version__)
        check_for_updates_thread.signal.connect(self.update_available_thread_response)
        self.threads.append(check_for_updates_thread)
        check_for_updates_thread.start()

    def update_available_thread_response(self, version: str, update_message: str) -> None:
        if not self.ignore_update:
            self.ignore_update = True
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("New Update Available")
            if update_message:
                update_notes = f"\n\nUpdate Notes:\n{update_message}"
            msg.setText(f"Current Version: {__version__}\nNew Version: {version}\n\nPlease consider updating to the latest version at your earliest convenience.{update_notes}\n\nWould you like to update?")
            msg.setStandardButtons(QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
            msg.setDefaultButton(QMessageBox.StandardButton.Yes)
            response = msg.exec()
            if response == QMessageBox.StandardButton.Yes:
                subprocess.Popen("start update.exe", shell=True)

    # * /\ THREADS /\

    def clear_layout(self, layout: QVBoxLayout | QWidget) -> None:
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())

    def set_layout_message(
        self,
        left_label: str,
        highlighted_message: str,
        right_label: str,
        highlighted_message_width: int,
        button_pressed_event=None,
    ) -> None:
        # self.clear_layout(#self.active_layout)
        self.tabs.clear()

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        # with contextlib.suppress(AttributeError):
        # self.active_layout.addWidget(self.tab_widget)
        tab = QScrollArea(self)
        content_widget = QWidget()
        tab.setWidget(content_widget)
        grid_layout = QGridLayout(content_widget)
        tab.setWidgetResizable(True)
        self.tabs["layout_message"] = grid_layout
        self.tab_widget.addTab(tab, "")

        lbl1 = QLabel(left_label)
        lbl1.setStyleSheet("font:30px")
        if not left_label:
            lbl1.setFixedWidth(650)
            lbl1.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        else:
            lbl1.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        font_size = QFont()
        font_size.setPointSize(25)
        btn = QPushButton(highlighted_message)
        btn.setFont(font_size)
        btn.setObjectName("default_dialog_button")
        if button_pressed_event is not None:
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(button_pressed_event)
        btn.setStyleSheet("QPushButton#default_dialog_button{text-align: center; vertical-align: center }")
        set_default_dialog_button_stylesheet(btn)
        btn.setFixedSize(highlighted_message_width, 45)
        lbl2 = QLabel(right_label)
        if not right_label:
            lbl2.setFixedWidth(650)
            lbl2.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        else:
            lbl2.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lbl2.setStyleSheet("font:30px")

        tab = self.tabs["layout_message"]
        tab.addWidget(lbl1, 0, 0)
        tab.addWidget(btn, 0, 1)
        tab.addWidget(lbl2, 0, 2)

    # * \/ OVERIDDEN UI EVENTS \/
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            return
        if event.mimeData().hasUrls:
            for url in event.mimeData().urls():
                if str(url.toLocalFile()).endswith(".xlsx") and self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Components":
                    event.setDropAction(Qt.DropAction.CopyAction)
                    event.accept()
                    self.set_layout_message("", "Add", "a new Purchase Order template", 80, None)
                elif str(url.toLocalFile()).endswith(".zip"):
                    event.setDropAction(Qt.DropAction.CopyAction)
                    event.accept()
                    self.set_layout_message("", "Load", "backup", 80, None)
                else:
                    event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        pass

    def dropEvent(self, event: QDropEvent) -> None:
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            return
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                if str(url.toLocalFile()).endswith(".xlsx") and self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Components":
                    files = [str(url.toLocalFile()) for url in event.mimeData().urls()]
                    self.add_po_templates(files)
                    break
            event.ignore()

    def closeEvent(self, event) -> None:
        self.save_geometry()
        self.save_menu_tab_order()
        super().closeEvent(event)

    # * /\ OVERIDDEN UI EVENTS /\
