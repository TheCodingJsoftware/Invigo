# sourcery skip: avoid-builtin-shadow
import cProfile
import configparser
import contextlib
import copy
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
import win32file
import winsound
from datetime import datetime, timedelta
from functools import partial
from typing import Any, Union

import markdown
import requests
import sympy
import win32api
from natsort import natsorted
from PyQt6 import QtWebEngineWidgets, uic
from PyQt6.QtCore import (
    QDate,
    QElapsedTimer,
    QEventLoop,
    QModelIndex,
    QSettings,
    Qt,
    QThread,
    QTimer,
    QUrl,
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QIcon,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QColorDialog,
    QComboBox,
    QCompleter,
    QDateEdit,
    QFileDialog,
    QFileIconProvider,
    QFontDialog,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from threads.changes_thread import ChangesThread
from threads.download_images_thread import DownloadImagesThread
from threads.download_thread import DownloadThread
from threads.get_order_number_thread import GetOrderNumberThread
from threads.get_previous_nests_data_thread import GetPreviousNestsDataThread
from threads.get_previous_nests_files_thread import GetPreviousNestsFilesThread
from threads.load_nests import LoadNests
from threads.remove_quantity import RemoveQuantityThread
from threads.send_sheet_report_thread import SendReportThread
from threads.set_order_number_thread import SetOrderNumberThread
from threads.upload_quoted_inventory import UploadBatch
from threads.upload_thread import UploadThread
from threads.workspace_get_file_thread import WorkspaceDownloadFiles
from threads.workspace_upload_file_thread import WorkspaceUploadThread
from ui.about_dialog import AboutDialog
from ui.add_component_dialog import AddComponentDialog
from ui.add_item_dialog import AddItemDialog
from ui.add_item_dialog_price_of_steel import AddItemDialogPriceOfSteel
from ui.add_job_dialog import AddJobDialog
from ui.add_workspace_item import AddWorkspaceItem
from ui.color_picker_dialog import ColorPicker
from ui.custom_widgets import (
    AssemblyMultiToolBox,
    LoadingScreen,
    ClickableLabel,
    CustomStandardItemModel,
    ComponentsCustomTableWidget,
    CustomTableWidget,
    CustomTabWidget,
    DeletePushButton,
    DraggableButton,
    DropWidget,
    ExchangeRateComboBox,
    FilterTabWidget,
    HumbleDoubleSpinBox,
    ItemsGroupBox,
    MultiToolBox,
    NotesPlainTextEdit,
    OrderStatusButton,
    PartInformationViewer,
    PdfTreeView,
    POPushButton,
    PriorityComboBox,
    RecordingWidget,
    RecutButton,
    RichTextPushButton,
    ScrollPositionManager,
    SelectRangeCalendar,
    MachineCutTimeSpinBox,
    TimeSpinBox,
    ViewTree,
    set_default_dialog_button_stylesheet,
)
from ui.edit_statuses_dialog import EditStatusesDialog
from ui.edit_tags_dialog import EditTagsDialog
from ui.generate_quote_dialog import GenerateQuoteDialog
from ui.generate_workorder_dialog import GenerateWorkorderDialog
from ui.generate_workspace_quote_dialog import GenerateWorkspaceQuoteDialog
from ui.image_viewer import QImageViewer
from ui.input_dialog import InputDialog
from ui.job_sorter_dialog import JobSorterDialog
from ui.load_window import LoadWindow
from ui.message_dialog import MessageDialog
from ui.recut_dialog import RecutDialog
from ui.select_date_dialog import SelectDateDialog
from ui.select_item_dialog import SelectItemDialog
from ui.select_timeline_dialog import SelectTimeLineDialog
from ui.set_custom_limit_dialog import SetCustomLimitDialog
from ui.set_order_pending_dialog import SetOrderPendingDialog
from ui.theme import set_theme
from ui.web_scrape_results_dialog import WebScrapeResultsDialog
from utils.calulations import calculate_overhead, calculate_scrap_percentage
from utils.colors import get_random_color
from utils.compress import compress_database, compress_folder
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.extract import extract
from utils.generate_quote import GenerateQuote
from utils.history_file import HistoryFile
from utils.inventory_excel_file import ExcelFile
from utils.ip_utils import get_server_ip_address, get_server_port
from utils.json_file import JsonFile
from utils.json_object import JsonObject
from utils.monday_excel_file import MondayExcelFile
from utils.po import check_po_directories, get_all_po
from utils.po_template import POTemplate
from utils.price_history_file import PriceHistoryFile
from utils.trusted_users import get_trusted_users
from utils.workspace.assembly import Assembly
from utils.workspace.item import Item
from utils.workspace.item_group import ItemGroup
from utils.workspace.workspace import Workspace
from web_scrapers.ebay_scraper import EbayScraper
from web_scrapers.exchange_rate import ExchangeRate

__author__: str = "Jared Gross"
__copyright__: str = "Copyright 2022-2023, TheCodingJ's"
__credits__: list[str] = ["Jared Gross"]
__license__: str = "MIT"
__name__: str = "Invigo"
__version__: str = "v2.2.21"
__updated__: str = "2023-08-30 12:32:51"
__maintainer__: str = "Jared Gross"
__email__: str = "jared@pinelandfarms.ca"
__status__: str = "Production"


def default_settings() -> None:
    """
    It checks if a setting exists in the settings file, and if it doesn't, it creates
    it with a default value
    """
    check_setting(setting="open_quote_when_generated", default_value=True)
    check_setting(setting="open_workorder_when_generated", default_value=True)
    check_setting(setting="open_packing_slip_when_generated", default_value=True)
    check_setting(setting="exchange_rate", default_value=1.0)
    check_setting(setting="dark_mode", default_value=True)  # deprecated
    check_setting(setting="sort_ascending", default_value=False)
    check_setting(setting="sort_descending", default_value=True)
    check_setting(setting="sort_quantity_in_stock", default_value=True)
    check_setting(setting="sort_priority", default_value=False)
    check_setting(setting="sort_alphabatical", default_value=False)
    check_setting(setting="server_ip", default_value="10.0.0.93")
    check_setting(setting="server_port", default_value=80)
    check_setting(setting="server_buffer_size", default_value=8192)  # deprecated
    check_setting(setting="server_time_out", default_value=10)  # deprecated
    check_setting(
        setting="geometry",
        default_value={"x": 200, "y": 200, "width": 1200, "height": 600},
    )
    check_setting(
        setting="last_opened",
        default_value=str(datetime.now()),
    )
    check_setting(setting="last_category_tab", default_value=0)
    check_setting(setting="last_toolbox_tab", default_value=0)
    check_setting(setting="last_dock_location", default_value=2)
    check_setting(setting="change_quantities_by", default_value="Category")
    check_setting(setting="inventory_file_name", default_value="inventory")
    check_setting(setting="path_to_order_number", default_value="order_number.json")
    check_setting(setting="trusted_users", default_value=["itsme", "jared", "joseph", "laserpc", "laser pc", "justin", "jordan"])
    check_setting(setting="quote_nest_directories", default_value=[])
    font = QFont("Segoe UI", 8)
    font.setWeight(400)
    font_data = {
        "family": font.family(),
        "pointSize": font.pointSize(),
        "weight": font.weight(),
        "italic": font.italic(),
    }
    check_setting(setting="tables_font", default_value=font_data)
    check_setting(
        setting="menu_tabs_order",
        default_value=[
            "Edit Inventory",
            "Sheets in Inventory",
            "Parts in Inventory",
            "OmniGen",
            "Workspace",
            "Chat",
            "View Inventory (Read Only)",
            "View Removed Quantities History (Read Only)",
            "View Price Changes History (Read Only)",
        ],
    )
    check_setting(
        setting="category_tabs_order",
        default_value={
            "Edit Inventory": [],
            "Sheets in Inventory": [],
            "Parts in Inventory": [],
            "Workspace": [],
        },
    )
    check_setting(
        setting="price_history_file_name",
        default_value=str(datetime.now().strftime("%B %d %A %Y")),
    )
    check_setting(
        setting="days_until_new_price_history_assessment",
        default_value=90,
    )


def check_setting(setting: str, default_value) -> None:
    """
    If the setting is not in the settings file, add it with the default value

    Args:
      setting (str): The name of the setting to check.
      default_value: The default value of the setting.
    """
    if settings_file.get_value(item_name=setting) is None:
        settings_file.add_item(item_name=setting, value=default_value)


def check_folders(folders: list[str]) -> None:
    """
    If the folder doesn't exist, create it

    Args:
      folders (list): list = ["data", "data/images", "data/images/thumbnails", "data/images/fullsize",
    "data/images/fullsize/temp"]
    """
    for folder in folders:
        with contextlib.suppress(FileExistsError):
            if not os.path.exists(folder):
                os.mkdir(folder)


def _play_celebrate_sound() -> None:
    winsound.PlaySound("sound.wav", winsound.SND_FILENAME)

def _play_boot_sound() -> None:
    winsound.PlaySound("boot.wav", winsound.SND_FILENAME)


check_folders(
    folders=[
        "logs",
        "data",
        "images",
        "backups",
        "Price History Files",
        "excel files",
        "PO's",
        "PO's/templates",
    ]
)

logging.basicConfig(
    filename="logs/app.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)


def excepthook(exc_type, exc_value, exc_traceback):
    """
    The above function is a custom exception hook that logs unhandled exceptions and then calls the
    default exception hook.

    Args:
      exc_type: The type of the exception that was raised. It is a class object representing the type of
    the exception (e.g., `TypeError`, `ValueError`, etc.).
      exc_value: The `exc_value` parameter in the `excepthook` function represents the actual exception
    object that was raised. It contains information about the exception, such as its type, message, and
    any additional data associated with it.
      exc_traceback: The traceback object that contains information about the exception's call stack. It
    includes the line numbers and function names of the code that led to the exception being raised.
    """
    win32api.MessageBox(
        0,
        f"A bug has shown itself. This error message has been sent to the server and an email has been sent to {__email__}, please be patient as {__maintainer__} attempts fixes this issue. It will most likely be fixed in the next update; if this error keeps happening then notify {__maintainer__}.\n\nexc_type:\n{exc_type}\n\nexc_value:\n{exc_value}\n\nexc_traceback:\n{exc_traceback}",
        "Unhandled exception - excepthook detected",
        0x40,
    )  # 0x40 for OK button

    logging.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)
    threading.Thread(target=send_error_report, args=(exc_type, exc_value, exc_traceback)).start()

def send_error_report(exc_type, exc_value, exc_traceback):
    SERVER_IP: str = get_server_ip_address()
    SERVER_PORT: int = get_server_port()
    url = f"http://{SERVER_IP}:{SERVER_PORT}/send_error_report"
    with open('logs/app.log', 'r') as error_log:
        error_data = error_log.read()
    data = {"error_log": f"User: {os.getlogin().title()}\nVersion: {__version__}\n\n{error_data}"}
    with contextlib.suppress(Exception):
        requests.post(url, data=data)


# Set the exception hook
sys.excepthook = excepthook
sys.setrecursionlimit(10**4)
sys.argv += ["--enable-features=WebComponentsV0Enabled"]

# 2048 is the hard limit
win32file._setmaxstdio(2048)

settings_file = JsonFile(file_name="settings")

default_settings()
inventory = JsonFile(file_name=f"data/{settings_file.get_value(item_name='inventory_file_name')}")
price_of_steel_inventory = JsonFile(file_name=f"data/{settings_file.get_value(item_name='inventory_file_name')} - Price of Steel")
parts_in_inventory = JsonFile(file_name=f"data/{settings_file.get_value(item_name='inventory_file_name')} - Parts in Inventory")
price_of_steel_information = JsonFile(file_name="price_of_steel_information.json")

user_workspace = Workspace("workspace - User")
admin_workspace = Workspace("workspace - Admin")
history_workspace = Workspace("workspace - History")

# This is for toggling between user and admin workspace for editing purposes

workspace_tags = JsonFile(file_name="data/workspace_settings")

geometry = JsonObject(JsonFile=settings_file, object_name="geometry")
category_tabs_order = JsonObject(JsonFile=settings_file, object_name="category_tabs_order")

history_file_date = datetime.strptime(settings_file.get_value("price_history_file_name"), "%B %d %A %Y")
days_from_last_price_history_assessment: int = int((datetime.now() - history_file_date).total_seconds() / 60 / 60 / 24)


class MainWindow(QMainWindow):
    """The class MainWindow inherits from the class QMainWindow"""

    def __init__(self):
        """
        It loads the UI and starts a thread that checks for changes in a JSON file.
        """
        super().__init__()
        self.loading_screen = LoadingScreen()
        self.loading_screen.hide()
        self.settings = QSettings(__name__, "MainWindow")  # Create QSettings instance

        uic.loadUi("ui/main_menu.ui", self)
        self.username = os.getlogin().title()
        self.trusted_user: bool = False
        self.setWindowTitle(f"{__name__} - {__version__} - {self.username}")
        self.setWindowIcon(QIcon(Icons.icon))

        check_po_directories()
        self.check_for_updates(on_start_up=True)

        if days_from_last_price_history_assessment > settings_file.get_value("days_until_new_price_history_assessment"):
            settings_file.add_item("price_history_file_name", str(datetime.now().strftime("%B %d %A %Y")))
            self.show_message_dialog(
                title="Price Assessment",  # 760a0acf
                message=f"It has been {settings_file.get_value('days_until_new_price_history_assessment')} days until the last price assessment. A new price history file has been created in the 'Price History Files' directory.",
            )

        # PDF VIEWER
        self.web_engine_view = QtWebEngineWidgets.QWebEngineView()
        settings = self.web_engine_view.settings()
        settings.setAttribute(self.web_engine_view.settings().WebAttribute.PluginsEnabled, True)
        self.web_engine_view.resize(640, 480)

        # VARIABLES
        self.theme: str = "dark"

        self.order_number: int = -1
        self.po_buttons: list[QPushButton] = []
        self.workspace_filter = {}
        self.parts_in_ineventory_filter = {}
        self.categories: list[str] = []
        self.active_layout: QVBoxLayout = None
        self.active_json_file: JsonFile = None
        self.active_workspace_file: Workspace = admin_workspace
        self.category: str = ""
        self.is_nest_generated_from_parts_in_inventory: bool = False
        self.downloading_changes: bool = False
        self.finished_downloading_all_files: bool = False
        self.finished_loading_tabs: bool = False
        self.files_downloaded_count: int = 0
        self.tables_font = QFont()
        self.tables_font.setFamily(settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(settings_file.get_value("tables_font")["italic"])
        self.tabs: dict[str, CustomTableWidget] = {}
        self.inventory_file_name: str = settings_file.get_value(item_name="inventory_file_name")
        self.last_item_selected_index: int = 0
        self.last_item_selected_name: str = None
        self.last_component_selected_name: str = None
        self.last_selected_menu_tab: str = settings_file.get_value("menu_tabs_order")[settings_file.get_value("last_toolbox_tab")]
        self.workspace_tables: dict[CustomTableWidget, Assembly] = {}
        self.workspace_information = {}  # idk the type hint
        self.threads: list[
            ChangesThread
            | DownloadThread
            | GetOrderNumberThread
            | LoadNests
            | RemoveQuantityThread
            | SetOrderNumberThread
            | UploadBatch
            | UploadThread
            | WorkspaceDownloadFiles
            | WorkspaceUploadThread
            | GetPreviousNestsFilesThread
            | GetPreviousNestsDataThread
        ] = []
        self.quote_nest_directories_list_widgets: dict[str, QTreeWidget] = {}
        self.quote_nest_information = {}
        self.quote_components_information = {}
        self.workspace_filter_tab_widget: FilterTabWidget = None
        self.sheet_nests_toolbox: MultiToolBox = None
        self.get_upload_file_response: bool = True
        self.scroll_position_manager = ScrollPositionManager()
        self.margins = (15, 15, 5, 5)  # top, bottom, left, right
        self.margin_format = (
            f"margin-top: {self.margins[0]}%; margin-bottom: {self.margins[1]}%; margin-left: {self.margins[2]}%; margin-right: {self.margins[3]}%;"
        )
        self.check_trusted_user()
        self.__load_ui()
        self.download_all_files()
        self.start_changes_thread(
            [
                f"{self.inventory_file_name}.json",
                f"{self.inventory_file_name} - Price of Steel.json",
                f"{self.inventory_file_name} - Parts in Inventory.json",
            ]
        )
        self.tool_box_menu_changed()
        self.quantities_change()
        self.start_exchange_rate_thread()
        # self.show()
        with contextlib.suppress(AttributeError):
            self.centralwidget.setEnabled(False)
        if geometry.get_value("x") == 0 and geometry.get_value("y") == 0:
            self.showMaximized()
        else:
            self.setGeometry(
                geometry.get_value("x"),
                geometry.get_value("y") + 30,
                geometry.get_value("width"),
                geometry.get_value("height") - 7,
            )
        self.show_whats_new()

    def __load_ui(self) -> None:
        """
        It loads the UI
        """

        menu_tabs_order = settings_file.get_value(item_name="menu_tabs_order")
        for tab_name in menu_tabs_order:
            index = self.get_tab_from_name(tab_name)
            if index != -1:
                self.tabWidget.tabBar().moveTab(index, menu_tabs_order.index(tab_name))

        self.lineEdit_search_items.textChanged.connect(self.update_edit_inventory_list_widget)
        self.lineEdit_search_parts_in_inventory.textChanged.connect(self.load_active_tab)
        # self.lineEdit_search_parts_in_inventory.returnPressed.connect(self.load_active_tab)
        self.radioButton_category.toggled.connect(self.quantities_change)
        self.radioButton_single.toggled.connect(self.quantities_change)

        if settings_file.get_value(item_name="change_quantities_by") == "Category":
            self.radioButton_category.setChecked(True)
            self.radioButton_single.setChecked(False)
        else:
            self.radioButton_category.setChecked(False)
            self.radioButton_single.setChecked(True)

        # Tool Box
        self.tabWidget.setCurrentIndex(settings_file.get_value(item_name="last_toolbox_tab"))
        self.tabWidget.currentChanged.connect(self.tool_box_menu_changed)

        # Send report button
        self.pushButton_send_sheet_report.clicked.connect(self.send_sheet_report)
        self.pushButton_send_sheet_report.setIcon(QIcon("icons/send_email.png"))

        # Load Nests
        self.comboBox_global_sheet_thickness.addItems(price_of_steel_information.get_value("thicknesses"))
        self.comboBox_global_sheet_thickness.wheelEvent = lambda event: event.ignore()
        self.comboBox_global_sheet_thickness.activated.connect(self.global_nest_thickness_change)
        self.comboBox_global_sheet_thickness.setEnabled(False)
        self.comboBox_global_sheet_material.addItems(price_of_steel_information.get_value("materials"))
        self.comboBox_global_sheet_material.wheelEvent = lambda event: event.ignore()
        self.comboBox_global_sheet_material.activated.connect(self.global_nest_material_change)
        self.comboBox_global_sheet_material.setEnabled(False)
        self.doubleSpinBox_global_sheet_length.setEnabled(False)
        self.doubleSpinBox_global_sheet_length.valueChanged.connect(self.global_nest_sheet_dim_change)
        self.doubleSpinBox_global_sheet_width.setEnabled(False)
        self.doubleSpinBox_global_sheet_width.valueChanged.connect(self.global_nest_sheet_dim_change)

        self.tree_model_previous_nests = QStandardItemModel()
        self.treeView_previous_nests.setModel(self.tree_model_previous_nests)
        self.pushButton_refresh_previous_nests.clicked.connect(self.load_previous_nests_files_thread)
        self.pushButton_load_previous_nests.clicked.connect(self.load_selected_previous_nests)

        self.tableWidget_quote_items = CustomTableWidget(self)
        self.tableWidget_quote_items.set_editable_column_index([4, 7, 8, 11])

        self.tableWidget_quote_items.setEnabled(False)
        self.tableWidget_quote_items.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_quote_items.setShowGrid(True)
        # tab.setAlternatingRowColors(True)
        self.tableWidget_quote_items.setSortingEnabled(False)
        self.tableWidget_quote_items.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget_quote_items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tableWidget_quote_items.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        headers: list[str] = [
            "Item",  # 0
            "Part name",  # 1
            "Material",  # 2
            "Thickness",  # 3
            "Qty",  # 4
            "Part Dim",  # 5
            "Cost of\nGoods",  # 6
            "Bend Cost",  # 7
            "Labor Cost",  # 8
            "Unit Price",  # 9
            "Price",  # 10
            "Shelf #", # 11
            "Recut",  # 12
            "Add Part to Inventory",  # 13
            "DEL",  # 14
            "",
        ]
        self.tableWidget_quote_items.setColumnCount(len(headers))
        self.tableWidget_quote_items.setHorizontalHeaderLabels(headers)
        self.clear_layout(self.verticalLayout_53)
        self.verticalLayout_53.addWidget(self.tableWidget_quote_items)
        clear_quote_items_button = QPushButton("Clear All Nests", self)
        clear_quote_items_button.setFixedWidth(150)
        clear_quote_items_button.clicked.connect(self.clear_all_nests)
        self.verticalLayout_53.addWidget(self.tableWidget_quote_items)
        self.verticalLayout_53.addWidget(clear_quote_items_button)
        self.tableWidget_quote_items.cellChanged.connect(self.quote_table_cell_changed)

        if self.tableWidget_quote_items.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
            self.tableWidget_quote_items.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            menu = QMenu(self)
            action = QAction(self)
            action.triggered.connect(self.delete_selected_quote_parts)
            action.setText("Delete Selected Parts")
            menu.addAction(action)
            self.tableWidget_quote_items.customContextMenuRequested.connect(partial(self.open_group_menu, menu))


        self.tableWidget_components_items = ComponentsCustomTableWidget(self)
        self.tableWidget_components_items.set_editable_column_index([1, 2, 3, 4, 5, 6])
        self.tableWidget_components_items.imagePasted.connect(self.component_image_pasted)

        self.tableWidget_components_items.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_components_items.setShowGrid(True)
        # tab.setAlternatingRowColors(True)
        self.tableWidget_components_items.setSortingEnabled(False)
        self.tableWidget_components_items.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget_components_items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tableWidget_components_items.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        headers: list[str] = [
            "Picture", # 0
            "Part Name",  # 1
            "Part #", # 2
            "Shelf #", # 3
            "Description", # 4
            "Qty",  # 5
            "Unit Price",  # 6
            "Price",  # 7
            "DEL",  # 8
            "",
        ]
        self.tableWidget_components_items.setColumnCount(len(headers))
        self.tableWidget_components_items.setHorizontalHeaderLabels(headers)
        self.clear_layout(self.verticalLayout_43)
        self.verticalLayout_43.addWidget(self.tableWidget_components_items)
        self.pushButton_clear_all_components.clicked.connect(self.clear_all_components)
        self.pushButton_add_component.clicked.connect(self.add_component)

        def save_scroll_position(tab_name: str, tab: CustomTableWidget):
            self.scroll_position_manager.save_scroll_position(tab_name=tab_name, scroll=tab)

        self.tableWidget_quote_items.verticalScrollBar().valueChanged.connect(partial(save_scroll_position, "OmniGen_Quote", self.tableWidget_quote_items))
        self.tableWidget_quote_items.horizontalScrollBar().valueChanged.connect(
            partial(save_scroll_position, "OmniGen_Quote", self.tableWidget_quote_items)
        )
        self.tableWidget_components_items.verticalScrollBar().valueChanged.connect(partial(save_scroll_position, "OmniGen_Components", self.tableWidget_components_items))
        self.tableWidget_components_items.horizontalScrollBar().valueChanged.connect(
            partial(save_scroll_position, "OmniGen_Components", self.tableWidget_components_items)
        )
        self.tableWidget_components_items.cellChanged.connect(self.components_table_cell_changed)
        self.tableWidget_components_items.itemClicked.connect(self.components_table_cell_clicked)
        if self.tableWidget_components_items.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
            self.tableWidget_components_items.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            menu = QMenu(self)
            action = QAction(self)
            action.triggered.connect(self.delete_selected_components)
            action.setText("Delete Selected Items")
            menu.addAction(action)
            self.tableWidget_components_items.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

        self.cutoff_widget = MultiToolBox(self)
        self.verticalLayout_cutoff.addWidget(self.cutoff_widget)
        cutoff_items = QListWidget(self)
        cutoff_items.doubleClicked.connect(partial(self.cutoff_sheet_double_clicked, cutoff_items))
        self.cutoff_widget.addItem(cutoff_items, "Cutoff Sheets")
        self.cutoff_widget.close_all()

        self.pushButton_load_nests.clicked.connect(self.process_selected_nests)
        self.pushButton_clear_selections.clicked.connect(self.clear_nest_selections)
        self.pushButton_refresh_directories.clicked.connect(self.refresh_nest_directories)
        self.pushButton_generate_quote.clicked.connect(self.generate_quote)

        # Filter
        self.pushButton_this_week.clicked.connect(partial(self.set_filter_calendar_day, 7))
        self.pushButton_next_2_days.clicked.connect(partial(self.set_filter_calendar_day, 2))
        self.pushButton_next_4_days.clicked.connect(partial(self.set_filter_calendar_day, 4))

        # Status
        self.status_button = RichTextPushButton(self)
        self.status_button.setText("Downloading all files, please wait...", color="yellow")
        self.status_button.setObjectName("status_button")
        self.status_button.setFlat(True)
        self.status_button.setFixedHeight(25)
        self.verticalLayout_status.addWidget(self.status_button)

        # Tab widget
        # self.load_categories()
        self.pushButton_create_new.clicked.connect(self.add_item)
        self.pushButton_add_new_sheet.clicked.connect(self.add_sheet_item)
        self.pushButton_add_quantity.clicked.connect(self.add_quantity)
        # self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_add_quantity.setIcon(QIcon(f"icons/list_add.png"))
        self.pushButton_remove_quantity.clicked.connect(self.remove_quantity)
        # self.pushButton_remove_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setIcon(QIcon(f"icons/list_remove.png"))
        self.listWidget_itemnames.itemSelectionChanged.connect(self.listWidget_item_changed)
        self.pushButton_remove_quantities_from_inventory.setIcon(QIcon(f"icons/list_remove.png"))

        self.pushButton_remove_quantities_from_inventory.clicked.connect(self.remove_quantity_from_part_inventory)

        # Action events
        # HELP
        # self.actionAbout_Qt.triggered.connect(qApp.aboutQt)
        # self.actionAbout_Qt.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMenuButton))
        self.actionCheck_for_Updates.triggered.connect(self.check_for_updates)
        self.actionCheck_for_Updates.setIcon(QIcon(f"icons/refresh.png"))
        self.actionAbout.triggered.connect(self.show_about_dialog)
        self.actionAbout.setIcon(QIcon(f"icons/about.png"))
        self.actionRelease_Notes.triggered.connect(partial(self.show_whats_new, True))
        self.actionRelease_Notes.setIcon(QIcon(f"icons/release_notes.png"))
        self.actionWebsite.triggered.connect(self.open_website)
        self.actionWebsite.setIcon(QIcon(f"icons/website.png"))
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
                    self.actionPriority,
                    self.actionAlphabatical,
                ],
            )
        )
        self.actionAlphabatical.setChecked(settings_file.get_value(item_name="sort_alphabatical"))
        self.actionAlphabatical.setEnabled(not settings_file.get_value(item_name="sort_alphabatical"))
        self.actionQuantity_in_Stock.triggered.connect(
            partial(
                self.action_group,
                "sorting",
                [
                    self.actionQuantity_in_Stock,
                    self.actionPriority,
                    self.actionAlphabatical,
                ],
            )
        )
        self.actionQuantity_in_Stock.setChecked(settings_file.get_value(item_name="sort_quantity_in_stock"))
        self.actionQuantity_in_Stock.setEnabled(not settings_file.get_value(item_name="sort_quantity_in_stock"))
        self.actionPriority.triggered.connect(
            partial(
                self.action_group,
                "sorting",
                [
                    self.actionQuantity_in_Stock,
                    self.actionPriority,
                    self.actionAlphabatical,
                ],
            )
        )
        self.actionPriority.setChecked(settings_file.get_value(item_name="sort_priority"))
        self.actionPriority.setEnabled(not settings_file.get_value(item_name="sort_priority"))
        self.actionAscending.triggered.connect(partial(self.action_group, "order", [self.actionAscending, self.actionDescending]))
        self.actionAscending.setChecked(settings_file.get_value(item_name="sort_ascending"))
        self.actionAscending.setEnabled(not settings_file.get_value(item_name="sort_ascending"))
        self.actionDescending.triggered.connect(partial(self.action_group, "order", [self.actionAscending, self.actionDescending]))
        self.actionDescending.setChecked(settings_file.get_value(item_name="sort_descending"))
        self.actionDescending.setEnabled(not settings_file.get_value(item_name="sort_descending"))
        self.actionSort.triggered.connect(self.sort_inventory)
        self.update_sorting_status_text()

        # PURCHASE ORDERS
        self.actionAdd_Purchase_Order.triggered.connect(partial(self.add_po_templates, [], True))
        self.actionRemove_Purchase_Order.triggered.connect(self.delete_po)
        self.actionOpen_Purchase_Order.triggered.connect(partial(self.open_po, None))
        self.actionOpen_Folder.triggered.connect(partial(self.open_folder, "PO's"))

        # QUOTE GENERATOR
        config = configparser.ConfigParser()
        config.read("laser_quote_variables.cfg")
        self.path_to_save_quotes = config.get("GLOBAL VARIABLES", "path_to_save_quotes")
        self.path_to_save_workorders = config.get("GLOBAL VARIABLES", "path_to_save_workorders")
        self.actionAdd_Nest_Directory.triggered.connect(self.add_nest_directory)
        self.actionRemove_Nest_Directory.triggered.connect(self.remove_nest_directory)
        self.actionOpen_Quotes_Directory.triggered.connect(partial(self.open_folder, self.path_to_save_quotes))
        self.actionOpen_Workorders_Directory.triggered.connect(partial(self.open_folder, self.path_to_save_workorders))

        self.comboBox_laser_cutting.currentIndexChanged.connect(self.laser_cost_changed)
        self.doubleSpinBox_cost_for_laser.valueChanged.connect(lambda: (self.update_quote_price(), self.update_sheet_prices()))

        self.spinBox_overhead_items.valueChanged.connect(lambda:(self.update_components_prices(), self.update_quote_price(), self.update_sheet_prices()))
        self.spinBox_profit_margin_items.valueChanged.connect(lambda:(self.update_components_prices(), self.update_quote_price(), self.update_sheet_prices()))

        self.spinBox_overhead_sheets.valueChanged.connect(lambda:(self.update_components_prices(), self.update_quote_price(), self.update_sheet_prices()))
        self.spinBox_profit_margin_sheets.valueChanged.connect(lambda:(self.update_components_prices(), self.update_quote_price(), self.update_sheet_prices()))

        self.pushButton_item_to_sheet.clicked.connect(self.match_item_to_sheet_price)
        self.pushButton_match_sheet_to_item.clicked.connect(self.match_sheet_to_item_price)

        # JOB SORTER
        self.actionOpenMenu.triggered.connect(self.open_job_sorter)

        # WORKSPACE
        self.actionEditTags.triggered.connect(self.open_tag_editor)
        self.actionEditStatuses.triggered.connect(self.open_status_editor)
        self.pushButton_generate_workorder.clicked.connect(partial(self.generate_workorder_dialog, []))
        self.pushButton_generate_workspace_quote.clicked.connect(partial(self.generate_workspace_quote_dialog, []))

        # FILE
        self.menuOpen_Category.setIcon(QIcon(f"icons/folder.png"))
        self.actionCreate_Category.triggered.connect(self.create_new_category)
        self.actionCreate_Category.setIcon(QIcon(f"icons/list_add.png"))
        self.actionDelete_Category.triggered.connect(self.delete_category)
        self.actionDelete_Category.setIcon(QIcon(f"icons/list_remove.png"))
        self.actionClone_Category.triggered.connect(self.clone_category)
        self.actionClone_Category.setIcon(QIcon(f"icons/tab_duplicate.png"))

        self.actionBackup.triggered.connect(self.backup_database)
        self.actionBackup.setIcon(QIcon(f"icons/backup.png"))
        self.actionLoad_Backup.triggered.connect(partial(self.load_backup, None))

        self.actionOpen_Item_History.triggered.connect(self.open_item_history)

        self.actionExit.triggered.connect(self.close)
        self.actionExit.setIcon(QIcon(f"icons/tab_close.png"))

        self.pushButton_hide_filter.clicked.connect(self.toggle_filter_tab_visibility)
        self.pushButton_hide_nests.clicked.connect(self.toggle_filter_tab_visibility_1)
        self.pushButton_hide_sheet_settings.clicked.connect(self.toggle_filter_tab_visibility_2)

        if not self.trusted_user:
            self.tabWidget.setTabVisible(settings_file.get_value("menu_tabs_order").index("Edit Inventory"), False)
            self.tabWidget.setTabVisible(
                settings_file.get_value("menu_tabs_order").index("View Price Changes History (Read Only)"),
                False,
            )
            self.tabWidget.setTabVisible(
                settings_file.get_value("menu_tabs_order").index("View Removed Quantities History (Read Only)"),
                False,
            )

    # * \/ SLOTS & SIGNALS \/
    def toggle_filter_tab_visibility(self) -> None:
        self.workspace_side_panel_2.setHidden(self.pushButton_hide_filter.isChecked())
        self.pushButton_hide_filter.setText("<\n\nF\ni\nl\nt\ne\nr\n\n<" if self.pushButton_hide_filter.isChecked() else ">\n\nF\ni\nl\nt\ne\nr\n\n>")

    def toggle_filter_tab_visibility_1(self) -> None:
        self.verticalLayout_nest_directories_2.setHidden(self.pushButton_hide_nests.isChecked())
        self.pushButton_hide_nests.setText("<\n\nN\ne\ns\nt\ns\n<" if self.pushButton_hide_nests.isChecked() else ">\n\nN\ne\ns\nt\ns\n\n>")

    def toggle_filter_tab_visibility_2(self) -> None:
        self.verticalLayout_32.setHidden(self.pushButton_hide_sheet_settings.isChecked())
        self.pushButton_hide_sheet_settings.setText(
            ">\n\nS\nh\ne\ne\nt\n\ns\ne\nt\nt\ni\nn\ng\ns\n\n>"
            if self.pushButton_hide_sheet_settings.isChecked()
            else "<\n\nS\nh\ne\ne\nt\n\ns\ne\nt\nt\ni\nn\ng\ns\n\n<"
        )

    def quick_load_category(self, name: str) -> None:
        """
        This function sets the current tab index of a tab widget based on the name of a category and
        then loads the tab.

        Args:
          name (str): The name of the category that needs to be loaded.
        """
        self.tab_widget.setCurrentIndex(category_tabs_order.get_value(self.tabWidget.tabText(self.tabWidget.currentIndex())).index(name))
        self.load_active_tab()

    def tool_box_menu_changed(self) -> None:
        """
        This function changes the active layout and menu options based on the selected tab in a GUI.
        """
        self.loading_screen.show()
        inventory.load_data()
        price_of_steel_inventory.load_data()
        parts_in_inventory.load_data()
        # with contextlib.suppress(KeyError):
        #     self.scroll_position_manager.saveScrollPosition(
        #         tab_name=f"{self.tabWidget.tabText(self.tabWidget.currentIndex())}_{self.category}", table=self.tabs[self.category]
        #     )
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "View Inventory (Read Only)":  # View Inventory (Read Only)
            self.menuSort.setEnabled(False)
            self.menuOpen_Category.setEnabled(False)
            self.active_layout = self.verticalLayout_4
            self.load_tree_view(inventory)
            self.status_button.setHidden(True)
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Edit Inventory":  # Edit Inventory
            if not self.trusted_user:
                self.show_not_trusted_user()
                return
            self.menuSort.setEnabled(True)
            self.menuOpen_Category.setEnabled(True)
            self.active_json_file = inventory
            self.active_layout = self.verticalLayout
            self.load_categories()
            self.status_button.setHidden(False)
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":  # Sheets in Inventory
            self.menuSort.setEnabled(True)
            self.menuOpen_Category.setEnabled(True)
            self.active_json_file = price_of_steel_inventory
            self.active_layout = self.verticalLayout_10
            self.load_categories()
            self.status_button.setHidden(False)
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Parts in Inventory":  # Parts in Inventory
            self.menuSort.setEnabled(True)
            self.menuOpen_Category.setEnabled(True)
            self.active_json_file = parts_in_inventory
            self.active_layout = self.verticalLayout_11
            self.load_categories()
            self.load_parts_in_inventory_filter_tab()
            self.status_button.setHidden(False)
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "OmniGen":  # OmniGen
            self.menuSort.setEnabled(False)
            self.menuOpen_Category.setEnabled(False)
            self.load_quote_generator_ui()
            self.status_button.setHidden(False)
        elif (
            self.tabWidget.tabText(self.tabWidget.currentIndex()) == "View Removed Quantities History (Read Only)"
        ):  # View Removed Quantities History (Read Only)
            self.menuSort.setEnabled(False)
            self.menuOpen_Category.setEnabled(False)
            if not self.trusted_user:
                self.show_not_trusted_user()
                return
            self.active_layout = self.verticalLayout_5
            self.load_history_view()
            self.status_button.setHidden(True)
        elif (
            self.tabWidget.tabText(self.tabWidget.currentIndex()) == "View Price Changes History (Read Only)"
        ):  # View Price Changes History (Read Only)
            self.menuSort.setEnabled(False)
            self.menuOpen_Category.setEnabled(False)
            if not self.trusted_user:
                self.show_not_trusted_user()
                return
            self.active_layout = self.horizontalLayout_8
            self.load_price_history_view()
            self.status_button.setHidden(True)
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            self.menuSort.setEnabled(False)
            self.menuOpen_Category.setEnabled(False)
            self.active_layout = self.workspace_layout
            self.load_categories()
        if not self.finished_loading_tabs:
            self.finished_loading_tabs = True
            self.load_workspace_filter_tab()
        settings_file.add_item("last_toolbox_tab", self.tabWidget.currentIndex())
        self.last_selected_menu_tab = self.tabWidget.tabText(self.tabWidget.currentIndex())

        self.loading_screen.hide()

    def move_to_category(self, tab: CustomTableWidget, category: str) -> None:
        """
        This function moves selected parts from one category to another in a custom table widget and
        updates the inventory accordingly.

        Args:
          tab (CustomTableWidget): CustomTableWidget object representing the table widget where the
        selected parts are located.
          category (str): A string representing the category to which the selected parts will be moved.
        """
        selected_parts = self.get_all_selected_parts(tab)
        for selected_part in selected_parts:
            copy_of_item = parts_in_inventory.get_data()[self.category][selected_part]
            parts_in_inventory.remove_object_item(self.category, selected_part)
            parts_in_inventory.add_item_in_object(category, selected_part)
            parts_in_inventory.change_object_item(category, selected_part, copy_of_item)
        self.load_active_tab()
        self.sync_changes()

    def copy_to_category(self, tab: CustomTableWidget, category: str) -> None:
        """
        This function copies selected parts from one category to another in a custom table widget and
        syncs the changes.

        Args:
          tab (CustomTableWidget): CustomTableWidget object representing the table widget where the
        selected parts are located.
          category (str): A string representing the category to which the selected parts will be copied.
        """
        selected_parts = self.get_all_selected_parts(tab)
        for selected_part in selected_parts:
            copy_of_item = parts_in_inventory.get_data()[self.category][selected_part]
            parts_in_inventory.add_item_in_object(category, selected_part)
            parts_in_inventory.change_object_item(category, selected_part, copy_of_item)
        self.sync_changes()

    def add_sheet_item(self) -> None:
        """
        It adds an item to a category

        Returns:
          The response from the dialog.
        """
        add_item_dialog = AddItemDialogPriceOfSteel(
            title=f'Add new sheet to "{self.category}"',
            message=f"Adding a new sheet to \"{self.category}\".\n\nPress 'Add' when finished.",
        )

        if add_item_dialog.exec():
            response = add_item_dialog.get_response()
            if response == DialogButtons.add:
                name: str = add_item_dialog.get_name()
                category_data = price_of_steel_inventory.get_value(item_name=self.category)
                for item in list(category_data.keys()):
                    if name == item:
                        self.show_error_dialog(
                            "Invalid name",
                            f"'{name}'\nis an invalid item name.\n\nCan't be the same as other names.",
                            dialog_buttons=DialogButtons.ok,
                        )
                        return

                price_of_steel_inventory.add_item_in_object(self.category, name)
                material: str = add_item_dialog.get_material()
                sheet_dimension: str = add_item_dialog.get_sheet_dimension()
                thickness: str = add_item_dialog.get_thickness()
                current_quantity: int = add_item_dialog.get_current_quantity()
                group: str = add_item_dialog.get_group()

                price_of_steel_inventory.change_object_in_object_item(self.category, name, "current_quantity", current_quantity)
                price_of_steel_inventory.change_object_in_object_item(self.category, name, "sheet_dimension", sheet_dimension)
                price_of_steel_inventory.change_object_in_object_item(self.category, name, "thickness", thickness)
                price_of_steel_inventory.change_object_in_object_item(self.category, name, "material", material)
                if group != "None":
                    price_of_steel_inventory.change_object_in_object_item(self.category, name, "group", group)
                price_of_steel_inventory.change_object_in_object_item(
                    self.category,
                    name,
                    "latest_change_current_quantity",
                    f"{self.username} - Item added at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                )
                # self.sort_inventory()
                self.load_active_tab()
                self.sync_changes()
            elif response == DialogButtons.cancel:
                return

    # NOTE SHEETS IN INVENTORY
    def order_status_button_sheets_in_inventory(self, item_name: str, button: OrderStatusButton, row_index: int) -> None:
        """
        This function updates the "is_order_pending" value of an item in a steel inventory object based
        on the status of an order status button.

        Args:
          item_name (str): A string representing the name of the item for which the order status button
        is being updated.
          button (OrderStatusButton): The button parameter is an instance of
        the OrderStatusButton class, which is a graphical user interface (GUI) element that allows the
        user to toggle the status of an order. The isChecked() method of the OrderStatusButton class
        returns a boolean value indicating whether the button is currently checked or not
        """
        select_date_dialog = SetOrderPendingDialog(
            self,
            button_names=DialogButtons.set_cancel,
            title="Set Expected Arrival Time & Quantity",
            message=f'Set an expected arrival time for "{item_name}" and the number of sheets ordered',
            label_text="Sheets Ordered:",
        )
        if button.isChecked() == True and select_date_dialog.exec():
            response = select_date_dialog.get_response()
            if response == DialogButtons.set:
                price_of_steel_inventory.change_object_in_object_item(
                    object_name=self.category,
                    item_name=item_name,
                    value_name="expected_arrival_time",
                    new_value=select_date_dialog.get_selected_date(),
                )
                price_of_steel_inventory.change_object_in_object_item(
                    object_name=self.category,
                    item_name=item_name,
                    value_name="order_pending_quantity",
                    new_value=select_date_dialog.get_order_quantity(),
                )
            else:
                self.load_active_tab()
                self.sync_changes()
                return
            price_of_steel_inventory.change_object_in_object_item(
                object_name=self.category,
                item_name=item_name,
                value_name="order_pending_date",
                new_value=datetime.now().strftime("%Y-%m-%d"),
            )
        elif button.isChecked() == False:
            input_dialog = InputDialog(
                title="Add Sheet Quantity",
                message=f"Do you want to add the incoming sheet quantity for \"{item_name}\"?",
                button_names=DialogButtons.add_no,
                placeholder_text=price_of_steel_inventory.data[self.category][item_name]['order_pending_quantity'],
            )
            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.add:
                    try:
                        input_number = float(input_dialog.inputText)
                        new_quantity = price_of_steel_inventory.data[self.category][item_name]['current_quantity'] + input_number
                        price_of_steel_inventory.change_object_in_object_item(
                            object_name=self.category,
                            item_name=item_name,
                            value_name="current_quantity",
                            new_value=new_quantity,
                        )
                    except Exception:
                        self.show_error_dialog(
                            title="Invalid number",
                            message=f"'{input_dialog.inputText}' is an invalid numnber",
                            dialog_buttons=DialogButtons.ok,
                        )
                        return
                elif response == DialogButtons.cancel:
                    return
        price_of_steel_inventory.change_object_in_object_item(
            object_name=self.category,
            item_name=item_name,
            value_name="is_order_pending",
            new_value=button.isChecked(),
        )

        self.load_active_tab()
        self.sync_changes()

    # NOTE SHEETS IN INVENTORY
    def arrival_date_change_sheets_in_inventory(self, item_name: str, arrival_date: QDateEdit) -> None:
        """
        The function `arrival_date_change` updates the expected arrival time of an item in the steel
        inventory and then reloads the active tab and syncs the changes.

        Args:
          item_name (str): The name of the item for which the arrival date is being changed.
          arrival_date (QDateEdit): The `arrival_date` parameter is a `QDateEdit` object, which is a
        widget that allows the user to select a date.
        """
        price_of_steel_inventory.change_object_in_object_item(
            object_name=self.category,
            item_name=item_name,
            value_name="expected_arrival_time",
            new_value=arrival_date.date().toString("yyyy-MM-dd"),
        )

        self.load_active_tab()
        self.sync_changes()

    # NOTE EDIT INVENTORY
    def order_status_button_edit_inventory(self, item_name: str, button: OrderStatusButton, row_index: int) -> None:
        """
        This function updates the "is_order_pending" value of an item in a steel inventory object based
        on the status of an order status button.

        Args:
          item_name (str): A string representing the name of the item for which the order status button
        is being updated.
          button (OrderStatusButton): The button parameter is an instance of
        the OrderStatusButton class, which is a graphical user interface (GUI) element that allows the
        user to toggle the status of an order. The isChecked() method of the OrderStatusButton class
        returns a boolean value indicating whether the button is currently checked or not
        """
        select_date_dialog = SetOrderPendingDialog(
            self,
            button_names=DialogButtons.set_cancel,
            title="Set Expected Arrival Time & Quantity",
            message=f'Set an expected arrival time for "{item_name}" and the number of parts ordered',
            label_text="Parts Ordered:",
        )
        part_number = self.get_value_from_category(item_name, 'part_number')
        if button.isChecked() == True and select_date_dialog.exec():
            response = select_date_dialog.get_response()
            if response == DialogButtons.set:
                inventory.change_object_in_object_item(
                    object_name=self.category,
                    item_name=item_name,
                    value_name="expected_arrival_time",
                    new_value=select_date_dialog.get_selected_date(),
                )
                inventory.change_object_in_object_item(
                    object_name=self.category,
                    item_name=item_name,
                    value_name="order_pending_quantity",
                    new_value=select_date_dialog.get_order_quantity(),
                )
                for category in inventory.get_keys():
                    if category == self.category:
                        continue
                    for item in list(inventory.data[category].keys()):
                        if part_number == inventory.data[category][item]["part_number"]:
                            inventory.change_object_in_object_item(
                                object_name=category,
                                item_name=item,
                                value_name="expected_arrival_time",
                                new_value=select_date_dialog.get_selected_date(),
                            )
                            inventory.change_object_in_object_item(
                                object_name=category,
                                item_name=item,
                                value_name="order_pending_quantity",
                                new_value=select_date_dialog.get_order_quantity(),
                            )
            else:
                self.load_active_tab()
                self.sync_changes()
                return
            inventory.change_object_in_object_item(
                object_name=self.category,
                item_name=item_name,
                value_name="order_pending_date",
                new_value=datetime.now().strftime("%Y-%m-%d"),
            )
            for category in inventory.get_keys():
                if category == self.category:
                    continue
                for item in list(inventory.data[category].keys()):
                    if part_number == inventory.data[category][item]["part_number"]:
                        inventory.change_object_in_object_item(
                            object_name=category,
                            item_name=item,
                            value_name="order_pending_date",
                            new_value=datetime.now().strftime("%Y-%m-%d"),
                        )
        elif button.isChecked() == False:
            input_dialog = InputDialog(
                title="Add Parts Quantity",
                message=f"Do you want to add the incoming quantity for \"{item_name}\"?",
                button_names=DialogButtons.add_no,
                placeholder_text=inventory.data[self.category][item_name]['order_pending_quantity'],
            )
            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.add:
                    try:
                        input_number = float(input_dialog.inputText)
                        old_quantity = inventory.data[self.category][item_name]['current_quantity']
                        new_quantity = old_quantity + input_number
                        inventory.change_object_in_object_item(
                            object_name=self.category,
                            item_name=item_name,
                            value_name="current_quantity",
                            new_value=new_quantity,
                        )
                        inventory.change_object_in_object_item(
                            self.category,
                            item_name,
                            "latest_change_current_quantity",
                            f"{self.username} - Changed from {old_quantity} to {new_quantity} at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                        )
                        for category in inventory.get_keys():
                            if category == self.category:
                                continue
                            for item in list(inventory.data[category].keys()):
                                if part_number == inventory.data[category][item]["part_number"]:
                                    inventory.change_object_in_object_item(
                                        object_name=category,
                                        item_name=item,
                                        value_name="current_quantity",
                                        new_value=new_quantity,
                                    )
                                    inventory.change_object_in_object_item(
                                        category,
                                        item,
                                        "latest_change_current_quantity",
                                        f"{self.username} - Changed from {old_quantity} to {new_quantity} at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                                    )
                    except Exception:
                        self.show_error_dialog(
                            title="Invalid number",
                            message=f"'{input_dialog.inputText}' is an invalid numnber",
                            dialog_buttons=DialogButtons.ok,
                        )
                        return
                elif response == DialogButtons.cancel:
                    return
        inventory.change_object_in_object_item(
            object_name=self.category,
            item_name=item_name,
            value_name="is_order_pending",
            new_value=button.isChecked(),
        )
        for category in inventory.get_keys():
            if category == self.category:
                continue
            for item in list(inventory.data[category].keys()):
                if part_number == inventory.data[category][item]["part_number"]:
                    inventory.change_object_in_object_item(
                        object_name=category,
                        item_name=item,
                        value_name="is_order_pending",
                        new_value=button.isChecked(),
                    )

        self.load_active_tab()
        self.sync_changes()

    # NOTE EDIT INVENTORY
    def arrival_date_change_edit_inventory(self, item_name: str, arrival_date: QDateEdit) -> None:
        """
        The function `arrival_date_change` updates the expected arrival time of an item in the steel
        inventory and then reloads the active tab and syncs the changes.

        Args:
          item_name (str): The name of the item for which the arrival date is being changed.
          arrival_date (QDateEdit): The `arrival_date` parameter is a `QDateEdit` object, which is a
        widget that allows the user to select a date.
        """
        inventory.change_object_in_object_item(
            object_name=self.category,
            item_name=item_name,
            value_name="expected_arrival_time",
            new_value=arrival_date.date().toString("yyyy-MM-dd"),
        )
        part_number = self.get_value_from_category(item_name, 'part_number')
        for category in inventory.get_keys():
            if category == self.category:
                continue
            for item in list(inventory.data[category].keys()):
                if part_number == inventory.data[category][item]["part_number"]:
                    inventory.change_object_in_object_item(
                        object_name=category,
                        item_name=item_name,
                        value_name="expected_arrival_time",
                        new_value=arrival_date.date().toString("yyyy-MM-dd"),
                    )
        self.load_active_tab()
        self.sync_changes()

    def name_change(self, tab: CustomTableWidget) -> None:
        """
        It checks if the name is the same as any other name in the category, and if it is, it sets the
        name back to the old name and displays an error message

        Args:
          category (str): str
          old_name (str): The name of the item before it was changed.
          name (QLineEdit): QLineEdit

        Returns:
          The return value is the result of the last expression evaluated in the function.
        """
        with contextlib.suppress(IndexError):
            old_name = self.get_all_selected_parts(tab)[0]
            new_name: str = None
            input_dialog = InputDialog(
                title="New Name",
                message=f'Enter a new name for: "{old_name}"',
                placeholder_text=old_name,
            )
            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.ok:
                    new_name = input_dialog.inputText
                elif response == DialogButtons.cancel:
                    return
            category_data = self.active_json_file.get_value(item_name=self.category)
            for item in list(category_data.keys()):
                if new_name == item:
                    self.show_error_dialog(
                        "Invalid name",
                        f'"{new_name}" is an invalid item name. Can\'t be the same as other names.',
                        dialog_buttons=DialogButtons.ok,
                    )
                    return
            self.active_json_file.change_item_name(self.category, old_name, new_name)
            self.sort_inventory()

    def use_exchange_rate_change(self, item_name: str, value_name: str, combo: QComboBox) -> None:
        """
        It changes the exchange rate

        Args:
          category (str): str - The category of the item
          item_name (QLineEdit): QLineEdit
          value_name (str): str = The name of the value to change
          combo (QComboBox): QComboBox
        """
        self.value_change(
            self.category,
            item_name,
            value_name,
            combo.currentText() == "USD",
        )
        tab = self.tabs[self.category]
        tab.blockSignals(True)
        row_index = tab.selectedItems()[0].row()
        price: float = self.get_value_from_category(item_name=item_name, key="price")
        current_quantity: float = self.get_value_from_category(item_name=item_name, key="current_quantity")
        unit_quantity: float = self.get_value_from_category(item_name=item_name, key="unit_quantity")
        modified_date: float = self.get_value_from_category(item_name=item_name, key="latest_change_price")
        use_exchange_rate: bool = self.get_value_from_category(item_name=item_name, key="use_exchange_rate")
        converted_price: float = price * self.get_exchange_rate() if use_exchange_rate else price / self.get_exchange_rate()
        # ITEM PRICE
        price_item = tab.item(row_index, 4)
        price_item.setText(f'${price:,.2f} {"USD" if use_exchange_rate else "CAD"}')
        price_item.setToolTip(f'${converted_price:,.2f} {"CAD" if use_exchange_rate else "USD"}\n{modified_date}')
        # TOTAL COST IN STOCK
        total_cost_in_stock_item = tab.item(row_index, 6)
        total_cost_in_stock_item.setText(f'${(price*max(current_quantity, 0)):,.2f} {"USD" if use_exchange_rate else "CAD"}')
        # TOTAL UNIT COST
        total_unit_cost_item = tab.item(row_index, 7)
        total_unit_cost_item.setText(f'${(price*unit_quantity):,.2f} {"USD" if use_exchange_rate else "CAD"}')
        tab.blockSignals(False)
        self.update_stock_costs()
        self.sync_changes()

    def priority_change(self, item_name: str, value_name: str, combo: QComboBox) -> None:
        """
        It changes the priority of a task

        Args:
          category (str): str - The category of the item
          item_name (QLineEdit): QLineEdit
          value_name (str): str = The name of the value to change
          combo (QComboBox): QComboBox
        """

        self.value_change(self.category, item_name, value_name, combo.currentIndex())
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)  # Adjust the blur radius as desired
        shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
        if combo.currentText() == "Medium":
            combo.setStyleSheet(f"color: yellow; border-color: gold; background-color: #413C28;{self.margin_format}")
            shadow.setColor(QColor(255, 215, 0))
        elif combo.currentText() == "High":
            combo.setStyleSheet(f"color: red; border-color: darkred; background-color: #3F1E25;{self.margin_format}")
            shadow.setColor(QColor(139, 0, 0))
        else:
            combo.setStyleSheet(self.margin_format)
            shadow.setColor(QColor(0, 0, 0, 255))
        # combo.setGraphicsEffect(shadow)
        self.sync_changes()

    def notes_changed(self, item_name: str, value_name: str, note: QPlainTextEdit) -> None:
        """
        It takes the category, item name, value name, and note as parameters and then calls the
        value_change function with the category, item name, value name, and note as parameters

        Args:
          category (str): str = The category of the item.
          item_name (QLineEdit): QLineEdit
          value_name (str): str = The name of the value that is being changed.
          note (QPlainTextEdit): QPlainTextEdit
        """
        data = inventory.get_data()
        part_number = self.get_value_from_category(item_name, "part_number")
        self.value_change(self.category, item_name, value_name, note.toPlainText())

        # for category, items in data.items():
        #     if category == self.category:
        #         continue
        #     for item, item_data in items.items():
        #         if part_number == item_data.get("part_number"):
        #             inventory.change_object_in_object_item(object_name=category, item_name=item, value_name="notes", new_value=note.toPlainText())
        self.sync_changes()

    def delete_item(self, item_name: str) -> None:
        """
        It removes an item from the inventory

        Args:
          category (str): str
          item_name (QLineEdit): QLineEdit
        """
        self.active_json_file.remove_object_item(self.category, item_name)
        self.load_active_tab()
        self.sync_changes()

    def delete_selected_items(self, tab: CustomTabWidget) -> None:
        """
        This function deletes selected items from a custom tab widget and updates the active JSON file
        and tab accordingly.

        Args:
          tab (CustomTabWidget): CustomTabWidget object representing the currently active tab in the
        GUI.
        """
        selected_parts = self.get_all_selected_parts(tab)
        for selected_part in selected_parts:
            with contextlib.suppress(KeyError):
                self.active_json_file.remove_object_item(self.category, selected_part)
        self.load_active_tab()
        self.sync_changes()

    def reset_selected_parts_quantity(self, tab: CustomTabWidget) -> None:
        """
        This function sets the current quantity of all selected parts in a custom tab widget to zero and
        then reloads the active tab and syncs the changes.

        Args:
          tab (CustomTabWidget): CustomTabWidget object representing the currently active tab in the
        GUI.
        """
        selected_parts = self.get_all_selected_parts(tab)
        for selected_part in selected_parts:
            self.active_json_file.change_object_in_object_item(self.category, selected_part, "current_quantity", 0)
        self.load_active_tab()
        self.sync_changes()

    def quantities_change(self) -> None:
        """
        If the radio button is checked, then the list widget is disabled, the add and remove buttons are
        enabled, and the add and remove buttons are connected to the add and remove quantity functions
        """
        if self.radioButton_category.isChecked():
            self.label.setText("Batches Multiplier:")
            self.pushButton_add_quantity.setText("Add Quantities")
            self.pushButton_remove_quantity.setText("Remove Quantities")
            settings_file.add_item(item_name="change_quantities_by", value="Category")
            # self.listWidget_itemnames.setEnabled(False)
            self.listWidget_itemnames.clearSelection()
            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(True)

            # self.pushButton_add_quantity.disconnect()
            self.pushButton_remove_quantity.disconnect()

            self.pushButton_remove_quantity.clicked.connect(self.remove_quantity_from_category)
            self.spinBox_quantity.setValue(0)
        else:
            self.pushButton_remove_quantity.setEnabled(False)
            self.pushButton_add_quantity.setEnabled(False)
            self.listWidget_itemnames.clearSelection()
            self.label.setText("Quantity:")
            self.pushButton_add_quantity.setText("Add Quantity")
            self.pushButton_remove_quantity.setText("Remove Quantity")
            settings_file.add_item(item_name="change_quantities_by", value="Item")

    def remove_quantity_from_category(self) -> None:
        """
        It removes a quantity of items from a category
        """
        are_you_sure_dialog = self.show_message_dialog(
            title="Are you sure?",
            message=f'Removing quantities from the whole selected category.\n\nAre you sure you want to remove a multiple of {self.spinBox_quantity.value()} quantities from each item in "{self.category}"?',
            dialog_buttons=DialogButtons.no_yes_cancel,
        )
        if are_you_sure_dialog in [DialogButtons.no, DialogButtons.cancel]:
            return
        self.play_celebrate_sound()


        self.status_button.setText("This may take awhile, please wait...", "yellow")
        self.radioButton_category.setEnabled(False)
        self.radioButton_single.setEnabled(False)
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        self.pushButton_create_new.setEnabled(False)
        self.centralwidget.setEnabled(False)
        self.listWidget_itemnames.setEnabled(False)

        remove_quantity_thread = RemoveQuantityThread(
            inventory,
            self.category,
            self.spinBox_quantity.value(),
        )
        with contextlib.suppress(AttributeError):
            self.generate_workorder(work_order={self.category: self.spinBox_quantity.value()})
        remove_quantity_thread.signal.connect(self.remove_quantity_thread_response)
        self.threads.append(remove_quantity_thread)
        remove_quantity_thread.start()

        history_file = HistoryFile()
        history_file.add_new_to_category(
            date=datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"),
            description=f"Removed a multiple of {self.spinBox_quantity.value()} quantities from each item in {self.category}",
        )
        if self.spinBox_quantity.value() > 1:
            history_file.add_new_to_category(
                date=datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"),
                description=f"Removed a multiple of {self.spinBox_quantity.value()} quantities from each item in {self.category}",
            )
        elif self.spinBox_quantity.value() == 1:
            history_file.add_new_to_category(
                date=datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"),
                description=f"Removed a multiple of {self.spinBox_quantity.value()} quantity from each item in {self.category}",
            )
        self.spinBox_quantity.setValue(0)

    # WORKSPACE
    def generate_workorder(self, work_order: dict[Assembly, int]) -> None:
        if admin_workspace.do_all_items_have_flow_tags() == False or admin_workspace.do_all_sub_assemblies_have_flow_tags() == False:
            self.show_message_dialog(
                title="Flow Tags not set",
                message="Items or sub-assemblies do not have flow tags set. All sub-assemblies and items need to have flow tags.",
            )
            return
        # Workspace order begins here
        date_created: str = QDate().currentDate().toString("yyyy-M-d")
        group_name_date_created = datetime.now()
        admin_workspace.load_data()
        for assembly, quantity in work_order.items():
            try:
                job_name = assembly.name
            except AttributeError:
                job_name = assembly
            for _ in range(quantity):
                user_workspace.load_data()
                try:
                    new_assembly = assembly.copy_assembly()
                except AttributeError:
                    continue
                # new_assembly: Assembly = admin_workspace.copy(job_name)
                if new_assembly is None:
                    continue
                new_assembly.rename(f"{job_name} - {datetime.now()}")
                # Job Assembly Data
                new_assembly.set_assembly_data(key="display_name", value=job_name)
                new_assembly.set_assembly_data(key="completed", value=False)
                new_assembly.set_assembly_data(key="starting_date", value=date_created)
                new_assembly.set_assembly_data(key="ending_date", value=date_created)
                new_assembly.set_assembly_data(key="status", value=None)
                new_assembly.set_assembly_data(key="group", value=f"{job_name} x {quantity} - {group_name_date_created}")
                new_assembly.set_assembly_data(key="group_color", value=get_random_color())
                # Sub-Assembly Data
                new_assembly.set_data_to_all_sub_assemblies(key="starting_date", value=date_created)
                new_assembly.set_data_to_all_sub_assemblies(key="ending_date", value=date_created)
                new_assembly.set_data_to_all_sub_assemblies(key="current_flow_state", value=0)
                new_assembly.set_data_to_all_sub_assemblies(key="completed", value=False)
                new_assembly.set_data_to_all_sub_assemblies(key="status", value=None)
                # All items in Assembly and Sub-Assembly
                new_assembly.set_default_value_to_all_items(key="starting_date", value=date_created)
                new_assembly.set_default_value_to_all_items(key="ending_date", value=date_created)
                new_assembly.set_default_value_to_all_items(key="current_flow_state", value=0)
                new_assembly.set_default_value_to_all_items(key="recoat", value=False)
                new_assembly.set_default_value_to_all_items(key="status", value=None)
                new_assembly.set_default_value_to_all_items(key="recut", value=False)
                new_assembly.set_default_value_to_all_items(key="recut_count", value=0)
                new_assembly.set_default_value_to_all_items(key="completed", value=False)

                # new_assembly.setup_timers_for_all_items()
                # new_assembly.setup_timers_for_all_assemblies()
                user_workspace.add_assembly(new_assembly)
                user_workspace.save()
        # NOTE because sync handles uploading logic differently
        self.upload_file(
            [
                "workspace - User.json",
            ],
            False,
        )

    # NOTE for EDIT INVENTORY
    def add_quantity(self) -> None:
        """
        It adds the value of the spinbox to the quantity of the item selected in the listwidget

        Args:
          item_name (str): str = the name of the item
          old_quantity (int): int = the quantity of the item before the change
        """
        data = inventory.get_data()
        table = self.tabs[self.category]
        selected_rows = list(set([item.row() for item in table.selectedItems()]))
        selected_items = [table.item(row, 0).text() for row in selected_rows]
        are_you_sure_dialog = self.show_message_dialog(
            title="Are you sure?",
            message=f'Adding quantities to a single item.\n\nAre you sure you want to add {self.spinBox_quantity.value()} quantities to "{selected_items}"?',
            dialog_buttons=DialogButtons.no_yes_cancel,
        )
        if are_you_sure_dialog in [DialogButtons.no, DialogButtons.cancel]:
            return
        for item_name in selected_items:
            part_number: str = data[self.category][item_name]["part_number"]
            current_quantity: int = data[self.category][item_name]["current_quantity"]
            inventory.change_object_in_object_item(self.category, item_name, "current_quantity", current_quantity + self.spinBox_quantity.value())
            inventory.change_object_in_object_item(
                self.category,
                item_name,
                "latest_change_current_quantity",
                f"{self.username} - Changed from {current_quantity} to {current_quantity + self.spinBox_quantity.value()} at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
            )
            for category in inventory.get_keys():
                if category == self.category:
                    continue
                for item in list(data[category].keys()):
                    if part_number == data[category][item]["part_number"]:
                        current_quantity: int = data[category][item]["current_quantity"]
                        inventory.change_object_in_object_item(category, item, "current_quantity", current_quantity + self.spinBox_quantity.value())
                        inventory.change_object_in_object_item(
                            category,
                            item,
                            "latest_change_current_quantity",
                            f"{self.username} - Changed from {current_quantity} to {current_quantity + self.spinBox_quantity.value()} at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                        )
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        # self.listWidget_item_changed()
        # self.listWidget_itemnames.setCurrentRow(self.last_item_selected_index)
        self.update_category_total_stock_costs()
        self.sort_inventory()
        self.sync_changes()

    # NOTE for EDIT INVENTORY
    def remove_quantity(self) -> None:
        """
        The function `remove_quantity` removes a specified quantity from selected items in an inventory
        system, updates the quantity in the inventory data, and performs other related tasks.

        Returns:
          The function does not have a return statement, so it returns None.
        """
        data = inventory.get_data()
        table = self.tabs[self.category]
        selected_rows = list(set([item.row() for item in table.selectedItems()]))
        selected_items = [table.item(row, 0).text() for row in selected_rows]
        are_you_sure_dialog = self.show_message_dialog(
            title="Are you sure?",
            message=f'Removing quantities from a single item.\n\nAre you sure you want to remove {self.spinBox_quantity.value()} quantities to "{selected_items}"?',
            dialog_buttons=DialogButtons.no_yes_cancel,
        )
        if are_you_sure_dialog in [DialogButtons.no, DialogButtons.cancel]:
            return
        logging.error(f"Remove quantity. 1-removing items from {self.category}")
        for item_name in selected_items:
            part_number: str = self.get_value_from_category(item_name, "part_number")
            current_quantity: int = self.get_value_from_category(item_name, "current_quantity")
            inventory.change_object_in_object_item(self.category, item_name, "current_quantity", current_quantity - self.spinBox_quantity.value())
            inventory.change_object_in_object_item(
                self.category,
                item_name,
                "latest_change_current_quantity",
                f"{self.username} - Changed from {current_quantity} to {current_quantity - self.spinBox_quantity.value()} at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
            )
            logging.error("Remove quantity. 1-removing items from inventory")
            for category in inventory.get_keys():
                if category == self.category:
                    continue
                for item in list(data[category].keys()):
                    if part_number == data[category][item]["part_number"]:
                        logging.error(f"Remove quantity. 1-match with {category}-{part_number}")
                        current_quantity: int = data[category][item]["current_quantity"]
                        logging.error(f"Remove quantity. 1-removing quantity from {category}-{part_number}")
                        inventory.change_object_in_object_item(category, item, "current_quantity", current_quantity - self.spinBox_quantity.value())
                        inventory.change_object_in_object_item(
                            category,
                            item,
                            "latest_change_current_quantity",
                            f"{self.username} - Changed from {current_quantity} to {current_quantity - self.spinBox_quantity.value()} at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                        )
                        logging.error(f"Remove quantity. 1-quantity removed from {category}-{part_number}")
            logging.error(f"Remove quantity. 1-creating history")
            history_file = HistoryFile()
            if self.spinBox_quantity.value() > 1:
                history_file.add_new_to_single_item(
                    date=datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"),
                    description=f'Removed {self.spinBox_quantity.value()} quantities from "{item_name}"',
                )
            elif self.spinBox_quantity.value() == 1:
                history_file.add_new_to_single_item(
                    date=datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"),
                    description=f'Removed {self.spinBox_quantity.value()} quantity from "{item_name}"',
                )

            logging.error("Remove quantity. 1-history made")
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        # self.listWidget_item_changed()
        # self.last_item_selected_index= 200
        # self.listWidget_itemnames.setCurrentRow(self.last_item_selected_index)
        self.update_category_total_stock_costs()
        self.sort_inventory()
        self.sync_changes()
        logging.error("Remove quantity. Donee")

    def listWidget_item_changed(self) -> None:
        """
        It's a function that changes the color of a QComboBox and QDoubleSpinBox when the user clicks on
        an item in a QListWidget.
        """
        try:
            self.last_item_selected_name = self.listWidget_itemnames.currentItem().text()
        except AttributeError:
            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(False)
            return
        try:
            quantity: int = self.get_value_from_category(self.last_item_selected_name, "current_quantity")
        except (KeyError, IndexError, TypeError):
            return
        # it brings incorrect results
        try:
            self.last_item_selected_index = list(list(inventory.get_data()[self.category].keys())).index(self.last_item_selected_name)
        except (ValueError, KeyError):
            return
        # self.last_item_selected_index=200
        table_widget: CustomTableWidget = self.tabs[self.category]
        table_widget.scrollTo(table_widget.model().index(self.last_item_selected_index, 0))
        table_widget.selectRow(self.last_item_selected_index)
        if self.radioButton_single.isChecked():
            self.pushButton_add_quantity.setEnabled(True)
            self.pushButton_remove_quantity.setEnabled(True)

            self.pushButton_add_quantity.disconnect()
            self.pushButton_remove_quantity.disconnect()

            self.pushButton_remove_quantity.clicked.connect(self.remove_quantity)
            self.pushButton_add_quantity.clicked.connect(self.add_quantity)
        self.spinBox_quantity.setValue(0)

    def value_change(self, category: str, item_name: str, value_name: str, new_value) -> None:
        """
        It changes the value of a value in a dictionary in a dictionary in a dictionary.

        Args:
          category (str): str = "category"
          item_name (str): str = the name of the item
          value_name (str): str = "current_quantity"
          new_value: str
        """
        add_quantity_state: bool = self.pushButton_add_quantity.isEnabled()
        remove_quantity_state: bool = self.pushButton_remove_quantity.isEnabled()
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        inventory.change_object_in_object_item(
            object_name=category,
            item_name=item_name,
            value_name=value_name,
            new_value=new_value,
        )
        self.pushButton_add_quantity.setEnabled(add_quantity_state)
        self.pushButton_remove_quantity.setEnabled(remove_quantity_state)

    def action_group(self, group_name: str, actions: list[QAction]) -> None:
        """
        It's a function that is called when a user clicks on a menu item in a menu bar. The function is
        supposed to check if the menu item is checked and if it is, it should uncheck the other menu
        items in the same group

        Args:
          group_name (str): str
          actions (list[QAction]): list[QAction]
        """
        if group_name == "order":
            if actions[0].isChecked() and settings_file.get_value(item_name="sort_descending"):
                actions[1].setChecked(False)
                actions[0].setEnabled(False)
                actions[1].setEnabled(True)
            if actions[1].isChecked() and settings_file.get_value(item_name="sort_ascending"):
                actions[0].setChecked(False)
                actions[1].setEnabled(False)
                actions[0].setEnabled(True)
        elif group_name == "sorting":
            if actions[0].isChecked() and (
                settings_file.get_value(item_name="sort_priority") or settings_file.get_value(item_name="sort_alphabatical")
            ):  # Quantity in Stock
                actions[1].setChecked(False)
                actions[2].setChecked(False)
                actions[0].setEnabled(False)
                actions[1].setEnabled(True)
                actions[2].setEnabled(True)
            elif actions[1].isChecked() and (
                settings_file.get_value(item_name="sort_quantity_in_stock") or settings_file.get_value(item_name="sort_alphabatical")
            ):  # Priority
                actions[0].setChecked(False)
                actions[2].setChecked(False)
                actions[0].setEnabled(True)
                actions[1].setEnabled(False)
                actions[2].setEnabled(True)
            elif actions[2].isChecked() and (
                settings_file.get_value(item_name="sort_priority") or settings_file.get_value(item_name="sort_quantity_in_stock")
            ):  # Alphabatical
                actions[0].setChecked(False)
                actions[1].setChecked(False)
                actions[0].setEnabled(True)
                actions[1].setEnabled(True)
                actions[2].setEnabled(False)

        settings_file.add_item(
            item_name="sort_quantity_in_stock",
            value=self.actionQuantity_in_Stock.isChecked(),
        )
        settings_file.add_item(
            item_name="sort_priority",
            value=self.actionPriority.isChecked(),
        )
        settings_file.add_item(
            item_name="sort_alphabatical",
            value=self.actionAlphabatical.isChecked(),
        )
        settings_file.add_item(
            item_name="sort_ascending",
            value=self.actionAscending.isChecked(),
        )
        settings_file.add_item(
            item_name="sort_descending",
            value=self.actionDescending.isChecked(),
        )
        self.update_sorting_status_text()

    # OMNIGEN
    def process_selected_nests(self) -> None:
        """
        This function processes selected nests by getting selected items and file paths, filtering the
        file paths based on selected items, and starting a thread to process the filtered file paths.
        """
        selected_nests = len(self.get_all_selected_nests())
        if selected_nests > 0:
            self.is_nest_generated_from_parts_in_inventory = False
            if selected_items := self.get_all_selected_nests():
                self.start_process_nest_thread(selected_items)

    # OMNIGEN
    def load_selected_previous_nests(self) -> None:
        """
        The function loads selected previous nests data in a separate thread.
        """
        self.pushButton_load_previous_nests.setEnabled(False)
        selected_indexes = self.treeView_previous_nests.selectionModel().selectedIndexes()
        selected_items = []
        for index in selected_indexes:
            try:
                if ".json" in index.data():
                    selected_items.append(index.data())
            except TypeError:
                continue
        if selected_items:
            self.load_previous_nests_data_thread(selected_items)

    # OMNIGEN
    def quote_table_cell_changed(self, row: int, col: int) -> None:
        if col not in [4, 7, 8, 11]:
            return
        item = self.tableWidget_quote_items.item(row, col)
        self.update_quote_price()

    # OMNIGEN
    def components_table_cell_changed(self, row: int, col: int) -> None:
        # Renaming item
        self.tableWidget_components_items.blockSignals(True)
        if col == 1:
            new_item_name = self.tableWidget_components_items.item(row, col).text()
            self.quote_components_information[new_item_name] = self.quote_components_information[self.last_component_selected_name]
            del self.quote_components_information[self.last_component_selected_name]
        # Part Number
        elif col == 2:
            item_name = self.tableWidget_components_items.item(row, 1).text()
            new_value = self.tableWidget_components_items.item(row, col).text()
            self.quote_components_information[item_name]['part_number'] = new_value
        # Shelf Number
        elif col == 3:
            item_name = self.tableWidget_components_items.item(row, 1).text()
            new_value = self.tableWidget_components_items.item(row, col).text()
            self.quote_components_information[item_name]['shelf_number'] = new_value
        # Description
        elif col == 4:
            item_name = self.tableWidget_components_items.item(row, 1).text()
            new_value = self.tableWidget_components_items.item(row, col).text()
            self.quote_components_information[item_name]['description'] = new_value
        # Quantity
        elif col == 5:
            item_name = self.tableWidget_components_items.item(row, 1).text()
            new_value = self.tableWidget_components_items.item(row, col).text()
            self.quote_components_information[item_name]['quantity'] = float(new_value)
        # Unit Price
        elif col == 6:
            item_name = self.tableWidget_components_items.item(row, 1).text()
            new_value = self.tableWidget_components_items.item(row, col).text().replace('$', '').replace(',', '')
            self.quote_components_information[item_name]['unit_price'] = float(new_value)
        self.tableWidget_components_items.blockSignals(False)
        self.update_components_prices()

    # OMNIGEN
    def components_table_cell_clicked(self, item: QTableWidgetItem) -> None:
        self.last_component_selected_name = item.text()

    # OMNIGEN
    def add_component(self) -> None:
        add_item_dialog = AddComponentDialog(
            title=f'Add new component to Quote',
            message=f"Adding a new item to Quote.\n\nPress 'Add' when finished.",
        )

        if add_item_dialog.exec():
            response = add_item_dialog.get_response()
            if response == DialogButtons.add:
                name: str = add_item_dialog.get_name()
                part_number: str= add_item_dialog.get_part_number()
                quantity: int = add_item_dialog.get_current_quantity()
                unit_price: float = add_item_dialog.get_item_price()
                use_exchange_rate: bool = add_item_dialog.get_exchange_rate()
                shelf_number: str = add_item_dialog.get_shelf_number()

                self.quote_components_information[name] = {'quantity': quantity, 'unit_price': unit_price, 'shelf_number': shelf_number, 'part_number': part_number, 'image_path': '', 'description': ''}
                self.load_components_table()
                self.update_quote_price()

    # OMNIGEN
    def clear_all_components(self) -> None:
        are_you_sure_dialog = self.show_message_dialog(
            title="Are you sure?",
            message=f'Are you sure you want to remove all items from this quote?',
            dialog_buttons=DialogButtons.no_yes_cancel,
        )
        if are_you_sure_dialog in [DialogButtons.no, DialogButtons.cancel]:
            return

        self.quote_components_information.clear()
        self.load_components_table()
        self.update_quote_price()

    # OMNIGEN
    def global_nest_material_change(self) -> None:
        """
        This function changes the material of all items in a table to the selected material from a combo
        box.
        """
        new_material = self.comboBox_global_sheet_material.currentText()
        for row in range(self.tableWidget_quote_items.rowCount()):
            self.tableWidget_quote_items.setItem(row, 2, QTableWidgetItem(new_material))
            self.tableWidget_quote_items.item(row, 2).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        for item in list(self.quote_nest_information.keys()):
            if item[0] == "_":
                self.quote_nest_information[item]["material"] = new_material
            else:
                for batch_name in list(self.quote_nest_information[item].keys()):
                    self.quote_nest_information[item][batch_name]["material"] = new_material
        toolbox_index: int = 0
        if new_material in {"304 SS", "409 SS", "Aluminium"}:
            self.comboBox_laser_cutting.setCurrentText("Nitrogen")
        else:
            self.comboBox_laser_cutting.setCurrentText("CO2")
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name[0] != "_":
                continue
            self.sheet_nests_toolbox.setItemText(
                toolbox_index,
                f"{self.quote_nest_information[nest_name]['gauge']} {self.quote_nest_information[nest_name]['material']} {self.quote_nest_information[nest_name]['sheet_dim']} - {nest_name.split('/')[-1].replace('.pdf', '')}",
            )
            combobox_material: QComboBox = self.sheet_nests_toolbox.getWidget(toolbox_index).findChildren(QComboBox)[0]
            combobox_material.setCurrentText(new_material)
            toolbox_index += 1
        self.update_quote_price()
        self.update_sheet_prices()

    # OMNIGEN
    def global_nest_thickness_change(self) -> None:
        """
        This function changes the thickness of all items in a table to a new global thickness selected
        from a combo box.
        """
        new_thickness = self.comboBox_global_sheet_thickness.currentText()
        for row in range(self.tableWidget_quote_items.rowCount()):
            self.tableWidget_quote_items.setItem(row, 3, QTableWidgetItem(new_thickness))
            self.tableWidget_quote_items.item(row, 3).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        for item in list(self.quote_nest_information.keys()):
            if item[0] == "_":
                self.quote_nest_information[item]["gauge"] = new_thickness
            else:
                for batch_name in list(self.quote_nest_information[item].keys()):
                    self.quote_nest_information[item][batch_name]["gauge"] = new_thickness
        toolbox_index: int = 0
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name[0] != "_":
                continue
            self.sheet_nests_toolbox.setItemText(
                toolbox_index,
                f"{self.quote_nest_information[nest_name]['gauge']} {self.quote_nest_information[nest_name]['material']} {self.quote_nest_information[nest_name]['sheet_dim']} - {nest_name.split('/')[-1].replace('.pdf', '')}",
            )
            combobox_thickness: QComboBox = self.sheet_nests_toolbox.getWidget(toolbox_index).findChildren(QComboBox)[1]
            combobox_thickness.setCurrentText(new_thickness)
            toolbox_index += 1
        self.update_quote_price()
        self.update_sheet_prices()

    # OMNIGEN
    def global_nest_sheet_dim_change(self) -> None:
        """
        The function `global_nest_sheet_dim_change` updates the sheet dimensions in a nested dictionary
        and updates the values in a GUI toolbox.
        """
        sheet_dim: str = f"{self.doubleSpinBox_global_sheet_length.value():.3f} x {self.doubleSpinBox_global_sheet_width.value():.3f}"
        for item in list(self.quote_nest_information.keys()):
            if item[0] == "_":
                self.quote_nest_information[item]["sheet_dim"] = sheet_dim
            else:
                for batch_name in list(self.quote_nest_information[item].keys()):
                    self.quote_nest_information[item][batch_name]["sheet_dim"] = sheet_dim
        toolbox_index: int = 0
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name[0] != "_":
                continue
            self.sheet_nests_toolbox.setItemText(
                toolbox_index,
                f"{self.quote_nest_information[nest_name]['gauge']} {self.quote_nest_information[nest_name]['material']} {self.quote_nest_information[nest_name]['sheet_dim']} - {nest_name.split('/')[-1].replace('.pdf', '')}",
            )
            doubleSpinBox_sheet_length: HumbleDoubleSpinBox = self.sheet_nests_toolbox.getWidget(toolbox_index).findChildren(HumbleDoubleSpinBox)[1]
            doubleSpinBox_sheet_length.setValue(self.doubleSpinBox_global_sheet_length.value())
            doubleSpinBox_sheet_width: HumbleDoubleSpinBox = self.sheet_nests_toolbox.getWidget(toolbox_index).findChildren(HumbleDoubleSpinBox)[2]
            doubleSpinBox_sheet_width.setValue(self.doubleSpinBox_global_sheet_width.value())
            toolbox_index += 1
        self.update_quote_price()
        self.update_scrap_percentages()
        self.update_sheet_prices()

    # OMNIGEN
    def sheet_nest_item_change(
        self,
        toolbox_index: int,
        input_method: QComboBox | HumbleDoubleSpinBox | tuple[HumbleDoubleSpinBox, HumbleDoubleSpinBox] | MachineCutTimeSpinBox,
        nest_name_to_update: str,
        item_to_change: str,
    ) -> None:
        """
        This function updates the information of a specific item in a nested sheet and updates the
        corresponding toolbox item and quote table.

        Args:
          toolbox_index (int): The index of the item in the toolbox that needs to be updated.
          input_method (QComboBox | HumbleDoubleSpinBox | tuple[HumbleDoubleSpinBox,
        HumbleDoubleSpinBox]): The input method can be one of three types: QComboBox,
        HumbleDoubleSpinBox, or a tuple of two HumbleDoubleSpinBoxes. This parameter is used to
        determine the current value of the input method and update the corresponding item in the quote
        nest information dictionary.
          nest_name_to_update (str): The name of the nest that needs to be updated.
          item_to_change (str): The name of the item in the quote nest information dictionary that needs
        to be updated with the new value.

        Returns:
          None is being returned.
        """
        if type(input_method) == QComboBox:
            current_value = input_method.currentText()
        elif type(input_method) == HumbleDoubleSpinBox or type(input_method) == MachineCutTimeSpinBox:
            current_value = input_method.value()
        elif type(input_method) == tuple:
            current_value = f"{input_method[0].value():.3f}x{input_method[1].value():.3f}"
        else:
            return
        for batch_name in list(self.quote_nest_information.keys()):
            if batch_name == "Components":
                continue
            if batch_name[0] == "_":
                if batch_name == nest_name_to_update and item_to_change == 'single_sheet_machining_time': # This changes a nest not a item in a nest
                    try:
                        self.quote_nest_information[nest_name]['single_sheet_machining_time'] = current_value
                        self.quote_nest_information[nest_name]['machining_time'] = current_value * self.quote_nest_information[nest_name]['quantity_multiplier']
                    except UnboundLocalError:
                        self.quote_nest_information[nest_name_to_update]['single_sheet_machining_time'] = current_value
                        self.quote_nest_information[nest_name_to_update]['machining_time'] = current_value * self.quote_nest_information[nest_name_to_update]['quantity_multiplier']
                continue
            for item in list(self.quote_nest_information[batch_name].keys()):
                nest_name = "_" + self.quote_nest_information[batch_name][item]["file_name"].replace("\\", "/")
                if nest_name == nest_name_to_update and type(input_method) != HumbleDoubleSpinBox:
                    self.quote_nest_information[batch_name][item][item_to_change] = current_value
        self.quote_nest_information[nest_name_to_update][item_to_change] = current_value
        nest_name = nest_name_to_update.split("/")[-1].replace(".pdf", "")
        self.sheet_nests_toolbox.setItemText(
            toolbox_index,
            f"{self.quote_nest_information[nest_name_to_update]['gauge']} {self.quote_nest_information[nest_name_to_update]['material']} {self.quote_nest_information[nest_name_to_update]['sheet_dim'].replace('x', ' x ')} - {nest_name}",
        )
        self.load_quote_table()
        self.update_quote_price()
        self.update_scrap_percentages()
        self.update_sheet_prices()
        self.load_nest_summary()

    def inventory_cell_changed(self, tab: CustomTableWidget):
        """
        This function updates the current item in a list widget based on the selected item in a table
        widget.

        Args:
          tab (CustomTableWidget): CustomTableWidget object representing the table widget where the cell
        change event occurred.
        """
        with contextlib.suppress(IndexError):
            selected_item = self.tabs[self.category].selectedItems()[0].text()
            if items := self.listWidget_itemnames.findItems(selected_item, Qt.MatchFlag.MatchExactly):
                item = items[0]
                self.listWidget_itemnames.setCurrentItem(item)

    def parts_in_inventory_cell_changed(self, tab: CustomTableWidget):
        """
        This function changes the text of a button based on the number of selected items in a table.

        Args:
          tab (CustomTableWidget): CustomTableWidget object representing the table widget where the
        inventory parts are displayed.
        """
        selected_items_count = len(self.get_all_selected_parts(tab))
        if selected_items_count == 0:
            self.pushButton_remove_quantities_from_inventory.setText("Remove Quantities from whole Category")
        else:
            self.pushButton_remove_quantities_from_inventory.setText(f"Remove Quantities from Selected ({selected_items_count}) Items")

    # OMNIGEN
    def cutoff_sheet_double_clicked(self, cutoff_items: QListWidget):
        """
        The function `cutoff_sheet_double_clicked` loads data from a steel inventory, retrieves
        information about a selected cutoff sheet, and updates various GUI elements with the retrieved
        information.

        Args:
          cutoff_items (QListWidget): The `cutoff_items` parameter is a QListWidget that contains a list
        of items representing cutoff sheets.

        Returns:
          nothing (None).
        """
        cutoff_sheets = price_of_steel_inventory.get_value("Cutoff")
        item_pressed: QListWidgetItem = cutoff_items.selectedItems()[0]
        for sheet in list(cutoff_sheets.keys()):
            if item_pressed.text() == sheet:
                sheet_material = price_of_steel_inventory.get_data()["Cutoff"][sheet]["material"]
                sheet_thickness = price_of_steel_inventory.get_data()["Cutoff"][sheet]["thickness"]
                sheet_dim_x = float(price_of_steel_inventory.get_data()["Cutoff"][sheet]["sheet_dimension"].split("x")[0].replace(" ", ""))
                sheet_dim_y = float(price_of_steel_inventory.get_data()["Cutoff"][sheet]["sheet_dimension"].split("x")[1].replace(" ", ""))
                self.comboBox_global_sheet_material.setCurrentText(sheet_material)
                self.comboBox_global_sheet_thickness.setCurrentText(sheet_thickness)
                self.doubleSpinBox_global_sheet_length.setValue(sheet_dim_x)
                self.doubleSpinBox_global_sheet_width.setValue(sheet_dim_y)
                self.global_nest_material_change()
                self.global_nest_sheet_dim_change()
                self.global_nest_thickness_change()
                return

    # * /\ SLOTS & SIGNALS /\
    # * \/ CALCULATION \/
    def calculuate_price_of_steel_summary(self) -> None:
        """
        It takes the current quantity of each item in the inventory, multiplies it by the cost per
        sheet, and then adds it to the total cost of the category.
        """
        category_data = price_of_steel_inventory.get_data()
        self.clear_layout(self.gridLayout_price_of_steel)
        total: float = 0.0
        i: int = 0
        for category in list(category_data.keys()):
            category_total: float = 0.0
            if category == "Price Per Pound":
                continue
            for item in list(category_data[category].keys()):
                current_quantity: int = category_data[category][item]["current_quantity"]
                sheet_dimension: str = category_data[category][item]["sheet_dimension"]
                thickness: str = category_data[category][item]["thickness"]
                material: str = category_data[category][item]["material"]
                try:
                    pounds_per_square_foot: float = float(price_of_steel_information.get_data()["pounds_per_square_foot"][material][thickness])
                except KeyError:
                    pounds_per_square_foot: float = 0.0
                sheet_length: float = float(sheet_dimension.split("x")[0])
                sheet_width: float = float(sheet_dimension.split("x")[1])
                try:
                    pounds_per_sheet: float = ((sheet_length * sheet_width) / 144) * pounds_per_square_foot
                except ZeroDivisionError:
                    pounds_per_sheet = 0.0
                try:
                    price_per_pound: float = float(price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"])
                except KeyError:
                    price_per_pound: float = 0.0
                cost_per_sheet = pounds_per_sheet * price_per_pound
                total_cost: float = current_quantity * cost_per_sheet
                category_total += total_cost
            lbl = QLabel(f"{category}:", self)
            self.gridLayout_price_of_steel.addWidget(lbl, i, 0)
            lbl = QLabel(f"${category_total:,.2f}", self)
            # lbl.setTextInteractionFlags(Qt.ItemFlag.TextSelectableByMouse)
            self.gridLayout_price_of_steel.addWidget(lbl, i, 1)
            total += category_total
            i += 1
        lbl = QLabel("Total:", self)
        lbl.setStyleSheet("border-top: 1px solid grey; border-bottom: 1px solid grey")
        self.gridLayout_price_of_steel.addWidget(lbl, i + 1, 0)
        lbl = QLabel(f"${total:,.2f}", self)
        lbl.setStyleSheet("border-top: 1px solid grey; border-bottom: 1px solid grey")
        self.gridLayout_price_of_steel.addWidget(lbl, i + 1, 1)

    def calculate_parts_in_inventory_summary(self) -> None:
        """
        It takes a dictionary of dictionaries of dictionaries and calculates the total value of each
        category and the total value of all categories.
        """

        while self.gridLayout_parts_in_inventory_summary.count():
            item = self.gridLayout_parts_in_inventory_summary.takeAt(0)
            widget = item.widget()
            widget.deleteLater()
        category_data = parts_in_inventory.get_data()
        # Idk why it does not exist somtimes
        if not category_data:
            return
        i: int = 0
        parts_in_inventory_total = {}
        for category in list(category_data.keys()):
            category_total: float = 0.0
            for part_name in list(category_data[category].keys()):
                price = category_data[category][part_name]["price"]
                quantity = category_data[category][part_name]["current_quantity"]
                category_total += price * quantity
                if category not in ["Recut", "Custom"]:
                    parts_in_inventory_total[part_name] = {
                        "price": price,
                        "current_quantity": quantity,
                    }
            if category in ["Recut", "Custom"]:
                lbl = QLabel(f"Total Cost in {category}:", self)
                self.gridLayout_parts_in_inventory_summary.addWidget(lbl, len(list(category_data.keys())) + i + 2, 0)
                lbl = QLabel(f"${category_total:,.2f}", self)
                self.gridLayout_parts_in_inventory_summary.addWidget(lbl, len(list(category_data.keys())) + i + 2, 1)
            else:
                lbl = QLabel(f"{category}:", self)
                self.gridLayout_parts_in_inventory_summary.addWidget(lbl, i, 0)
                lbl = QLabel(f"${category_total:,.2f}", self)
                self.gridLayout_parts_in_inventory_summary.addWidget(lbl, i, 1)
            i += 1
        total: float = 0.0
        for part_name in list(parts_in_inventory_total.keys()):
            price = parts_in_inventory_total[part_name]["price"]
            quantity = parts_in_inventory_total[part_name]["current_quantity"]
            total += price * quantity
        lbl = QLabel("Total Stoves in Inventory:", self)
        lbl.setStyleSheet("border-top: 1px solid grey; border-bottom: 1px solid grey")
        self.gridLayout_parts_in_inventory_summary.addWidget(lbl, i + 1, 0)
        lbl = QLabel(f"${total:,.2f}", self)
        lbl.setStyleSheet("border-top: 1px solid grey; border-bottom: 1px solid grey")
        self.gridLayout_parts_in_inventory_summary.addWidget(lbl, i + 1, 1)

    # * /\ CALCULATION /\

    def remove_quantity_from_part_inventory(self) -> None:
        """
        This function removes a specified quantity of parts from the inventory and updates the inventory
        data accordingly.

        Returns:
          None is being returned.
        """
        batch_multiplier: int = self.spinBox_quantity_for_inventory.value()
        selected_parts = self.get_all_selected_parts(self.tabs[self.category])
        if len(selected_parts) > 0:
            are_you_sure_dialog = self.show_message_dialog(
                title="Are you sure?",
                message=f'Removing quantities from the selected ({len(self.get_all_selected_parts(self.tabs[self.category]))}) items.\n\nAre you sure you want to remove a multiple of {batch_multiplier} quantities from each selected item in "{self.category}"?',
                dialog_buttons=DialogButtons.no_yes_cancel,
            )
            if are_you_sure_dialog in [DialogButtons.no, DialogButtons.cancel]:
                return
            self.pushButton_remove_quantities_from_inventory.setEnabled(False)
            self.spinBox_quantity_for_inventory.setValue(0)
            category_data = parts_in_inventory.get_data()
            part_names_to_check = []

            for part_name in selected_parts:
                part_names_to_check.append(part_name)
                unit_quantity: int = category_data[self.category][part_name]["unit_quantity"]
                current_quantity: int = category_data[self.category][part_name]["current_quantity"]
                new_quantity = current_quantity - (unit_quantity * batch_multiplier)
                category_data[self.category][part_name]["current_quantity"] = new_quantity
                category_data[self.category][part_name][
                    "modified_date"
                ] = f'{self.username} - Removed {unit_quantity*batch_multiplier} quantity at {str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"))}'
            for category in list(category_data.keys()):
                if category in ["Recut", self.category]:
                    continue
                for part_name in list(category_data[category].keys()):
                    if part_name in part_names_to_check:
                        unit_quantity: int = category_data[category][part_name]["unit_quantity"]
                        current_quantity: int = category_data[category][part_name]["current_quantity"]
                        new_quantity = current_quantity - (unit_quantity * batch_multiplier)
                        category_data[category][part_name]["current_quantity"] = new_quantity
                        category_data[category][part_name][
                            "modified_date"
                        ] = f'{self.username} - Removed {unit_quantity*batch_multiplier} quantity at {str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"))}'
        else:
            are_you_sure_dialog = self.show_message_dialog(
                title="Are you sure?",
                message=f'Removing quantities from the whole selected category.\n\nAre you sure you want to remove a multiple of {batch_multiplier} quantities from each item in "{self.category}"?',
                dialog_buttons=DialogButtons.no_yes_cancel,
            )
            if are_you_sure_dialog in [DialogButtons.no, DialogButtons.cancel]:
                return
            self.play_celebrate_sound()
            self.pushButton_remove_quantities_from_inventory.setEnabled(False)
            self.spinBox_quantity_for_inventory.setValue(0)
            category_data = parts_in_inventory.get_data()
            part_names_to_check = list(category_data[self.category].keys())
            for part_name in list(category_data[self.category].keys()):
                unit_quantity: int = category_data[self.category][part_name]["unit_quantity"]
                current_quantity: int = category_data[self.category][part_name]["current_quantity"]
                new_quantity = current_quantity - (unit_quantity * batch_multiplier)
                category_data[self.category][part_name]["current_quantity"] = new_quantity
                category_data[self.category][part_name][
                    "modified_date"
                ] = f'{self.username} - Removed {unit_quantity*batch_multiplier} quantity at {str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"))}'
            for category in list(category_data.keys()):
                if category in ["Recut", self.category]:
                    continue
                for part_name in list(category_data[category].keys()):
                    if part_name in part_names_to_check:
                        unit_quantity: int = category_data[category][part_name]["unit_quantity"]
                        current_quantity: int = category_data[category][part_name]["current_quantity"]
                        new_quantity = current_quantity - (unit_quantity * batch_multiplier)
                        category_data[category][part_name]["current_quantity"] = new_quantity
                        category_data[category][part_name][
                            "modified_date"
                        ] = f'{self.username} - Removed {unit_quantity*batch_multiplier} quantity at {str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"))}'
        parts_in_inventory.save_data(category_data)

        for category in parts_in_inventory.get_data():
            parts_in_inventory.sort(category=category, item_name="current_quantity", ascending=True)

        self.pushButton_remove_quantities_from_inventory.setText("Remove Quantities from whole Category")
        self.pushButton_remove_quantities_from_inventory.setEnabled(True)
        self.load_categories()
        self.calculate_parts_in_inventory_summary()
        self.sync_changes()

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
            settings_file.add_item("tables_font", font_data)
            self.load_active_tab()

    def update_sorting_status_text(self) -> None:
        """
        It updates the status tip of the sorting actions in the menu bar.
        """
        sorting_from_alphabet: str = "A"
        sorting_to_alphabet: str = "Z"

        sorting_from_number: str = "0"
        sorting_to_number: str = "9"

        sorting_from_priority: str = "Low"
        sorting_to_priority: str = "High"

        if self.actionAscending.isChecked():
            self.actionAlphabatical.setStatusTip(f"Sort from {sorting_from_alphabet} to {sorting_to_alphabet}")
            self.actionPriority.setStatusTip(f"Sort from {sorting_from_priority} to {sorting_to_priority}")
            self.actionQuantity_in_Stock.setStatusTip(f"Sort from {sorting_from_number} to {sorting_to_number}")
        else:
            self.actionAlphabatical.setStatusTip(f"Sort from {sorting_to_alphabet} to {sorting_from_alphabet}")
            self.actionPriority.setStatusTip(f"Sort from {sorting_to_priority} to {sorting_from_priority}")
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
        elif self.actionPriority.isChecked():
            if self.actionAscending.isChecked():
                self.actionSort.setStatusTip(f"Sort from {sorting_from_priority} to {sorting_to_priority}")
            else:
                self.actionSort.setStatusTip(f"Sort from {sorting_to_priority} to {sorting_from_priority}")
            self.actionAscending.setStatusTip(f"Sort from {sorting_from_priority} to {sorting_to_priority}")
            self.actionDescending.setStatusTip(f"Sort from {sorting_to_priority} to {sorting_from_priority}")

    def update_edit_inventory_list_widget(self) -> None:
        """
        It takes the text from a lineEdit widget and searches for it in a dictionary. If the text is
        found, it adds the key to a listWidget

        Returns:
          the value of the item_name key in the category_data dictionary.
        """
        search_input: str = self.lineEdit_search_items.text()
        category_data = inventory.get_value(item_name=self.category)
        self.listWidget_itemnames.disconnect()
        self.listWidget_itemnames.clear()
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        try:
            for item in natsorted(list(category_data.keys())):
                if search_input.lower() in item.lower() or search_input.lower() in category_data[item]["part_number"].lower():
                    self.listWidget_itemnames.addItem(item)
            self.listWidget_itemnames.itemSelectionChanged.connect(self.listWidget_item_changed)
        except (AttributeError, TypeError):
            self.listWidget_itemnames.itemSelectionChanged.connect(self.listWidget_item_changed)
            return

    # NOTE EDIT INVENTORY
    def update_stock_costs(self) -> None:
        """
        It takes the current quantity of an item, multiplies it by the price of the item, and then
        multiplies that by the exchange rate
        """
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) != "Edit Inventory":
            return
        self.label_total_unit_cost.setText(f"Total Unit Cost: ${inventory.get_total_unit_cost(self.category, self.get_exchange_rate()):,.2f}")
        tab = self.tabs[self.category]
        tab.blockSignals(True)
        for row_index in range(tab.rowCount()):
            item_name: str = tab.item(row_index, 0).text()
            total_cost_item = tab.item(row_index, 6)
            total_unit_cost_item = tab.item(row_index, 7)
            price: float = self.get_value_from_category(item_name, "price")
            current_quantity: float = self.get_value_from_category(item_name, "current_quantity")
            unit_quantity: float = self.get_value_from_category(item_name, "unit_quantity")
            use_exchange_rate: bool = self.get_value_from_category(item_name=item_name, key="use_exchange_rate")
            total_cost_item.setText(f'${(max(current_quantity, 0) * price):,.2f} {"USD" if use_exchange_rate else "CAD"}')
            total_unit_cost_item.setText(f'${(unit_quantity * price):,.2f} {"USD" if use_exchange_rate else "CAD"}')
        tab.blockSignals(False)

    # NOTE EDIT INVENTORY
    def update_category_total_stock_costs(self) -> None:
        """
        It takes a list of categories, and then sums up the total cost of all items in those categories
        """
        total_stock_costs = {}

        categories = inventory.get_data()
        # Idk why it does not exist somtimes
        if not categories:
            return
        for category in list(categories.keys()):
            total_category_stock_cost: float = 0.0
            for item in list(categories[category].keys()):
                use_exchange_rate: bool = categories[category][item]["use_exchange_rate"] == "USD"
                exchange_rate: float = self.get_exchange_rate() if use_exchange_rate else 1
                price: float = categories[category][item]["price"]
                current_quantity: int = categories[category][item]["current_quantity"]
                price = max(current_quantity * price * exchange_rate, 0)
                total_category_stock_cost += price
            total_stock_costs[category] = total_category_stock_cost
        total_stock_costs["Polar Total Stock Cost"] = inventory.get_total_stock_cost_for_similar_categories("Polar")
        total_stock_costs["BL Total Stock Cost"] = inventory.get_total_stock_cost_for_similar_categories("BL")
        total_stock_costs = dict(sorted(total_stock_costs.items()))
        self.clear_layout(self.gridLayout_Categor_Stock_Prices)
        lbl = QLabel("Stock Costs:", self)
        self.gridLayout_Categor_Stock_Prices.addWidget(lbl, 0, 0)
        i: int = 0
        for i, stock_cost in enumerate(total_stock_costs, start=1):
            lbl = QLabel(stock_cost, self)
            if "Total" in stock_cost:
                lbl.setStyleSheet("border-top: 1px solid grey; border-bottom: 1px solid grey")
            self.gridLayout_Categor_Stock_Prices.addWidget(lbl, i, 0)
            lbl = QLabel(f"${total_stock_costs[stock_cost]:,.2f}", self)
            # lbl.setTextInteractionFlags(Qt.ItemFlag.TextSelectableByMouse)
            if "Total" in stock_cost:
                lbl.setStyleSheet("border-top: 1px solid grey; border-bottom: 1px solid grey")
            self.gridLayout_Categor_Stock_Prices.addWidget(lbl, i, 1)
        lbl = QLabel("Total Cost in Stock:", self)
        lbl.setStyleSheet("border-top: 1px solid grey")
        self.gridLayout_Categor_Stock_Prices.addWidget(lbl, i + 1, 0)
        lbl = QLabel(f"${inventory.get_total_stock_cost(self.get_exchange_rate()):,.2f}", self)
        # lbl.setTextInteractionFlags(Qt.ItemFlag.TextSelectableByMouse)
        lbl.setStyleSheet("border-top: 1px solid grey")
        self.gridLayout_Categor_Stock_Prices.addWidget(lbl, i + 1, 1)

    # NOTE SHEETS IN INVENTORY
    def update_all_parts_in_inventory_price(self) -> None:
        """
        It takes the weight and machine time of a part, and uses that to calculate the price of the part
        """
        data = parts_in_inventory.get_data()
        # Idk why it does not exist somtimes
        if not data:
            return
        for category in list(data.keys()):
            if category in ["Custom", "Recut"]:
                continue
            for part_name in list(data[category].keys()):
                weight: float = data[category][part_name]["weight"]
                machine_time: float = data[category][part_name]["machine_time"]
                material: str = data[category][part_name]["material"]
                price_per_pound: float = price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"]
                cost_for_laser: float = self.get_nitrogen_laser_cost() if material in {"304 SS", "409 SS", "Aluminium"} else self.get_co2_laser_cost()
                parts_in_inventory.change_object_in_object_item(
                    object_name=category,
                    item_name=part_name,
                    value_name="price",
                    new_value=float((machine_time * (cost_for_laser / 60)) + (weight * price_per_pound)),
                )

    def set_table_row_color(self, table, row_index, color):
        """
        This function sets the background color of a row in a table widget in PyQt6.

        Args:
          table: The table parameter is a QTableWidget object, which represents a table widget in PyQt6.
        It contains rows and columns of cells, each of which can contain a QTableWidgetItem object.
          row_index: The index of the row in the table that you want to set the background color for.
          color: The color parameter is a string that represents the color that the row should be set
        to. It can be any valid color name or a hexadecimal value representing the color. For example,
        "red", "#FF0000", or "rgb(255, 0, 0)" could all be valid
        """
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setBackground(QColor(color))

    def set_table_row_text_color(self, table, row_index, color):
        """
        This function sets the text color of a specific row in a table widget in PyQt6.

        Args:
          table: a QTableWidget object representing the table widget
          row_index: The index of the row in the table where the text color needs to be set.
          color: The color parameter is a string that represents the color that you want to set for the
        text in the table row. It can be any valid color name or a hexadecimal value representing the
        color. For example, "red", "#FF0000", "blue", "#0000FF", etc.
        """
        for j in range(table.columnCount()):
            item = table.item(row_index, j)
            if not item:
                item = QTableWidgetItem()
                table.setItem(row_index, j, item)
            item.setForeground(QColor(color))

    # OMNIGEN
    def _get_item_data(self) -> dict:
        """
        The function `_get_item_data` retrieves item data from a table widget and returns it as a
        dictionary.

        Returns:
          a dictionary called `item_data`.
        """
        self.tableWidget_quote_items.blockSignals(True)
        nest_name: str = ""

        item_data = {}
        for row in range(self.tableWidget_quote_items.rowCount()):
            item_name = self.tableWidget_quote_items.item(row, 1).text()
            try:
                quantity = int(self.tableWidget_quote_items.item(row, 4).text())
            except ValueError:  # A merged cell
                nest_name = f"{self.tableWidget_quote_items.item(row, 0).text()}.pdf"
                continue
            except AttributeError:
                return
            bend_cost_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 7)
            labor_cost_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 8)
            bend_cost = 0.0
            labor_cost = 0.0
            try:
                bend_cost: float = float(bend_cost_item.text().replace("$", "").replace(",", ""))
                labor_cost: float = float(labor_cost_item.text().replace("$", "").replace(",", ""))
            except AttributeError:
                self.tableWidget_quote_items.blockSignals(False)
                return
            except ValueError:
                pass
            try:
                weight: float = self.quote_nest_information[nest_name][item_name]["weight"]
            except KeyError:  # This does something important but I dont know exactly what.
                self.tableWidget_quote_items.blockSignals(False)
                return
            machine_time: float = self.quote_nest_information[nest_name][item_name]["machine_time"]
            material: str = self.quote_nest_information[nest_name][item_name]["material"]
            if material == 'Null': # Its from Edit Inventory
                price_per_pound = 0.0
                COGS: float = self.quote_nest_information[nest_name][item_name]["price"]
                if isinstance(COGS, str):
                    COGS = float(COGS.replace('$',''))
            else:
                price_per_pound: float = price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"]
                cost_for_laser: float = self.doubleSpinBox_cost_for_laser.value()
                COGS: float = float((machine_time * (cost_for_laser / 60)) + (weight * price_per_pound))
            item_data.setdefault(item_name, {"bend_cost": 0.0, "labor_cost": 0.0, "COGS": 0.0, "quantity": 0})
            item_data[item_name]['bend_cost'] = bend_cost
            item_data[item_name]['labor_cost'] = labor_cost
            item_data[item_name]['COGS'] = COGS
            item_data[item_name]['quantity'] += quantity
        self.tableWidget_quote_items.blockSignals(False)
        return item_data

    # OMNIGEN
    def match_item_to_sheet_price(self) -> None:
        """
        The function `match_item_to_sheet_price` adjusts the prices of items to match a target sheet
        price and updates the corresponding values in a table.

        Returns:
          The function does not have a return statement, so it does not return any value.
        """
        # changing item price to match sheet price
        if not self.pushButton_item_to_sheet.isChecked():
            self.update_quote_price()
            return
        target_value: float = float(self.label_total_sheet_cost.text().replace('Total Cost for Sheets: $', '').replace(',', ''))

        def _calculate_total_cost(item_data: dict, include_extra_costs: bool=False) -> float:
            total_item_cost = 0.0
            for item, item_data in item_data.items():
                COGS = item_data['COGS']
                quantity = item_data['quantity']
                bend_cost = item_data['bend_cost']
                labor_cost = item_data['labor_cost']
                if include_extra_costs:
                    unit_price = (
                        calculate_overhead(COGS, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
                        + calculate_overhead(bend_cost, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
                        + calculate_overhead(labor_cost, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
                    )
                else:
                    unit_price = calculate_overhead(COGS, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
                price = unit_price * quantity
                total_item_cost += price
            return total_item_cost

        def _adjust_item_price(item_data, amount: float):
            for item, data in item_data.items():
                data['COGS'] = data['COGS'] + amount
            return item_data

        item_data = self._get_item_data()
        new_item_cost = _calculate_total_cost(item_data)
        difference = round(new_item_cost - target_value, 2)
        amount_changed: float = 0
        while abs(difference) > 0.5:
            if difference > 0: # Need to decrease cost for items
                item_data = _adjust_item_price(item_data, -(abs(difference)/1000))
            else: # Need to increase cost for items
                item_data = _adjust_item_price(item_data, abs(difference)/1000)
            new_item_cost = _calculate_total_cost(item_data)
            amount_changed += abs(difference) / 1000
            difference = round(new_item_cost - target_value, 2)

        self.tableWidget_quote_items.blockSignals(True)
        nest_name = ''
        for row in range(self.tableWidget_quote_items.rowCount()):
            item_name = self.tableWidget_quote_items.item(row, 1).text()
            try:
                quantity = int(self.tableWidget_quote_items.item(row, 4).text())
            except ValueError:  # A merged cell
                nest_name = f"{self.tableWidget_quote_items.item(row, 0).text()}.pdf"
                continue
            except AttributeError:
                self.tableWidget_quote_items.blockSignals(False)
                return
            COGS = item_data[item_name]['COGS']
            bend_cost = item_data[item_name]['bend_cost']
            labor_cost = item_data[item_name]['labor_cost']
            unit_price = (
                calculate_overhead(COGS, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
                + calculate_overhead(bend_cost, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
                + calculate_overhead(labor_cost, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
            )
            price = unit_price * quantity
            COGS_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 6)
            unit_price_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 9)
            price_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 10)
            COGS_item.setText(f"${COGS:,.2f}")
            unit_price_item.setText(f"${unit_price:,.2f}")
            price_item.setText(f"${price:,.2f}")
            self.quote_nest_information[nest_name][item_name]["quoting_unit_price"] = unit_price
            self.quote_nest_information[nest_name][item_name]["quoting_price"] = price
        self.tableWidget_quote_items.blockSignals(False)
        self.status_button.setText(f"Each item price changed ${amount_changed:,.2f}", "lime")
        total_item_cost = self.get_components_prices() + _calculate_total_cost(item_data, include_extra_costs=True)
        self.label_total_item_cost.setText(f"Total Cost for Items: ${total_item_cost:,.2f}")
        self.tableWidget_quote_items.resizeColumnsToContents()

    # OMNIGEN
    def match_sheet_to_item_price(self) -> None:
        target_value: float = float(self.label_total_item_cost.text().replace('Total Cost for Items: $', '').replace(',', ''))
        best_difference = float('inf')
        best_profit_margin_index = 0

        for profit_margin_index in range(0, 101):
            new_sheet_cost: float = self._get_total_sheet_cost(profit_margin_index, self.spinBox_overhead_sheets.value())
            difference = abs(new_sheet_cost - target_value)

            if difference < best_difference:
                best_difference = difference
                best_profit_margin_index = profit_margin_index
        self.spinBox_profit_margin_sheets.setValue(best_profit_margin_index)

    # OMNIGEN
    def clear_nest_selections(self) -> None:
        """
        This function clears the selection of all list widgets in a dictionary of quote nest
        directories.
        """
        for tree_view in self.quote_nest_directories_list_widgets.values():
            tree_view.clearSelection()

    # OMNIGEN
    def clear_all_nests(self) -> None:
        self.quote_nest_information.clear()
        self.clear_layout(self.verticalLayout_sheets)
        self.update_sheet_prices()
        self.load_quote_table()

    # OMNIGEN
    def nest_directory_item_selected(self) -> None:
        # self.process_selected_nests()
        selected_nests = len(self.get_all_selected_nests())
        if selected_nests == 0:
            self.pushButton_load_nests.setEnabled(False)
        else:
            self.pushButton_load_nests.setEnabled(True)
        self.pushButton_load_nests.setText(f"Load {selected_nests} Nest{'' if selected_nests == 1 else 's'}")

    # OMNIGEN
    def previous_nest_directory_item_selected(self):
        """
        The function selects and counts the number of previous nest directories in a tree view and
        updates a button's text and enabled state accordingly.
        """
        selected_indexes: list[QStandardItem] = self.treeView_previous_nests.selectionModel().selectedIndexes()
        selected_items: list[str] = []
        for index in selected_indexes:
            try:
                if ".json" in index.data():
                    selected_items.append(index.data())
            except TypeError:
                continue
        selected_nests = len(selected_items)
        if selected_nests == 0:
            self.pushButton_load_previous_nests.setEnabled(False)
        else:
            self.pushButton_load_previous_nests.setEnabled(True)
        self.pushButton_load_previous_nests.setText(f"Load {selected_nests} Previous Nest{'' if selected_nests == 1 else 's'}")

    # OMNIGEN
    def save_quote_table_values(self) -> None:
        """
        This function saves the quantities of items in a quote table to a dictionary.
        """
        nest_name: str = ""
        for row in range(self.tableWidget_quote_items.rowCount()):
            item_name = self.tableWidget_quote_items.item(row, 1).text()
            try:
                quantity = int(self.tableWidget_quote_items.item(row, 4).text())
            except ValueError:  # A merged cell
                nest_name = f"{self.tableWidget_quote_items.item(row, 0).text()}.pdf"
                continue
            recut_button: RecutButton = self.tableWidget_quote_items.cellWidget(row, 12)
            self.quote_nest_information[nest_name][item_name]["quantity"] = quantity
            self.quote_nest_information[nest_name][item_name]["recut"] = recut_button.isChecked()
            self.quote_nest_information[nest_name][item_name]["bend_cost"] = self.tableWidget_quote_items.item(row, 7).text()
            self.quote_nest_information[nest_name][item_name]["labor_cost"] = self.tableWidget_quote_items.item(row, 8).text()
            self.quote_nest_information[nest_name][item_name]["unit_price"] = self.tableWidget_quote_items.item(row, 9).text()
            self.quote_nest_information[nest_name][item_name]["price"] = self.tableWidget_quote_items.item(row, 10).text()
            self.quote_nest_information[nest_name][item_name]["shelf_number"] = self.tableWidget_quote_items.item(row, 11).text()

    # OMNIGEN
    def laser_cost_changed(self) -> None:
        cost_for_laser: float = self.get_nitrogen_laser_cost() if self.comboBox_laser_cutting.currentText() == "Nitrogen" else self.get_co2_laser_cost()
        self.doubleSpinBox_cost_for_laser.setValue(cost_for_laser)

    # OMNIGEN
    def _get_total_item_cost(self, profit_margin: int, overhead: int) -> float:
        total_item_cost: float = 0.0

        for row in range(self.tableWidget_quote_items.rowCount()):
            item_name = self.tableWidget_quote_items.item(row, 1).text()
            try:
                quantity = int(self.tableWidget_quote_items.item(row, 4).text())
            except ValueError:  # A merged cell
                nest_name = f"{self.tableWidget_quote_items.item(row, 0).text()}.pdf"
                continue
            except AttributeError:
                return
            bend_cost_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 7)
            labor_cost_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 8)
            unit_price_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 9)
            bend_cost = 0.0
            labor_cost = 0.0
            try:
                unit_price: float = float(unit_price_item.text().replace("$", "").replace(",", ""))
                bend_cost: float = float(bend_cost_item.text().replace("$", "").replace(",", ""))
                labor_cost: float = float(labor_cost_item.text().replace("$", "").replace(",", ""))
            except AttributeError:
                return
            except ValueError:
                pass
            try:
                weight: float = self.quote_nest_information[nest_name][item_name]["weight"]
            except KeyError:  # This does something important but I dont know exactly what.
                return
            machine_time: float = self.quote_nest_information[nest_name][item_name]["machine_time"]
            material: str = self.quote_nest_information[nest_name][item_name]["material"]
            if material == 'Null': # Its from Edit Inventory
                COGS: float = self.quote_nest_information[nest_name][item_name]["price"]
                if isinstance(COGS, str):
                    COGS = float(COGS.replace('$',''))
            else:
                price_per_pound: float = price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"]
                # The above code is declaring a variable named "cost_for_laser" of type float and
                # assigning it the value of "self.doubleSpinBox_cost_for_laser".
                cost_for_laser: float = self.doubleSpinBox_cost_for_laser.value()
                COGS: float = float((machine_time * (cost_for_laser / 60)) + (weight * price_per_pound))

            unit_price = (
                calculate_overhead(COGS, profit_margin / 100, overhead / 100)
                + calculate_overhead(bend_cost, profit_margin / 100, overhead / 100)
                + calculate_overhead(labor_cost, profit_margin / 100, overhead / 100)
            )

            price = unit_price * quantity
            total_item_cost += price
        return total_item_cost

    # OMNIGEN
    def update_quote_price(self) -> None:
        """
        This function updates the unit price and total price of items in a table based on their weight,
        machine time, material, and other factors.

        Returns:
          Nothing is being returned, as the return statement is only executed if a KeyError is raised in
        the try-except block.
        """
        total_item_cost: float = 0.0
        self.tableWidget_quote_items.blockSignals(True)
        nest_name: str = ""
        for row in range(self.tableWidget_quote_items.rowCount()):
            item_name = self.tableWidget_quote_items.item(row, 1).text()
            try:
                quantity = int(self.tableWidget_quote_items.item(row, 4).text())
            except ValueError:  # A merged cell
                nest_name = f"{self.tableWidget_quote_items.item(row, 0).text()}.pdf"
                continue
            except AttributeError:
                return
            COGS_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 6)
            bend_cost_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 7)
            labor_cost_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 8)
            unit_price_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 9)
            price_item: QTableWidgetItem = self.tableWidget_quote_items.item(row, 10)
            bend_cost = 0.0
            labor_cost = 0.0
            try:
                unit_price: float = float(unit_price_item.text().replace("$", "").replace(",", ""))
                bend_cost: float = float(bend_cost_item.text().replace("$", "").replace(",", ""))
                labor_cost: float = float(labor_cost_item.text().replace("$", "").replace(",", ""))
            except AttributeError:
                self.tableWidget_quote_items.blockSignals(False)
                return
            except ValueError:
                pass
            try:
                weight: float = self.quote_nest_information[nest_name][item_name]["weight"]
            except KeyError:  # This does something important but I dont know exactly what.
                self.tableWidget_quote_items.blockSignals(False)
                return
            machine_time: float = self.quote_nest_information[nest_name][item_name]["machine_time"]
            material: str = self.quote_nest_information[nest_name][item_name]["material"]
            if material == 'Null': # Its from Edit Inventory
                price_per_pound = 0.0
                COGS: float = self.quote_nest_information[nest_name][item_name]["price"]
                if isinstance(COGS, str):
                    COGS = float(COGS.replace('$',''))
            else:
                price_per_pound: float = price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"]
                cost_for_laser: float = self.doubleSpinBox_cost_for_laser.value()
                COGS: float = float((machine_time * (cost_for_laser / 60)) + (weight * price_per_pound))

            unit_price = (
                calculate_overhead(COGS, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
                + calculate_overhead(bend_cost, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
                + calculate_overhead(labor_cost, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
            )

            price = unit_price * quantity
            total_item_cost += price

            COGS_item.setText(f"${COGS:,.2f}")
            bend_cost_item.setText(f"${bend_cost:,.2f}")
            labor_cost_item.setText(f"${labor_cost:,.2f}")
            unit_price_item.setText(f"${unit_price:,.2f}")
            price_item.setText(f"${price:,.2f}")
            self.quote_nest_information[nest_name][item_name]["quoting_unit_price"] = unit_price
            self.quote_nest_information[nest_name][item_name]["quoting_price"] = price

        total_item_cost += self.get_components_prices()
        self.label_total_item_cost.setText(f"Total Cost for Items: ${total_item_cost:,.2f}")
        self.tableWidget_quote_items.resizeColumnsToContents()
        self.tableWidget_quote_items.blockSignals(False)
        if self.pushButton_item_to_sheet.isChecked():
            self.match_item_to_sheet_price()

    # OMNIGEN
    def update_scrap_percentages(self) -> None:
        toolbox_index: int = 0
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name[0] != "_":
                continue
            self.sheet_nests_toolbox.setItemText(
                toolbox_index,
                f"{self.quote_nest_information[nest_name]['gauge']} {self.quote_nest_information[nest_name]['material']} {self.quote_nest_information[nest_name]['sheet_dim']} - {nest_name.split('/')[-1].replace('.pdf', '')}",
            )
            label_scrap_percentage: QLabel = self.sheet_nests_toolbox.getWidget(toolbox_index).findChildren(QLabel)[9]
            label_scrap_percentage.setText(f"{calculate_scrap_percentage(nest_name, self.quote_nest_information):,.2f}%")
            toolbox_index += 1

    # OMNIGEN
    def _get_total_sheet_cost(self, profit_margin: int, overhead: int) -> float:
        total_sheet_cost: float = 0.0
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name[0] != "_":
                continue
            sheet_cost = self.get_sheet_cost(nest_name) * self.quote_nest_information[nest_name]['quantity_multiplier']
            cutting_cost = self.get_cutting_cost(nest_name) * self.quote_nest_information[nest_name]['quantity_multiplier']
            total_sheet_cost += calculate_overhead((sheet_cost + cutting_cost), profit_margin / 100, overhead / 100)
        return total_sheet_cost

    # OMNIGEN
    def update_sheet_prices(self) -> None:
        """
        The function `update_sheet_prices` updates the prices of sheets in a toolbox and calculates the
        total cost for sheets.
        """
        total_sheet_cost: float = 0.0
        toolbox_index: int = 0
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name[0] != "_":
                continue
            sheet_cost = self.get_sheet_cost(nest_name) * self.quote_nest_information[nest_name]['quantity_multiplier']
            cutting_cost = self.get_cutting_cost(nest_name)
            self.sheet_nests_toolbox.setItemText(
                toolbox_index,
                f"{self.quote_nest_information[nest_name]['gauge']} {self.quote_nest_information[nest_name]['material']} {self.quote_nest_information[nest_name]['sheet_dim']} - {nest_name.split('/')[-1].replace('.pdf', '')}",
            )
            try:
                label_sheet_cost: QLabel = self.sheet_nests_toolbox.getWidget(toolbox_index).findChildren(QLabel)[10]
            except AttributeError: # NOTE Because of some not understood reason when a nest is generated and nests haven't been made
                return
            label_sheet_cost.setText(f"${sheet_cost:,.2f}")

            label_cutting_cost: QLabel = self.sheet_nests_toolbox.getWidget(toolbox_index).findChildren(QLabel)[11]
            label_cutting_cost.setText(f"${cutting_cost:,.2f}")

            label_cutting_time: QLabel = self.sheet_nests_toolbox.getWidget(toolbox_index).findChildren(QLabel)[12]
            cut_time = self.get_total_cutting_time(nest_name)
            label_cutting_time.setText(cut_time)

            toolbox_index += 1

            total_sheet_cost += calculate_overhead((sheet_cost + cutting_cost), self.spinBox_profit_margin_sheets.value() / 100, self.spinBox_overhead_sheets.value() / 100)
        self.label_total_sheet_cost.setText(f"Total Cost for Sheets: ${total_sheet_cost:,.2f}")

    # OMNIGEN
    def get_sheet_cost(self, nest_name: str) -> float:
        """
        The function calculates the price of a sheet based on its dimensions, material, gauge, and
        quantity.

        Args:
          nest_name (str): The `nest_name` parameter is a string that represents the name of a nest.

        Returns:
          the calculated price of a sheet based on the given nest name.
        """
        gauge = self.quote_nest_information[nest_name]['gauge']
        material = self.quote_nest_information[nest_name]['material']
        if gauge == 'Null' or material == "Null":
            return 0.0
        sheet_dim_x, sheet_dim_y = self.quote_nest_information[nest_name]['sheet_dim'].replace(' x ', 'x').split('x')
        price_per_pound: float = price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"]
        try:
            pounds_per_square_foot: float = float(price_of_steel_information.get_data()["pounds_per_square_foot"][material][gauge])
        except KeyError:
            pounds_per_square_foot: float = 0.0
        try:
            pounds_per_sheet: float = ((float(sheet_dim_x) * float(sheet_dim_y)) / 144) * pounds_per_square_foot
        except ZeroDivisionError:
            pounds_per_sheet = 0.0
        return price_per_pound * pounds_per_sheet

    # OMNIGEN
    def get_cutting_cost(self, nest_name: str) -> float:
        """
        The function calculates the cutting cost based on the machining time and the type of laser
        cutting used.

        Args:
          nest_name (str): The `nest_name` parameter is a string that represents the name of the nest
        for which you want to calculate the cutting cost.

        Returns:
          the cutting cost, which is calculated by multiplying the machining time (in hours) by the cost
        for laser cutting.
        """
        try:
            machining_time: float = (self.quote_nest_information[nest_name]['single_sheet_machining_time'] * self.quote_nest_information[nest_name]['quantity_multiplier']) / 3600
        except KeyError:
            machining_time = 0
        cost_for_laser: float = self.doubleSpinBox_cost_for_laser.value()
        return machining_time * cost_for_laser

    # OMNIGEN
    def get_total_cutting_time(self, nest_name: str) -> str:
        """
        The function `get_cutting_time` calculates the total cutting time in hours, minutes, and seconds
        based on the given nest name.

        Args:
          nest_name (str): The `nest_name` parameter is a string that represents the name of the nest
        for which we want to calculate the cutting time.

        Returns:
          a formatted string that represents the cutting time in hours, minutes, and seconds.
        """
        try:
            total_seconds = float(self.quote_nest_information[nest_name]['single_sheet_machining_time']) * self.quote_nest_information[nest_name]['quantity_multiplier']
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
        except KeyError:
            return "Null"

    # OMNIGEN
    def get_sheet_cut_time(self, nest_name: str) -> str:
        """
        The function `get_cutting_time` calculates the total cutting time in hours, minutes, and seconds
        based on the given nest name.

        Args:
          nest_name (str): The `nest_name` parameter is a string that represents the name of the nest
        for which we want to calculate the cutting time.

        Returns:
          a formatted string that represents the cutting time in hours, minutes, and seconds.
        """
        try:
            total_seconds = float(self.quote_nest_information[nest_name]['single_sheet_machining_time'])
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
        except KeyError:
            return "Null"

    # OMNIGEN
    def get_nitrogen_laser_cost(self) -> float:
        program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        config = configparser.ConfigParser()
        config.read(f"{program_directory}/laser_quote_variables.cfg")
        return float(config.get("GLOBAL VARIABLES", "nitrogen_cost_per_hour"))

    # OMNIGEN
    def get_co2_laser_cost(self) -> int:
        program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
        config = configparser.ConfigParser()
        config.read(f"{program_directory}/laser_quote_variables.cfg")
        return float(config.get("GLOBAL VARIABLES", "co2_cost_per_hour"))

    # * /\ UPDATE UI ELEMENTS /\
    def sort_inventory(self) -> None:
        """
        It sorts the inventory based on the sorting method selected by the user
        """

        sorting_method: str = ""
        if self.actionQuantity_in_Stock.isChecked():
            sorting_method = "current_quantity"
        elif self.actionPriority.isChecked():
            sorting_method = "priority"
        elif self.actionAlphabatical.isChecked():
            sorting_method = "alphabet"
        self.active_json_file.sort(self.category, sorting_method, not self.actionAscending.isChecked())
        self.sync_changes()
        self.load_active_tab()

    # * \/ GETTERS \/
    def get_all_part_numbers(self) -> list[str]:
        """
        It takes the data from the inventory module, loops through the data, and returns a list of all
        the part numbers

        Returns:
          A list of all the part numbers in the inventory.
        """
        data = inventory.get_data()
        part_numbers = []
        for category in list(data.keys()):
            try:
                part_numbers.extend(data[category][item]["part_number"] for item in list(data[category].keys()))
            except KeyError:
                continue
        return list(set(part_numbers))

    def get_all_part_names(self) -> list[str]:
        """
        It takes the data from the inventory module, loops through the data, and returns a list of all
        the part names

        Returns:
          A list of all the part names in the inventory.
        """
        data = inventory.get_data()
        part_names = []
        for category in list(data.keys()):
            part_names.extend(iter(list(data[category].keys())))
        # part_names = list(set(part_names))
        return part_names

    def get_exchange_rate(self) -> float:
        """
        It returns the exchange rate from the settings file

        Returns:
          The exchange rate from the settings file.
        """
        return settings_file.get_value(item_name="exchange_rate")

    def get_value_from_category(self, item_name: str, key: str) -> Any:
        """
        It returns the value of a key in a dictionary, if the key exists. If the key doesn't exist, it
        returns a string

        Args:
          item_name (str): The name of the item you want to get the data from.
          key (str): str = The key of the item you want to get.

        Returns:
          The value of the key in the item_name dictionary.
        """
        try:
            return self.active_json_file.data[self.category][item_name][key]
        except KeyError:
            return "No changes yet." if "latest" in key else None

    def get_all_files_from_directory(self, folder_path: str, suffix: str) -> list[str]:
        """
        This function returns a list of all files in a directory that have a specified suffix.

        Args:
          folder_path (str): The path of the directory from which you want to retrieve files.
          suffix (str): The suffix parameter is a string that represents the file extension that we want
        to filter the files by. For example, if we want to get all the files with a ".txt" extension, we
        would set suffix to ".txt".

        Returns:
          a list of file names that end with the specified suffix in the specified folder path.
        """
        return [f"{folder_path}/{f}" for f in os.listdir(folder_path) if f.endswith(suffix)]

    # OMNIGEN
    def get_index_from_quote_table(self, item_name: str) -> int:
        """
        This function searches for a specific item name in a quote table and returns its row index if
        found, otherwise it returns None.

        Args:
          item_name (str): A string representing the name of an item to search for in a table.
        """
        for row in range(self.tableWidget_quote_items.rowCount()):
            item = self.tableWidget_quote_items.item(row, 1)
            if item is not None and item.text() == item_name:
                row_index = row
                break
        else:
            # Handle case where target string was not found
            row_index = None

    # OMNIGEN
    def get_quantity_multiplier(self, item_name: str, nest_name: str) -> int:
        """
        This Python function returns the quantity multiplier of an item based on its name and file
        location in a dictionary.

        Args:
          item_name (str): a string representing the name of an item

        Returns:
          The function `get_quantity_multiplier` returns an integer value, which is either the
        `quantity_multiplier` value of the `item_name` key in the `quote_nest_information` dictionary,
        or 1 if the `item_name` key is not found in the dictionary.
        """
        items_nest = "_" + self.quote_nest_information[nest_name][item_name]["file_name"].replace("\\", "/")

        if matches := {k: v for k, v in self.quote_nest_information.items() if k == items_nest}:
            return int(matches[items_nest]["quantity_multiplier"])
        else:
            return 1

    # OMNIGEN
    def get_all_selected_nests(self) -> list[str]:
        """
        This function returns a list of strings representing the data of all selected indexes in
        multiple tree views.

        Returns:
          A list of strings containing the data from the selected indexes in all the tree views in
        `self.quote_nest_directories_list_widgets`.
        """
        selected_nests = []
        for tree_view in self.quote_nest_directories_list_widgets.values():
            selected_nests.extend(tree_view.full_paths)
        return list(set(selected_nests))

    def get_menu_tab_order(self) -> list[str]:
        return [self.tabWidget.tabText(i) for i in range(self.tabWidget.count())]

    def get_tab_from_name(self, name: str) -> int:
        """
        This function finds the index of a tab in a tab widget by its name.

        Args:
          name (str): A string representing the name of the tab that needs to be found.

        Returns:
          an integer value which represents the index of the tab with the given name in the tab widget.
        If the tab is not found, it returns -1.
        """
        return next(
            (i for i in range(self.tabWidget.count()) if self.tabWidget.tabText(i) == name),
            -1,
        )

    def get_all_gauges(self) -> list[str]:
        """
        This function retrieves a list of all gauges from the inventory data.

        Returns:
          A list of unique gauge values extracted from the "gauge" key of each item in the inventory
        data.
        """
        data = parts_in_inventory.get_data()
        gauges = []
        for category in list(data.keys()):
            try:
                gauges.extend(data[category][item]["gauge"] for item in list(data[category].keys()))
            except KeyError:
                continue
        return list(set(gauges))

    def get_all_materials(self) -> list[str]:
        """
        This function retrieves a list of all gauges from the inventory data.

        Returns:
          A list of unique gauge values extracted from the "gauge" key of each item in the inventory
        data.
        """
        data = parts_in_inventory.get_data()
        materials = []
        for category in list(data.keys()):
            try:
                materials.extend(data[category][item]["material"] for item in list(data[category].keys()))
            except KeyError:
                continue
        return list(set(materials))

    def get_all_selected_parts(self, tab: CustomTableWidget) -> list[str]:
        """
        This function returns a list of selected items from a custom table widget that do not match any
        items in two other lists.

        Args:
          tab (CustomTableWidget): CustomTableWidget object representing the table widget from which the
        selected items are retrieved.

        Returns:
          A list of strings containing the text of all selected items in the given CustomTableWidget
        object, except for those that contain any of the strings in the lists returned by the methods
        `get_all_materials()` and `get_all_gauges()`.
        """
        selected_rows = tab.selectedItems()

        def check_lists_for_match(item_name: str, list1: list[str], list2: list[str]) -> bool:
            for string1 in list1:
                if string1 in item_name:
                    return True
            for string2 in list2:
                if string2 in item_name:
                    return True
            return False

        return [
            item.text()
            for item in selected_rows
            if not check_lists_for_match(item.text(), self.get_all_materials(), self.get_all_gauges()) and item.column() == 0
        ]

    def get_all_flow_tags(self) -> list[str]:
        """
        This function returns a list of strings where each string is a combination of flow tags joined
        by "->".

        Returns:
          A list of strings where each string is a concatenation of two or more flow tags separated by "
        -> ". The flow tags are obtained from the "flow_tags" key in the "workspace_tags" dictionary.
        """
        flow_tags: list[str] = []
        for group, group_data in workspace_tags.get_value("flow_tags").items():
            flow_tags.extend(group_data)
        return [" ➜ ".join(flow_tag) for flow_tag in flow_tags]

    def get_all_statuses(self) -> list[str]:
        """
        This function retrieves all unique statuses from a dictionary of flow tags.

        Returns:
          A list of unique status strings from the `flow_tag_statuses` dictionary obtained from the
        `workspace_tags` object.
        """
        data = workspace_tags.get_value("flow_tag_statuses")
        statuses = set()
        for flow_tag in data:
            for status in data[flow_tag]:
                statuses.add(status)
        return list(statuses)

    def get_all_job_names(self) -> list[str]:
        """
        The function `get_all_job_names` retrieves all job names from the admin workspace's data.

        Returns:
          a list of job names.
        """
        self.active_workspace_file.load_data()
        job_names: list[str] = [job.name for job in self.active_workspace_file.data]
        return job_names

    def get_all_workspace_items(self) -> list[Item]:
        """
        The function `get_all_workspace_items` retrieves all items from the admin workspace.

        Returns:
          a list of items.
        """
        self.active_workspace_file.load_data()
        all_items: list[Item] = []
        for assembly in self.active_workspace_file.data:
            all_items.extend(assembly.get_all_items())
        return all_items

    def get_all_workspace_item_names(self) -> list[str]:
        """
        The function `get_all_workspace_item_names` returns a list of unique names of all items in a
        workspace.

        Returns:
          a list of unique item names from all the workspace items.
        """
        all_items = self.get_all_workspace_items()
        unique_item_names = {item.name for item in all_items}
        return list(unique_item_names)

    # * /\ GETTERS /\
    def save_geometry(self) -> None:
        """
        It saves the geometry of the window to the settings file
        """
        geometry.set_value(item_name="x", value=max(self.pos().x(), 0))
        geometry.set_value(item_name="y", value=max(self.pos().y(), 0))
        geometry.set_value(item_name="width", value=self.size().width())
        geometry.set_value(item_name="height", value=self.size().height())

    def save_menu_tab_order(self) -> None:
        settings_file.add_item(item_name="menu_tabs_order", value=self.get_menu_tab_order())

    # * \/ Dialogs \/
    def show_about_dialog(self) -> None:
        """
        It creates an AboutDialog object and shows it.
        """
        dialog = AboutDialog(
            self,
            __name__,
            __version__,
            __updated__,
            "https://github.com/TheCodingJsoftware/Inventory-Manager",
        )
        dialog.show()

    def show_message_dialog(self, title: str, message: str, dialog_buttons: str = DialogButtons.ok) -> str:
        """
        It creates a message dialog, shows it, and returns the response

        Args:
          title (str): str = The title of the dialog
          message (str): str = The message to display in the dialog
          dialog_buttons (str): str = DialogButtons.ok

        Returns:
          The response is being returned.
        """
        message_dialog = MessageDialog(self, Icons.information, dialog_buttons, title, message)
        message_dialog.show()

        return message_dialog.get_response() if message_dialog.exec() else ""

    def show_error_dialog(
        self,
        title: str,
        message: str,
        dialog_buttons: str = DialogButtons.ok_save_copy_cancel,
    ) -> str:
        """
        It creates a dialog box with a message and a title, and returns the response

        Args:
          title (str): str = The title of the dialog
          message (str): str = The message to be displayed in the dialog.
          dialog_buttons (str): str = DialogButtons.ok_save_copy_cancel,

        Returns:
          The response from the dialog.
        """
        message_dialog = MessageDialog(self, Icons.critical, dialog_buttons, title, message)
        message_dialog.show()

        response = message_dialog.get_response() if message_dialog.exec() else ""

        if response == DialogButtons.copy:
            pixmap = QPixmap(self.message_dialog.grab())
            QApplication.clipboard().setPixmap(pixmap)
        elif response == DialogButtons.save:
            self.generate_error_log(message_dialog=message_dialog)
        return response

    def show_web_scrape_results(self, data) -> None:
        """
        Shows results of webscrape

        Args:
          data: a list of dictionaries
        """
        # # QApplication.restoreOverrideCursor()
        results = WebScrapeResultsDialog(title="Results", message="Ebay search results", data=data)
        if results.exec():
            response = results.get_response()
            if response == DialogButtons.ok:
                return

    def show_whats_new(self, show: bool = False) -> None:
        """
        If the latest version of the program is newer than the last time the program was opened, show
        the changelog.
        """

        def markdown_to_html(markdown_text):
            html = markdown.markdown(markdown_text)
            return html

        try:
            response = requests.get("https://api.github.com/repos/thecodingjsoftware/Inventory-Manager/releases/latest")
            version: str = response.json()["name"].replace(" ", "")
            if version == __version__ or show:
                build_date = time.strptime(__updated__, "%Y-%m-%d %H:%M:%S")
                current_date = time.strptime(
                    settings_file.get_value(item_name="last_opened"),
                    "%Y-%m-%d %H:%M:%S.%f",
                )
                if current_date < build_date or show:
                    with open("CHANGELOG.md", "r") as change_log_file:
                        self.show_message_dialog(title="Whats new?", message=markdown_to_html(change_log_file.read()))
                    settings_file.add_item(item_name="last_opened", value=str(datetime.now()))
        except Exception:
            return

    def show_not_trusted_user(self) -> None:
        """
        It shows a message dialog with a title and a message
        """
        self.tabWidget.setCurrentIndex(settings_file.get_value("menu_tabs_order").index(self.last_selected_menu_tab))
        self.show_message_dialog(
            title="Permission error",
            message="You don't have permission to change inventory items.\n\nnot sorry \n\n(:",
        )

    def add_item(self) -> None:
        """
        It adds an item to a category

        Returns:
          The response from the dialog.
        """
        add_item_dialog = AddItemDialog(
            title=f'Add new item to "{self.category}"',
            message=f"Adding a new item to \"{self.category}\".\n\nPress 'Add' when finished.",
        )

        if add_item_dialog.exec():
            response = add_item_dialog.get_response()
            if response == DialogButtons.add:
                name: str = add_item_dialog.get_name()
                category_data = inventory.get_value(item_name=self.category)
                for item in list(category_data.keys()):
                    if name == item:
                        self.show_error_dialog(
                            "Invalid name",
                            f"'{name}'\nis an invalid item name.\n\nCan't be the same as other names.",
                            dialog_buttons=DialogButtons.ok,
                        )
                        return

                priority: int = add_item_dialog.get_priority()
                unit_quantity: float = add_item_dialog.get_unit_quantity()
                current_quantity: int = add_item_dialog.get_current_quantity()
                price: float = add_item_dialog.get_item_price()
                notes: str = add_item_dialog.get_notes()
                part_number: str = add_item_dialog.get_part_number()
                use_exchange_rate: bool = add_item_dialog.get_exchange_rate()
                group: str = add_item_dialog.get_group()

                try:
                    inventory.add_item_in_object(self.category, name)
                    inventory.change_object_in_object_item(self.category, name, "part_number", part_number)
                except KeyError:
                    self.show_error_dialog(
                        "Invalid characters",
                        f"'{name}'\nis an invalid item name.",
                        dialog_buttons=DialogButtons.ok,
                    )
                    return
                inventory.change_object_in_object_item(self.category, name, "unit_quantity", unit_quantity)
                inventory.change_object_in_object_item(self.category, name, "current_quantity", current_quantity)
                inventory.change_object_in_object_item(self.category, name, "price", price)
                inventory.change_object_in_object_item(self.category, name, "use_exchange_rate", use_exchange_rate)
                inventory.change_object_in_object_item(self.category, name, "priority", priority)
                inventory.change_object_in_object_item(self.category, name, "notes", notes)
                if group != "None":
                    inventory.change_object_in_object_item(self.category, name, "group", group)
                inventory.change_object_in_object_item(
                    self.category,
                    name,
                    "latest_change_name",
                    f"Item added\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                )
                inventory.change_object_in_object_item(
                    self.category,
                    name,
                    "latest_change_part_number",
                    f"Item added\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                )
                inventory.change_object_in_object_item(
                    self.category,
                    name,
                    "latest_change_unit_quantity",
                    f"Item added\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                )
                inventory.change_object_in_object_item(
                    self.category,
                    name,
                    "latest_change_current_quantity",
                    f"Item added\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                )
                inventory.change_object_in_object_item(
                    self.category,
                    name,
                    "latest_change_price",
                    f"Item added\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                )
                inventory.change_object_in_object_item(
                    self.category,
                    name,
                    "latest_change_use_exchange_price",
                    f"Item added\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                )
                inventory.change_object_in_object_item(
                    self.category,
                    name,
                    "latest_change_priority",
                    f"Item added\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                )
                inventory.change_object_in_object_item(
                    self.category,
                    name,
                    "latest_change_notes",
                    f"Item added\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}",
                )
                self.sort_inventory()
                # self.load_active_tab()
            elif response == DialogButtons.cancel:
                return

    def set_custom_quantity_limit(self, tab: CustomTableWidget) -> None:
        """
        This function sets custom quantity limits for an item in a table widget and updates the table
        row color based on the current quantity and the new limits.

        Args:
          item_name (QComboBox): The name of the item for which the custom quantity limit is being set.
        It can be either a string representing the name of the item or a QComboBox object representing
        the dropdown menu for selecting the item.
        """
        with contextlib.suppress(AttributeError):
            table_widget: CustomTableWidget = self.tabs[self.category]
            try:
                selected_index = tab.selectedIndexes()[0].row()
            except IndexError:
                return

        item_name = tab.item(selected_index, 0).text()

        red_limit: int = self.get_value_from_category(item_name=item_name, key="red_limit")
        yellow_limit: int = self.get_value_from_category(item_name=item_name, key="yellow_limit")

        set_custom_limit_dialog = SetCustomLimitDialog(
            title="Set Custom Quantity Limit",
            message=f'Set a Custom Color Quantity Limit for:\n"{item_name}"',
            red_limit=red_limit,
            yellow_limit=yellow_limit,
        )

        if set_custom_limit_dialog.exec():
            response = set_custom_limit_dialog.get_response()
            if response == DialogButtons.set:
                red_limit: float = set_custom_limit_dialog.get_red_limit()
                yellow_limit: float = set_custom_limit_dialog.get_yellow_limit()
                try:
                    self.active_json_file.change_object_in_object_item(self.category, item_name, "red_limit", red_limit)
                    self.active_json_file.change_object_in_object_item(self.category, item_name, "yellow_limit", yellow_limit)
                except KeyError:
                    return
                current_quantity = self.get_value_from_category(item_name=item_name, key="current_quantity")
                if current_quantity <= red_limit:
                    self.set_table_row_color(tab, selected_index, "#3F1E25")
                elif current_quantity <= yellow_limit:
                    self.set_table_row_color(tab, selected_index, "#413C28")
                else:
                    self.set_table_row_color(tab, selected_index, "#2c2c2c")
                self.sync_changes()
                if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
                    self.load_active_tab()

    # ! deprecated
    def search_ebay(self) -> None:
        """
        It opens a dialog box, and if the user clicks ok, it starts a thread that scrapes ebay for the
        user's input.

        Returns:
          The response is a DialogButtons enum.
        """
        input_dialog = InputDialog(title="Search Ebay", message="Search for anything")
        if input_dialog.exec():
            response = input_dialog.get_response()
            if response == DialogButtons.ok:
                input_text = input_dialog.inputText
                ebay_scraper_thread = EbayScraper(item_to_search=input_text)
                # # QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
                ebay_scraper_thread.signal.connect(self.show_web_scrape_results)
                self.threads.append(ebay_scraper_thread)
                ebay_scraper_thread.start()
            elif response == DialogButtons.cancel:
                return

    def create_new_category(self, event=None) -> None:
        """
        It creates a new category

        Args:
          event: The event that triggered the function.

        Returns:
          The return value of the function is None.
        """
        input_dialog = InputDialog(title="Create category", message="Enter a name for a new category.")
        if input_dialog.exec():
            response = input_dialog.get_response()
            if response == DialogButtons.ok:
                input_text = input_dialog.inputText
                for category in self.categories:
                    if input_text in [category, "+"]:
                        self.show_error_dialog(
                            title="Invalid name",
                            message=f"'{input_text}' is an invalid name for a category.\n\nCan't have two categories with the same name.",
                            dialog_buttons=DialogButtons.ok,
                        )
                        return
                self.active_json_file.add_item(item_name=input_text, value={})
                self.sync_changes()
                self.load_categories()
            elif response == DialogButtons.cancel:
                return

    def delete_category(self) -> None:
        """
        It's a function that deletes a category from a list of categories

        Returns:
          The response from the dialog.
        """
        select_item_dialog = SelectItemDialog(
            button_names=DialogButtons.discard_cancel,
            title="Delete category",
            message="Select a category to delete.\n\nThis action is permanent and cannot\nbe undone.",
            items=self.categories,
        )

        if select_item_dialog.exec():
            response = select_item_dialog.get_response()
            if response == DialogButtons.discard:
                if select_item_dialog.get_selected_item() in [
                    "Price Per Pound",
                    "Recut",
                    "Custom",
                ]:
                    self.show_error_dialog(
                        "no",
                        "Cannot delete this category, it is special. ;)",
                        dialog_buttons=DialogButtons.ok,
                    )
                    return
                try:
                    self.active_json_file.remove_item(select_item_dialog.get_selected_item())
                except AttributeError:
                    return
                settings_file.add_item(item_name="last_category_tab", value=0)
                self.sync_changes()
                self.load_categories()
            elif response == DialogButtons.cancel:
                return

    def clone_category(self) -> None:
        """
        It's a function that opens a dialog box that allows the user to select a category to clone

        Returns:
          The response from the dialog.
        """
        select_item_dialog = SelectItemDialog(
            button_names=DialogButtons.clone_cancel,
            title="Clone category",
            message="Select a category to clone.",
            items=self.categories,
        )

        if select_item_dialog.exec():
            response = select_item_dialog.get_response()
            if response == DialogButtons.clone:
                try:
                    for category in self.categories:
                        if select_item_dialog.get_selected_item() in [
                            "Price Per Pound",
                            "Recut",
                            "Custom",
                        ]:
                            self.show_error_dialog(
                                "no",
                                "Cannot clone this category, it is special. ;)",
                                dialog_buttons=DialogButtons.ok,
                            )
                            return
                        if f"Clone from: {select_item_dialog.get_selected_item()} Double click me rename me" == category:
                            self.show_error_dialog(
                                "Invalid name",
                                f"'Clone from: {select_item_dialog.get_selected_item()} Double click me rename me'\nalready exists.\n\nCan't be the same as other names.",
                                dialog_buttons=DialogButtons.ok,
                            )
                            return
                    self.active_json_file.clone_key(select_item_dialog.get_selected_item())
                except AttributeError:
                    return
                self.sync_changes()
                self.load_categories()
            elif response == DialogButtons.cancel:
                return

    def rename_category(self, index) -> None:
        """
        It takes the index of the tab that was clicked, opens a dialog box, and if the user clicks ok,
        it renames the tab.

        Args:
          index: The index of the tab that was clicked.

        Returns:
          The return value of the function is the return value of the last expression evaluated, or None
        if no expression was evaluated.
        """
        if (
            self.tab_widget.tabText(0) == ""
            or self.tab_widget.tabText(index) == "Price Per Pound"
            or self.tab_widget.tabText(index) == "Recut"
            or self.tab_widget.tabText(index) == "Custom"
        ):
            return
        input_dialog = InputDialog(
            title="Rename category",
            message=f"Enter a new name for '{self.tab_widget.tabText(index)}'.",
            placeholder_text=self.tab_widget.tabText(index),
        )

        if input_dialog.exec():
            response = input_dialog.get_response()
            if response == DialogButtons.ok:
                input_text = input_dialog.inputText
                for category in self.categories:
                    if input_text in [category, "+"]:
                        self.show_error_dialog(
                            title="Invalid name",
                            message=f"'{input_text}'\nis an invalid name for a category.\n\nCan't have two categories with the same name.",
                            dialog_buttons=DialogButtons.ok,
                        )
                        return
                self.active_json_file.change_key_name(key_name=self.tab_widget.tabText(index), new_name=input_text)
                self.sync_changes()
                self.load_categories()
            elif response == DialogButtons.cancel:
                return

    def open_group_menu(self, menu: QMenu) -> None:
        """
        It opens a menu at the current cursor position

        Args:
          menu (QMenu): QMenu
        """
        menu.exec(QCursor.pos())

    # OMNIGEN
    def add_nest_directory(self) -> None:
        """
        This function adds a new directory to a list of quote nest directories and refreshes the list.
        """
        nest_directories: list[str] = settings_file.get_value("quote_nest_directories")
        if new_nest_directory := QFileDialog.getExistingDirectory(self, "Open directory", "/"):
            nest_directories.append(new_nest_directory)
            settings_file.add_item(item_name="quote_nest_directories", value=nest_directories)
            self.refresh_nest_directories()

    # OMNIGEN
    def remove_nest_directory(self) -> None:
        """
        This function removes a selected nest directory from a list of nest directories and updates the
        settings file.
        """
        nest_directories: list[str] = settings_file.get_value("quote_nest_directories")
        select_item_dialog = SelectItemDialog(
            button_names=DialogButtons.discard_cancel,
            title="Remove Nest Directory",
            message="Select a nest directory to delete. (from gui. not system)\n\nThis action is permanent and cannot be undone.",
            items=nest_directories,
        )

        if select_item_dialog.exec():
            response = select_item_dialog.get_response()
            if response == DialogButtons.discard:
                try:
                    nest_directories.remove(select_item_dialog.get_selected_item())
                except ValueError:  # No Item was selected
                    return
                settings_file.add_item(item_name="quote_nest_directories", value=nest_directories)
                self.refresh_nest_directories()
            elif response == DialogButtons.cancel:
                return

    # OMNIGEN
    def _get_quoted_parts_list_information(self) -> dict:
        """
        This function calculates the quoting unit price and quoting price for each item in a batch based
        on its weight, quantity, machine time, material, and overhead costs.

        Returns:
          A dictionary containing information about quoted parts list.
        """
        batch_data = {}
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name == 'Components':
                continue
            if nest_name[0] == "_":
                batch_data[nest_name] = self.quote_nest_information[nest_name]
            else:
                for item in self.quote_nest_information[nest_name]:
                    try:
                        batch_data[item]["quantity"] += self.quote_nest_information[nest_name][item]["quantity"]
                        batch_data[item]['quoting_price'] = batch_data[item]["quantity"] * batch_data[item]["quoting_unit_price"]
                        batch_data[item]['price'] = f'${batch_data[item]["quoting_price"]:,.2f}'
                    except KeyError:
                        batch_data[item] = self.quote_nest_information[nest_name][item]
        batch_data['Components'] = self.quote_components_information
        for component in list(batch_data['Components'].keys()):
            unit_price = batch_data['Components'][component]['unit_price']
            quantity = batch_data['Components'][component]['quantity']
            batch_data['Components'][component]['quoting_price'] = calculate_overhead(unit_price*quantity, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
        return batch_data

    # OMNIGEN
    def _get_grouped_quoted_parts_list_information(self) -> dict:
        """
        This function calculates the quoting unit price and quoting price for each item in a batch based
        on its weight, quantity, machine time, material, and overhead costs.

        Returns:
          A dictionary containing information about quoted parts list.
        """
        batch_data = {}
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name == 'Components':
                continue
            if nest_name[0] == "_":
                batch_data[nest_name] = self.quote_nest_information[nest_name]
            else:
                batch_data[nest_name] = {}
                for item in self.quote_nest_information[nest_name]:
                    batch_data[nest_name][item] = self.quote_nest_information[nest_name][item]
                    batch_data[nest_name][item]['quoting_price'] = batch_data[nest_name][item]["quantity"] * batch_data[nest_name][item]["quoting_unit_price"]
                    batch_data[nest_name][item]['price'] = f'${batch_data[nest_name][item]["quoting_price"]:,.2f}'
        batch_data['Components'] = self.quote_components_information
        for component in list(batch_data['Components'].keys()):
            unit_price = batch_data['Components'][component]['unit_price']
            quantity = batch_data['Components'][component]['quantity']
            batch_data['Components'][component]['quoting_price'] = calculate_overhead(unit_price*quantity, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100)
        return batch_data

    # OMNIGEN
    def generate_quote(self) -> None:
        """
        This function generates a quote, work order, or packing slip based on user input and updates
        inventory if necessary.

        Returns:
          The function does not have a return statement, so it returns None by default.
        """
        select_item_dialog = GenerateQuoteDialog(
            button_names=DialogButtons.generate_cancel,
            title="Quote Generator",
            message="Select which ever you need.\n\nPress Generate when ready.",
        )

        if select_item_dialog.exec():
            response = select_item_dialog.get_response()
            if response == DialogButtons.generate:
                try:
                    action = select_item_dialog.get_selected_item()
                except AttributeError:
                    return
                should_generate_quote, should_generate_workorder, should_update_inventory, should_generate_packing_slip, should_group_items = action
                should_remove_sheet_quantities = select_item_dialog.should_remove_sheet_quantities()
                if should_generate_packing_slip:
                    self.get_order_number_thread()
                    loop = QEventLoop()
                    QTimer.singleShot(200, loop.quit)
                    loop.exec()
                    self.set_order_number_thread(self.order_number + 1)

                self.save_quote_table_values()
                if should_group_items:
                    batch_data = self._get_grouped_quoted_parts_list_information()
                else:
                    batch_data = self._get_quoted_parts_list_information()
                # batch_data = self.quote_nest_information
                settings_file.load_data()

                option_string: str = ""

                try:
                    if should_generate_quote or should_generate_packing_slip:
                        option_string = "Quote" if should_generate_quote else "Packing Slip"
                        file_name: str = f'{option_string} - {datetime.now().strftime("%A, %d %B %Y %H-%M-%S-%f")}'
                        config = configparser.ConfigParser()
                        config.read("laser_quote_variables.cfg")
                        path_to_save_quotes = config.get("GLOBAL VARIABLES", "path_to_save_quotes")
                        if should_generate_quote:
                            generate_quote = GenerateQuote(
                                (True, False, should_update_inventory, False, should_group_items),
                                file_name,
                                batch_data,
                                self.order_number,
                            )
                            if settings_file.get_value('open_quote_when_generated'):
                                self.open_folder(f"{path_to_save_quotes}/{file_name}.html")
                        elif should_generate_packing_slip:
                            generate_quote = GenerateQuote(
                                (False, False, should_update_inventory, True, should_group_items),
                                file_name,
                                batch_data,
                                self.order_number,
                            )
                            if settings_file.get_value('open_packing_slip_when_generated'):
                                self.open_folder(f"{path_to_save_quotes}/{file_name}.html")

                    if should_generate_workorder or should_update_inventory:
                        file_name: str = f'Workorder - {datetime.now().strftime("%A, %d %B %Y %H-%M-%S-%f")}'
                        generate_workorder = GenerateQuote((False, True, should_update_inventory, False, should_group_items), file_name, batch_data, self.order_number)
                except FileNotFoundError:
                    self.show_error_dialog(
                        "File not found, aborted",
                        'Invalid paths set for "path_to_sheet_prices" or "price_of_steel_information" in config file "laser_quote_variables.cfg"\n\nGenerating Quote Aborted.',
                    )
                    return

                batch_data_to_upload = self.quote_nest_information
                batch_data_to_upload['Components'] = self.quote_components_information

                batch_data_to_upload_copy = copy.deepcopy(batch_data_to_upload)
                if not should_remove_sheet_quantities:
                    for nest, nest_data in batch_data_to_upload.items():
                        if nest[0] == '_':
                            print('deleting')
                            del batch_data_to_upload_copy[nest]
                self.upload_batch_to_inventory_thread(batch_data_to_upload_copy, should_update_inventory, should_generate_quote)
                if should_update_inventory and not self.is_nest_generated_from_parts_in_inventory:
                    self.upload_batched_parts_images(batch_data)
                self.status_button.setText("Generating complete", "lime")
                if should_generate_workorder and settings_file.get_value('open_workorder_when_generated'):
                    config = configparser.ConfigParser()
                    config.read("laser_quote_variables.cfg")
                    path_to_save_workorders = config.get("GLOBAL VARIABLES", "path_to_save_workorders")
                    self.open_folder(f"{path_to_save_workorders}/{file_name}.html")
            elif response == DialogButtons.cancel:
                return

    # NOTE PARTS IN INVENTORY
    def generate_quote_with_selected_parts(self, tab: CustomTableWidget) -> None:
        """
        This function generates a quote with selected parts and their corresponding information.

        Args:
          tab (CustomTableWidget): The parameter `tab` is of type `CustomTableWidget` and is used as an
        input to the `generate_quote_with_selected_parts` method. It is likely a reference to a table
        widget object that contains information about selected parts.
        """
        selected_parts = self.get_all_selected_parts(tab)
        try:
            sheet_gauge: str = self.get_value_from_category(item_name=selected_parts[0], key="gauge")
            sheet_dimension: str = self.get_value_from_category(item_name=selected_parts[0], key="sheet_dim")
            sheet_material: str = self.get_value_from_category(item_name=selected_parts[0], key="material")
            self.is_nest_generated_from_parts_in_inventory = True
        except IndexError:  # No item selected
            return
        self.quote_nest_information.clear()
        self.quote_nest_information.setdefault("/CUSTOM NEST.pdf", {})
        self.quote_nest_information.setdefault("_/CUSTOM NEST.pdf", {
            "quantity_multiplier": 1,  # Sheet count
            "gauge": sheet_gauge,
            "material": sheet_material,
            "sheet_dim": "0.000x0.000" if sheet_dimension is None else sheet_dimension,
            "scrap_percentage": 0.0,
            "single_sheet_machining_time": 0.0,
            "machining_time": 0.0
        })
        for part_name in selected_parts:
            self.quote_nest_information["/CUSTOM NEST.pdf"][part_name] = parts_in_inventory.get_data()[self.category].get(part_name)
            self.quote_nest_information["/CUSTOM NEST.pdf"][part_name]["file_name"] = "/CUSTOM NEST.pdf"
        self.tabWidget.setCurrentIndex(self.get_menu_tab_order().index("OmniGen"))
        self.download_required_images(self.quote_nest_information["/CUSTOM NEST.pdf"])
        # self.load_nests()

    # NOTE PARTS IN INVENTORY
    def add_selected_parts_to_quote(self, tab: CustomTableWidget) -> None:
        """
        The function adds selected parts to a quote and generates a custom nest PDF file.

        Args:
          tab (CustomTableWidget): The `tab` parameter is of type `CustomTableWidget`.

        Returns:
          In this code, if no item is selected, the function will return and no further action will be
        taken.
        """
        selected_parts = self.get_all_selected_parts(tab)
        try:
            sheet_gauge: str = self.get_value_from_category(item_name=selected_parts[0], key="gauge")
            sheet_dimension: str = self.get_value_from_category(item_name=selected_parts[0], key="sheet_dim")
            sheet_material: str = self.get_value_from_category(item_name=selected_parts[0], key="material")
            self.is_nest_generated_from_parts_in_inventory = True
        except IndexError:  # No item selected
            return
        self.quote_nest_information.setdefault("/CUSTOM NEST.pdf", {})
        self.quote_nest_information.setdefault("_/CUSTOM NEST.pdf", {
            "quantity_multiplier": 1,  # Sheet count
            "gauge": sheet_gauge,
            "material": sheet_material,
            "sheet_dim": "0.000x0.000" if sheet_dimension is None else sheet_dimension,
            "scrap_percentage": 0.0,
            "single_sheet_machining_time": 0.0,
            "machining_time": 0.0
        })
        for part_name in selected_parts:
            self.quote_nest_information["/CUSTOM NEST.pdf"][part_name] = parts_in_inventory.get_data()[self.category].get(part_name)
            self.quote_nest_information["/CUSTOM NEST.pdf"][part_name]["file_name"] = "/CUSTOM NEST.pdf"
        self.tabWidget.setCurrentIndex(self.get_menu_tab_order().index("OmniGen"))
        self.download_required_images(self.quote_nest_information["/CUSTOM NEST.pdf"])
        # self.load_nests()

    # OMNIGEN
    def open_image(self, path: str, title: str) -> None:
        image_viewer = QImageViewer(self, path, title)
        image_viewer.show()

    def open_pdf(self, path: str) -> None:
        url = QUrl.fromLocalFile(path)
        self.web_engine_view.load(url)
        self.web_engine_view.show()

    # NOTE PARTS IN INVENTORY
    def view_part_information(self, tab: CustomTableWidget) -> None:
        try:
            selected_part = self.get_all_selected_parts(tab)[0]
        except IndexError:
            return
        item_dialog = PartInformationViewer(
            selected_part,
            parts_in_inventory.get_data()[self.category][selected_part],
        )
        if item_dialog.exec():
            if item_dialog.get_response() == 'apply':
                parts_in_inventory.get_data()[self.category][selected_part] = item_dialog.get_data()
                self.load_categories()


    def set_order_number(self) -> None:
        """
        This function sets the order number by prompting the user to input a new integer value and
        updating the corresponding JSON file.

        Returns:
          None.
        """
        self.get_order_number_thread()
        loop = QEventLoop()
        QTimer.singleShot(200, loop.quit)
        loop.exec()

        input_dialog = InputDialog(
            title="Set a Order Number",
            message="Enter a Order Number as an integer",
            button_names=DialogButtons.set_cancel,
            placeholder_text=self.order_number,
        )
        if input_dialog.exec():
            response = input_dialog.get_response()
            if response in [DialogButtons.set, DialogButtons.ok]:
                try:
                    input_number = int(input_dialog.inputText)
                    self.set_order_number_thread(input_number)
                except Exception:
                    self.show_error_dialog(
                        title="Invalid number",
                        message=f"'{input_dialog.inputText}' is an invalid numnber",
                        dialog_buttons=DialogButtons.ok,
                    )
                    return
            elif response == DialogButtons.cancel:
                return

    def open_job_sorter(self) -> None:
        job_sorter_menu = JobSorterDialog(
            self, title="Job Sorter", message="Make sure all paths are set properly before pressing Sort, this is irreversible."
        )
        job_sorter_menu.show()

    def open_tag_editor(self) -> None:
        tag_editor = EditTagsDialog(
            self,
            title="Flow Tags",
            message='Create and edit flow tags and set attributes.\n\nIf a tag box is left as \'None\' it will not be part of the flow.\n"Starts Timer" starts the timer if the flow tag has a timer enabled, timers will be stop automatically when flow tag is changed.\nTags such as, "Staging", "Editing", and "Planning" cannot be used as flow tags, nothing will be checked if you use them, it could break everything, so, don\'t use them.',
        )

        def upload_workspace_settings():
            self.status_button.setText(f'Synching - {datetime.now().strftime("%r")}', "lime")
            self.upload_file(
                ["workspace_settings.json"],
                False,
            )

        tag_editor.accepted.connect(lambda: (upload_workspace_settings(), self.load_categories()))
        tag_editor.exec()

    def open_status_editor(self) -> None:
        status_editor = EditStatusesDialog(self)
        status_editor.show()

    # WORKSPACE
    def generate_workorder_dialog(self, job_names: list[str] = None) -> None:
        workorder = GenerateWorkorderDialog(
            self,
            title="Generate Workorder",
            message="Set quantity for selected jobs",
            button_names=DialogButtons.generate_cancel,
            job_names=job_names,
        )
        if workorder.exec():
            response = workorder.get_response()
            if response == DialogButtons.generate:
                s = workorder.get_workorder()
                self.generate_workorder(work_order=workorder.get_workorder())

    # WORKSPACE
    def generate_workspace_quote_dialog(self, job_names: list[str] = None) -> None:
        quote = GenerateWorkspaceQuoteDialog(
            self,
            title="Generate Quote",
            message="Set quantity for selected jobs",
            button_names=DialogButtons.generate_cancel,
            job_names=job_names,
        )
        if quote.exec():
            response = quote.get_response()
            if response == DialogButtons.generate:
                self.quote_nest_information.clear()
                for assembly, quantity in quote.get_workorder().items():
                    self.quote_nest_information.setdefault(f"_/{assembly.name}.pdf", {
                        "quantity_multiplier": quantity,  # Sheet count
                        "gauge": "Null",
                        "material": "Null",
                        "sheet_dim": "0.000x0.000",
                        "scrap_percentage": 0.0,
                        "single_sheet_machining_time": 0.0,
                        "machining_time": 0.0
                    })
                    self.quote_nest_information.setdefault(f"{assembly.name}.pdf", {})
                    for item in assembly.items:
                        part_name = item.name
                        self.quote_nest_information[f"{assembly.name}.pdf"].setdefault(part_name, {})
                        for category in parts_in_inventory.data.keys():
                            for part in parts_in_inventory.data[category].keys():
                                if part == part_name:
                                    self.quote_nest_information[f"{assembly.name}.pdf"][part_name] = parts_in_inventory.get_data()[category].get(part_name)
                        if not self.quote_nest_information[f"{assembly.name}.pdf"][part_name]:
                            for category in inventory.data.keys():
                                for part in inventory.data[category].keys():
                                    if part == part_name:
                                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name] = inventory.get_data()[category].get(part_name)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name]["quantity"] = item.get_value('parts_per')
                        try:
                            self.quote_nest_information[f"{assembly.name}.pdf"][part_name]["notes"] += f"\n{item.get_value('notes')}"
                        except KeyError:
                            self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("notes", item.get_value('notes'))
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("flow_tag", item.get_value('flow_tag'))
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("machine_time", 0)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("weight", 0)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("part_number", 0)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("image_index", part_name)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("surface_area", 0)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("cutting_length", 0)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name]["file_name"] = f"{assembly.name}.pdf"
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("piercing_time", 0)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("piercing_points", 0)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("gauge", "Null")
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("material", "Null")
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("recut", False)
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("shelf_number", "")
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("sheet_dim", "Null")
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("part_dim", "Null")
                        self.quote_nest_information[f"{assembly.name}.pdf"][part_name].setdefault("geofile_name", 'Null')
                        sorted_keys = natsorted(self.quote_nest_information.keys())
                        sorted_dict = {key: self.quote_nest_information[key] for key in sorted_keys}
                        self.quote_nest_information = sorted_dict
                    self.download_required_images(self.quote_nest_information[f"{assembly.name}.pdf"])
                self.tabWidget.setCurrentIndex(self.get_menu_tab_order().index("OmniGen"))
                self.load_nests()
    # * /\ Dialogs /\

    # * \/ INVENTORY TABLE CHANGES \/
    # NOTE for Edit Inventory
    def edit_inventory_item_changes(self, item: QTableWidgetItem) -> None:
        tab = self.tabs[self.category]
        tab.blockSignals(False)
        row_index = item.row()
        col_index = item.column()
        item_name: str = tab.item(item.row(), 0).text()
        try:
            new_part_number: str = tab.item(item.row(), 1).text()
            old_part_number = self.get_value_from_category(item_name, "part_number")
            unit_quantity: float = float(sympy.sympify(tab.item(item.row(), 2).text().replace(" ", "").replace(",", ""), evaluate=True))
            current_quantity: float = float(sympy.sympify(tab.item(item.row(), 3).text().replace(" ", "").replace(",", ""), evaluate=True))
            old_current_quantity = self.get_value_from_category(item_name, "current_quantity")
            price: float = float(
                sympy.sympify(
                    tab.item(item.row(), 4).text().replace("$", "").replace("CAD", "").replace("USD", "").replace(" ", "").replace(",", ""),
                    evaluate=True,
                )
            )
            old_price = self.get_value_from_category(item_name, "price")
        except (ValueError, TypeError, SyntaxError) as e:
            print(e)
            item.setForeground(QColor("red"))
            self.status_button.setText(f"{item_name}: Enter a valid number, aborted!", "red")
            return
        # QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        if col_index == 1:  # Part Number
            inventory.change_object_in_object_item(self.category, item_name, "part_number", new_part_number)
            for category, items in inventory.get_data().items():
                if category == self.category:
                    continue
                for item, item_data in items.items():
                    if old_part_number == item_data.get("part_number"):
                        inventory.change_object_in_object_item(
                            object_name=category, item_name=item, value_name="part_number", new_value=new_part_number
                        )
        elif col_index == 2:  # Quantity per Unit
            inventory.change_object_in_object_item(self.category, item_name, "unit_quantity", unit_quantity)
            tab.blockSignals(False)
            unit_quantity_item = tab.item(item.row(), 2)
            tab.blockSignals(True)
            unit_quantity_item.setText(str(unit_quantity))
            self.update_stock_costs()
        elif col_index == 3:  # Quantity in Stock
            inventory.change_object_in_object_item(self.category, item_name, "current_quantity", current_quantity)
            modified_date: str = (
                f"{self.username} - Changed from {old_current_quantity} to {current_quantity} at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}"
            )

            tab.blockSignals(False)
            tab.item(row_index, col_index).setToolTip(modified_date)
            tab.blockSignals(True)
            inventory.change_object_in_object_item(self.category, item_name, "latest_change_current_quantity", modified_date)
            for category, items in inventory.get_data().items():
                if category == self.category:
                    continue
                for item, item_data in items.items():
                    if new_part_number == item_data.get("part_number"):
                        inventory.change_object_in_object_item(category, item, "latest_change_current_quantity", modified_date)
                        inventory.change_object_in_object_item(
                            object_name=category, item_name=item, value_name="current_quantity", new_value=current_quantity
                        )
            self.sort_inventory()
        elif col_index == 4:  # Item Price
            use_exchange_rate: bool = self.get_value_from_category(item_name=item_name, key="use_exchange_rate")
            modified_date: str = f"{self.username} - Changed from {old_price} to {price} at {datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}"
            converted_price: float = price * self.get_exchange_rate() if use_exchange_rate else price / self.get_exchange_rate()
            tab.blockSignals(False)
            price_item = tab.item(row_index, col_index)
            tab.blockSignals(True)
            price_item.setText(f'${price:,.2f} {"USD" if use_exchange_rate else "CAD"}')
            price_item.setToolTip(f'${converted_price:,.2f} {"CAD" if use_exchange_rate else "USD"}\n{modified_date}')
            inventory.change_object_in_object_item(self.category, item_name, "price", price)
            inventory.change_object_in_object_item(self.category, item_name, "latest_change_price", modified_date)
            self.update_stock_costs()
            for category, items in inventory.get_data().items():
                if category == self.category:
                    continue
                for item, item_data in items.items():
                    if new_part_number == item_data.get("part_number"):
                        inventory.change_object_in_object_item(object_name=category, item_name=item, value_name="price", new_value=price)
                        inventory.change_object_in_object_item(
                            object_name=category, item_name=item, value_name="latest_change_price", new_value=modified_date
                        )
        elif col_index == 9:  # Shelf Number
            tab.blockSignals(False)
            shelf_number = tab.item(row_index, col_index).text()
            tab.blockSignals(True)
            inventory.change_object_in_object_item(self.category, item_name, "shelf_number", shelf_number)
            for category, items in inventory.get_data().items():
                if category == self.category:
                    continue
                for item, item_data in items.items():
                    if new_part_number == item_data.get("part_number"):
                        inventory.change_object_in_object_item(category, item_name, "shelf_number", shelf_number)
        tab.blockSignals(False)
        if col_index != 3:
            self.sync_changes()
        # QApplication.restoreOverrideCursor()

    # NOTE for Parts in Inventory
    def parts_in_inventory_item_changes(self, item: QTableWidgetItem) -> None:
        category_data = parts_in_inventory.get_data()
        tab = self.tabs[self.category]
        tab.blockSignals(False)
        item_name: str = tab.item(item.row(), 0).text()
        row_index = item.row()
        column_index = item.column()
        try:
            item_price: float = float(sympy.sympify(tab.item(row_index, 1).text().replace("$", "").replace(" ", "").replace(",", ""), evaluate=True))
            unit_quantity: float = float(sympy.sympify(tab.item(row_index, 2).text().replace(",", ""), evaluate=True))
            current_quantity: float = float(sympy.sympify(tab.item(row_index, 3).text().replace(",", ""), evaluate=True))
            new_modified_date: str = (
                f'{self.username} - Manually set to {current_quantity} quantity at {str(datetime.now().strftime("%B %d %A %Y %I:%M:%S %p"))}'
            )
        except (ValueError, TypeError, SyntaxError) as e:
            item.setForeground(QColor("red"))
            self.status_button.setText(f"{item_name}: Enter a valid number, aborted!", "red")
            return

        item.setForeground(QColor("white"))

        if column_index == 1:
            price_item = tab.item(row_index, 1)
            tab.blockSignals(True)
            price_item.setText(f"${item_price:,.2f}")
        elif column_index == 5:
            shelf_item = tab.item(row_index, 5).text()
            tab.blockSignals(True)
            parts_in_inventory.change_object_in_object_item(self.category, item_name, "shelf_number", shelf_item)
        elif column_index == 3:
            notes_item = tab.item(row_index, 6)
            tab.blockSignals(True)
            notes_item.setText(new_modified_date)
            parts_in_inventory.change_object_in_object_item(self.category, item_name, "modified_date", new_modified_date)

        tab.blockSignals(False)

        for category in list(category_data.keys()):
            if category in ["Recut", self.category]:
                continue
            if item_name in list(parts_in_inventory.get_data()[category].keys()):
                parts_in_inventory.change_object_in_object_item(
                    object_name=category,
                    item_name=item_name,
                    value_name="current_quantity",
                    new_value=current_quantity,
                )
                parts_in_inventory.change_object_in_object_item(
                    object_name=category,
                    item_name=item_name,
                    value_name="modified_date",
                    new_value=new_modified_date,
                )
        parts_in_inventory.change_object_in_object_item(self.category, item_name, "unit_quantity", unit_quantity)
        parts_in_inventory.change_object_in_object_item(self.category, item_name, "price", item_price)
        parts_in_inventory.change_object_in_object_item(self.category, item_name, "current_quantity", current_quantity)

        self.calculate_parts_in_inventory_summary()
        self.sync_changes()
        self.load_active_tab()
        # QApplication.restoreOverrideCursor()

    # NOTE for Sheets in Inventory
    def sheets_in_inventory_item_changes(self, item: QTableWidgetItem) -> None:
        tab = self.tabs[self.category]
        tab.blockSignals(False)
        row_index: int = item.row()
        column_index: int = item.column()
        item_name: str = tab.item(row_index, 0).text()
        if self.category == "Price Per Pound":
            try:
                new_price: float = float(
                    sympy.sympify(tab.item(row_index, 1).text().replace("$", "").replace(" ", "").replace(",", ""), evaluate=True)
                )
            except (ValueError, TypeError, SyntaxError) as e:
                item.setForeground(QColor("red"))
                self.status_button.setText(f"{item_name}: Enter a valid number, aborted!", "red")
                tab.blockSignals(False)
                return
            price_item = tab.item(item.row(), 1)
            tab.blockSignals(True)
            price_item.setText(f"${new_price:,.2f}")
            tab.blockSignals(False)
            old_price = self.get_value_from_category(item_name, "price")
            modified_date: str = (
                f'{self.username} - Modified from ${old_price:,.2f} to ${new_price:,.2f} at {datetime.now().strftime("%B %d %A %Y %I:%M:%S %p")}'
            )
            price_of_steel_inventory.change_object_in_object_item(self.category, item_name, "price", new_price)
            price_of_steel_inventory.change_object_in_object_item(self.category, item_name, "latest_change_price", modified_date)
        else:
            try:
                new_quantity: float = float(sympy.sympify(tab.item(row_index, 2).text().replace(" ", "").replace(",", ""), evaluate=True))
            except (ValueError, TypeError, SyntaxError) as e:
                item.setForeground(QColor("red"))
                self.status_button.setText(f"{item_name}: Enter a valid number, aborted!", "red")
                return
            notes: str = tab.item(row_index, 6).text()
            old_quantity: float = self.get_value_from_category(item_name, "current_quantity")
            modified_date: str = (
                f"{self.username} - Manually set to {new_quantity} from {old_quantity} at {datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
            )
            red_quantity_limit: int = self.get_value_from_category(item_name, "red_limit")
            if red_quantity_limit is None:
                red_quantity_limit: int = 4
            if new_quantity > red_quantity_limit:
                price_of_steel_inventory.change_object_in_object_item(self.category, item_name, "has_sent_warning", False)
            price_of_steel_inventory.change_object_in_object_item(self.category, item_name, "notes", notes)
            price_of_steel_inventory.change_object_in_object_item(self.category, item_name, "current_quantity", new_quantity)
            price_of_steel_inventory.change_object_in_object_item(self.category, item_name, "latest_change_current_quantity", modified_date)
        tab.blockSignals(False)
        self.load_active_tab()
        self.sync_changes()
        # QApplication.restoreOverrideCursor()

    # NOTE for workspace
    def workspace_item_changed(self, item: QTableWidgetItem) -> None:
        pass

    # * /\ INVENTORY TABLE CHANGES /\

    # * \/ Load UI \/
    def load_history_view(self) -> None:
        """
        It loads the history view of the application.
        """
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
        """
        It loads the history view of the application.
        """
        # CATEOGRY HISTORY
        self.priceHistoryTable.clear()
        self.priceHistoryTable.setRowCount(0)
        self.priceHistoryTable.setHorizontalHeaderLabels(("Date;Part Name;Part #;Old Price;New Price").split(";"))
        self.priceHistoryTable.setColumnWidth(0, 270)
        self.priceHistoryTable.setColumnWidth(1, 600)
        price_history_file = PriceHistoryFile(file_name=f"{settings_file.get_value(item_name='price_history_file_name')}.xlsx")
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

    def load_tree_view(self, inventory: JsonFile):
        """
        > This function loads the inventory into the tree view

        Args:
          inventory: The inventory object that is being displayed.
        """
        self.clear_layout(self.search_layout)
        tree_view = ViewTree(data=inventory.get_data())
        self.search_layout.addWidget(tree_view, 0, 0)

    def load_categories(self) -> None:
        """
        It loads the categories from the inventory file and creates a tab for each category.
        """
        if (
            not self.trusted_user
            and self.tabWidget.tabText(self.tabWidget.currentIndex()) != "Sheets in Inventory"
            and self.tabWidget.tabText(self.tabWidget.currentIndex()) != "Parts in Inventory"
            and self.tabWidget.tabText(self.tabWidget.currentIndex()) != "View Inventory (Read Only)"
        ):
            # print(self.last_selected_menu_tab)
            # self.tabWidget.setCurrentIndex(settings_file.get_value('menu_tabs_order').index(self.last_selected_menu_tab))
            # self.show_not_trusted_user()

            self.set_layout_message("Insufficient Privileges, Access Denied", "", "", 0)
            return

        # No idea what this is supposed to do, but im too scared to delete it - Jared
        # JsonFile(file_name=f"data/{self.inventory_file_name}")
        # JsonFile(file_name=f"data/{self.inventory_file_name} - Price of Steel")
        # JsonFile(file_name=f"data/{self.inventory_file_name} - Parts in Inventory")
        workspace_tags.load_data()
        admin_workspace.load_data()
        user_workspace.load_data()
        # # QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) not in ["Edit Inventory", "Parts in Inventory", "Sheets in Inventory", "Workspace"]:
            return
        self.clear_layout(self.active_layout)
        self.tabs.clear()
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) != "Workspace":
            if self.active_json_file is None:
                return
            else:
                self.categories = self.active_json_file.get_keys()
        self.menuOpen_Category.clear()
        for i, category in enumerate(self.categories):
            action = QAction(self)
            action.setIcon(QIcon(f"icons/project_open.png"))
            action.triggered.connect(partial(self.quick_load_category, category))
            action.setText(category)
            self.menuOpen_Category.addAction(action)
        self.tab_widget = CustomTabWidget(self)
        # self.tab_widget.setStyleSheet("QTabBar::tab::disabled {width: 0; height: 0; margin: 0; padding: 0; border: none;} ")
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_category)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        i: int = -1
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            if self.trusted_user:
                edit_tabs = ["Staging", "Planning", "Editing", "Recut"]
            else:
                edit_tabs = ["Recut"]
            for i, category in enumerate(edit_tabs + workspace_tags.get_value("all_tags")):
                tab = QWidget(self)
                layout = QVBoxLayout(tab)
                tab.setLayout(layout)
                self.tabs[category] = tab
                self.tab_widget.addTab(tab, category)
        else:
            for i, category in enumerate(self.categories):
                tab = CustomTableWidget(self)
                if category == "Price Per Pound" and self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
                    self.pushButton_add_new_sheet.setEnabled(False)
                elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
                    self.pushButton_add_new_sheet.setEnabled(True)
                if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Edit Inventory":
                    tab.itemSelectionChanged.connect(partial(self.inventory_cell_changed, tab))
                    tab.itemChanged.connect(self.edit_inventory_item_changes)
                if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
                    tab.itemChanged.connect(self.sheets_in_inventory_item_changes)
                if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Parts in Inventory":
                    tab.itemSelectionChanged.connect(partial(self.parts_in_inventory_cell_changed, tab))
                    tab.itemChanged.connect(self.parts_in_inventory_item_changes)
                self.tabs[category] = tab
                self.tab_widget.addTab(tab, category)

        if i == -1:
            tab = QScrollArea(self)
            content_widget = QWidget()
            content_widget.setObjectName("tab")
            tab.setWidget(content_widget)
            tab.setWidgetResizable(True)
            layout = QVBoxLayout(content_widget)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            try:
                self.tabs[category] = layout
            except UnboundLocalError:
                return
            self.tab_widget.addTab(tab, "")
            i += 1
        with contextlib.suppress(Exception):
            self.tab_widget.set_tab_order(category_tabs_order.get_value(self.tabWidget.tabText(self.tabWidget.currentIndex())))
        self.tab_widget.setCurrentIndex(settings_file.get_value("last_category_tab"))
        self.tab_widget.currentChanged.connect(self.load_active_tab)
        self.active_layout.addWidget(self.tab_widget)
        self.update_category_total_stock_costs()
        self.update_all_parts_in_inventory_price()
        self.calculate_parts_in_inventory_summary()
        self.load_active_tab()

    def load_active_tab(self) -> None:
        """
        It loads the data from the inventory file and displays it in the GUI

        Returns:
          The return value is a list of QWidget objects.
        """
        try:
            self.category = self.tab_widget.tabText(self.tab_widget.currentIndex())
        except AttributeError:
            return
        self.po_buttons.clear()
        self.pushButton_create_new.setEnabled(True)
        self.radioButton_category.setEnabled(True)
        self.radioButton_single.setEnabled(True)

        try:
            self.clear_layout(self.tabs[self.category])
        except (IndexError, KeyError):
            return
        settings_file.add_item("last_category_tab", self.tab_widget.currentIndex())
        tab: CustomTableWidget = self.tabs[self.category]
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) != "Workspace":
            try:
                category_data = self.active_json_file.get_value(item_name=self.category)
            except AttributeError:
                return
            if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Edit Inventory":
                autofill_search_options = natsorted(list(set(self.get_all_part_names() + self.get_all_part_numbers())))
                completer = QCompleter(autofill_search_options, self)
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                self.lineEdit_search_items.setCompleter(completer)
            if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Parts in Inventory":
                autofill_search_options = natsorted(
                    list(set(parts_in_inventory.get_value(self.tab_widget.tabText(self.tab_widget.currentIndex())).keys()))
                )
                completer = QCompleter(autofill_search_options, self)
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                self.lineEdit_search_parts_in_inventory.setCompleter(completer)

            self.update_edit_inventory_list_widget()
            self.update_category_total_stock_costs()
            self.calculuate_price_of_steel_summary()
            self.label_category_name.setText(f"Category: {self.category}")
            self.quantities_change()
            try:
                if not list(category_data.keys()):
                    self.pushButton_create_new.setEnabled(True)
                    self.pushButton_add_quantity.setEnabled(False)
                    self.pushButton_remove_quantity.setEnabled(False)
                    self.radioButton_category.setEnabled(False)
                    self.radioButton_single.setEnabled(False)
                    # # QApplication.restoreOverrideCursor()
                    return
            except AttributeError:
                self.set_layout_message("You need to", "create", "a category", 120, self.create_new_category)
                self.pushButton_create_new.setEnabled(False)
                self.pushButton_add_quantity.setEnabled(False)
                self.pushButton_remove_quantity.setEnabled(False)
                self.radioButton_category.setEnabled(False)
                self.radioButton_single.setEnabled(False)
                # # QApplication.restoreOverrideCursor()
                return

            if self.category == "Price Per Pound" and self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
                self.pushButton_add_new_sheet.setEnabled(False)
            elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
                self.pushButton_add_new_sheet.setEnabled(True)
            if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Edit Inventory":
                self.load_inventory_items(tab, category_data)
            elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
                self.price_of_steel_item(tab, category_data)
            elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Parts in Inventory":
                self.load_inventory_parts(tab, category_data)

            self.scroll_position_manager.restore_scroll_position(
                tab_name=f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} {self.category}", scroll=tab
            )

            def save_scroll_position(tab_name: str, tab: CustomTableWidget):
                self.scroll_position_manager.save_scroll_position(tab_name=tab_name, scroll=tab)

            tab.verticalScrollBar().valueChanged.connect(
                partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} {self.category}", tab)
            )
            tab.horizontalScrollBar().valueChanged.connect(
                partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} {self.category}", tab)
            )
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            self.load_workspace()
        with contextlib.suppress(IndexError):
            category_tabs_order.set_value(
                self.tabWidget.tabText(self.tabWidget.currentIndex()),
                value=self.tabWidget.currentWidget().findChildren(CustomTabWidget)[0].get_tab_order(),
            )

    # NOTE PARTS IN INVENTYORY
    def load_inventory_parts(self, tab: CustomTableWidget, category_data: dict) -> None:
        """
        This function loads inventory parts data into a custom table widget in a graphical user
        interface.

        Args:
          tab (CustomTableWidget): The tab parameter is a CustomTableWidget object, which is a custom
        widget used to display data in a table format.
          category_data (dict): A dictionary containing data for items in a specific category. The keys
        of the dictionary are the names of the items, and the values are dictionaries containing various
        information about the item such as its current quantity, unit quantity, price, modified date,
        and limits for quantity levels.
        """
        tab.blockSignals(True)
        tab.set_editable_column_index([2, 3, 5])
        tab.setEnabled(False)
        tab.clear()
        tab.setShowGrid(True)
        tab.setRowCount(0)
        tab.setSortingEnabled(False)
        tab.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tab.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        tab.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        tab.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        headers: list[str] = ["Part Name", "Item Price", "Quantity Per Unit", "Quantity in Stock", "Cost in Stock", "Shelf #", "Modified Date", "DEL"]
        tab.setColumnCount(len(headers))
        tab.setHorizontalHeaderLabels(headers)
        grouped_data = parts_in_inventory.sort_by_multiple_tags(category=category_data, tags_ids=["material", "gauge"])
        row_index: int = 0

        try:
            materials: list[QPushButton] = self.parts_in_ineventory_filter["materials"]
            thicknesses: list[QPushButton] = self.parts_in_ineventory_filter["thicknesses"]
        except KeyError:  # This is because loading runs before the filter system is loaded.
            self.load_parts_in_inventory_filter_tab()
            self.load_inventory_parts(tab, category_data)
            return

        for group in list(grouped_data.keys()):
            group_material = group.split(";")[0]
            group_thickness = group.split(";")[1]
            group_name = group.replace(";", " ")

            if selected_materials := [button.text() for button in materials if button.isChecked()]:
                if group_material not in selected_materials:
                    continue

            if selected_thicknesses := [button.text() for button in thicknesses if button.isChecked()]:
                if group_thickness not in selected_thicknesses:
                    continue

            # We check to see if there are any items to show, if not, we dont loop through the group data
            for item in list(grouped_data[group].keys()):
                if self.lineEdit_search_parts_in_inventory.text() in item:
                    break
            else:
                continue

            tab.insertRow(row_index)
            item = QTableWidgetItem(group_name)
            item.setTextAlignment(4)  # Align text center
            font = QFont()
            font.setPointSize(15)
            item.setFont(font)
            tab.setItem(row_index, 0, item)
            tab.setSpan(row_index, 0, 1, tab.columnCount())
            self.set_table_row_color(tab, row_index, "#292929")
            row_index += 1
            for item in list(grouped_data[group].keys()):
                if self.lineEdit_search_parts_in_inventory.text() not in item:
                    continue
                item_material: str = self.get_value_from_category(item_name=item, key="material")
                item_thickness: str = self.get_value_from_category(item_name=item, key="gauge")
                shelf_number: str = self.get_value_from_category(item_name=item, key="shelf_number")
                if shelf_number == None:
                    shelf_number = ""

                if selected_materials := [button.text() for button in materials if button.isChecked()]:
                    if item_material not in selected_materials:
                        continue

                if selected_thicknesses := [button.text() for button in thicknesses if button.isChecked()]:
                    if item_thickness not in selected_thicknesses:
                        continue

                col_index: int = 0
                tab.insertRow(row_index)
                tab.setRowHeight(row_index, 40)

                current_quantity: int = self.get_value_from_category(item_name=item, key="current_quantity")
                unit_quantity: int = self.get_value_from_category(item_name=item, key="unit_quantity")
                price: float = self.get_value_from_category(item_name=item, key="price")

                if self.category not in ["Recut", "Custom"]:
                    weight: float = self.get_value_from_category(item_name=item, key="weight")
                    machine_time: float = self.get_value_from_category(item_name=item, key="machine_time")
                    material: str = self.get_value_from_category(item_name=item, key="material")
                    price_per_pound: float = price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"]
                    cost_for_laser: float = self.get_nitrogen_laser_cost() if material in {"304 SS", "409 SS", "Aluminium"} else self.get_co2_laser_cost()
                    price = float((machine_time * (cost_for_laser / 60)) + (weight * price_per_pound))

                modified_date: str = self.get_value_from_category(item_name=item, key="modified_date")
                red_limit: float = self.get_value_from_category(item_name=item, key="red_limit")
                if red_limit is None:
                    red_limit = 2
                yellow_limit: float = self.get_value_from_category(item_name=item, key="yellow_limit")
                if yellow_limit is None:
                    yellow_limit = 5
                tab.setItem(row_index, col_index, QTableWidgetItem(f"{item}"))
                tab.item(row_index, col_index).setFont(self.tables_font)

                col_index += 1
                # PRICE
                tab.setItem(row_index, col_index, QTableWidgetItem(f"${price:,.2f}"))
                tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                tab.item(row_index, col_index).setFont(self.tables_font)

                col_index += 1
                # UNIT QUANTITY
                tab.setItem(row_index, col_index, QTableWidgetItem(f"{unit_quantity}"))
                tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                tab.item(row_index, col_index).setFont(self.tables_font)

                col_index += 1
                # QUANTITY
                tab.setItem(row_index, col_index, QTableWidgetItem(f"{current_quantity}"))
                tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                tab.item(row_index, col_index).setFont(self.tables_font)

                col_index += 1
                # TOTAL COST
                tab.setItem(
                    row_index,
                    col_index,
                    QTableWidgetItem(f"${(price*current_quantity):,.2f}"),
                )
                tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                tab.item(row_index, col_index).setFont(self.tables_font)

                col_index += 1
                # SHELF NUMBER
                tab.setItem(row_index, col_index, QTableWidgetItem(shelf_number))
                tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                tab.item(row_index, col_index).setFont(self.tables_font)

                col_index += 1
                # MODFIED DATE
                tab.setItem(row_index, col_index, QTableWidgetItem(modified_date))
                tab.item(row_index, col_index).setFont(self.tables_font)

                col_index += 1
                # DELETE
                btn_delete = DeletePushButton(
                    parent=self,
                    tool_tip=f"Delete {item} permanently from {self.category}",
                    icon=QIcon(f"icons/trash.png"),
                )
                btn_delete.setStyleSheet("margin-top: 3%; margin-bottom: 3%; margin-left: 10%; margin-right: 10%;")
                btn_delete.clicked.connect(partial(self.delete_item, item))
                tab.setCellWidget(row_index, col_index, btn_delete)
                if self.category != "Recut":
                    if current_quantity <= red_limit:
                        self.set_table_row_color(tab, row_index, "#3F1E25")
                    elif current_quantity <= yellow_limit:
                        self.set_table_row_color(tab, row_index, "#413C28")
                row_index += 1
        tab.setEnabled(True)
        tab.resizeColumnsToContents()
        if tab.rowCount() == 0:
            tab.insertRow(0)
            tab.setItem(0, 0, QTableWidgetItem("Nothing to show"))
            tab.item(0, 0).setFont(self.tables_font)
            tab.resizeColumnsToContents()
            return
        if tab.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
            tab.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            menu = QMenu(self)
            action = QAction(self)
            action.setText("View Parts Data")
            action.triggered.connect(partial(self.view_part_information, tab))
            menu.addAction(action)
            menu.addSeparator()
            action = QAction(self)
            if self.category != "Recut":
                action.setText("Set Custom Quantity Limit")
                action.triggered.connect(partial(self.set_custom_quantity_limit, tab))
                menu.addAction(action)
                menu.addSeparator()
            categories = QMenu(menu)
            categories.setTitle("Move selected parts to category")
            for i, category in enumerate(parts_in_inventory.get_keys()):
                if self.category == category or category == "Recut":
                    continue
                if i == 1:
                    categories.addSeparator()
                action = QAction(self)
                action.setText(category)
                action.triggered.connect(partial(self.move_to_category, tab, category))
                categories.addAction(action)
            menu.addMenu(categories)

            categories = QMenu(menu)
            categories.setTitle("Copy selected parts to category")
            for i, category in enumerate(parts_in_inventory.get_keys()):
                if self.category == category or category == "Recut":
                    continue
                if i == 1:
                    categories.addSeparator()
                action = QAction(self)
                action.setText(category)
                action.triggered.connect(partial(self.copy_to_category, tab, category))
                categories.addAction(action)
            menu.addMenu(categories)
            action = QAction(self)
            action.setText("Delete selected parts")
            action.triggered.connect(partial(self.delete_selected_items, tab))
            menu.addAction(action)
            action = QAction(self)
            action.setText("Set selected parts to zero quantity")
            action.triggered.connect(partial(self.reset_selected_parts_quantity, tab))
            menu.addAction(action)
            menu.addSeparator()
            if self.category != "Recut":
                action1 = QAction(self)
                action1.setText("Generate Quote with Selected Parts")
                action1.triggered.connect(partial(self.generate_quote_with_selected_parts, tab))
                menu.addAction(action1)
                action2 = QAction(self)
                action2.setText("Add Selected Parts to Quote")
                action2.triggered.connect(partial(self.add_selected_parts_to_quote, tab))
                menu.addAction(action2)
            tab.customContextMenuRequested.connect(partial(self.open_group_menu, menu))
        tab.blockSignals(False)
        # QApplication.restoreOverrideCursor()

    # NOTE SHEETS IN INVENTORY
    def price_of_steel_item(self, tab: CustomTableWidget, category_data: dict) -> None:
        """
        This function takes a QVBoxLayout, an int, and a dict and returns None.

        Args:
          tab (QVBoxLayout): QVBoxLayout
          category_data (dict): dict = {
        """
        tab.blockSignals(True)
        tab.setEnabled(False)
        tab.clear()
        tab.setShowGrid(True)
        tab.setRowCount(0)
        tab.setSortingEnabled(False)
        tab.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tab.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        tab.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        tab.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        # QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        row_index: int = 0
        if self.category == "Price Per Pound":
            headers: list[str] = ["Material", "Price", "Modified Date"]
            tab.setColumnCount(len(headers))
            tab.setHorizontalHeaderLabels(headers)
            tab.horizontalHeader().setStretchLastSection(True)
            tab.set_editable_column_index([1])
            for material in list(price_of_steel_inventory.get_data()[self.category].keys()):
                tab.insertRow(row_index)
                tab.setRowHeight(row_index, 40)
                price = self.get_value_from_category(item_name=material, key="price")
                latest_change_price = self.get_value_from_category(item_name=material, key="latest_change_price").replace("\n", " ")
                # SHEET NAME
                tab.setItem(row_index, 0, QTableWidgetItem(material))
                tab.item(row_index, 0).setFont(self.tables_font)
                # PRICE
                tab.setItem(row_index, 1, QTableWidgetItem(f"${price:,.2f}"))
                tab.item(row_index, 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                tab.item(row_index, 1).setFont(self.tables_font)
                # MODIFIED DATE
                tab.setItem(row_index, 2, QTableWidgetItem(latest_change_price))
                tab.item(row_index, 2).setFont(self.tables_font)
                row_index += 1
        else:
            headers: list[str] = [
                "Sheet Name",
                "Cost per Sheet",
                "Quantity\nin Stock",
                "Total Cost in Stock",
                "Order Status",
                "Set Arrival Time",
                "Notes",
                "Modified Date",
                "DEL",
            ]
            tab.setColumnCount(len(headers))
            tab.setHorizontalHeaderLabels(headers)
            tab.set_editable_column_index([2, 6])
            grouped_data = price_of_steel_inventory.sort_by_groups(category=category_data, groups_id="material")
            for group in list(grouped_data.keys()):
                tab.insertRow(row_index)
                item = QTableWidgetItem(group)
                item.setTextAlignment(4)  # Align text center

                font = QFont()
                font.setPointSize(15)
                item.setFont(font)
                tab.setItem(row_index, 0, item)
                tab.setSpan(row_index, 0, 1, tab.columnCount())
                self.set_table_row_color(tab, row_index, "#292929")
                row_index += 1
                for item in list(grouped_data[group].keys()):
                    col_index: int = 0
                    tab.insertRow(row_index)
                    current_quantity: float = self.get_value_from_category(item_name=item, key="current_quantity")
                    notes: str = self.get_value_from_category(item_name=item, key="notes")
                    modified_date: str = self.get_value_from_category(item_name=item, key="latest_change_current_quantity").replace("\n", " ")
                    thickness: str = self.get_value_from_category(item_name=item, key="thickness")
                    material: str = self.get_value_from_category(item_name=item, key="material")
                    sheet_dimension: str = self.get_value_from_category(item_name=item, key="sheet_dimension").replace(" x ", "x")
                    # POUNDS PER SQUARE FOOT
                    try:
                        pounds_per_square_foot: float = float(price_of_steel_information.get_data()["pounds_per_square_foot"][material][thickness])
                    except KeyError:
                        pounds_per_square_foot: float = 0.0
                    # POUNDS PER SHEET
                    try:
                        sheet_length = float(sheet_dimension.split("x")[0])
                        sheet_width = float(sheet_dimension.split("x")[1])
                    except AttributeError:
                        return
                    try:
                        pounds_per_sheet: float = ((sheet_length * sheet_width) / 144) * pounds_per_square_foot
                    except ZeroDivisionError:
                        pounds_per_sheet = 0.0
                    # PRICE PER POUND
                    try:
                        price_per_pound: float = float(price_of_steel_inventory.get_data()["Price Per Pound"][material]["price"])
                    except KeyError:
                        price_per_pound: float = 0.0

                    red_limit: float = self.get_value_from_category(item_name=item, key="red_limit")
                    if red_limit is None:
                        red_limit = 4
                    yellow_limit: float = self.get_value_from_category(item_name=item, key="yellow_limit")
                    if yellow_limit is None:
                        yellow_limit = 10

                    is_order_pending = self.get_value_from_category(item_name=item, key="is_order_pending")
                    if is_order_pending is None:
                        is_order_pending = False

                    # COST PER SHEET
                    cost_per_sheet = pounds_per_sheet * price_per_pound

                    # TOTAL COST
                    total_cost = cost_per_sheet * current_quantity

                    # ITEM
                    tab.setItem(row_index, col_index, QTableWidgetItem(item))
                    tab.item(row_index, col_index).setFont(self.tables_font)
                    col_index += 1
                    # COST
                    tab.setItem(row_index, col_index, QTableWidgetItem(f"${cost_per_sheet:,.2f}"))
                    tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    tab.item(row_index, col_index).setFont(self.tables_font)
                    col_index += 1
                    # CURRENT QUANTITY
                    tab.setItem(row_index, col_index, QTableWidgetItem(str(current_quantity)))
                    tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    tab.item(row_index, col_index).setFont(self.tables_font)
                    col_index += 1
                    # COST IN STOCK
                    tab.setItem(row_index, col_index, QTableWidgetItem(f"${total_cost:,.2f}"))
                    tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    tab.item(row_index, col_index).setFont(self.tables_font)
                    col_index += 1
                    # ORDER STATUS
                    order_status_button = OrderStatusButton()
                    order_status_button.setChecked(is_order_pending)
                    order_status_button.clicked.connect(partial(self.order_status_button_sheets_in_inventory, item, order_status_button, row_index))
                    order_status_button.setStyleSheet("margin-top: 3%; margin-bottom: 3%; margin-left: 5%; margin-right: 5%;")
                    tab.setCellWidget(row_index, col_index, order_status_button)
                    col_index += 1
                    if is_order_pending:
                        with contextlib.suppress(AttributeError):
                            arrival_date = QDateEdit()
                            expected_arrival_time: str = self.get_value_from_category(item_name=item, key="expected_arrival_time")
                            order_quantity: float = self.get_value_from_category(item_name=item, key="order_pending_quantity")
                            order_status_button.setText(f"Order Pending ({int(order_quantity)})")
                            year, month, day = map(int, expected_arrival_time.split("-"))
                            date = QDate(year, month, day)
                            arrival_date.setDate(date)
                            arrival_date.setCalendarPopup(True)
                            arrival_date.dateChanged.connect(partial(self.arrival_date_change_sheets_in_inventory, item, arrival_date))
                            tab.setCellWidget(row_index, col_index, arrival_date)
                        order_pending_date: str = self.get_value_from_category(item_name=item, key="order_pending_date")
                        order_status_button.setToolTip(f"Order Pending was set at {order_pending_date} for {order_quantity} sheets")

                    col_index += 1
                    # NOTES
                    tab.setItem(row_index, col_index, QTableWidgetItem(notes))
                    tab.item(row_index, col_index).setFont(self.tables_font)
                    col_index += 1
                    # MODIFIED DATE
                    tab.setItem(row_index, col_index, QTableWidgetItem(modified_date))
                    tab.item(row_index, col_index).setFont(self.tables_font)
                    col_index += 1

                    # DELETE
                    btn_delete = DeletePushButton(
                        parent=self,
                        tool_tip=f"Delete {item} permanently from {self.category}",
                        icon=QIcon(f"icons/trash.png"),
                    )
                    # btn_delete.setFixedSize(26, 26)
                    btn_delete.clicked.connect(partial(self.delete_item, item))
                    btn_delete.setStyleSheet("margin-top: 3%; margin-bottom: 3%; margin-left: 10%; margin-right: 10%;")
                    tab.setCellWidget(row_index, col_index, btn_delete)
                    if current_quantity <= red_limit:
                        self.set_table_row_color(tab, row_index, "#3F1E25")
                    elif current_quantity <= yellow_limit:
                        self.set_table_row_color(tab, row_index, "#413C28")
                    if is_order_pending:
                        self.set_table_row_color(tab, row_index, "#29422c")
                    row_index += 1

        tab.setEnabled(True)
        tab.resizeColumnsToContents()
        tab.blockSignals(False)
        if self.category == "Price Per Pound":
            tab.setColumnWidth(1, 200)
        else:
            tab.setColumnWidth(5, 100)
            tab.setColumnWidth(6, 200)
        if tab.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
            tab.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            menu = QMenu(self)
            action = QAction(self)
            action.triggered.connect(partial(self.set_custom_quantity_limit, tab))
            action.setText("Set Custom Quantity Limit")
            menu.addAction(action)
            tab.customContextMenuRequested.connect(partial(self.open_group_menu, menu))
        # QApplication.restoreOverrideCursor()

    # NOTE EDIT INVENTORY
    def load_inventory_items(self, tab: CustomTableWidget, category_data: dict) -> None:
        """
        This function loads data into a QTableWidget for a specific category.

        Args:
          tab (QTableWidget): The QTableWidget object that is being loaded with data.
          category_data (dict): The `category_data` parameter is a dictionary containing information
        about the items in a particular category. The keys of the dictionary are the names of the items,
        and the values are dictionaries containing various information about each item, such as its part
        number, current quantity, price, priority, and notes. This
        """
        tab.blockSignals(True)
        tab.setEnabled(False)
        tab.clear()
        tab.setShowGrid(True)
        # tab.setAlternatingRowColors(True)
        tab.setRowCount(0)
        tab.setSortingEnabled(False)
        tab.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tab.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        tab.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        tab.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tab.set_editable_column_index([1, 2, 3, 4, 9])
        headers: list[str] = [
            "Part Name",
            "Part Number",
            "Quantity Per Unit",
            "Quantity in Stock",
            "Item Price",
            "USD/CAD",
            "Total Cost in Stock",
            "Total Unit Cost",
            "Priority",
            "Shelf #",
            "Notes",
            "Order Status",
            "Set Arrival Time",
            "PO",
            "DEL",
        ]
        tab.setColumnCount(len(headers))
        tab.setHorizontalHeaderLabels(headers)
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)

        # else:
        po_menu = QMenu(self)
        for po in get_all_po():
            po_menu.addAction(po, partial(self.open_po, po))
        for row_index in range(len(list(category_data.keys()))):
            item = list(category_data.keys())[row_index]

            part_number: str = self.get_value_from_category(item_name=item, key="part_number")
            self.get_value_from_category(item_name=item, key="group")

            current_quantity: float = float(self.get_value_from_category(item_name=item, key="current_quantity"))

            unit_quantity: float = float(self.get_value_from_category(item_name=item, key="unit_quantity"))
            priority: int = self.get_value_from_category(item_name=item, key="priority")
            price: float = self.get_value_from_category(item_name=item, key="price")
            notes: str = self.get_value_from_category(item_name=item, key="notes")
            shelf_number: str = "" if self.get_value_from_category(item_name=item, key="shelf_number") == None else self.get_value_from_category(item_name=item, key="shelf_number")
            use_exchange_rate: bool = self.get_value_from_category(item_name=item, key="use_exchange_rate")
            converted_price: float = price * self.get_exchange_rate() if use_exchange_rate else price / self.get_exchange_rate()
            exchange_rate: float = self.get_exchange_rate() if use_exchange_rate else 1
            total_cost_in_stock: float = current_quantity * price * exchange_rate
            total_cost_in_stock = max(total_cost_in_stock, 0)
            total_unit_cost: float = unit_quantity * price * exchange_rate
            is_order_pending = self.get_value_from_category(item_name=item, key="is_order_pending")
            if is_order_pending is None:
                is_order_pending = False
            self.get_value_from_category(item_name=item, key="latest_change_part_number")
            # latest_change_unit_quantity: str = self.get_value_from_category(item_name=item, key="latest_change_unit_quantity")
            latest_change_current_quantity = self.get_value_from_category(item_name=item, key="latest_change_current_quantity")
            latest_change_price: str = self.get_value_from_category(item_name=item, key="latest_change_price")
            # latest_change_use_exchange_rate: str = self.get_value_from_category(item_name=item, key="latest_change_use_exchange_rate")
            # latest_change_priority: str = self.get_value_from_category(item_name=item, key="latest_change_priority")
            # latest_change_notes: str = self.get_value_from_category(item_name=item, key="latest_change_notes")
            self.get_value_from_category(item_name=item, key="latest_change_name")

            red_limit: float = self.get_value_from_category(item_name=item, key="red_limit")
            if red_limit is None:
                red_limit = 10
            yellow_limit: float = self.get_value_from_category(item_name=item, key="yellow_limit")
            if yellow_limit is None:
                yellow_limit = 20

            col_index: int = 0

            tab.insertRow(row_index)
            tab.setRowHeight(row_index, 60)

            # PART NAME
            table_item = QTableWidgetItem(item)
            table_item.setFont(self.tables_font)
            tab.setItem(row_index, col_index, table_item)
            tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            tab.item(row_index, col_index).setToolTip(item)

            col_index += 1

            # PART NUMBER
            tab.setItem(row_index, col_index, QTableWidgetItem(part_number))
            tab.item(row_index, col_index).setFont(self.tables_font)
            tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            col_index += 1

            # UNIT QUANTITY
            tab.setItem(row_index, col_index, QTableWidgetItem(str(unit_quantity)))
            tab.item(row_index, col_index).setFont(self.tables_font)
            tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            col_index += 1

            # ITEM QUANTITY
            tab.setItem(row_index, col_index, QTableWidgetItem(str(current_quantity)))
            tab.item(row_index, col_index).setFont(self.tables_font)
            tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            tab.item(row_index, col_index).setToolTip(latest_change_current_quantity)

            col_index += 1

            # PRICE
            tab.setItem(row_index, col_index, QTableWidgetItem(f'${price:,.2f} {"USD" if use_exchange_rate else "CAD"}'))
            tab.item(row_index, col_index).setFont(self.tables_font)
            tab.item(row_index, col_index).setToolTip(f'${converted_price:,.2f} {"CAD" if use_exchange_rate else "USD"}\n{latest_change_price}')
            tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            col_index += 1

            # EXCHANGE RATE
            combo_exchange_rate = ExchangeRateComboBox(
                parent=self,
                selected_item="USD" if use_exchange_rate else "CAD",
            )
            combo_exchange_rate.currentIndexChanged.connect(
                partial(
                    self.use_exchange_rate_change,
                    item,
                    "use_exchange_rate",
                    combo_exchange_rate,
                )
            )
            combo_exchange_rate.setStyleSheet(self.margin_format)
            # layout.addWidget(combo_exchange_rate)
            tab.setCellWidget(row_index, col_index, combo_exchange_rate)

            col_index += 1

            # TOTAL COST
            tab.setItem(row_index, col_index, QTableWidgetItem(f"${total_cost_in_stock:,.2f} {combo_exchange_rate.currentText()}"))
            tab.item(row_index, col_index).setFont(self.tables_font)
            tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            col_index += 1

            # TOTAL UNIT COST
            tab.setItem(row_index, col_index, QTableWidgetItem(f"${total_unit_cost:,.2f} {combo_exchange_rate.currentText()}"))
            tab.item(row_index, col_index).setFont(self.tables_font)
            tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            col_index += 1

            # PRIORITY
            combo_priority = PriorityComboBox(parent=self, selected_item=priority)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)  # Adjust the blur radius as desired
            shadow.setOffset(0, 0)  # Set the shadow offset (x, y)
            if combo_priority.currentText() == "Medium":
                combo_priority.setStyleSheet(f"color: yellow; border-color: gold; background-color: #413C28;{self.margin_format}")
                shadow.setColor(QColor(255, 215, 0))
            elif combo_priority.currentText() == "High":
                combo_priority.setStyleSheet(f"color: red; border-color: darkred; background-color: #3F1E25;{self.margin_format}")
                shadow.setColor(QColor(139, 0, 0))
            else:
                combo_priority.setStyleSheet(self.margin_format)
                shadow.setColor(QColor(0, 0, 0, 255))
            # combo_priority.setGraphicsEffect(shadow)
            combo_priority.currentIndexChanged.connect(
                partial(
                    self.priority_change,
                    item,
                    "priority",
                    combo_priority,
                )
            )
            tab.setCellWidget(row_index, col_index, combo_priority)

            col_index += 1
            # SHELF NUMBER
            tab.setItem(row_index, col_index, QTableWidgetItem(shelf_number))
            tab.item(row_index, col_index).setFont(self.tables_font)
            tab.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            col_index += 1
            # NOTES
            text_notes = NotesPlainTextEdit(self, notes, "")
            text_notes.textChanged.connect(partial(self.notes_changed, item, "notes", text_notes))
            tab.setCellWidget(row_index, col_index, text_notes)
            col_index += 1

            # ORDER STATUS
            order_status_button = OrderStatusButton()
            order_status_button.setChecked(is_order_pending)
            order_status_button.clicked.connect(partial(self.order_status_button_edit_inventory, item, order_status_button, row_index))
            order_status_button.setStyleSheet("margin-top: 3%; margin-bottom: 3%; margin-left: 5%; margin-right: 5%;")
            tab.setCellWidget(row_index, col_index, order_status_button)
            col_index += 1
            if is_order_pending:
                with contextlib.suppress(AttributeError):
                    arrival_date = QDateEdit()
                    expected_arrival_time: str = self.get_value_from_category(item_name=item, key="expected_arrival_time")
                    order_quantity: float = self.get_value_from_category(item_name=item, key="order_pending_quantity")
                    order_status_button.setText(f"Order Pending ({int(order_quantity)})")
                    year, month, day = map(int, expected_arrival_time.split("-"))
                    date = QDate(year, month, day)
                    arrival_date.setDate(date)
                    arrival_date.setCalendarPopup(True)
                    arrival_date.dateChanged.connect(partial(self.arrival_date_change_edit_inventory, item, arrival_date))
                    tab.setCellWidget(row_index, col_index, arrival_date)
                order_pending_date: str = self.get_value_from_category(item_name=item, key="order_pending_date")
                order_status_button.setToolTip(f"Order Pending was set at {order_pending_date} for {order_quantity} items")

            col_index += 1
            # PURCHASE ORDER
            btn_po = POPushButton(parent=self)
            btn_po.setMenu(po_menu)
            btn_po.setStyleSheet(f"{self.margin_format} background-color: rgba(65, 65, 65, 150); border: none;")
            tab.setCellWidget(row_index, col_index, btn_po)
            self.po_buttons.append(btn_po)

            col_index += 1

            # DELETE
            btn_delete = DeletePushButton(
                parent=self,
                tool_tip=f"Delete {item} permanently from {self.category}",
                icon=QIcon(f"icons/trash.png"),
            )
            btn_delete.clicked.connect(partial(self.delete_item, item))
            btn_delete.setStyleSheet(self.margin_format)
            tab.setCellWidget(row_index, col_index, btn_delete)
            if current_quantity <= red_limit:
                self.set_table_row_color(tab, row_index, "#3F1E25")
            elif current_quantity <= yellow_limit:
                self.set_table_row_color(tab, row_index, "#413C28")
            if is_order_pending:
                self.set_table_row_color(tab, row_index, "#29422c")

        self.update_stock_costs()
        # set context menu
        if tab.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
            tab.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            menu = QMenu(self)
            action = QAction(self)
            action.triggered.connect(partial(self.set_custom_quantity_limit, tab))
            action.setText("Set Custom Quantity Limit")
            menu.addAction(action)
            menu.addSeparator()
            action = QAction(self)
            action.triggered.connect(partial(self.name_change, tab))
            action.setText("Change part name")
            menu.addAction(action)
            tab.customContextMenuRequested.connect(partial(self.open_group_menu, menu))
        tab.resizeColumnsToContents()
        tab.setColumnWidth(0, 250)
        tab.setColumnWidth(1, 150)
        tab.setEnabled(True)
        tab.blockSignals(False)
        with contextlib.suppress(Exception):
            # self.last_item_selected_index = list(category_data.keys()).index(self.last_item_selected_name)
            tab.scrollTo(tab.model().index(self.last_item_selected_index, 0))
            tab.selectRow(self.last_item_selected_index)
            # self.listWidget_itemnames.setCurrentRow(self.last_item_selected_index)
        QApplication.restoreOverrideCursor()

    # STAGING/EDITING
    def assembly_items_table_clicked(self, item: QTableWidgetItem) -> None:
        """
        The function assigns the text of the clicked item in an assembly items table to a variable.

        Args:
          item (QTableWidgetItem): The parameter "item" is of type QTableWidgetItem. It represents the
        item that was clicked in the assembly items table.
        """
        self.last_selected_assemly_item = item.text()

    # STAGING/EDITING
    def assembly_items_table_cell_changed(self, table: CustomTableWidget, assembly: Assembly, item: QTableWidgetItem) -> None:
        """
        The function `assembly_items_table_cell_changed` handles changes made to cells in a table,
        specifically for an assembly item table, and updates the corresponding assembly item and saves
        the changes.

        Args:
          table (CustomTableWidget): The `table` parameter is a `CustomTableWidget` object, which
        represents a custom table widget in the user interface.
          assembly (Assembly): The "assembly" parameter is an instance of the Assembly class, which
        represents a collection of items. It contains methods and attributes related to managing and
        manipulating the items in the assembly.
          item (QTableWidgetItem): The `item` parameter is a QTableWidgetItem object that represents the
        cell that was changed in the table.

        Returns:
          In the code snippet provided, the function `assembly_items_table_cell_changed` does not have a
        return statement. Therefore, it does not explicitly return any value.
        """
        item_text = item.text()
        row = item.row()
        column = item.column()
        try:
            selected_item_name = table.item(row, 0).text()
        except AttributeError:
            return
        if column == 0:  # Item Name
            if row == table.rowCount() or assembly.exists(selected_item_name):
                return
            assembly_item = assembly.get_item(self.last_selected_assemly_item)
            assembly_item.rename(item_text)
            self.active_workspace_file.save()
            self.sync_changes()
        elif column == 8:  # Parts Per
            assembly_item = assembly.get_item(selected_item_name)
            item_text = item_text.replace(",", "").replace(" ", "")
            assembly_item.set_value(key="parts_per", value=float(sympy.sympify(item_text, evaluate=True)))
            self.active_workspace_file.save()
            self.sync_changes()
            return
        plus_button = table.cellWidget(table.rowCount() - 1, 0)
        plus_button.setEnabled(not assembly.exists(""))

    # STAGING/EDITING
    def load_assemblies_items_file_layout(
        self, file_category: str, files_layout: QHBoxLayout, assembly: Assembly, item: Item, show_dropped_widget: bool = True
    ) -> None:
        """
        The function `load_assemblies_items_file_layout` loads files associated with an item into a
        QHBoxLayout and adds them as buttons, with the option to show a drop widget.

        Args:
          file_category (str): The `file_category` parameter is a string that represents the category of
        files to be loaded. It is used to retrieve the files from the `item` object.
          files_layout (QHBoxLayout): The `files_layout` parameter is a QHBoxLayout object that
        represents the layout where the draggable buttons will be added.
          assembly (Assembly): The "assembly" parameter is an instance of the Assembly class. It
        represents an assembly object.
          item (Item): The "item" parameter is an instance of the Item class. It represents an item in
        the application and contains various properties and values associated with that item.
          show_dropped_widget (bool): The parameter "show_dropped_widget" is a boolean flag that
        determines whether or not to show a "DropWidget" in the layout. If it is set to True, a
        "DropWidget" will be added to the layout. If it is set to False, the "DropWidget" will. Defaults
        to True
        """
        self.clear_layout(files_layout)
        files = item.get_value(key=file_category)
        for file in files:
            btn = DraggableButton(self)
            file_name = os.path.basename(file)
            file_ext = file_name.split(".")[-1].upper()
            file_path = f"{os.path.dirname(os.path.realpath(__file__))}/data/workspace/{file_ext}/{file_name}"
            btn.setFile(file_path)
            btn.setFixedWidth(30)
            btn.setText(file_ext)
            btn.setToolTip("Press to open")
            btn.buttonClicked.connect(partial(self.download_workspace_file, file))
            files_layout.addWidget(btn)
        if show_dropped_widget:
            drop_widget = DropWidget(self, assembly, item, files_layout, file_category)
            files_layout.addWidget(drop_widget)

    # STAGING/EDITING
    def handle_dropped_file(
        self, label: QLabel, file_paths: list[str], assembly: Assembly, item: Item, files_layout: QHBoxLayout, file_category: str
    ) -> None:
        """
        The function handles dropped files by adding them to a set, updating the item's value, saving
        the changes, syncing the changes, uploading the files, updating the status button, and reloading
        the file layout.

        Args:
          label (QLabel): The `label` parameter is a QLabel widget that displays the text "Drag Here".
          file_paths (list[str]): A list of file paths that were dropped onto the label.
          assembly (Assembly): The "assembly" parameter is an instance of the Assembly class. It
        represents a collection of related items or components.
          item (Item): The `item` parameter represents an object or data structure that contains
        information about an item. It likely has methods to get and set values for different keys or
        attributes.
          files_layout (QHBoxLayout): The `files_layout` parameter is a QHBoxLayout object that
        represents the layout where the files will be displayed.
          file_category (str): The `file_category` parameter represents the category or type of the file
        being handled. It is used to identify and categorize the files in the system.
        """
        files = set(item.get_value(key=file_category))
        for file_path in file_paths:
            files.add(file_path)
        item.set_value(key=file_category, value=list(files))
        self.active_workspace_file.save()
        self.sync_changes()
        self.upload_workspace_files(file_paths)
        self.status_button.setText("Upload starting", color="lime")
        label.setText("Drag Here")
        label.setStyleSheet("background-color: rgba(30,30,30,100);")
        self.load_assemblies_items_file_layout(file_category=file_category, files_layout=files_layout, assembly=assembly, item=item)

    # STAGING/EDITING
    def delete_workspace_item(self, assembly: Assembly, table: CustomTableWidget, row_index: int):
        """
        The function deletes an item from an assembly and updates the table and button connections
        accordingly.

        Args:
          assembly (Assembly): The "assembly" parameter is an instance of the Assembly class. It
        represents a collection of items.
          table (CustomTableWidget): The "table" parameter is a CustomTableWidget object, which is a
        custom widget that represents a table. It is used to display and manipulate data in a tabular
        format.
          row_index (int): The `row_index` parameter is an integer that represents the index of the row
        in the `table` widget that needs to be deleted.
        """
        item: Item = assembly.get_item(table.item(row_index, 0).text())
        assembly.remove_item(item=item)
        table.removeRow(row_index)
        for row in range(table.rowCount() - 1):
            # end of table, there is no delete button there
            delete_button: DeletePushButton = table.cellWidget(row, table.columnCount() - 1)
            delete_button.disconnect()
            delete_button.clicked.connect(partial(self.delete_workspace_item, assembly, table, row))
        self.active_workspace_file.save()
        self.sync_changes()

    # STAGING/EDITING
    def load_edit_assembly_items_table(self, assembly: Assembly) -> CustomTableWidget:
        workspace_tags.load_data()
        headers: list[str] = [
            "Item Name",
            "Bending Files",
            "Welding Files",
            "CNC/Milling Files",
            "Thickness",
            "Material Type",
            "Paint Type",
            "Paint Color",
            "Parts Per",
            "Flow Tag",
            "Expected time to complete",
            "Notes",
            "DEL",
        ]
        #     table.setStyleSheet(
        #     f"QTableView {{ gridline-color: white; }} QTableWidget::item {{ border-color: white; }}"
        # )

        table = CustomTableWidget()
        table.blockSignals(True)
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setFont(self.tables_font)
        table.setShowGrid(True)
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        def select_color(item: Item, color_button: QComboBox) -> str:
            color_button.disconnect()
            if color_button.currentText() == "Select Color":
                workspace_tags.load_data()
                color = ColorPicker()
                color.show()
                if color.exec():
                    item.set_value(key="paint_color", value=color.getHex(True))
                    color_name = color.getColorName()
                    self.active_workspace_file.save()
                    self.sync_changes()
                    color_button.setStyleSheet(
                        f'QComboBox{{border-radius: 0.001em; background-color: {item.get_value("paint_color")}}} {"QMenu { background-color: rgb(22,22,22);}"}'
                    )
                    data = workspace_tags.get_data()
                    data["paint_colors"][color_name] = color.getHex(True)
                    workspace_tags.save_data(data)
                    workspace_tags.load_data()
                    color_button.clear()
                    color_button.addItems(list(workspace_tags.get_value("paint_colors").keys()))
                    color_button.addItem("Select Color")
                    color_button.setCurrentText(color_name)
            else:
                if color_button.currentText() == "None":
                    color_button.setStyleSheet(
                        f'QComboBox{{border-radius: 0.001em; background-color: transparent}} {"QMenu { background-color: rgb(22,22,22);}"}'
                    )
                    color_button.setCurrentText("None")
                    item.set_value(key="paint_color", value=None)
                else:
                    workspace_tags.load_data()
                    for color_name, color_code in workspace_tags.get_value("paint_colors").items():
                        if color_code == workspace_tags.get_data()["paint_colors"][color_button.currentText()]:
                            color_button.setCurrentText(color_name)
                            item.set_value(key="paint_color", value=color_code)
                    color_button.setStyleSheet(
                        f'QComboBox{{border-radius: 0.001em; background-color: {workspace_tags.get_data()["paint_colors"][color_button.currentText()]}}} {"QMenu { background-color: rgb(22,22,22);}"}'
                    )
                self.active_workspace_file.save()
            self.sync_changes()
            color_button.currentTextChanged.connect(partial(select_color, item, color_button))

        # def set_timer(timer_box: QComboBox, item: Item) -> None:
        #     timer_box.disconnect()

        #     timer_box.currentTextChanged.connect(partial(set_timer, timer_box, item))

        def add_timers(table: CustomTableWidget, item: Item, timer_layout: QHBoxLayout) -> None:
            self.clear_layout(timer_layout)
            workspace_tags.load_data()
            for flow_tag in item.get_value("timers"):
                try:
                    workspace_tags.get_value("attributes")[flow_tag]["is_timer_enabled"]
                except (KeyError, TypeError):
                    continue
                if workspace_tags.get_value("attributes")[flow_tag]["is_timer_enabled"]:
                    widget = QWidget()
                    layout = QVBoxLayout(widget)
                    widget.setLayout(layout)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.addWidget(QLabel(flow_tag))
                    timer_box = TimeSpinBox(widget)
                    with contextlib.suppress(KeyError):
                        timer_box.setValue(item.get_timer(flow_tag))
                    timer_box.editingFinished.connect(
                        lambda flow_tag=flow_tag, timer_box=timer_box: (
                            item.set_timer(flow_tag=flow_tag, time=timer_box),
                            self.active_workspace_file.save(),
                            self.sync_changes(),
                        )
                    )
                    layout.addWidget(timer_box)
                    timer_layout.addWidget(widget)
                table.resizeColumnsToContents()

        def flow_tag_box_change(table: CustomTableWidget, tag_box: QComboBox, item: Item, timer_layout: QHBoxLayout) -> None:
            if tag_box.currentText() == "Select Flow Tag":
                return
            tag_box.setStyleSheet("QComboBox#tag_box{border-radius: 0.001em;}")
            item.set_value(key="flow_tag", value=tag_box.currentText().split(" ➜ "))
            timers = {}
            for tag in tag_box.currentText().split(" ➜ "):
                timers[tag] = {}
            item.set_value(key="timers", value=timers)
            self.active_workspace_file.save()
            add_timers(table, item, timer_layout)
            self.sync_changes()

        def notes_change(table: CustomTableWidget, notes: NotesPlainTextEdit, item: Item) -> None:
            item.set_value(key="notes", value=notes.toPlainText())
            self.active_workspace_file.save()
            self.sync_changes()

        def add_item(row_index: int, item: Item):
            col_index: int = 0
            table.insertRow(row_index)
            table.setRowHeight(row_index, 50)
            table.setItem(row_index, col_index, QTableWidgetItem(item.name))
            col_index += 1
            for file_column in ["Bending Files", "Welding Files", "CNC/Milling Files"]:
                button_widget = QWidget()
                files_layout = QHBoxLayout()
                files_layout.setContentsMargins(0, 0, 0, 0)
                files_layout.setSpacing(0)
                button_widget.setLayout(files_layout)
                self.load_assemblies_items_file_layout(file_category=file_column, files_layout=files_layout, assembly=assembly, item=item)
                table.setCellWidget(row_index, col_index, button_widget)
                col_index += 1
            thickness_box = QComboBox(self)
            thickness_box.wheelEvent = lambda event: event.ignore()
            thickness_box.setObjectName("thickness_box")
            thickness_box.setStyleSheet("QComboBox#thickness_box{border-radius: 0.001em;}")
            if not item.data["thickness"]:
                thickness_box.addItem("Select Thickness")
            thickness_box.addItems(price_of_steel_information.get_value("thicknesses"))
            thickness_box.setCurrentText(item.data["thickness"])
            thickness_box.currentTextChanged.connect(
                lambda: (item.set_value(key="thickness", value=thickness_box.currentText()), self.active_workspace_file.save(), self.sync_changes())
            )
            table.setCellWidget(row_index, col_index, thickness_box)
            col_index += 1
            material_box = QComboBox(self)
            material_box.wheelEvent = lambda event: event.ignore()
            material_box.setObjectName("material_box")
            material_box.setStyleSheet("QComboBox#material_box{border-radius: 0.001em;}")
            if not item.data["material"]:
                material_box.addItem("Select Material")
            material_box.addItems(price_of_steel_information.get_value("materials"))
            material_box.setCurrentText(item.data["material"])
            material_box.currentTextChanged.connect(
                lambda: (item.set_value(key="material", value=material_box.currentText()), self.active_workspace_file.save(), self.sync_changes())
            )
            table.setCellWidget(row_index, col_index, material_box)
            col_index += 1
            button_paint_type = QComboBox(self)
            button_paint_type.wheelEvent = lambda event: event.ignore()
            if not item.data["paint_type"]:
                button_paint_type.addItem("Select Paint Type")
            button_paint_type.addItems(["None", "Powder", "Wet Paint"])
            button_paint_type.setCurrentText("None")
            button_paint_type.setStyleSheet("border-radius: 0.001em; ")
            button_paint_type.setCurrentText(item.get_value(key="paint_type"))
            button_paint_type.currentTextChanged.connect(
                lambda: (
                    item.set_value(key="paint_type", value=button_paint_type.currentText()),
                    self.active_workspace_file.save(),
                    self.sync_changes(),
                )
            )
            table.setCellWidget(row_index, col_index, button_paint_type)
            col_index += 1
            button_color = QComboBox(self)
            button_color.wheelEvent = lambda event: event.ignore()
            button_color.addItem("None")
            button_color.addItems(list(workspace_tags.get_value("paint_colors").keys()) or ["Select Color"])
            button_color.addItem("Select Color")
            if item.get_value("paint_color") != None:
                for color_name, color_code in workspace_tags.get_value("paint_colors").items():
                    if color_code == item.get_value("paint_color"):
                        button_color.setCurrentText(color_name)
                button_color.setStyleSheet(
                    f'QComboBox{{border-radius: 0.001em; background-color: {item.get_value("paint_color")}}} {"QMenu { background-color: rgb(22,22,22);}"}'
                )
            else:
                button_color.setCurrentText("Set Color")
                button_color.setStyleSheet("border-radius: 0.001em; ")
            button_color.currentTextChanged.connect(partial(select_color, item, button_color))
            table.setCellWidget(row_index, col_index, button_color)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(str(item.data["parts_per"])))
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1

            # timer_box = QComboBox(self)
            # timer_box.addItems(["Set Timer For"] + item.data["flow_tag"])
            # timer_box.setCurrentIndex(0)
            # timer_box.currentTextChanged.connect(partial(set_timer, timer_box, item))
            timer_widget = QWidget()
            timer_layout = QHBoxLayout(timer_widget)
            timer_layout.setContentsMargins(0, 0, 0, 0)
            timer_widget.setLayout(timer_layout)
            add_timers(table=table, item=item, timer_layout=timer_layout)

            tag_box = QComboBox(self)
            tag_box.wheelEvent = lambda event: event.ignore()
            tag_box.setObjectName("tag_box")
            tag_box.setStyleSheet("QComboBox#tag_box{border-radius: 0.001em;}")
            if not item.data["flow_tag"]:
                tag_box.addItem("Select Flow Tag")
                tag_box.setStyleSheet("QComboBox#tag_box{color: red; border-radius: 0.001em; border-color: darkred; background-color: #3F1E25;}")
            tag_box.addItems(self.get_all_flow_tags())
            if item.data["flow_tag"]:
                tag_box.setCurrentText(" ➜ ".join(item.data["flow_tag"]))
            tag_box.currentTextChanged.connect(partial(flow_tag_box_change, table, tag_box, item, timer_layout))
            table.setCellWidget(row_index, col_index, tag_box)
            col_index += 1
            table.setCellWidget(row_index, col_index, timer_widget)
            col_index += 1
            notes = NotesPlainTextEdit(self, item.data['notes'], "Add notes...")
            notes.setFixedHeight(50)
            notes.textChanged.connect(partial(notes_change, table, notes, item))
            table.setCellWidget(row_index, col_index, notes)
            col_index += 1
            delete_button = DeletePushButton(
                self,
                tool_tip=f"Delete {item.name} forever from {assembly.name}",
                icon=QIcon(f"icons/trash.png"),
            )
            delete_button.clicked.connect(partial(self.delete_workspace_item, assembly, table, row_index))
            delete_button.setStyleSheet("margin-top: 10px; margin-bottom: 10px; margin-right: 4px; margin-left: 4px;")
            table.setCellWidget(row_index, col_index, delete_button)

        row_index: int = 0
        for item in assembly.items:
            if not item.get_value("show"):
                continue
            add_item(row_index, item)
            row_index += 1

        def add_new_item():
            input_dialog = AddWorkspaceItem(
                title="Add Workspace Item", message="Enter Item Name",
            )

            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.add:
                    item_name = input_dialog.get_name()
                    material = input_dialog.material
                    thickness = input_dialog.thickness
                else:
                    return
            table.blockSignals(True)

            if self.category == "Staging":
                item_data = {
                    "Bending Files": [],
                    "Welding Files": [],
                    "CNC/Milling Files": [],
                    "thickness": thickness,
                    "material": material,
                    "paint_type": None,
                    "paint_color": None,
                    "parts_per": 0,
                    "flow_tag": [],
                    "timers": {},
                    "customer": "",
                    "ship_to": "",
                    "show": True,
                    "notes": "",
                }
            else:  # EDITING
                date_created: str = QDate().currentDate().toString("yyyy-M-d")
                item_data = {
                    "Bending Files": [],
                    "Welding Files": [],
                    "CNC/Milling Files": [],
                    "thickness": thickness,
                    "material": material,
                    "paint_type": None,
                    "paint_color": None,
                    "parts_per": 0,
                    "flow_tag": [],
                    "timers": {},
                    "customer": "",
                    "ship_to": "",
                    "show": True,
                    "notes": "",
                    # New stuff
                    "recoat": False,
                    "recut": False,
                    "recut_count": 0,
                    "completed": False,
                    "current_flow_state": 0,
                    "starting_date": date_created,
                    "ending_date": date_created,
                    "status": None,
                }
            item = Item(name=item_name, data=item_data)
            add_item(table.rowCount() - 1, item)
            assembly.add_item(item)
            self.active_workspace_file.save()
            self.sync_changes()
            item_group_box: QGroupBox = table.parentWidget()
            item_group_box.setFixedHeight(item_group_box.height() + 45)
            table.setFixedHeight(45 * (len(assembly.items) + 3))
            table.blockSignals(False)

        def add_item_button(on_load: bool = False):
            row_count = table.rowCount()
            if row_count > 0:
                table.removeCellWidget(row_count - 1, 0)
            plus_button = QPushButton(self)
            plus_button.setObjectName("plus_button")
            plus_button.setStyleSheet("QPushButton#plus_button{margin: 2px;}")
            plus_button.setText("Add Item")
            plus_button.clicked.connect(add_new_item)
            plus_button.clicked.connect(add_item_button)
            plus_button.setEnabled(not assembly.exists(""))
            if on_load:
                table.insertRow(table.rowCount())  # Insert a new row at the end
                table.setCellWidget(row_count, 0, plus_button)  # Add the button to the first column of the last row
            else:
                table.setCellWidget(table.rowCount() - 1, 0, plus_button)  # Add the button to the first column of the last row

        table.itemChanged.connect(partial(self.assembly_items_table_cell_changed, table, assembly))
        table.itemClicked.connect(self.assembly_items_table_clicked)

        add_item_button(on_load=True)

        table.set_editable_column_index([0, 8])
        table.blockSignals(False)
        table.resizeColumnsToContents()
        self.workspace_tables[table] = assembly
        # header = table.horizontalHeader()
        # header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Set the first column to Fixed

        return table

    # STAGING/EDITING
    def load_edit_assembly_widget(self, assembly: Assembly, workspace_information: dict, group_color: str, parent=None) -> QWidget:
        """
        The load_edit_assembly_widget function is used to create a widget that can be added to the MultiToolBox in the
        load_edit_assembly_items_table function. The load_edit_assembly_widget function takes an assembly as its only argument and returns
        a QWidget object. The returned QWidget contains a group box with a table widget for displaying items, and another group box
        with buttons for adding sub assemblies, deleting sub assemblies, duplicating sub assemblies, etc.

        :param self: Access the other functions in the class
        :param assembly: Assembly: Pass the assembly object to the function
        :param parent: Set the parent of the widget
        :return: A widget that contains a table of items and sub assemblies
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(h_layout)
        # widget.setLayout(h_layout)
        timer_widget = QWidget(widget)
        timer_layout = QHBoxLayout(timer_widget)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_widget.setLayout(timer_layout)

        color_widget = QWidget(widget)
        color_widget.setHidden(True)
        _color_layout = QVBoxLayout()
        paint_color_layout = QHBoxLayout()
        paint_color_layout.setContentsMargins(0, 0, 0, 0)
        _color_layout.addLayout(paint_color_layout)
        paint_type_layout = QHBoxLayout()
        paint_type_layout.setContentsMargins(0, 0, 0, 0)
        _color_layout.addLayout(paint_type_layout)
        paint_amount_layout = QHBoxLayout()
        paint_amount_layout.setContentsMargins(0, 0, 0, 0)
        _color_layout.addLayout(paint_amount_layout)
        color_widget.setLayout(_color_layout)
        # Create the "Items" group box
        if assembly.get_assembly_data("has_items"):
            # TODO
            def load_excel_file(files: list[str]):
                total_data: dict[str, list[Item]] = {}
                for file in files:
                    monday_excel_file = MondayExcelFile(file)
                    total_data.update(monday_excel_file.get_data())
                for job_name, job_data in total_data.items():
                    for item in job_data:
                        assembly.add_item(item)
                self.active_workspace_file.save()
                self.sync_changes()
                self.load_workspace()

            items_groupbox = ItemsGroupBox(self)
            items_groupbox.filesDropped.connect(load_excel_file)
            items_groupbox.setAcceptDrops(True)
            # items_groupbox.setMinimumHeight(500)
            items_layout = QVBoxLayout()
            items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            items_groupbox.setLayout(items_layout)

        # Create and configure the table widget
        if assembly.get_assembly_data("has_items"):
            table_widget = self.load_edit_assembly_items_table(assembly)
            table_widget.setFixedHeight(45 * (len(assembly.items) + 3))

        def select_color(assembly: Assembly, color_button: QComboBox) -> str:
            color_button.disconnect()
            if color_button.currentText() == "Select Color":
                workspace_tags.load_data()
                color = ColorPicker()
                color.show()
                if color.exec():
                    assembly.set_assembly_data(key="paint_color", value=color.getHex(True))
                    color_name = color.getColorName()
                    self.active_workspace_file.save()
                    self.sync_changes()
                    color_button.setStyleSheet(
                        f'QComboBox{{background-color: {assembly.get_assembly_data("paint_color")}}} {"QMenu { background-color: rgb(22,22,22);}"}'
                    )
                    data = workspace_tags.get_data()
                    data["paint_colors"][color_name] = color.getHex(True)
                    workspace_tags.save_data(data)
                    workspace_tags.load_data()
                    color_button.clear()
                    color_button.addItems(list(workspace_tags.get_value("paint_colors").keys()))
                    color_button.addItem("Select Color")
                    color_button.setCurrentText(color_name)
            else:
                if color_button.currentText() == "None":
                    color_button.setStyleSheet(f'QComboBox{{background-color: transparent}} {"QMenu { background-color: rgb(22,22,22);}"}')
                    color_button.setCurrentText("None")
                    assembly.set_assembly_data(key="paint_color", value=None)
                else:
                    workspace_tags.load_data()
                    for color_name, color_code in workspace_tags.get_value("paint_colors").items():
                        if color_code == workspace_tags.get_data()["paint_colors"][color_button.currentText()]:
                            color_button.setCurrentText(color_name)
                            assembly.set_assembly_data(key="paint_color", value=color_code)
                    color_button.setStyleSheet(
                        f'QComboBox{{background-color: {workspace_tags.get_data()["paint_colors"][color_button.currentText()]}}} {"QMenu { background-color: rgb(22,22,22);}"}'
                    )
                self.active_workspace_file.save()
            self.sync_changes()
            color_button.currentTextChanged.connect(partial(select_color, assembly, color_button))

        def add_timers(timer_layout: QHBoxLayout) -> None:
            self.clear_layout(timer_layout)
            workspace_tags.load_data()
            for flow_tag in assembly.get_assembly_data("flow_tag"):
                try:
                    workspace_tags.get_value("attributes")[flow_tag]["is_timer_enabled"]
                except (KeyError, TypeError):
                    continue
                if workspace_tags.get_value("attributes")[flow_tag]["is_timer_enabled"]:
                    _widget = QWidget()
                    layout = QVBoxLayout(_widget)
                    # _widget.setLayout(layout)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.addWidget(QLabel(flow_tag))
                    timer_box = TimeSpinBox()
                    with contextlib.suppress(KeyError, TypeError):
                        timer_box.setValue(assembly.assembly_data["timers"][flow_tag]["time_to_complete"])
                    timer_box.editingFinished.connect(
                        lambda flow_tag=flow_tag, timer_box=timer_box: (
                            assembly.set_timer(flow_tag=flow_tag, time=timer_box),
                            self.active_workspace_file.save(),
                            self.sync_changes(),
                        )
                    )
                    layout.addWidget(timer_box)
                    timer_layout.addWidget(_widget)

        def flow_tag_change(timer_layout: QHBoxLayout, color_widget: QWidget, flow_tag_combobox: QComboBox):
            flow_tag_combobox.setStyleSheet("")
            assembly.set_assembly_data("flow_tag", flow_tag_combobox.currentText().split(" ➜ "))
            color_widget.setHidden(all(keyword not in flow_tag_combobox.currentText().lower() for keyword in ["paint", "powder"]))
            timers = {}
            for tag in flow_tag_combobox.currentText().split(" ➜ "):
                timers[tag] = {}
            assembly.set_assembly_data(key="timers", value=timers)
            self.active_workspace_file.save()
            self.sync_changes()
            add_timers(timer_layout)

        def get_grid_widget() -> QWidget:
            # Add the table widget to the "Items" group box
            grid_widget = QWidget()
            grid = QGridLayout(grid_widget)
            time_box = TimeSpinBox()
            time_box.setValue(assembly.get_assembly_data(key="expected_time_to_complete"))
            time_box.editingFinished.connect(
                lambda: (
                    assembly.set_assembly_data(key="expected_time_to_complete", value=time_box.value()),
                    self.active_workspace_file.save(),
                    self.sync_changes(),
                )
            )
            grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
            flow_tag_combobox = QComboBox()
            flow_tag_combobox.setObjectName("tag_box")
            flow_tag_combobox.wheelEvent = lambda event: event.ignore()
            if not assembly.get_assembly_data("flow_tag"):
                flow_tag_combobox.addItem("Select Flow Tag")
                flow_tag_combobox.setStyleSheet("QComboBox#tag_box{color: red; border-color: darkred; background-color: #3F1E25;}")
            flow_tag_combobox.addItems(self.get_all_flow_tags())
            flow_tag_combobox.setCurrentText(" ➜ ".join(assembly.get_assembly_data("flow_tag")))
            flow_tag_combobox.currentTextChanged.connect(partial(flow_tag_change, timer_layout, color_widget, flow_tag_combobox))
            grid.addWidget(QLabel("Expected time to complete:"), 0, 0)
            grid.addWidget(time_box, 0, 1)
            grid.addWidget(QLabel("Flow Tag:"), 1, 0)
            grid.addWidget(flow_tag_combobox, 1, 1)
            button_color = QComboBox(self)
            button_color.wheelEvent = lambda event: event.ignore()
            button_color.addItem("None")
            button_color.addItems(list(workspace_tags.get_value("paint_colors").keys()) or ["Select Color"])
            button_color.addItem("Select Color")
            if assembly.get_assembly_data("paint_color") != None:
                for color_name, color_code in workspace_tags.get_value("paint_colors").items():
                    if color_code == assembly.get_assembly_data("paint_color"):
                        button_color.setCurrentText(color_name)
                button_color.setStyleSheet(
                    f'QComboBox{{background-color: {assembly.get_assembly_data("paint_color")}}} {"QMenu { background-color: rgb(22,22,22);}"}'
                )
            else:
                button_color.setCurrentText("Set Color")
            button_color.currentTextChanged.connect(partial(select_color, assembly, button_color))
            paint_color_layout.addWidget(QLabel("Paint Color:"))
            paint_color_layout.addWidget(button_color)

            button_paint_type = QComboBox(self)
            button_paint_type.wheelEvent = lambda event: event.ignore()
            if not assembly.get_assembly_data("paint_type"):
                button_paint_type.addItem("Select Paint Type")
            button_paint_type.addItems(["None", "Powder", "Wet Paint"])
            button_paint_type.setCurrentText("None")
            button_paint_type.setCurrentText(assembly.get_assembly_data(key="paint_type"))
            button_paint_type.currentTextChanged.connect(
                lambda: (
                    assembly.set_assembly_data(key="paint_type", value=button_paint_type.currentText()),
                    self.active_workspace_file.save(),
                    self.sync_changes(),
                )
            )
            paint_type_layout.addWidget(QLabel("Paint Type:"))
            paint_type_layout.addWidget(button_paint_type)

            lineedit_paint_amount = HumbleDoubleSpinBox(self)
            with contextlib.suppress(TypeError):
                lineedit_paint_amount.setValue(assembly.get_assembly_data(key="paint_amount"))
            lineedit_paint_amount.setSuffix(" gallons")
            lineedit_paint_amount.editingFinished.connect(
                lambda: (
                    assembly.set_assembly_data(key="paint_amount", value=lineedit_paint_amount.value()),
                    self.active_workspace_file.save(),
                    self.sync_changes(),
                )
            )
            paint_amount_layout.addWidget(QLabel("Paint Amount:"))
            paint_amount_layout.addWidget(lineedit_paint_amount)
            color_widget.setHidden(all(keyword not in flow_tag_combobox.currentText().lower() for keyword in ["paint", "powder"]))
            return grid_widget

        grid_widget = get_grid_widget()
        add_timers(timer_layout)

        if assembly.get_assembly_data("has_items"):
            h_layout.addWidget(grid_widget)
            items_layout.addWidget(table_widget)
        else:
            h_layout.addWidget(grid_widget)
        h_layout.addWidget(timer_widget)
        h_layout.addWidget(color_widget)

        # Add the "Items" group box to the main layout
        if assembly.get_assembly_data("has_items"):
            layout.addWidget(items_groupbox)

        # Create the "Add Sub Assembly" button
        pushButton_add_sub_assembly = QPushButton("Add Sub Assembly")
        pushButton_add_sub_assembly.setFixedWidth(120)

        if assembly.get_assembly_data("has_sub_assemblies"):
            sub_assembly_groupbox = QGroupBox("Sub Assemblies")
            sub_assembly_groupbox_layout = QVBoxLayout()
            sub_assembly_groupbox.setLayout(sub_assembly_groupbox_layout)

        workspace_information.setdefault(assembly.name, {"tool_box": None, "sub_assemblies": {}})
        try:
            workspace_information[assembly.name]["tool_box"] = workspace_information[assembly.name]["tool_box"].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        # Create the MultiToolBox for sub assemblies
        sub_assemblies_toolbox = AssemblyMultiToolBox()
        sub_assemblies_toolbox.layout().setSpacing(0)

        def add_sub_assembly():
            input_dialog = InputDialog(
                title="Add Sub Assembly",
                message="Enter a name for a new sub assembly",
                placeholder_text="",
            )

            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.ok:
                    input_text = input_dialog.inputText
                    if self.category == "Staging":
                        assembly_data = {
                            "expected_time_to_complete": 0.0,
                            "has_items": True,
                            "has_sub_assemblies": True,
                            "flow_tag": [],
                            "timers": {},
                            "paint_color": None,
                            "paint_type": None,
                            "paint_amount": 0,
                        }
                    else:
                        date_created: str = QDate().currentDate().toString("yyyy-M-d")
                        assembly_data = {
                            "expected_time_to_complete": 0.0,
                            "has_items": True,
                            "has_sub_assemblies": True,
                            "flow_tag": [],
                            "timers": {},
                            "paint_color": None,
                            "paint_type": None,
                            "paint_amount": 0,
                            # new stuff
                            "starting_data": date_created,
                            "ending_date": date_created,
                            "current_flow_state": 0,
                            "completed": False,
                            "status": None,
                        }
                    new_assembly: Assembly = Assembly(
                        name=input_text,
                        assembly_data=assembly_data,
                    )
                    assembly.add_sub_assembly(new_assembly)
                    self.active_workspace_file.save()
                    self.sync_changes()
                    workspace_information.setdefault(new_assembly.name, {"tool_box": None, "sub_assemblies": {}})
                    sub_assembly_widget = self.load_edit_assembly_widget(
                        new_assembly,
                        workspace_information[new_assembly.name]["sub_assemblies"],
                        group_color=self.active_workspace_file.get_group_color(assembly.get_master_assembly().get_assembly_data(key="group")),
                    )  # Load the widget for the new assembly
                    sub_assemblies_toolbox.addItem(
                        sub_assembly_widget, new_assembly.name, base_color=group_color
                    )  # Add the widget to the MultiToolBox
                    delete_button = sub_assemblies_toolbox.getLastDeleteButton()
                    delete_button.clicked.connect(partial(delete_sub_assembly, new_assembly, sub_assembly_widget))
                    duplicate_button = sub_assemblies_toolbox.getLastDuplicateButton()
                    duplicate_button.clicked.connect(partial(duplicate_sub_assembly, new_assembly))
                    input_box = sub_assemblies_toolbox.getLastInputBox()
                    input_box.editingFinished.connect(partial(rename_sub_assembly, new_assembly, input_box))
                    self.load_edit_assembly_context_menus()
                    # self.sync_changes()
                    # self.load_categories()
                elif response == DialogButtons.cancel:
                    return

        def delete_sub_assembly(sub_assembly_to_delete: Assembly, widget_to_delete: QWidget):
            assembly.delete_sub_assembly(sub_assembly_to_delete)
            self.active_workspace_file.save()
            self.sync_changes()
            sub_assemblies_toolbox.removeItem(widget_to_delete)

        def duplicate_sub_assembly(assembly_to_duplicate: Assembly):
            new_assembly = assembly.copy_sub_assembly(assembly_to_duplicate)
            assembly.add_sub_assembly(new_assembly)
            new_assembly.set_assembly_data(key="widget_color", value=get_random_color())
            self.active_workspace_file.save()
            self.sync_changes()
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            workspace_information.setdefault(new_assembly.name, {"tool_box": None, "sub_assemblies": {}})
            assembly_widget = self.load_edit_assembly_widget(
                new_assembly,
                workspace_information[new_assembly.name]["sub_assemblies"],
                group_color=self.active_workspace_file.get_group_color(assembly.get_master_assembly().get_assembly_data(key="group")),
            )
            sub_assemblies_toolbox.addItem(assembly_widget, new_assembly.name, base_color=group_color)
            delete_button = sub_assemblies_toolbox.getLastDeleteButton()
            delete_button.clicked.connect(partial(delete_sub_assembly, new_assembly, assembly_widget))
            duplicate_button = sub_assemblies_toolbox.getLastDuplicateButton()
            duplicate_button.clicked.connect(partial(duplicate_sub_assembly, new_assembly))
            input_box = sub_assemblies_toolbox.getLastInputBox()
            input_box.editingFinished.connect(partial(rename_sub_assembly, new_assembly, input_box))

            self.load_edit_assembly_context_menus()

        def rename_sub_assembly(assembly_to_rename: Assembly, input_box: QLineEdit):
            assembly_to_rename.rename(input_box.text())
            self.active_workspace_file.save()
            self.sync_changes()

        if assembly.get_assembly_data("has_sub_assemblies"):
            pushButton_add_sub_assembly.clicked.connect(add_sub_assembly)
            # Add the sub assemblies MultiToolBox to the main layout
            sub_assembly_groupbox_layout.addWidget(pushButton_add_sub_assembly)
            sub_assembly_groupbox_layout.addWidget(sub_assemblies_toolbox)
            layout.addWidget(sub_assembly_groupbox)
            if len(assembly.sub_assemblies) > 0:
                for i, sub_assembly in enumerate(assembly.sub_assemblies):
                    # Load the sub assembly recursively and add it to the sub assemblies MultiToolBox
                    sub_assembly_widget = self.load_edit_assembly_widget(
                        sub_assembly, workspace_information=workspace_information[assembly.name]["sub_assemblies"], group_color=group_color
                    )
                    sub_assemblies_toolbox.addItem(sub_assembly_widget, sub_assembly.name, base_color=group_color)
                    delete_button = sub_assemblies_toolbox.getLastDeleteButton()
                    delete_button.clicked.connect(partial(delete_sub_assembly, sub_assembly, sub_assembly_widget))
                    duplicate_button = sub_assemblies_toolbox.getLastDuplicateButton()
                    duplicate_button.clicked.connect(partial(duplicate_sub_assembly, sub_assembly))
                    input_box = sub_assemblies_toolbox.getLastInputBox()
                    input_box.editingFinished.connect(partial(rename_sub_assembly, sub_assembly, input_box))
                sub_assemblies_toolbox.close_all()
        if saved_workspace_prefs:
            sub_assemblies_toolbox.set_widgets_visibility(workspace_information[assembly.name]["tool_box"])
        workspace_information[assembly.name]["tool_box"] = sub_assemblies_toolbox
        return widget

    # STAGING/EDITING
    def load_edit_assembly_tab(self) -> None:
        with contextlib.suppress(AttributeError):
            self.workspace_filter_tab_widget.clear_selections("Flow Tags")
        self.workspace_information.setdefault(self.category, {"group_tool_box": None})
        try:
            self.workspace_information[self.category]["group_tool_box"] = self.workspace_information[self.category][
                "group_tool_box"
            ].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        scroll_area = QScrollArea(self)

        def save_scroll_position(tab_name: str, scroll: QScrollArea):
            self.scroll_position_manager.save_scroll_position(tab_name=tab_name, scroll=scroll)

        scroll_area.verticalScrollBar().valueChanged.connect(
            partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} {self.category}", scroll_area)
        )
        scroll_area.horizontalScrollBar().valueChanged.connect(
            partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} {self.category}", scroll_area)
        )
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(scroll_area)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(1)
        scroll_area.setWidget(scroll_content)

        # workspace_data = self.active_workspace_file.get_data()
        self.active_workspace_file.get_filtered_data(self.workspace_filter)
        grouped_data = self.active_workspace_file.get_grouped_data()

        group_tool_boxes: dict[str, QWidget] = {}
        group_tool_box = AssemblyMultiToolBox(scroll_content)

        def set_assembly_inputbox_context_menu(
            input_box: QLineEdit, multi_tool_box: AssemblyMultiToolBox, assembly_widget: QWidget, assembly: Assembly
        ) -> None:
            input_box.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            menu = QMenu(input_box)
            groups_menu = QMenu(menu)
            groups_menu.setTitle("Move to Group")
            for menu_group in self.active_workspace_file._get_all_groups():
                if menu_group == assembly.get_assembly_data(key="group"):
                    continue
                action = QAction(groups_menu)
                action.triggered.connect(partial(move_to_group, multi_tool_box, assembly_widget, assembly, menu_group, False))
                action.setText(menu_group)
                groups_menu.addAction(action)
            action = QAction(groups_menu)
            action.triggered.connect(partial(move_to_group, multi_tool_box, assembly_widget, assembly, "menu_group", True))
            action.setText("Create Group")
            groups_menu.addAction(action)
            menu.addMenu(groups_menu)
            input_box.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

        def add_job():
            input_dialog = AddJobDialog(
                title="Add Job", message="Enter a name for a new job", group_names=self.active_workspace_file._get_all_groups()
            )

            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.add:
                    job_name, has_items, has_sub_assemblies = input_dialog.get_selected_items()
                    group = input_dialog.get_group_name()
                    group_color = get_random_color()
                    if group in list(grouped_data.keys()):
                        for assembly in self.active_workspace_file.data:
                            if assembly.get_assembly_data(key="group") == group:
                                group_color = assembly.get_assembly_data(key="group_color")
                    new_assembly: Assembly = Assembly(
                        name=job_name,
                        assembly_data={
                            "expected_time_to_complete": 0.0,
                            "has_items": has_items,
                            "has_sub_assemblies": has_sub_assemblies,
                            "group": group,
                            "group_color": group_color,
                            "flow_tag": [],
                            "timers": {},
                        },
                    )
                    try:
                        multi_tool_box = self.workspace_information[self.category][group]["tool_box"]
                    except (KeyError, TypeError):
                        multi_tool_box = None

                    if multi_tool_box is None:
                        group_widget = QWidget()
                        group_layout = QVBoxLayout(group_widget)
                        group_widget.setLayout(group_layout)
                        group_tool_box.addItem(group_widget, group, base_color=group_color)
                        # group_tool_box.open(len(group_tool_box.buttons) - 1)
                        delete_button = group_tool_box.getLastDeleteButton()
                        delete_button.clicked.connect(partial(delete_group, group_tool_box, group, group_widget))
                        duplicate_button = group_tool_box.getLastDuplicateButton()
                        duplicate_button.clicked.connect(partial(duplicate_group, group))
                        input_box = group_tool_box.getLastInputBox()
                        input_box.editingFinished.connect(partial(rename_group, group_tool_box, group, input_box))
                        group_tool_boxes[group] = group_widget
                        self.workspace_information[self.category].setdefault(group, {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None})

                        multi_tool_box = AssemblyMultiToolBox()
                        multi_tool_box.layout().setSpacing(0)
                        group_tool_boxes[group].layout().addWidget(multi_tool_box)

                    self.active_workspace_file.add_assembly(new_assembly)
                    self.active_workspace_file.save()
                    self.sync_changes()
                    self.workspace_information[self.category][group].setdefault(new_assembly.name, {"tool_box": None, "sub_assemblies": {}})
                    sub_assembly_widget = self.load_edit_assembly_widget(
                        assembly=new_assembly,
                        workspace_information=self.workspace_information[self.category][group][new_assembly.name]["sub_assemblies"],
                        group_color=group_color,
                    )  # Load the widget for the new assembly
                    multi_tool_box.addItem(sub_assembly_widget, new_assembly.name, base_color=group_color)  # Add the widget to the MultiToolBox
                    # multi_tool_box.open_all()
                    delete_button = multi_tool_box.getLastDeleteButton()
                    delete_button.clicked.connect(partial(delete_assembly, multi_tool_box, new_assembly, sub_assembly_widget))
                    duplicate_button = multi_tool_box.getLastDuplicateButton()
                    duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box, new_assembly))
                    input_box = multi_tool_box.getLastInputBox()
                    input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box, new_assembly, input_box))
                elif response == DialogButtons.cancel:
                    return

        def delete_assembly(multi_tool_box: AssemblyMultiToolBox, sub_assembly_to_delete: Assembly, widget_to_delete: QWidget):
            self.active_workspace_file.remove_assembly(sub_assembly_to_delete)
            self.active_workspace_file.save()
            self.sync_changes()
            multi_tool_box.removeItem(widget_to_delete)

        def duplicate_assembly(multi_tool_box: AssemblyMultiToolBox, assembly_to_duplicate: Assembly):
            new_assembly = self.active_workspace_file.duplicate_assembly(assembly_to_duplicate)
            self.active_workspace_file.save()
            self.sync_changes()
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            self.workspace_information.setdefault(new_assembly.name, {"tool_box": None, "sub_assemblies": {}})
            assembly_widget = self.load_edit_assembly_widget(
                new_assembly,
                workspace_information=self.workspace_information[new_assembly.name]["sub_assemblies"],
                group_color=self.active_workspace_file.get_group_color(assembly_to_duplicate.get_master_assembly().get_assembly_data(key="group")),
            )
            multi_tool_box.addItem(assembly_widget, new_assembly.name, base_color=new_assembly.get_assembly_data(key="group_color"))
            delete_button = multi_tool_box.getLastDeleteButton()
            delete_button.clicked.connect(partial(delete_assembly, multi_tool_box, new_assembly, assembly_widget))
            duplicate_button = multi_tool_box.getLastDuplicateButton()
            duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box, new_assembly))
            input_box = multi_tool_box.getLastInputBox()
            input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box, new_assembly, input_box))
            set_assembly_inputbox_context_menu(
                input_box=input_box, multi_tool_box=multi_tool_box, assembly_widget=assembly_widget, assembly=new_assembly
            )

            multi_tool_box.close(len(multi_tool_box.buttons) - 1)

        def rename_sub_assembly(multi_tool_box: AssemblyMultiToolBox, assembly_to_rename: Assembly, input_box: QLineEdit):
            assembly_to_rename.rename(input_box.text())
            self.active_workspace_file.save()
            self.sync_changes()

        def delete_group(group_tool_box: AssemblyMultiToolBox, group: str, widget_to_delete: QWidget):
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            grouped_data = self.active_workspace_file.get_grouped_data()
            with contextlib.suppress(KeyError):
                for assembly in grouped_data[group]:
                    self.active_workspace_file.remove_assembly(assembly)
                self.active_workspace_file.save()
                self.sync_changes()
            group_tool_box.removeItem(widget_to_delete)
            del self.workspace_information[self.category][group]

        def duplicate_group(group: str):
            new_group_name: str = f"{group} - (Copy)"
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            grouped_data = self.active_workspace_file.get_grouped_data()
            group_color = get_random_color()
            for assembly in grouped_data[group]:
                new_assembly = self.active_workspace_file.duplicate_assembly(assembly)
                new_assembly.set_assembly_data(key="group", value=new_group_name)
                new_assembly.set_assembly_data(key="group_color", value=group_color)
                self.active_workspace_file.save()
            self.sync_changes()

            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            grouped_data = self.active_workspace_file.get_grouped_data()

            group_widget = QWidget()
            group_layout = QVBoxLayout(group_widget)
            group_widget.setLayout(group_layout)
            group_tool_box.addItem(group_widget, new_group_name, base_color=group_color)
            # group_tool_box.open(len(group_tool_box.buttons) - 1)
            delete_button = group_tool_box.getLastDeleteButton()
            delete_button.clicked.connect(partial(delete_group, group_tool_box, new_group_name, group_widget))
            duplicate_button = group_tool_box.getLastDuplicateButton()
            duplicate_button.clicked.connect(partial(duplicate_group, new_group_name))
            input_box = group_tool_box.getLastInputBox()
            input_box.editingFinished.connect(partial(rename_group, group_tool_box, new_group_name, input_box))
            group_tool_boxes[new_group_name] = group_widget
            self.workspace_information[self.category].setdefault(new_group_name, {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None})

            multi_tool_box = AssemblyMultiToolBox()
            multi_tool_box.layout().setSpacing(0)
            for i, assembly in enumerate(grouped_data[new_group_name]):
                assembly_widget = self.load_edit_assembly_widget(
                    assembly=assembly,
                    workspace_information=self.workspace_information[self.category][new_group_name]["sub_assemblies"],
                    group_color=group_color,
                )
                multi_tool_box.addItem(assembly_widget, assembly.name, base_color=group_color)
                delete_button = multi_tool_box.getDeleteButton(i)
                delete_button.clicked.connect(partial(delete_assembly, multi_tool_box, assembly, assembly_widget))
                duplicate_button = multi_tool_box.getDuplicateButton(i)
                duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box, assembly))
                input_box = multi_tool_box.getInputBox(i)
                input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box, assembly, input_box))
                set_assembly_inputbox_context_menu(
                    input_box=input_box, multi_tool_box=multi_tool_box, assembly_widget=assembly_widget, assembly=assembly
                )

            multi_tool_box.close_all()
            # pushButton_add_job = QPushButton(scroll_content)
            # pushButton_add_job.setText("Add Job")
            # pushButton_add_job.clicked.connect(add_assembly)
            self.workspace_information[self.category][group]["tool_box"] = multi_tool_box
            group_tool_boxes[new_group_name].layout().addWidget(multi_tool_box)
            # group_tool_box.addItem()

        def rename_group(group_tool_box: AssemblyMultiToolBox, group: str, input_box: QLineEdit):
            self.active_workspace_file.get_filtered_data(self.workspace_filter)
            grouped_data = self.active_workspace_file.get_grouped_data()
            try:
                for assembly in grouped_data[group]:
                    assembly.set_assembly_data(key="group", value=input_box.text())
            except KeyError:  # The assembly mustve been deleted?
                return
            self.active_workspace_file.save()
            self.sync_changes()

        def move_to_group(
            multi_tool_box_to_move_from: AssemblyMultiToolBox,
            assembly_widget_to_move: QWidget,
            assembly: Assembly,
            group: str,
            prompt_group_name: bool = False,
        ):
            if prompt_group_name:
                input_dialog = InputDialog(title="Create group", message="Enter a name for a group.")
                if input_dialog.exec():
                    response = input_dialog.get_response()
                    if response == DialogButtons.ok:
                        group = input_dialog.inputText
                    elif response == DialogButtons.cancel:
                        return
            assembly.set_assembly_data(key="group", value=group)
            self.active_workspace_file.save()
            self.sync_changes()
            try:
                multi_tool_box_to_move_to = self.workspace_information[self.category][group]["tool_box"]
            except KeyError:  # The group does not exist because the user craeted a new one
                group_widget = QWidget()
                group_layout = QVBoxLayout(group_widget)
                group_widget.setLayout(group_layout)
                group_tool_box.addItem(group_widget, group)
                # group_tool_box.open(len(group_tool_box.buttons) - 1)
                delete_button = group_tool_box.getLastDeleteButton()
                delete_button.clicked.connect(partial(delete_group, group_tool_box, group, group_widget))
                duplicate_button = group_tool_box.getLastDuplicateButton()
                duplicate_button.clicked.connect(partial(duplicate_group, group_tool_box, group))
                input_box = group_tool_box.getLastInputBox()
                input_box.editingFinished.connect(partial(rename_group, group_tool_box, group, input_box))
                group_tool_boxes[group] = group_widget
                self.workspace_information[self.category].setdefault(group, {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None})
                multi_tool_box = AssemblyMultiToolBox()
                multi_tool_box.layout().setSpacing(0)
                self.workspace_information[self.category][group]["tool_box"] = multi_tool_box
                group_tool_boxes[group].layout().addWidget(multi_tool_box)
                multi_tool_box_to_move_to = multi_tool_box

            assembly_widget = self.load_edit_assembly_widget(
                assembly=assembly, workspace_information=self.workspace_information[self.category][group]["sub_assemblies"]
            )
            multi_tool_box_to_move_to.addItem(assembly_widget, assembly.name)
            delete_button = multi_tool_box_to_move_to.getLastDeleteButton()
            delete_button.clicked.connect(partial(delete_assembly, multi_tool_box_to_move_to, assembly, assembly_widget))
            duplicate_button = multi_tool_box_to_move_to.getLastDuplicateButton()
            duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box_to_move_to, assembly))
            input_box = multi_tool_box_to_move_to.getLastInputBox()
            input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box_to_move_to, assembly, input_box))
            set_assembly_inputbox_context_menu(
                input_box=input_box, multi_tool_box=multi_tool_box_to_move_to, assembly_widget=assembly_widget, assembly=assembly
            )
            multi_tool_box_to_move_to.close(len(multi_tool_box_to_move_to.buttons) - 1)
            multi_tool_box_to_move_from.removeItem(assembly_widget_to_move)

        for i, group in enumerate(self.active_workspace_file.get_all_groups()):
            group_widget = QWidget()
            group_layout = QVBoxLayout(group_widget)
            group_widget.setLayout(group_layout)
            group_color = self.active_workspace_file.get_group_color(group)
            group_tool_box.addItem(group_widget, group, base_color=group_color)
            delete_button = group_tool_box.getDeleteButton(i)
            delete_button.clicked.connect(partial(delete_group, group_tool_box, group, group_widget))
            duplicate_button = group_tool_box.getDuplicateButton(i)
            duplicate_button.clicked.connect(partial(duplicate_group, group))
            input_box = group_tool_box.getInputBox(i)
            input_box.editingFinished.connect(partial(rename_group, group_tool_box, group, input_box))
            group_tool_boxes[group] = group_widget
            self.workspace_information[self.category].setdefault(group, {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None})
        group_tool_box.close_all()
        if saved_workspace_prefs:
            group_tool_box.set_widgets_visibility(self.workspace_information[self.category]["group_tool_box"])
        self.workspace_information[self.category]["group_tool_box"] = group_tool_box
        if len(group_tool_box.buttons) == 0:
            scroll_layout.addWidget(QLabel("Nothing to show.", self))
        else:
            scroll_layout.addWidget(group_tool_box)
        for group in grouped_data:
            try:
                self.workspace_information[self.category][group]["tool_box"] = self.workspace_information[self.category][group][
                    "tool_box"
                ].get_widget_visibility()
                saved_workspace_prefs = True
            except (AttributeError, RuntimeError):
                saved_workspace_prefs = False
            multi_tool_box = AssemblyMultiToolBox()
            multi_tool_box.layout().setSpacing(0)
            group_color = self.active_workspace_file.get_group_color(group)
            for i, assembly in enumerate(grouped_data[group]):
                assembly_widget = self.load_edit_assembly_widget(
                    assembly=assembly,
                    workspace_information=self.workspace_information[self.category][group]["sub_assemblies"],
                    group_color=group_color,
                )
                multi_tool_box.addItem(assembly_widget, assembly.name, base_color=group_color)
                delete_button = multi_tool_box.getDeleteButton(i)
                delete_button.clicked.connect(partial(delete_assembly, multi_tool_box, assembly, assembly_widget))
                duplicate_button = multi_tool_box.getDuplicateButton(i)
                duplicate_button.clicked.connect(partial(duplicate_assembly, multi_tool_box, assembly))
                input_box = multi_tool_box.getInputBox(i)
                input_box.editingFinished.connect(partial(rename_sub_assembly, multi_tool_box, assembly, input_box))
                set_assembly_inputbox_context_menu(
                    input_box=input_box, multi_tool_box=multi_tool_box, assembly_widget=assembly_widget, assembly=assembly
                )

            multi_tool_box.close_all()
            if saved_workspace_prefs:
                multi_tool_box.set_widgets_visibility(self.workspace_information[self.category][group]["tool_box"])
            # pushButton_add_job = QPushButton(scroll_content)
            # pushButton_add_job.setText("Add Job")
            # pushButton_add_job.clicked.connect(add_assembly)
            self.workspace_information[self.category][group]["tool_box"] = multi_tool_box
            group_tool_boxes[group].layout().addWidget(multi_tool_box)

        # multi_tool_box.close_all()
        # scroll_layout.addWidget(pushButton_add_job)

        self.pushButton_add_job.disconnect()
        self.pushButton_add_job.clicked.connect(add_job)
        self.tab_widget.currentWidget().layout().addWidget(scroll_area)
        self.scroll_position_manager.restore_scroll_position(
            tab_name=f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} {self.category}", scroll=scroll_area
        )

    # USER
    def load_view_assembly_items_table(self, assembly: Assembly) -> CustomTableWidget:
        workspace_tags.load_data()
        headers: list[str] = [
            "Item Name",  # 0
            "Bending Files",  # 1
            "Welding Files",  # 2
            "CNC/Milling Files",  # 3
            "Thickness",  # 4
            "Material Type",  # 5
            "Paint Type",  # 6
            "Paint Color",  # 7
            "Quantity",  # 8
            "Flow Tag Controls",  # 9
            "Set Timers",  # 10
        ]
        #     table.setStyleSheet(
        #     f"QTableView {{ gridline-color: white; }} QTableWidget::item {{ border-color: white; }}"
        # )

        table = CustomTableWidget(self)
        # table.hideColumn()
        table.blockSignals(True)
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setFont(self.tables_font)
        table.setShowGrid(True)
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.hideColumn(1)
        table.hideColumn(2)
        table.hideColumn(3)
        table.hideColumn(6)
        table.hideColumn(7)
        table.hideColumn(10)

        def toggle_timer(item: Item, toggle_timer_button: QPushButton, recording_widget: RecordingWidget) -> None:
            item_flow_tag: str = item.get_value("flow_tag")[item.get_value("current_flow_state")]
            timer_data = item.get_value("timers")
            is_recording: bool = not timer_data[item_flow_tag]["recording"]
            toggle_timer_button.setChecked(is_recording)
            toggle_timer_button.setText("Stop" if is_recording else "Start")
            recording_widget.setHidden(not is_recording)
            timer_data[item_flow_tag]["recording"] = is_recording
            if is_recording:
                timer_data[item_flow_tag].setdefault("time_taken_intervals", [])
                timer_data[item_flow_tag]["time_taken_intervals"].append([str(datetime.now())])
            else:
                timer_data[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
            item.set_value(key="timers", value=timer_data)

            user_workspace.save()
            self.sync_changes()

        def recut(item: Item) -> None:
            input_dialog = RecutDialog(
                title="Set Recut Count", message=f"Select or Input recut count for: {item.name}", max_value=item.get_value(key="parts_per")
            )
            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.ok:
                    recut_count = int(input_dialog.inputText)
                    parent_assembly = item.parent_assembly
                    new_item = Item(name=f"{item.name} - Recut #{item.get_value('recut_count') + 1}", data=item.copy_data())
                    new_item.set_value(key="parts_per", value=recut_count)
                    new_item.set_value(key="completed", value=False)
                    new_item.set_value(key="current_flow_state", value=new_item.get_value("flow_tag").index("Laser Cutting"))
                    new_item.set_value(key="recut", value=True)
                    parent_assembly.add_item(new_item)
                    item.set_value(key="recut_count", value=item.get_value("recut_count") + 1)
                    item.set_value(key="parts_per", value=item.get_value(key="parts_per") - recut_count)
                    user_workspace.save()
                    self.sync_changes()
                    self.load_workspace()

        def move_to_next_flow(item: Item, row_index: int) -> None:
            item_flow_tag: str = item.get_value("flow_tag")[item.get_value("current_flow_state")]
            if workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                timer_data = item.get_value("timers")
                try:
                    timer_data[item_flow_tag]["recording"]
                except KeyError:
                    timer_data[item_flow_tag]["recording"] = False
                if timer_data[item_flow_tag]["recording"]:
                    timer_data[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                    timer_data[item_flow_tag]["recording"] = False
                    item.set_value(key="timers", value=timer_data)
            if item_flow_tag == "Laser Cutting":
                item.set_value(key="recut", value=False)
            item.set_value(key="current_flow_state", value=item.get_value(key="current_flow_state") + 1)
            item.set_value(key="status", value=None)
            if item.get_value(key="current_flow_state") == len(item.get_value(key="flow_tag")):
                item.set_value(key="completed", value=True)
                item.set_value(key="date_completed", value=str(datetime.now()))
                if assembly.get_assembly_data('current_flow_state') == -1: # NOTE Custom Job
                    completed_assemblies: list[Assembly] = []
                    history_workspace.load_data()
                    for main_assembly in user_workspace.data:
                        # Assembly is 100% complete
                        if user_workspace.get_completion_percentage(main_assembly)[0] == 1.0:
                            main_assembly.set_assembly_data(key='completed', value=True)
                            completed_assemblies.append(main_assembly)
                            history_workspace.add_assembly(main_assembly)
                            history_workspace.save()
                            self.play_celebrate_sound()
                    for completed_assembly in completed_assemblies:
                        user_workspace.remove_assembly(completed_assembly)
            user_workspace.save()
            self.sync_changes()
            self.load_workspace()

        def item_status_changed(status_box: QComboBox, item: Item, row_index: int, toggle_timer_button: QPushButton) -> None:
            if (
                workspace_tags.get_value("flow_tag_statuses")[item.get_value("flow_tag")[item.get_value("current_flow_state")]][
                    status_box.currentText()
                ]["start_timer"]
                and workspace_tags.get_value("attributes")[item.get_value("flow_tag")[item.get_value("current_flow_state")]]["is_timer_enabled"]
                and item.get_value("timers")[item.get_value("flow_tag")[item.get_value("current_flow_state")]]["recording"] == False
            ):
                toggle_timer_button.click()
            if workspace_tags.get_value("flow_tag_statuses")[item.get_value("flow_tag")[item.get_value("current_flow_state")]][
                status_box.currentText()
            ]["completed"]:
                move_to_next_flow(item=item, row_index=row_index)
            else:
                item.set_value(key="status", value=status_box.currentText())

            user_workspace.save()
            self.sync_changes()

        def add_item(row_index: int, item: Item):
            if item.get_value(key="completed") == False:
                try:
                    item_flow_tag: str = item.get_value("flow_tag")[item.get_value("current_flow_state")]
                except IndexError:  # This happens when an item was added from the Editing tab without a flow tag
                    return
            else:
                if assembly.get_assembly_data("current_flow_state") >= 0:
                    item_flow_tag: str = assembly.get_assembly_data("flow_tag")[assembly.get_assembly_data("current_flow_state")]
                else:  # Custom Job
                    item_flow_tag: str = "Custom Job"

            col_index: int = 0
            table.insertRow(row_index)
            table.setRowHeight(row_index, 50)
            table.setItem(row_index, col_index, QTableWidgetItem(item.name))  # 0
            col_index += 1
            for file_column in ["Bending Files", "Welding Files", "CNC/Milling Files"]:
                button_widget = QWidget()
                files_layout = QHBoxLayout()
                files_layout.setContentsMargins(0, 0, 0, 0)
                files_layout.setSpacing(0)
                button_widget.setLayout(files_layout)
                self.load_assemblies_items_file_layout(
                    file_category=file_column, files_layout=files_layout, assembly=assembly, item=item, show_dropped_widget=False
                )
                table.setCellWidget(row_index, col_index, button_widget)
                col_index += 1
            if "bend" in item_flow_tag.lower():
                table.showColumn(1)
            if "weld" in item_flow_tag.lower():
                table.showColumn(2)
            if "cut" in item_flow_tag.lower():
                table.showColumn(3)
            if "paint" in item_flow_tag.lower():
                table.showColumn(6)
                table.showColumn(7)

            table.setItem(row_index, col_index, QTableWidgetItem(item.data["thickness"]))  # 4
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(item.data["material"]))  # 5
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(str(item.data["paint_type"])))  # 6
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            button_color = QComboBox(self)
            button_color.setEnabled(False)
            if item.get_value("paint_color") != None:
                for color_name, color_code in workspace_tags.get_value("paint_colors").items():
                    if color_code == item.get_value("paint_color"):
                        button_color.addItem(color_name)
                        button_color.setCurrentText(color_name)
                        button_color.setStyleSheet(
                            f'QComboBox{{border-radius: 0.001em; background-color: {item.get_value("paint_color")}}} {"QMenu { background-color: rgb(22,22,22);}"}'
                        )
                        break
            table.setCellWidget(row_index, col_index, button_color)  # 7
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(str(item.data["parts_per"])))  # 8
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1

            # timer_box = QComboBox(self)
            # timer_box.addItems(["Set Timer For"] + item.data["flow_tag"])
            # timer_box.setCurrentIndex(0)
            # timer_box.currentTextChanged.connect(partial(set_timer, timer_box, item))
            # timer_widget = QWidget()
            # timer_layout = QHBoxLayout(timer_widget)
            # timer_layout.setContentsMargins(0, 0, 0, 0)
            # timer_widget.setLayout(timer_layout)

            # current_tag = QComboBox(self)
            # current_tag.wheelEvent = lambda event: event.ignore()
            # current_tag.setObjectName("tag_box")
            # current_tag.setStyleSheet("QComboBox#tag_box{margin: 2px;}")
            flow_tag_controls_widget = QWidget(self)
            h_layout = QHBoxLayout(flow_tag_controls_widget)
            flow_tag_controls_widget.setLayout(h_layout)
            h_layout.setSpacing(0)
            h_layout.setContentsMargins(0, 0, 0, 0)
            # TIMER WIDGET
            timer_widget = QWidget(self)
            timer_layout = QHBoxLayout(timer_widget)
            timer_widget.setLayout(timer_layout)
            recording_widget = RecordingWidget(timer_widget)
            toggle_timer_button = QPushButton(timer_widget)

            if item.get_value(key="completed") == False:
                if not list(workspace_tags.get_value("flow_tag_statuses")[item_flow_tag].keys()):
                    try:
                        button_next_flow_state = QPushButton(self)
                        button_next_flow_state.setFixedHeight(50)
                        button_next_flow_state.setObjectName("flow_tag_button")
                        button_flow_state_name: str = "Mark as Done!"
                        if "bend" in item_flow_tag.lower():
                            button_flow_state_name = "Bent"
                        if "weld" in item_flow_tag.lower():
                            button_flow_state_name = "Welded"
                        if "cut" in item_flow_tag.lower():
                            button_flow_state_name = "Laser Cut"
                        if "paint" in item_flow_tag.lower():
                            button_flow_state_name = "Painted"
                        if "pick" in item_flow_tag.lower():
                            button_flow_state_name = "Picked"
                        if "assem" in item_flow_tag.lower():
                            button_flow_state_name = "Assembled"
                        button_next_flow_state.setText(button_flow_state_name)
                        button_next_flow_state.clicked.connect(partial(move_to_next_flow, item, row_index))
                        button_next_flow_state.setStyleSheet("border-radius: 0.001em;")
                        # QTableWidgetItem(item.data["flow_tag"][item.data["current_flow_state"]])
                        h_layout.addWidget(button_next_flow_state)
                        # table.setCellWidget(row_index, col_index, button_next_flow_state)
                    except IndexError:
                        table.setItem(row_index, col_index, QTableWidgetItem("Null"))
                        table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                else:
                    status_box = QComboBox(self)
                    status_box.setFixedHeight(50)
                    status_box.setObjectName("flow_tag_status_button")
                    status_box.addItems(list(workspace_tags.get_value("flow_tag_statuses")[item_flow_tag].keys()))
                    status_box.setCurrentText(item.get_value("status"))
                    status_box.setStyleSheet("border-radius: 0.001em;")
                    status_box.currentTextChanged.connect(partial(item_status_changed, status_box, item, row_index, toggle_timer_button))
                    # table.setCellWidget(row_index, col_index, status_box)
                    h_layout.addWidget(status_box)
            # if ["paint", "quote", "ship"] not in item_flow_tag.lower():
            if all(tag not in item_flow_tag.lower() for tag in ["laser", "quote", "ship"]):  # tags where Recut should not be shown
                recut_button = QPushButton(self)
                recut_button.setText("Recut")
                recut_button.setObjectName("recut_button")
                recut_button.clicked.connect(partial(recut, item))
                h_layout.addWidget(recut_button)
            with contextlib.suppress(IndexError, KeyError):
                next_flow_tag = item.get_value("flow_tag")[item.get_value("current_flow_state") + 1]
                h_layout.addWidget(QLabel(workspace_tags.get_value("attributes")[next_flow_tag]["next_flow_tag_message"], self))
            # if item.get_value(key="recut_count") > 0:
            #     h_layout.addWidget(QLabel(f"Recut Count: {item.get_value(key='recut_count')}", self))

            table.setCellWidget(row_index, col_index, flow_tag_controls_widget)
            col_index += 1
            if item.get_value(key="completed") == False and workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                is_recording: bool = item.get_value("timers")[item_flow_tag].setdefault("recording", False)
                toggle_timer_button.setCheckable(True)
                toggle_timer_button.setChecked(is_recording)
                recording_widget.setHidden(not is_recording)
                toggle_timer_button.setObjectName("recording_button")
                toggle_timer_button.setText("Stop" if is_recording else "Start")
                toggle_timer_button.clicked.connect(partial(toggle_timer, item, toggle_timer_button, recording_widget))
                timer_layout.addWidget(toggle_timer_button)
                timer_layout.addWidget(recording_widget)
                table.setCellWidget(row_index, col_index, timer_widget)
                table.showColumn(10)

        row_index: int = 0
        for item in assembly.items:
            if item.get_value("show") == False:
                continue
            add_item(row_index, item)
            row_index += 1
        if row_index == 0:
            return QLabel("No Items to Show", self)

        table.itemChanged.connect(partial(self.assembly_items_table_cell_changed, table, assembly))
        table.itemClicked.connect(self.assembly_items_table_clicked)

        table.blockSignals(False)
        table.resizeColumnsToContents()
        self.workspace_tables[table] = assembly
        # header = table.horizontalHeader()
        # header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Set the first column to Fixed

        return table

    # USER
    def load_view_assembly_widget(self, assembly: Assembly, workspace_information: dict, group_color: str, parent=None) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setSpacing(1)
        layout.setContentsMargins(1, 1, 1, 1)
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(h_layout)
        # widget.setLayout(h_layout)
        timer_widget = QWidget()
        timer_layout = QHBoxLayout(timer_widget)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_widget.setLayout(timer_layout)
        # Create the "Items" group box
        items_groupbox = QGroupBox("Items")
        # items_groupbox.setMinimumHeight(500)
        items_layout = QVBoxLayout()
        items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        items_groupbox.setLayout(items_layout)

        # Create and configure the table widget
        if assembly.get_assembly_data("has_items"):
            table_widget = self.load_view_assembly_items_table(assembly)
            table_widget.setFixedHeight(40 * (len(assembly.items) + 2))
            # if isinstance(table_widget, QLabel): # Its empty
            #     return QLabel("Empty", self)

        def get_grid_widget() -> QWidget:
            # Add the table widget to the "Items" group box
            grid_widget = QWidget(widget)
            grid = QGridLayout(grid_widget)

            timer_widget = QWidget()
            timer_layout = QHBoxLayout(timer_widget)
            timer_layout.setContentsMargins(0, 0, 0, 0)
            timer_widget.setLayout(timer_layout)

            grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
            grid.addWidget(
                QLabel(
                    f"Timeline: {assembly.get_assembly_data('starting_date')} to {assembly.get_assembly_data('ending_date')}, ({QDate.fromString(assembly.get_assembly_data('starting_date'), 'yyyy-M-d').daysTo(QDate.fromString(assembly.get_assembly_data('ending_date'), 'yyyy-M-d'))} days)"
                ),
                0,
                0,
            )
            if assembly.all_sub_assemblies_complete() and assembly.all_items_complete():
                try:
                    assembly_flow_tag: str = assembly.get_assembly_data(key="flow_tag")[assembly.get_assembly_data(key="current_flow_state")]
                except IndexError:
                    return

                def toggle_timer(assembly: Assembly, toggle_timer_button: QPushButton, recording_widget: RecordingWidget) -> None:
                    assembly_flow_tag: str = assembly.get_assembly_data(key="flow_tag")[assembly.get_assembly_data(key="current_flow_state")]
                    timer_data = assembly.get_assembly_data(key="timers")
                    is_recording: bool = not timer_data[assembly_flow_tag]["recording"]
                    toggle_timer_button.setChecked(is_recording)
                    toggle_timer_button.setText("Stop" if is_recording else "Start")
                    recording_widget.setHidden(not is_recording)
                    timer_data[assembly_flow_tag]["recording"] = is_recording
                    if is_recording:
                        timer_data[assembly_flow_tag].setdefault("time_taken_intervals", [])
                        timer_data[assembly_flow_tag]["time_taken_intervals"].append([str(datetime.now())])
                    else:
                        timer_data[assembly_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                    assembly.set_assembly_data(key="timers", value=timer_data)
                    user_workspace.save()
                    self.sync_changes()

                def move_to_next_flow(assembly: Assembly) -> None:
                    item_flow_tag: str = assembly.get_assembly_data("flow_tag")[assembly.get_assembly_data("current_flow_state")]
                    if workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                        timer_data = assembly.get_assembly_data("timers")
                        try:
                            timer_data[item_flow_tag]["recording"]
                        except KeyError:
                            timer_data[item_flow_tag]["recording"] = False
                        if timer_data[item_flow_tag]["recording"]:
                            timer_data[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                            timer_data[item_flow_tag]["recording"] = False
                            assembly.set_assembly_data(key="timers", value=timer_data)
                    assembly.set_assembly_data(key="current_flow_state", value=assembly.get_assembly_data(key="current_flow_state") + 1)
                    assembly.set_assembly_data(key="status", value=None)
                    if assembly.get_assembly_data(key="current_flow_state") == len(assembly.get_assembly_data(key="flow_tag")):
                        assembly.set_assembly_data(key="completed", value=True)
                        assembly.set_assembly_data(key="date_completed", value=str(datetime.now()))
                        completed_assemblies: list[Assembly] = []
                        history_workspace.load_data()
                        for main_assembly in user_workspace.data:
                            # Assembly is 100% complete
                            if main_assembly.get_assembly_data(key="completed"):
                                completed_assemblies.append(main_assembly)
                                history_workspace.add_assembly(main_assembly)
                                history_workspace.save()
                                self.play_celebrate_sound()
                        for completed_assembly in completed_assemblies:
                            user_workspace.remove_assembly(completed_assembly)
                    user_workspace.save()
                    self.sync_changes()
                    self.load_workspace()

                def item_status_changed(status_box: QComboBox, assembly: Assembly, toggle_timer_button: QPushButton) -> None:
                    if (
                        workspace_tags.get_value("flow_tag_statuses")[
                            assembly.get_assembly_data("flow_tag")[assembly.get_assembly_data("current_flow_state")]
                        ][status_box.currentText()]["start_timer"]
                        and workspace_tags.get_value("attributes")[
                            assembly.get_assembly_data("flow_tag")[assembly.get_assembly_data("current_flow_state")]
                        ]["is_timer_enabled"]
                        and assembly.get_assembly_data("timers")[
                            assembly.get_assembly_data("flow_tag")[assembly.get_assembly_data("current_flow_state")]
                        ]["recording"]
                        == False
                    ):
                        toggle_timer_button.click()
                    if workspace_tags.get_value("flow_tag_statuses")[
                        assembly.get_assembly_data("flow_tag")[assembly.get_assembly_data("current_flow_state")]
                    ][status_box.currentText()]["completed"]:
                        move_to_next_flow(assembly=assembly)
                    else:
                        assembly.set_assembly_data(key="status", value=status_box.currentText())
                    user_workspace.save()
                    self.sync_changes()

                timer_widget = QWidget(self)
                timer_layout = QHBoxLayout(timer_widget)
                timer_widget.setLayout(timer_layout)
                recording_widget = RecordingWidget(timer_widget)
                toggle_timer_button = QPushButton(timer_widget)
                if workspace_tags.get_value("attributes")[assembly_flow_tag]["is_timer_enabled"]:
                    is_recording: bool = assembly.get_assembly_data(key="timers")[assembly_flow_tag].setdefault("recording", False)
                    toggle_timer_button.setCheckable(True)
                    toggle_timer_button.setChecked(is_recording)
                    recording_widget.setHidden(not is_recording)
                    toggle_timer_button.setObjectName("recording_button")
                    toggle_timer_button.setText("Stop" if is_recording else "Start")
                    toggle_timer_button.clicked.connect(partial(toggle_timer, assembly, toggle_timer_button, recording_widget))
                    timer_layout.addWidget(toggle_timer_button)
                    timer_layout.addWidget(recording_widget)
                    grid.addWidget(QLabel("Timer:"), 1, 1)
                    grid.addWidget(timer_widget, 1, 2)

                flow_tag_controls_widget = QWidget(self)
                h_layout = QHBoxLayout(flow_tag_controls_widget)
                flow_tag_controls_widget.setLayout(h_layout)
                # h_layout.setSpacing(0)
                h_layout.setContentsMargins(0, 0, 0, 0)
                if not list(workspace_tags.get_value("flow_tag_statuses")[assembly_flow_tag].keys()):
                    with contextlib.suppress(IndexError):
                        button_next_flow_state = QPushButton(self)
                        button_next_flow_state.setObjectName("flow_tag_button")
                        button_flow_state_name: str = "Mark as Done!"
                        if "bend" in assembly_flow_tag.lower():
                            button_flow_state_name = "Bent"
                        if "weld" in assembly_flow_tag.lower():
                            button_flow_state_name = "Welded"
                        if "cut" in assembly_flow_tag.lower():
                            button_flow_state_name = "Laser Cut"
                        if "paint" in assembly_flow_tag.lower():
                            button_flow_state_name = "Painted"
                        if "pick" in assembly_flow_tag.lower():
                            button_flow_state_name = "Picked"
                        if "assem" in assembly_flow_tag.lower():
                            button_flow_state_name = "Assembled"
                        button_next_flow_state.setText(button_flow_state_name)
                        button_next_flow_state.clicked.connect(partial(move_to_next_flow, assembly))
                        # QTableWidgetItem(item.data["flow_tag"][item.data["current_flow_state"]])
                        h_layout.addWidget(button_next_flow_state)
                        grid.addWidget(QLabel("Flow Tag:"), 0, 1)
                        grid.addWidget(button_next_flow_state, 0, 2)
                        with contextlib.suppress(IndexError):
                            next_flow_tag = assembly.get_assembly_data(key="flow_tag")[assembly.get_assembly_data(key="current_flow_state") + 1]
                            grid.addWidget(
                                QLabel(workspace_tags.get_value("attributes")[next_flow_tag]["next_flow_tag_message"], self),
                                0,
                                3,
                            )
                else:
                    status_box = QComboBox(self)
                    status_box.setObjectName("flow_tag_status_button")
                    status_box.addItems(list(workspace_tags.get_value("flow_tag_statuses")[assembly_flow_tag].keys()))
                    status_box.setCurrentText(assembly.get_assembly_data("status"))
                    status_box.currentTextChanged.connect(partial(item_status_changed, status_box, assembly, toggle_timer_button))
                    # table.setCellWidget(row_index, col_index, status_box)
                    grid.addWidget(QLabel("Status:"), 0, 1)
                    grid.addWidget(status_box, 0, 2)
                    with contextlib.suppress(IndexError, KeyError):
                        next_flow_tag = assembly.get_assembly_data(key="flow_tag")[assembly.get_assembly_data(key="current_flow_state") + 1]
                        grid.addWidget(
                            QLabel(workspace_tags.get_value("attributes")[next_flow_tag]["next_flow_tag_message"], self),
                            0,
                            3,
                        )
                if all(keyword not in assembly_flow_tag for keyword in ["paint", "powder"]) and assembly.get_assembly_data(key="paint_color") != None:
                    paint_color: str = "None"
                    for color_name, color_code in workspace_tags.get_value("paint_colors").items():
                        if color_code == assembly.get_assembly_data(key="paint_color"):
                            paint_color = color_name
                    paint_type: str = assembly.get_assembly_data(key="paint_type")
                    paint_amount: float = assembly.get_assembly_data(key="paint_amount")
                    grid.addWidget(
                        QLabel(f'Assembly needs to be painted "{paint_color}" using "{paint_type}", the expected amount is {paint_amount} gallons'),
                        0,
                        4,
                    )

            return grid_widget

        grid_widget = get_grid_widget()

        if assembly.get_assembly_data("has_items"):
            items_layout.addWidget(table_widget)
        h_layout.addWidget(grid_widget)
        # h_layout.addWidget(timer_widget)

        # Add the "Items" group box to the main layout
        # if assembly.get_assembly_data("has_items") and user_workspace.is_assembly_empty(assembly=assembly):
        #     layout.addWidget(items_groupbox)

        # Create the MultiToolBox for sub assemblies
        workspace_information.setdefault(assembly.name, {"tool_box": None, "sub_assemblies": {}})
        try:
            workspace_information[assembly.name]["tool_box"] = workspace_information[assembly.name]["tool_box"].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        sub_assemblies_toolbox = MultiToolBox(widget)
        sub_assemblies_toolbox.layout().setSpacing(0)
        # if assembly.get_assembly_data("has_sub_assemblies"):
        sub_assembly_groupbox = QGroupBox("Sub Assemblies")
        sub_assembly_groupbox_layout = QVBoxLayout()
        sub_assembly_groupbox.setLayout(sub_assembly_groupbox_layout)
        # Add the sub assemblies MultiToolBox to the main layout
        sub_assembly_groupbox_layout.addWidget(sub_assemblies_toolbox)
        # if len(assembly.sub_assemblies) > 0:
        if assembly.get_assembly_data("has_items"):
            layout.addWidget(items_groupbox)
        # added_items_group_widget = True
        # if not added_sub_assemblies_group_widget:
        # added_sub_assemblies_group_widget = True
        for i, sub_assembly in enumerate(assembly.sub_assemblies):
            if sub_assembly.get_assembly_data(key="show") == True and sub_assembly.get_assembly_data(key="completed") == False:
                sub_assembly_widget = self.load_view_assembly_widget(
                    assembly=sub_assembly, workspace_information=workspace_information[assembly.name]["sub_assemblies"], group_color=group_color
                )
                sub_assemblies_toolbox.addItem(sub_assembly_widget, f"{sub_assembly.name}", base_color=group_color)
                # sub_assemblies_toolbox.close(i)
        sub_assemblies_toolbox.close_all()
        if saved_workspace_prefs:
            sub_assemblies_toolbox.set_widgets_visibility(workspace_information[assembly.name]["tool_box"])
        workspace_information[assembly.name]["tool_box"] = sub_assemblies_toolbox
        if len(sub_assemblies_toolbox.widgets) > 0:
            layout.addWidget(sub_assembly_groupbox)
        return widget

    # USER
    def load_view_table_summary(self) -> None:
        selected_tab: str = self.tab_widget.tabText(self.tab_widget.currentIndex())
        if selected_tab == "Recut":
            self.workspace_filter["show_recut"] = True
            with contextlib.suppress(AttributeError):
                self.workspace_filter_tab_widget.clear_selections("Flow Tags")
        else:
            self.workspace_filter["show_recut"] = False
        scroll_area = QScrollArea()

        def save_scroll_position(tab_name: str, scroll: QScrollArea):
            self.scroll_position_manager.save_scroll_position(tab_name=tab_name, scroll=scroll)

        scroll_area.verticalScrollBar().valueChanged.connect(
            partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} table_summary {self.category}", scroll_area)
        )
        scroll_area.horizontalScrollBar().valueChanged.connect(
            partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} table_summary {self.category}", scroll_area)
        )
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(self)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(1)
        scroll_area.setWidget(scroll_content)

        workspace_data = user_workspace.get_filtered_data(self.workspace_filter)
        grouped_items: ItemGroup = user_workspace.get_grouped_items()
        # Need to all have same flow tag
        grouped_items.filter_items(flow_tag=self.category)

        headers: list[str] = [
            "Item Name",  # 0
            "Bending Files",  # 1
            "Welding Files",  # 2
            "CNC/Milling Files",  # 3
            "Thickness",  # 4
            "Material Type",  # 5
            "Paint Type",  # 6
            "Paint Color",  # 7
            "Quantity",  # 8
            "Flow Tag Controls",  # 9
            "Set Timers",  # 10
        ]
        #     table.setStyleSheet(
        #     f"QTableView {{ gridline-color: white; }} QTableWidget::item {{ border-color: white; }}"
        # )

        table = CustomTableWidget(scroll_content)
        table.blockSignals(True)
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setFont(self.tables_font)
        table.setShowGrid(True)
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.hideColumn(1)
        table.hideColumn(2)
        table.hideColumn(3)
        table.hideColumn(6)
        table.hideColumn(7)
        table.hideColumn(10)

        def toggle_timer(item_name: str, toggle_timer_button: QPushButton, recording_widget: RecordingWidget) -> None:
            for item in grouped_items.data[item_name]:
                item_flow_tag: str = item.get_value("flow_tag")[item.get_value("current_flow_state")]
                timer_data = item.get_value("timers")
                try:
                    is_recording: bool = not timer_data[item_flow_tag]["recording"]
                except KeyError:
                    is_recording: bool = True
                toggle_timer_button.setChecked(is_recording)
                toggle_timer_button.setText("Stop" if is_recording else "Start")
                recording_widget.setHidden(not is_recording)
                timer_data[item_flow_tag]["recording"] = is_recording
                if is_recording:
                    timer_data[item_flow_tag].setdefault("time_taken_intervals", [])
                    timer_data[item_flow_tag]["time_taken_intervals"].append([str(datetime.now())])
                else:
                    timer_data[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                item.set_value(key="timers", value=timer_data)

            user_workspace.save()
            self.sync_changes()

        def recut(item_name: str) -> None:
            max_recut_count: int = 0
            item = grouped_items.get_item(item_name)
            for item in grouped_items.get_item_list(item_name):
                max_recut_count = item.get_value(key="parts_per")
                if max_recut_count != 0:
                    break
            if max_recut_count == 0:
                self.show_message_dialog(title="No More Quantity", message="Quantity limit exceeded")
                return
            input_dialog = RecutDialog(title="Set Recut Count", message=f"Select or Input recut count for: {item.name}", max_value=max_recut_count)
            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.ok:
                    recut_count = int(input_dialog.inputText)
                    parent_assembly = item.parent_assembly
                    new_item = Item(name=f"{item.name} - Recut #{item.get_value('recut_count') + 1}", data=item.copy_data())
                    new_item.set_value(key="parts_per", value=recut_count)
                    new_item.set_value(key="current_flow_state", value=new_item.get_value("flow_tag").index("Laser Cutting"))
                    new_item.set_value(key="recut", value=True)
                    parent_assembly.add_item(new_item)
                    item.set_value(key="recut_count", value=item.get_value("recut_count") + 1)
                    item.set_value(key="parts_per", value=item.get_value(key="parts_per") - recut_count)
                    user_workspace.save()
                    self.sync_changes()
                    self.load_workspace()

        def move_to_next_flow(item_name: str, row_index: int) -> None:
            for item in grouped_items.data[item_name]:
                item_flow_tag: str = item.get_value("flow_tag")[item.get_value("current_flow_state")]
                if workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                    timer_data = item.get_value("timers")
                    try:
                        timer_data[item_flow_tag]["recording"]
                    except KeyError:
                        timer_data[item_flow_tag]["recording"] = False
                    if timer_data[item_flow_tag]["recording"]:
                        timer_data[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                        timer_data[item_flow_tag]["recording"] = False
                        item.set_value(key="timers", value=timer_data)
                if item_flow_tag == "Laser Cutting":
                    item.set_value(key="recut", value=False)
                item.set_value(key="current_flow_state", value=item.get_value(key="current_flow_state") + 1)
                item.set_value(key="status", value=None)
                if item.get_value(key="current_flow_state") == len(item.get_value(key="flow_tag")):
                    item.set_value(key="completed", value=True)
                    item.set_value(key="date_completed", value=str(datetime.now()))
                    assembly: Assembly = item.parent_assembly
                    if assembly.get_assembly_data('current_flow_state') == -1: # NOTE Custom Job
                        completed_assemblies: list[Assembly] = []
                        history_workspace.load_data()
                        for main_assembly in user_workspace.data:
                            # Assembly is 100% complete
                            if user_workspace.get_completion_percentage(main_assembly)[0] == 1.0:
                                main_assembly.set_assembly_data(key='completed', value=True)
                                completed_assemblies.append(main_assembly)
                                history_workspace.add_assembly(main_assembly)
                                history_workspace.save()
                                self.play_celebrate_sound()
                        for completed_assembly in completed_assemblies:
                            user_workspace.remove_assembly(completed_assembly)
            user_workspace.save()
            self.sync_changes()
            self.load_workspace()

        def item_status_changed(status_box: QComboBox, item_name: str, row_index: int, toggle_timer_button: QPushButton) -> None:
            for item in grouped_items.data[item_name]:
                if (
                    workspace_tags.get_value("flow_tag_statuses")[item.get_value("flow_tag")[item.get_value("current_flow_state")]][
                        status_box.currentText()
                    ]["start_timer"]
                    and workspace_tags.get_value("attributes")[item.get_value("flow_tag")[item.get_value("current_flow_state")]]["is_timer_enabled"]
                    and item.get_value("timers")[item.get_value("flow_tag")[item.get_value("current_flow_state")]]["recording"] == False
                ):
                    toggle_timer_button.click()
                if workspace_tags.get_value("flow_tag_statuses")[item.get_value("flow_tag")[item.get_value("current_flow_state")]][
                    status_box.currentText()
                ]["completed"]:
                    # grouped_items.update_values(item_to_update=item_name, key="status", value=status_box.currentText())
                    move_to_next_flow(item_name=item.name, row_index=row_index)
                else:
                    item.set_value(key="status", value=status_box.currentText())
                    # grouped_items.update_values(item_to_update=item_name, key="status", value=status_box.currentText())

            user_workspace.save()
            self.sync_changes()

        def add_item(row_index: int, item_name: str):
            first_item: Item = grouped_items.get_item(item_name=item_name)
            item_flow_tag: str = first_item.get_value("flow_tag")[first_item.get_value("current_flow_state")]
            col_index: int = 0
            table.insertRow(row_index)
            table.setRowHeight(row_index, 50)
            table.setItem(row_index, col_index, QTableWidgetItem(item_name))  # 0
            table.item(row_index, col_index).setToolTip(f"Items: {grouped_items.to_string(item_name)}")
            col_index += 1
            for file_column in ["Bending Files", "Welding Files", "CNC/Milling Files"]:
                button_widget = QWidget()
                files_layout = QHBoxLayout()
                files_layout.setContentsMargins(0, 0, 0, 0)
                files_layout.setSpacing(0)
                button_widget.setLayout(files_layout)
                self.load_assemblies_items_file_layout(
                    file_category=file_column,
                    files_layout=files_layout,
                    assembly=first_item.parent_assembly,
                    item=first_item,
                    show_dropped_widget=False,
                )
                table.setCellWidget(row_index, col_index, button_widget)
                col_index += 1
            if "bend" in item_flow_tag.lower():
                table.showColumn(1)
            elif "weld" in item_flow_tag.lower():
                table.showColumn(2)
            elif "cut" in item_flow_tag.lower():
                table.showColumn(3)
            if "paint" in item_flow_tag.lower():
                table.showColumn(6)
                table.showColumn(7)

            table.setItem(row_index, col_index, QTableWidgetItem(first_item.data["thickness"]))  # 4
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(first_item.data["material"]))  # 5
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(str(first_item.data["paint_type"])))  # 6
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1
            button_color = QComboBox(self)
            button_color.setEnabled(False)
            if first_item.get_value("paint_color") != None:
                for color_name, color_code in workspace_tags.get_value("paint_colors").items():
                    if color_code == first_item.get_value("paint_color"):
                        button_color.addItem(color_name)
                        button_color.setCurrentText(color_name)
                        button_color.setStyleSheet(
                            f'QComboBox{{border-radius: 0.001em; background-color: {first_item.get_value("paint_color")}}} {"QMenu { background-color: rgb(22,22,22);}"}'
                        )
                        break
            table.setCellWidget(row_index, col_index, button_color)  # 7
            col_index += 1
            table.setItem(row_index, col_index, QTableWidgetItem(str(grouped_items.get_total_quantity(item_name))))  # 8
            table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            col_index += 1

            # timer_box = QComboBox(self)
            # timer_box.addItems(["Set Timer For"] + item.data["flow_tag"])
            # timer_box.setCurrentIndex(0)
            # timer_box.currentTextChanged.connect(partial(set_timer, timer_box, item))
            # timer_widget = QWidget()
            # timer_layout = QHBoxLayout(timer_widget)
            # timer_layout.setContentsMargins(0, 0, 0, 0)
            # timer_widget.setLayout(timer_layout)

            # current_tag = QComboBox(self)
            # current_tag.wheelEvent = lambda event: event.ignore()
            # current_tag.setObjectName("tag_box")
            # current_tag.setStyleSheet("QComboBox#tag_box{margin: 2px;}")
            flow_tag_controls_widget = QWidget(self)
            h_layout = QHBoxLayout(flow_tag_controls_widget)
            flow_tag_controls_widget.setLayout(h_layout)
            h_layout.setSpacing(0)
            h_layout.setContentsMargins(0, 0, 0, 0)

            timer_widget = QWidget(self)
            timer_layout = QHBoxLayout(timer_widget)
            timer_widget.setLayout(timer_layout)
            recording_widget = RecordingWidget(timer_widget)
            toggle_timer_button = QPushButton(timer_widget)

            if self.category != "Recut":
                if not list(workspace_tags.get_value("flow_tag_statuses")[item_flow_tag].keys()):
                    try:
                        button_next_flow_state = QPushButton(self)
                        button_next_flow_state.setFixedHeight(50)
                        button_next_flow_state.setObjectName("flow_tag_button")
                        button_flow_state_name: str = "Mark as Done!"
                        if "bend" in item_flow_tag.lower():
                            button_flow_state_name = "Bent"
                        if "weld" in item_flow_tag.lower():
                            button_flow_state_name = "Welded"
                        if "cut" in item_flow_tag.lower():
                            button_flow_state_name = "Laser Cut"
                        if "paint" in item_flow_tag.lower():
                            button_flow_state_name = "Painted"
                        if "pick" in item_flow_tag.lower():
                            button_flow_state_name = "Picked"
                        if "assem" in item_flow_tag.lower():
                            button_flow_state_name = "Assembled"
                        button_next_flow_state.setText(button_flow_state_name)
                        button_next_flow_state.clicked.connect(partial(move_to_next_flow, item_name, row_index))
                        button_next_flow_state.setStyleSheet("border-radius: 0.001em;")
                        h_layout.addWidget(button_next_flow_state)
                    except IndexError:
                        table.setItem(row_index, col_index, QTableWidgetItem("Null"))
                        table.item(row_index, col_index).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                else:
                    status_box = QComboBox(self)
                    status_box.setFixedHeight(50)
                    status_box.setObjectName("flow_tag_status_button")
                    status_box.addItems(list(workspace_tags.get_value("flow_tag_statuses")[item_flow_tag].keys()))
                    status_box.setCurrentText(first_item.get_value("status"))
                    status_box.setStyleSheet("border-radius: 0.001em;")
                    status_box.currentTextChanged.connect(partial(item_status_changed, status_box, item_name, row_index, toggle_timer_button))
                    # table.setCellWidget(row_index, col_index, status_box)
                    h_layout.addWidget(status_box)
            else:
                button_next_flow_state = QPushButton(self)
                button_next_flow_state.setObjectName("flow_tag_button")
                button_next_flow_state.setText("Laser Cut")
                button_next_flow_state.clicked.connect(partial(move_to_next_flow, item_name, row_index))
                button_next_flow_state.setStyleSheet("border-radius: 0.001em;")
                h_layout.addWidget(button_next_flow_state)
            if all(tag not in item_flow_tag.lower() for tag in ["laser", "quote", "ship"]):  # tags where Recut should not be shown
                recut_button = QPushButton(self)
                recut_button.setText("Recut")
                recut_button.setObjectName("recut_button")
                recut_button.clicked.connect(partial(recut, item_name))
                h_layout.addWidget(recut_button)
            with contextlib.suppress(IndexError, KeyError):
                next_flow_tag = first_item.get_value("flow_tag")[first_item.get_value("current_flow_state") + 1]
                h_layout.addWidget(QLabel(workspace_tags.get_value("attributes")[next_flow_tag]["next_flow_tag_message"], self))
            table.setCellWidget(row_index, col_index, flow_tag_controls_widget)
            col_index += 1

            if workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                is_recording: bool = first_item.get_value("timers")[item_flow_tag].setdefault("recording", False)
                toggle_timer_button.setCheckable(True)
                toggle_timer_button.setChecked(is_recording)
                recording_widget.setHidden(not is_recording)
                toggle_timer_button.setObjectName("recording_button")
                toggle_timer_button.setText("Stop" if is_recording else "Start")
                toggle_timer_button.clicked.connect(partial(toggle_timer, item_name, toggle_timer_button, recording_widget))
                timer_layout.addWidget(toggle_timer_button)
                timer_layout.addWidget(recording_widget)
                table.setCellWidget(row_index, col_index, timer_widget)
                table.showColumn(10)

        row_index: int = 0
        for item_name, items in grouped_items.data.items():
            if len(items) == 0:
                continue
            # if item.get_value("show") == False or item.get_value("completed") == True:
            add_item(row_index, item_name)
            row_index += 1
        # Creating Context Menu
        table.blockSignals(False)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        menu = QMenu(self)
        if self.category != "Recut" and len(workspace_tags.get_value("flow_tag_statuses")[self.category]) > 0:
            set_status_menu = QMenu("Set Status", self)
            for status in workspace_tags.get_value("flow_tag_statuses")[self.category]:
                status_action = QAction(status, self)
                status_action.triggered.connect(partial(self.change_selected_table_items_status, table, grouped_items, status))
                set_status_menu.addAction(status_action)
            menu.addMenu(set_status_menu)
        done_action = QAction("Mark all as Done", self)
        done_action.triggered.connect(partial(self.move_selected_table_items_to_next_flow_state, table, grouped_items))
        menu.addAction(done_action)
        download_action = QAction("Download all files", self)
        download_action.triggered.connect(partial(self.download_all_selected_items_files, table, grouped_items))
        menu.addAction(download_action)
        table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

        scroll_layout.addWidget(table)
        table.resizeColumnsToContents()

        if row_index == 0:
            self.tab_widget.currentWidget().layout().addWidget(QLabel("No Items to Show", self))
        else:
            self.tab_widget.currentWidget().layout().addWidget(scroll_area)
        self.scroll_position_manager.restore_scroll_position(
            tab_name=f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} table_summary {self.category}", scroll=scroll_area
        )

    # USER
    def load_view_assembly_tab(self) -> None:
        selected_tab: str = self.tab_widget.tabText(self.tab_widget.currentIndex())
        self.workspace_filter["show_recut"] = selected_tab == "Recut"
        self.workspace_information.setdefault(selected_tab, {"group_tool_box": None})
        try:
            self.workspace_information[selected_tab]["group_tool_box"] = self.workspace_information[selected_tab][
                "group_tool_box"
            ].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        with contextlib.suppress(AttributeError):
            self.workspace_filter_tab_widget.clear_selections("Flow Tags")
            self.workspace_filter_tab_widget.enable_button(selected_tab)
        if self.pushButton_show_sub_assembly.isChecked():
            scroll_area = QScrollArea()

            def save_scroll_position(tab_name: str, scroll: QScrollArea):
                self.scroll_position_manager.save_scroll_position(tab_name=tab_name, scroll=scroll)

            scroll_area.verticalScrollBar().valueChanged.connect(
                partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} {self.category}", scroll_area)
            )
            scroll_area.horizontalScrollBar().valueChanged.connect(
                partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} {self.category}", scroll_area)
            )
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget(self)
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_layout.setContentsMargins(0, 0, 0, 0)
            scroll_layout.setSpacing(1)
            scroll_area.setWidget(scroll_content)
            filtered_data = user_workspace.get_filtered_data(self.workspace_filter)
            group_tool_boxes: dict[str, QWidget] = {}
            group_tool_box = MultiToolBox(scroll_content)
            for group in user_workspace.get_all_groups():
                group_widget = QWidget()
                group_layout = QVBoxLayout(group_widget)
                group_widget.setLayout(group_layout)
                group_tool_box.addItem(group_widget, group, base_color=user_workspace.get_group_color(group))
                group_tool_boxes[group] = group_widget
                self.workspace_information[selected_tab].setdefault(group, {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None})
            group_tool_box.close_all()
            if saved_workspace_prefs:
                group_tool_box.set_widgets_visibility(self.workspace_information[selected_tab]["group_tool_box"])
            self.workspace_information[selected_tab]["group_tool_box"] = group_tool_box
            if len(group_tool_box.buttons) == 0:
                scroll_layout.addWidget(QLabel("Nothing to show.", self))
            else:
                scroll_layout.addWidget(group_tool_box)
            grouped_data = user_workspace.get_grouped_data()
            for group in grouped_data:
                try:
                    self.workspace_information[selected_tab][group]["tool_box"] = self.workspace_information[selected_tab][group][
                        "tool_box"
                    ].get_widget_visibility()
                    saved_workspace_prefs = True
                except (AttributeError, RuntimeError):
                    saved_workspace_prefs = False
                multi_tool_box = MultiToolBox()
                multi_tool_box.layout().setSpacing(0)
                for assembly in grouped_data[group]:
                    if assembly.get_assembly_data(key="show") == True and assembly.get_assembly_data(key="completed") == False:
                        assembly_widget = self.load_view_assembly_widget(
                            assembly=assembly,
                            workspace_information=self.workspace_information[selected_tab][group]["sub_assemblies"],
                            group_color=user_workspace.get_group_color(group),
                        )
                        multi_tool_box.addItem(
                            assembly_widget,
                            f'{assembly.get_assembly_data(key="display_name")} - Items: {user_workspace.get_completion_percentage(assembly)[0]*100}% - Assemblies: {user_workspace.get_completion_percentage(assembly)[1]*100}%',
                            base_color=user_workspace.get_group_color(group),
                        )
                group_tool_boxes[group].layout().addWidget(multi_tool_box)
                multi_tool_box.close_all()
                if saved_workspace_prefs:
                    multi_tool_box.set_widgets_visibility(self.workspace_information[selected_tab][group]["tool_box"])
                # else:

                self.workspace_information[selected_tab][group]["tool_box"] = multi_tool_box
            self.tab_widget.currentWidget().layout().addWidget(scroll_area)
            self.scroll_position_manager.restore_scroll_position(
                tab_name=f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} {self.category}", scroll=scroll_area
            )
        elif self.pushButton_show_item_summary.isChecked():
            self.load_view_table_summary()
        self.load_view_assembly_context_menus()

    # PLANNING
    def load_planning_assembly_items_table(self, assembly: Assembly) -> CustomTableWidget:
        workspace_tags.load_data()
        headers: list[str] = ["Name", "Set Date", "Current Timeline"]  # 0  # 1  # 2

        table = CustomTableWidget(self)
        # table.hideColumn()
        table.blockSignals(True)
        table.setRowCount(0)
        table.setColumnCount(len(headers))
        table.setFont(self.tables_font)
        table.setShowGrid(True)
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        item_group = ItemGroup()

        for item in assembly.items:
            item_group.add_item_to_group(group_name=f'{item.data.get("material")} {item.data.get("thickness")}', item=item)

        def get_date_edit_widget(row_index: int, group_name: str) -> QWidget:
            widget = QWidget()
            h_layout = QHBoxLayout(widget)
            h_layout.setSpacing(0)
            h_layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(h_layout)

            def set_time_line():
                timeline_dialog = SelectTimeLineDialog(
                    self,
                    button_names=DialogButtons.set_cancel,
                    title="Set Timeline",
                    message=f"Set timeline for all items in {group}",
                    starting_date=item_group.get_item(group).get_value("starting_date"),
                    ending_date=item_group.get_item(group).get_value("ending_date"),
                )
                if timeline_dialog.exec():
                    if timeline_dialog.get_response() == DialogButtons.set:
                        timeline = timeline_dialog.get_timeline()
                        start_time: QDate = timeline[0]
                        end_time: QDate = timeline[1]

                        string_start_time = start_time.toString("yyyy-M-d")
                        string_end_time = end_time.toString("yyyy-M-d")

                        for item in item_group.get_item_list(group_name):
                            item.set_value("starting_date", string_start_time)
                            item.set_value("ending_date", string_end_time)
                        user_workspace.save()
                        self.upload_file(
                            [
                                "workspace - User.json",
                            ],
                            False,
                        )

                        table.setItem(
                            row_index,
                            2,
                            QTableWidgetItem(f"{string_start_time} to {string_end_time}, ({start_time.daysTo(end_time)} days)"),
                        )  # 0
                    else:
                        return

            set_date = QPushButton("Set Timeline")
            set_date.setFixedHeight(50)
            set_date.setStyleSheet("border-radius: none;")
            set_date.clicked.connect(set_time_line)

            h_layout.addWidget(set_date)

            return widget

        def add_item(row_index: int, group: str):
            col_index: int = 0
            table.insertRow(row_index)
            table.setRowHeight(row_index, 50)
            items_count = len(item_group.get_item_list(group))
            table.setItem(row_index, col_index, QTableWidgetItem(f'{group} - ({items_count} item{"s" if items_count > 1 else ""})'))  # 0
            items_tool_tip: str = ""
            for i, item in enumerate(item_group.get_item_list(group), start=1):
                items_tool_tip += f"{i}. {item.name}\n"
            table.item(row_index, col_index).setToolTip(items_tool_tip)
            col_index += 1
            table.setCellWidget(row_index, col_index, get_date_edit_widget(row_index, group))  # 4
            col_index += 1
            table.setItem(
                row_index,
                col_index,
                QTableWidgetItem(
                    f'{item_group.get_item(group).get_value("starting_date")} to {item_group.get_item(group).get_value("ending_date")}, ({QDate.fromString(item_group.get_item(group).get_value("starting_date"), "yyyy-M-d").daysTo(QDate.fromString(item_group.get_item(group).get_value("ending_date"), "yyyy-M-d"))} days)'
                ),
            )  # 0
            table.resizeColumnsToContents()

        row_index: int = 0
        for group in item_group.data:
            add_item(row_index, group)
            row_index += 1
        if row_index == 0:
            return QLabel("No Items to Show", self)

        table.blockSignals(False)
        table.resizeColumnsToContents()
        self.workspace_tables[table] = assembly
        # header = table.horizontalHeader()
        # header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Set the first column to Fixed

        return table

    # PLANNING
    def load_planning_assembly_widget(self, assembly: Assembly, workspace_information: dict, group_color: str, parent=None) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setSpacing(1)
        layout.setContentsMargins(1, 1, 1, 1)
        h_layout = QHBoxLayout()
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(h_layout)
        # widget.setLayout(h_layout)
        timer_widget = QWidget()
        timer_layout = QHBoxLayout(timer_widget)
        timer_layout.setContentsMargins(0, 0, 0, 0)
        timer_widget.setLayout(timer_layout)
        # Create the "Items" group box
        items_groupbox = QGroupBox("Items")
        # items_groupbox.setMinimumHeight(500)
        items_layout = QVBoxLayout()
        items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        items_groupbox.setLayout(items_layout)

        # Create and configure the table widget
        if assembly.get_assembly_data("has_items"):
            table_widget = self.load_planning_assembly_items_table(assembly)
            table_widget.setFixedHeight(40 * (len(assembly.items) + 2))
            # if isinstance(table_widget, QLabel): # Its empty
            #     return QLabel("Empty", self)

        def get_grid_widget() -> QWidget:
            # Add the table widget to the "Items" group box
            grid_widget = QWidget(widget)
            grid = QGridLayout(grid_widget)
            grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
            timeline_label = QLabel(
                f"{assembly.get_assembly_data('starting_date')} to {assembly.get_assembly_data('ending_date')}, ({QDate.fromString(assembly.get_assembly_data('starting_date'), 'yyyy-M-d').daysTo(QDate.fromString(assembly.get_assembly_data('ending_date'), 'yyyy-M-d'))} days)"
            )

            def set_time_line():
                timeline_dialog = SelectTimeLineDialog(
                    self,
                    button_names=DialogButtons.set_cancel,
                    title="Set Timeline",
                    message=f"Set timeline for sub assembly: {assembly.name}",
                    starting_date=assembly.get_assembly_data("starting_date"),
                    ending_date=assembly.get_assembly_data("ending_date"),
                )
                if timeline_dialog.exec():
                    if timeline_dialog.get_response() == DialogButtons.set:
                        timeline = timeline_dialog.get_timeline()
                        start_time: QDate = timeline[0]
                        end_time: QDate = timeline[1]

                        string_start_time = start_time.toString("yyyy-M-d")
                        string_end_time = end_time.toString("yyyy-M-d")

                        assembly.set_assembly_data("starting_date", string_start_time)
                        assembly.set_assembly_data("ending_date", string_end_time)

                        user_workspace.save()
                        self.upload_file(
                            [
                                "workspace - User.json",
                            ],
                            False,
                        )

                        timeline_label.setText(f"{string_start_time} to {string_end_time}, ({start_time.daysTo(end_time)} days)")
                    else:
                        return

            set_date = QPushButton("Set Timeline")
            set_date.clicked.connect(set_time_line)
            grid.addWidget(set_date, 0, 1)
            grid.addWidget(timeline_label, 0, 2)

            return grid_widget

        grid_widget = get_grid_widget()

        if assembly.get_assembly_data("has_items"):
            items_layout.addWidget(table_widget)
        h_layout.addWidget(grid_widget)
        # Create the MultiToolBox for sub assemblies
        workspace_information.setdefault(assembly.name, {"tool_box": None, "sub_assemblies": {}})
        try:
            workspace_information[assembly.name]["tool_box"] = workspace_information[assembly.name]["tool_box"].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        sub_assemblies_toolbox = MultiToolBox(widget)
        sub_assemblies_toolbox.layout().setSpacing(0)
        # if assembly.get_assembly_data("has_sub_assemblies"):
        sub_assembly_groupbox = QGroupBox("Sub Assemblies")
        sub_assembly_groupbox_layout = QVBoxLayout()
        sub_assembly_groupbox.setLayout(sub_assembly_groupbox_layout)
        # Add the sub assemblies MultiToolBox to the main layout
        sub_assembly_groupbox_layout.addWidget(sub_assemblies_toolbox)
        # if len(assembly.sub_assemblies) > 0:
        if assembly.get_assembly_data("has_items"):
            layout.addWidget(items_groupbox)
        # added_items_group_widget = True
        # if not added_sub_assemblies_group_widget:
        # added_sub_assemblies_group_widget = True
        for i, sub_assembly in enumerate(assembly.sub_assemblies):
            if sub_assembly.get_assembly_data(key="show") == True and sub_assembly.get_assembly_data(key="completed") == False:
                sub_assembly_widget = self.load_planning_assembly_widget(
                    assembly=sub_assembly, workspace_information=workspace_information[assembly.name]["sub_assemblies"], group_color=group_color
                )
                sub_assemblies_toolbox.addItem(sub_assembly_widget, f"{sub_assembly.name}", base_color=group_color)
                # sub_assemblies_toolbox.close(i)
        sub_assemblies_toolbox.close_all()
        if saved_workspace_prefs:
            sub_assemblies_toolbox.set_widgets_visibility(workspace_information[assembly.name]["tool_box"])
        workspace_information[assembly.name]["tool_box"] = sub_assemblies_toolbox
        if len(sub_assemblies_toolbox.widgets) > 0:
            layout.addWidget(sub_assembly_groupbox)
        return widget

    # PLANNING
    def load_planning_assembly_tab(self) -> None:
        self.workspace_information.setdefault("Planning", {"group_tool_box": None})
        try:
            self.workspace_information["Planning"]["group_tool_box"] = self.workspace_information["Planning"][
                "group_tool_box"
            ].get_widget_visibility()
            saved_workspace_prefs = True
        except (AttributeError, RuntimeError):
            saved_workspace_prefs = False
        with contextlib.suppress(AttributeError):
            self.workspace_filter_tab_widget.clear_selections("Flow Tags")
        scroll_area = QScrollArea()

        def save_scroll_position(tab_name: str, scroll: QScrollArea):
            self.scroll_position_manager.save_scroll_position(tab_name=tab_name, scroll=scroll)

        scroll_area.verticalScrollBar().valueChanged.connect(
            partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} Planning", scroll_area)
        )
        scroll_area.horizontalScrollBar().valueChanged.connect(
            partial(save_scroll_position, f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} Planning", scroll_area)
        )
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget(self)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(1)
        scroll_area.setWidget(scroll_content)
        filtered_data = user_workspace.get_filtered_data(self.workspace_filter)
        group_tool_boxes: dict[str, QWidget] = {}
        group_tool_box = MultiToolBox(scroll_content)
        for group in user_workspace.get_all_groups():
            group_widget = QWidget()
            group_layout = QVBoxLayout(group_widget)
            group_widget.setLayout(group_layout)
            group_tool_box.addItem(group_widget, group, base_color=user_workspace.get_group_color(group))
            group_tool_boxes[group] = group_widget
            self.workspace_information["Planning"].setdefault(group, {"tool_box": None, "sub_assemblies": {}, "group_tool_box": None})
        group_tool_box.close_all()
        if saved_workspace_prefs:
            group_tool_box.set_widgets_visibility(self.workspace_information["Planning"]["group_tool_box"])
        self.workspace_information["Planning"]["group_tool_box"] = group_tool_box
        if len(group_tool_box.buttons) == 0:
            scroll_layout.addWidget(QLabel("Nothing to show.", self))
        else:
            scroll_layout.addWidget(group_tool_box)
        grouped_data = user_workspace.get_grouped_data()
        for group in grouped_data:
            try:
                self.workspace_information["Planning"][group]["tool_box"] = self.workspace_information["Planning"][group][
                    "tool_box"
                ].get_widget_visibility()
                saved_workspace_prefs = True
            except (AttributeError, RuntimeError):
                saved_workspace_prefs = False
            multi_tool_box = MultiToolBox()
            multi_tool_box.layout().setSpacing(0)
            for assembly in grouped_data[group]:
                if assembly.get_assembly_data(key="show") == True and assembly.get_assembly_data(key="completed") == False:
                    assembly_widget = self.load_planning_assembly_widget(
                        assembly=assembly,
                        workspace_information=self.workspace_information["Planning"][group]["sub_assemblies"],
                        group_color=user_workspace.get_group_color(group),
                    )
                    multi_tool_box.addItem(
                        assembly_widget,
                        f'{assembly.get_assembly_data(key="display_name")} - Items: {user_workspace.get_completion_percentage(assembly)[0]*100}% - Assemblies: {user_workspace.get_completion_percentage(assembly)[1]*100}%',
                        base_color=user_workspace.get_group_color(group),
                    )
            group_tool_boxes[group].layout().addWidget(multi_tool_box)
            multi_tool_box.close_all()
            if saved_workspace_prefs:
                multi_tool_box.set_widgets_visibility(self.workspace_information["Planning"][group]["tool_box"])
            # else:

            self.workspace_information["Planning"][group]["tool_box"] = multi_tool_box
        self.tab_widget.currentWidget().layout().addWidget(scroll_area)
        self.scroll_position_manager.restore_scroll_position(
            tab_name=f"{self.tabWidget.tabText(self.tabWidget.currentIndex())} Planning", scroll=scroll_area
        )

    # * \/ CONTEXT MENU \/
    # USER
    def move_selected_table_items_to_next_flow_state(self, table: CustomTableWidget, assembly: Assembly | ItemGroup) -> None:
        """
        The function moves selected items from a table to the next flow state in an assembly, updating
        their attributes accordingly.

        Args:
          table (CustomTableWidget): The "table" parameter is of type CustomTableWidget. It represents a
        custom table widget that contains the selected items.
          assembly (Assembly): The `assembly` parameter is an instance of the `Assembly` class. It
        represents a collection of items that need to go through different flow states.
        """
        selected_items_from_table: list[str] = self.get_all_selected_parts(table)
        if isinstance(assembly, Assembly):
            items_to_update: list[Item] = [item for item in assembly.items if item.name in selected_items_from_table]
        elif isinstance(assembly, ItemGroup):
            items_to_update = []
            for item in selected_items_from_table:
                items_to_update.extend(assembly.get_item_list(item))

        def move_to_next_flow(item: Item) -> None:
            item_flow_tag: str = item.get_value("flow_tag")[item.get_value("current_flow_state")]
            if workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                timer_data = item.get_value("timers")
                try:
                    timer_data[item_flow_tag]["recording"]
                except KeyError:
                    timer_data[item_flow_tag]["recording"] = False
                if timer_data[item_flow_tag]["recording"]:
                    timer_data[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                    timer_data[item_flow_tag]["recording"] = False
                    item.set_value(key="timers", value=timer_data)
            if item_flow_tag == "Laser Cutting":
                item.set_value(key="recut", value=False)
            item.set_value(key="current_flow_state", value=item.get_value(key="current_flow_state") + 1)
            item.set_value(key="status", value=None)
            if item.get_value(key="current_flow_state") == len(item.get_value(key="flow_tag")):
                item.set_value(key="completed", value=True)
                item.set_value(key="date_completed", value=str(datetime.now()))
                assembly: Assembly = item.parent_assembly
                if assembly.get_assembly_data('current_flow_state') == -1: # NOTE Custom Job
                    completed_assemblies: list[Assembly] = []
                    history_workspace.load_data()
                    for main_assembly in user_workspace.data:
                        # Assembly is 100% complete
                        if user_workspace.get_completion_percentage(main_assembly)[0] == 1.0:
                            main_assembly.set_assembly_data(key='completed', value=True)
                            completed_assemblies.append(main_assembly)
                            history_workspace.add_assembly(main_assembly)
                            history_workspace.save()
                            self.play_celebrate_sound()
                    for completed_assembly in completed_assemblies:
                        user_workspace.remove_assembly(completed_assembly)

        for item in items_to_update:
            move_to_next_flow(item)
        user_workspace.save()
        self.sync_changes()
        self.load_workspace()

    # USER
    def change_selected_table_items_status(self, table: CustomTableWidget, assembly: Assembly | ItemGroup, status: str) -> None:
        """
        The function `change_selected_table_items_status` updates the status of selected items in a
        table based on their current flow state and the provided status.

        Args:
          table (CustomTableWidget): The `table` parameter is of type `CustomTableWidget`. It represents
        a custom table widget object.
          assembly (Assembly): The `assembly` parameter represents an assembly object. It is a
        collection of items that are being processed or worked on.
          status (str): The "status" parameter in the given function is a string that represents the new
        status to be assigned to the selected items in the table.
        """
        selected_items_from_table: list[str] = self.get_all_selected_parts(table)
        if isinstance(assembly, Assembly):
            items_to_update: list[Item] = [item for item in assembly.items if item.name in selected_items_from_table]
        elif isinstance(assembly, ItemGroup):
            items_to_update = []
            for item in selected_items_from_table:
                items_to_update.extend(assembly.get_item_list(item))

        def move_to_next_flow(item: Item) -> None:
            item_flow_tag: str = item.get_value("flow_tag")[item.get_value("current_flow_state")]
            if workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]:
                timer_data = item.get_value("timers")
                try:
                    timer_data[item_flow_tag]["recording"]
                except KeyError:
                    timer_data[item_flow_tag]["recording"] = False
                if timer_data[item_flow_tag]["recording"]:
                    timer_data[item_flow_tag]["time_taken_intervals"][-1].append(str(datetime.now()))
                    timer_data[item_flow_tag]["recording"] = False
                    item.set_value(key="timers", value=timer_data)
            if item_flow_tag == "Laser Cutting":
                item.set_value(key="recut", value=False)
            item.set_value(key="current_flow_state", value=item.get_value(key="current_flow_state") + 1)
            item.set_value(key="status", value=None)
            if item.get_value(key="current_flow_state") == len(item.get_value(key="flow_tag")):
                item.set_value(key="completed", value=True)
                item.set_value(key="date_completed", value=str(datetime.now()))
                assembly: Assembly = item.parent_assembly
                if assembly.get_assembly_data('current_flow_state') == -1: # NOTE Custom Job
                    completed_assemblies: list[Assembly] = []
                    history_workspace.load_data()
                    for main_assembly in user_workspace.data:
                        # Assembly is 100% complete
                        if user_workspace.get_completion_percentage(main_assembly)[0] == 1.0:
                            main_assembly.set_assembly_data(key='completed', value=True)
                            completed_assemblies.append(main_assembly)
                            history_workspace.add_assembly(main_assembly)
                            history_workspace.save()
                            self.play_celebrate_sound()
                    for completed_assembly in completed_assemblies:
                        user_workspace.remove_assembly(completed_assembly)

        for item in items_to_update:
            item_flow_tag: str = item.get_value("flow_tag")[item.get_value("current_flow_state")]
            if (
                workspace_tags.get_value("flow_tag_statuses")[item_flow_tag][status]["start_timer"]
                and workspace_tags.get_value("attributes")[item_flow_tag]["is_timer_enabled"]
                and item.get_value("timers")[item_flow_tag]["recording"] == False
            ):
                timer_data = item.get_value("timers")
                timer_data[item_flow_tag]["recording"] = True
                timer_data[item_flow_tag].setdefault("time_taken_intervals", [])
                timer_data[item_flow_tag]["time_taken_intervals"].append([str(datetime.now())])
                item.set_value(key="timers", value=timer_data)
            if workspace_tags.get_value("flow_tag_statuses")[item_flow_tag][status]["completed"]:
                move_to_next_flow(item=item)
            else:
                item.set_value(key="status", value=status)

        user_workspace.save()
        self.sync_changes()
        self.load_workspace()

    # USER
    def download_all_selected_items_files(self, table: CustomTableWidget, assembly: Assembly | ItemGroup) -> None:
        selected_items_from_table: list[str] = self.get_all_selected_parts(table)
        if isinstance(assembly, Assembly):
            items_to_update: list[Item] = [item for item in assembly.items if item.name in selected_items_from_table]
        elif isinstance(assembly, ItemGroup):
            items_to_update = []
            for item in selected_items_from_table:
                items_to_update.extend(assembly.get_item_list(item))

        print("in progress")

    # USER
    def load_view_assembly_context_menus(self) -> None:
        """
        The function `load_view_assembly_context_menus` sets up custom context menus for tables in a
        workspace.
        """
        for table, main_assembly in self.workspace_tables.items():
            # set context menu
            with contextlib.suppress(RuntimeError):
                if table.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
                    table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                    menu = QMenu(self)
                    set_status_menu = QMenu("Set Status", self)
                    if len(workspace_tags.get_value("flow_tag_statuses")[self.category]) > 0:
                        for status in workspace_tags.get_value("flow_tag_statuses")[self.category]:
                            status_action = QAction(status, self)
                            status_action.triggered.connect(partial(self.change_selected_table_items_status, table, main_assembly, status))
                            set_status_menu.addAction(status_action)
                        menu.addMenu(set_status_menu)
                    done_action = QAction("Mark all as Done", self)
                    done_action.triggered.connect(partial(self.move_selected_table_items_to_next_flow_state, table, main_assembly))
                    menu.addAction(done_action)
                    download_action = QAction("Download all files", self)
                    download_action.triggered.connect(partial(self.download_all_selected_items_files, table, main_assembly))
                    menu.addAction(download_action)
                    table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    # STAGING/EDITING
    def copy_items_to(self, table: CustomTableWidget, assembly_copy_from: Assembly, assembly_copy_to: Assembly) -> None:
        """
        The function copies selected items from one assembly to another assembly, checking for duplicates and saving the changes.

        Args:
          table (CustomTableWidget): The `table` parameter is of type `CustomTableWidget` and represents
        the table widget from which the items will be copied.
          assembly_copy_from (Assembly): The `assembly_copy_from` parameter is an instance of the
        `Assembly` class. It represents the assembly from which items will be copied.
          assembly_copy_to (Assembly): `assembly_copy_to` is an instance of the `Assembly` class. It
        represents the assembly where the items will be copied to.

        Returns:
          None
        """
        selected_items_from_table: list[str] = self.get_all_selected_parts(table)
        items_to_copy: list[Item] = [item for item in assembly_copy_from.items if item.name in selected_items_from_table]

        for item_to_copy in items_to_copy:
            if item_to_copy.name in [other_item.name for other_item in assembly_copy_to.items]:
                self.show_message_dialog(title="Duplicates", message=f"There are duplicate items in '{assembly_copy_to.name}'")
                return

        for item_to_copy in items_to_copy:
            assembly_copy_to.add_item(item_to_copy)

        self.active_workspace_file.save()
        self.sync_changes()
        self.load_workspace()

    # STAGING/EDITING
    def move_items_to(self, table: CustomTableWidget, assembly_copy_from: Assembly, assembly_copy_to: Assembly) -> None:
        """
        The function moves selected items from one assembly to another assembly, checking for duplicates and saving the changes.

        Args:
          table (CustomTableWidget): The `table` parameter is of type `CustomTableWidget` and represents
        the table widget from which the items are selected.
          assembly_copy_from (Assembly): The parameter `assembly_copy_from` is an instance of the
        `Assembly` class. It represents the assembly from which the items will be copied/moved.
          assembly_copy_to (Assembly): The parameter `assembly_copy_to` is an instance of the `Assembly`
        class. It represents the assembly where the items will be moved to.

        Returns:
          None
        """
        selected_items_from_table: list[str] = self.get_all_selected_parts(table)
        items_to_move: list[Item] = [item for item in assembly_copy_from.items if item.name in selected_items_from_table]

        for item_to_move in items_to_move:
            if item_to_move.name in [other_item.name for other_item in assembly_copy_to.items]:
                self.show_message_dialog(title="Duplicates", message=f"There are duplicate items in '{assembly_copy_to.name}'")
                return

        for item_to_move in items_to_move:
            assembly_copy_to.add_item(item_to_move)
            assembly_copy_from.remove_item(item_to_move)

        self.active_workspace_file.save()
        self.sync_changes()
        self.load_workspace()

    # STAGING/EDITING
    def delete_selected_items_from_workspace(self, table: CustomTableWidget, assembly: Assembly) -> None:
        """
        The function deletes selected items from a workspace by clicking on the delete buttons
        associated with the selected rows in a table.

        Args:
          table (CustomTableWidget): The `table` parameter is of type `CustomTableWidget`, which is a
        custom widget representing a table. It is used to access the selected indexes and widgets in the
        table.
          assembly (Assembly): The `assembly` parameter is an instance of the `Assembly` class. It is
        used as an argument to the function to indicate the specific assembly object that the selected
        items belong to.
        """
        selected_indexes = table.selectedIndexes()
        selected_rows = list({selected_index.row() for selected_index in selected_indexes})
        delete_buttons: list[DeletePushButton] = [
            table.cellWidget(selected_row, table.columnCount() - 1) for selected_row in selected_rows if selected_row != table.rowCount() - 1
        ]

        for delete_button in delete_buttons:
            delete_button.click()

    # STAGING/EDITING
    def generate_workorder_with_selected_items(self, table: CustomTableWidget, assembly: Assembly) -> None:
        selected_indexes = table.selectedIndexes()
        selected_rows = list({selected_index.row() for selected_index in selected_indexes})
        selected_items: list[Item] = []
        for item in assembly.items:
            for row in selected_rows:
                if item.name == table.item(row, 0).text():
                    selected_items.append(item)
                    continue
        user_workspace.load_data()
        group_color = get_random_color() if user_workspace.get_group_color("Custom Jobs") is None else user_workspace.get_group_color("Custom Jobs")
        date_created: str = QDate().currentDate().toString("yyyy-M-d")
        custom_assembly = Assembly(
            name=f"Custom Job ({len(selected_items)} items) - {datetime.now()}",
            assembly_data={
                "expected_time_to_complete": 0.0,
                "has_items": True,
                "has_sub_assemblies": False,
                "group": "Custom Jobs",
                "group_color": group_color,
                "flow_tag": [],
                "timers": {},
                "completed": False,
                "display_name": f"Custom Job ({len(selected_items)} items)",
                "starting_date": date_created,
                "ending_date": date_created,
                "status": None,
                "current_flow_state": -1,
            },
        )
        for item in selected_items:
            custom_assembly.add_item(item)
        custom_assembly.set_default_value_to_all_items(key="starting_date", value=date_created)
        custom_assembly.set_default_value_to_all_items(key="ending_date", value=date_created)
        custom_assembly.set_default_value_to_all_items(key="current_flow_state", value=0)
        custom_assembly.set_default_value_to_all_items(key="recoat", value=False)
        custom_assembly.set_default_value_to_all_items(key="status", value=None)
        custom_assembly.set_default_value_to_all_items(key="recut", value=False)
        custom_assembly.set_default_value_to_all_items(key="recut_count", value=0)
        custom_assembly.set_default_value_to_all_items(key="completed", value=False)
        user_workspace.add_assembly(custom_assembly)
        user_workspace.save()
        # NOTE This is because sync handels file uploads differently
        self.status_button.setText(f'Synching - {datetime.now().strftime("%r")}', "lime")
        self.upload_file(
            [
                "workspace - User.json",
            ],
            False,
        )

    # STAGING/EDITING
    def set_tables_selected_items_value(self, table: CustomTableWidget, assembly: Assembly, key: str, value: Any) -> None:
        """
        The function sets the value of a specific key for selected items in a table, based on the
        provided assembly.

        Args:
          table (CustomTableWidget): The "table" parameter is of type CustomTableWidget. It represents a
        custom table widget used in the application.
          assembly (Assembly): The "assembly" parameter is an object of the "Assembly" class. It
        represents a collection of items that are assembled together.
          key (str): The `key` parameter is a string that represents the attribute or property of the
        `Item` objects in the `assembly` that you want to modify. It determines which property of the
        `Item` objects will be changed.
          value (Any): The "value" parameter in the given function is a variable that represents the new
        value to be set for the specified key in the items of the assembly. The type of the "value"
        parameter can vary depending on the key being set.
        """
        selected_items_from_table: list[str] = self.get_all_selected_parts(table)
        items_to_change: list[Item] = [item for item in assembly.items if item.name in selected_items_from_table]

        if key == "paint_color":
            value = workspace_tags.get_value("paint_colors")[value]
        elif key == "flow_tag":
            value: list[str] = value.split(" ➜ ")

        for item in items_to_change:
            item.set_value(key=key, value=value)
        if self.category == "Staging" or self.category == "Editing":
            self.active_workspace_file.save()
        else:
            user_workspace.save()
        self.sync_changes()
        self.load_workspace()

    # STAGING/EDITING
    def load_edit_assembly_context_menus(self) -> None:
        """
        The function `load_edit_assembly_context_menus` sets up the context menus for a table in a GUI
        application.
        """
        for table, main_assembly in self.workspace_tables.items():
            # set context menu
            with contextlib.suppress(RuntimeError):
                if table.contextMenuPolicy() != Qt.ContextMenuPolicy.CustomContextMenu:
                    table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                    menu = QMenu(self)
                    generate_workrder = QAction("Generate Workorder with Selected Items", self)
                    generate_workrder.triggered.connect(partial(self.generate_workorder_with_selected_items, table, main_assembly))
                    menu.addSeparator()
                    menu.addAction(generate_workrder)
                    copy_to_menu = QMenu(self)
                    copy_to_menu.setTitle("Copy items to")
                    move_to_menu = QMenu(self)
                    move_to_menu.setTitle("Move items to")

                    def get_all_assemblies_menu(menu: QMenu, action: str, assembly: Assembly = None) -> QMenu:
                        if assembly is None:
                            for assembly in self.active_workspace_file.data:
                                assembly_action = QAction(assembly.name, self)
                                if main_assembly == assembly:
                                    assembly_action.setText(f"{assembly_action.text()} - (You are Here)")
                                elif not assembly.get_assembly_data(key="has_items"):
                                    assembly_action.setText(f"{assembly_action.text()} - (No Items)")
                                if not assembly.get_assembly_data(key="has_items") or main_assembly == assembly:
                                    assembly_action.setEnabled(False)
                                # assembly_action.toggled.connect(self.copy_selected_items_to(table, assembly))
                                if action == "copy":
                                    assembly_action.triggered.connect(partial(self.copy_items_to, table, main_assembly, assembly))
                                elif action == "move":
                                    assembly_action.triggered.connect(partial(self.move_items_to, table, main_assembly, assembly))
                                menu.addAction(assembly_action)

                                if assembly.sub_assemblies:
                                    assembly_menu = menu.addMenu("Sub Assemblies")
                                    assembly_menu.addSeparator()
                                    create_sub_assemblies_submenu(assembly_menu, action, assembly.sub_assemblies)

                        return menu

                    def create_sub_assemblies_submenu(parent_menu: QMenu, action: str, sub_assemblies: list[Assembly]) -> None:
                        for sub_assembly in sub_assemblies:
                            assembly_action = QAction(sub_assembly.name, self)
                            if main_assembly == sub_assembly:
                                assembly_action.setText(f"{assembly_action.text()} - (You are Here)")
                            elif not sub_assembly.get_assembly_data(key="has_items"):
                                assembly_action.setText(f"{assembly_action.text()} - (No Items)")
                            if not sub_assembly.get_assembly_data(key="has_items") or main_assembly == sub_assembly:
                                assembly_action.setEnabled(False)
                            if action == "copy":
                                assembly_action.triggered.connect(partial(self.copy_items_to, table, main_assembly, sub_assembly))
                            elif action == "move":
                                assembly_action.triggered.connect(partial(self.move_items_to, table, main_assembly, sub_assembly))
                            parent_menu.addAction(assembly_action)
                            if sub_assembly.sub_assemblies:
                                sub_assembly_menu = parent_menu.addMenu("Sub Assemblies")
                                parent_menu.addSeparator()
                                create_sub_assemblies_submenu(sub_assembly_menu, action, sub_assembly.sub_assemblies)

                    menu.addMenu(get_all_assemblies_menu(menu=copy_to_menu, action="copy"))
                    menu.addMenu(get_all_assemblies_menu(menu=move_to_menu, action="move"))
                    menu.addSeparator()

                    materials_menu = QMenu(self)
                    materials_menu.setTitle("Set Materials")
                    for material in price_of_steel_information.get_value("materials"):
                        material_action = QAction(material, self)
                        material_action.triggered.connect(partial(self.set_tables_selected_items_value, table, main_assembly, "material", material))
                        materials_menu.addAction(material_action)
                    menu.addMenu(materials_menu)

                    thickness_menu = QMenu(self)
                    thickness_menu.setTitle("Set Thicknesses")
                    for thickness in price_of_steel_information.get_value("thicknesses"):
                        thickness_action = QAction(thickness, self)
                        thickness_action.triggered.connect(
                            partial(self.set_tables_selected_items_value, table, main_assembly, "thickness", thickness)
                        )
                        thickness_menu.addAction(thickness_action)
                    menu.addMenu(thickness_menu)

                    flowtags_menu = QMenu(self)
                    flowtags_menu.setTitle("Set Flow Tag")
                    for flow_tag in self.get_all_flow_tags():
                        flowtag_action = QAction(flow_tag, self)
                        flowtag_action.triggered.connect(partial(self.set_tables_selected_items_value, table, main_assembly, "flow_tag", flow_tag))
                        flowtags_menu.addAction(flowtag_action)
                    menu.addMenu(flowtags_menu)

                    paint_color_menu = QMenu(self)
                    paint_color_menu.setTitle("Set Paint Color")
                    for color in list(workspace_tags.get_value("paint_colors").keys()):
                        color_action = QAction(color, self)
                        color_action.triggered.connect(partial(self.set_tables_selected_items_value, table, main_assembly, "paint_color", color))
                        paint_color_menu.addAction(color_action)
                    menu.addMenu(paint_color_menu)

                    paint_type_menu = QMenu(self)
                    paint_type_menu.setTitle("Set Paint Type")
                    for paint_type in ["None", "Powder", "Wet Paint"]:
                        paint_type_action = QAction(paint_type, self)
                        paint_type_action.triggered.connect(
                            partial(self.set_tables_selected_items_value, table, main_assembly, "paint_type", paint_type)
                        )
                        paint_type_menu.addAction(paint_type_action)
                    menu.addMenu(paint_type_menu)

                    delete_selected_items = QAction("Delete Selected Items", self)
                    delete_selected_items.triggered.connect(partial(self.delete_selected_items_from_workspace, table, main_assembly))
                    menu.addSeparator()
                    menu.addAction(delete_selected_items)

                    # action = QAction(self)
                    # action.triggered.connect(partial(self.name_change, table))
                    # action.setText("Change part name")
                    # menu.addAction(action)
                    table.customContextMenuRequested.connect(partial(self.open_group_menu, menu))

    # * /\ CONTEXT MENU /\

    # WORKSPACE
    def load_workspace(self) -> None:
        admin_workspace.load_data()
        user_workspace.load_data()
        if self.category == "Staging" or self.category == "Editing":
            if self.category == "Staging":  # Staging
                self.active_workspace_file = admin_workspace
            else:  # Editing
                self.active_workspace_file = user_workspace
            if self.category == "Staging":  # Staging
                self.pushButton_add_job.setHidden(False)
                self.pushButton_generate_workorder.setHidden(False)
                self.pushButton_generate_workspace_quote.setHidden(False)
                self.pushButton_show_item_summary.setEnabled(True)
                self.pushButton_show_sub_assembly.setEnabled(True)
            else:  # Editing
                self.pushButton_use_filter.setEnabled(False)
                self.pushButton_use_filter.setChecked(False)
                self.pushButton_add_job.setHidden(True)
                self.pushButton_generate_workorder.setHidden(True)
                self.pushButton_generate_workspace_quote.setHidden(True)
                self.pushButton_show_item_summary.setEnabled(False)
                self.pushButton_show_sub_assembly.setEnabled(False)
            self.pushButton_use_filter.setEnabled(True)
            self.pushButton_show_item_summary.setEnabled(True)
            self.pushButton_show_sub_assembly.setEnabled(True)
            self.workspace_tables.clear()
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            self.tab_widget.widget(self.tab_widget.currentIndex())
            self.clear_layout(self.tab_widget.currentWidget().layout())
            self.load_edit_assembly_tab()
            self.load_edit_assembly_context_menus()
            QApplication.restoreOverrideCursor()
        elif self.category == "Planning":
            self.workspace_tables.clear()
            self.pushButton_add_job.setHidden(True)
            self.pushButton_generate_workorder.setHidden(True)
            self.pushButton_generate_workspace_quote.setHidden(True)
            self.pushButton_use_filter.setEnabled(False)
            self.pushButton_use_filter.setChecked(False)
            self.pushButton_show_item_summary.setEnabled(False)
            self.pushButton_show_sub_assembly.setEnabled(False)
            self.pushButton_show_item_summary.setChecked(False)
            self.pushButton_show_sub_assembly.setChecked(True)
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            self.tab_widget.widget(self.tab_widget.currentIndex())
            self.clear_layout(self.tab_widget.currentWidget().layout())
            self.load_planning_assembly_tab()
            QApplication.restoreOverrideCursor()
        else:
            self.workspace_tables.clear()
            self.pushButton_add_job.setHidden(True)
            self.pushButton_generate_workorder.setHidden(True)
            self.pushButton_generate_workspace_quote.setHidden(True)
            self.pushButton_use_filter.setEnabled(False)
            self.pushButton_use_filter.setChecked(True)
            self.pushButton_show_item_summary.setEnabled(True)
            self.pushButton_show_sub_assembly.setEnabled(True)
            QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
            self.tab_widget.widget(self.tab_widget.currentIndex())
            self.clear_layout(self.tab_widget.currentWidget().layout())
            self.load_view_assembly_tab()
            QApplication.restoreOverrideCursor()

    # NOTE FOR PARTS IN INVENTORY
    def load_parts_in_inventory_filter_tab(self) -> None:
        """
        The function `load_parts_in_inventory_filter_tab` clears and updates the filter tab for parts in
        inventory.
        """
        self.parts_in_ineventory_filter.clear()
        self.clear_layout(self.verticalLayout_parts_filter)

        self.parts_in_inventory_filter_tab_widget = FilterTabWidget(columns=2, parent=self)
        self.parts_in_inventory_filter_tab_widget.add_tab("Materials")
        self.parts_in_inventory_filter_tab_widget.add_tab("Thicknesses")
        self.parts_in_inventory_filter_tab_widget.add_buttons_to_tab("Materials", price_of_steel_information.get_value("materials"))
        self.parts_in_inventory_filter_tab_widget.add_buttons_to_tab("Thicknesses", price_of_steel_information.get_value("thicknesses"))
        self.parts_in_ineventory_filter["search"] = self.lineEdit_search_parts_in_inventory
        self.parts_in_ineventory_filter["materials"] = self.parts_in_inventory_filter_tab_widget.get_buttons("Materials")
        self.parts_in_ineventory_filter["thicknesses"] = self.parts_in_inventory_filter_tab_widget.get_buttons("Thicknesses")
        self.parts_in_inventory_filter_tab_widget.update_tab_button_visibility(0)
        self.parts_in_inventory_filter_tab_widget.filterButtonPressed.connect(self.load_active_tab)

        self.verticalLayout_parts_filter.addWidget(self.parts_in_inventory_filter_tab_widget)

    # WORKSPACE
    def set_filter_calendar_day(self, days: int) -> None:
        """
        The function sets the filter for the calendar day by specifying the number of days and updating
        the calendar accordingly.

        Args:
          days (int): The `days` parameter is an integer that represents the number of days to set the
        filter for in the calendar.
        """
        calendar: SelectRangeCalendar = self.verticalLayout_calendar_select_range.layout().itemAt(0).widget()
        if not calendar.from_date:
            calendar.from_date = QDate().currentDate()
        if days != 7:
            to_date: QDate = calendar.from_date.addDays(days)
        else:
            current_date = QDate.currentDate()
            calendar.from_date = current_date.addDays(-current_date.dayOfWeek() + 1)
            to_date = calendar.from_date.addDays(4)
        calendar.set_range(to_date)
        calendar.setSelectedDate(to_date)
        self.load_workspace()

    # WORKSPACE
    def load_workspace_filter_tab(self) -> None:
        """
        The function `load_workspace_filter_tab` sets up the filter tab in a workspace by adding tabs
        and buttons for filtering different categories of items.
        """
        self.workspace_filter.clear()
        self.clear_layout(self.filter_layout)
        self.clear_layout(self.verticalLayout_calendar_select_range)

        self.workspace_filter_tab_widget = FilterTabWidget(columns=2, parent=self)
        self.workspace_filter_tab_widget.add_tab("Materials")
        self.workspace_filter_tab_widget.add_tab("Thicknesses")
        self.workspace_filter_tab_widget.add_tab("Paint")
        self.workspace_filter_tab_widget.add_tab("Statuses")
        self.workspace_filter_tab_widget.add_tab("Flow Tags")
        self.workspace_filter_tab_widget.add_buttons_to_tab("Flow Tags", workspace_tags.get_value("all_tags"))
        self.workspace_filter_tab_widget.add_buttons_to_tab("Statuses", self.get_all_statuses())
        self.workspace_filter_tab_widget.add_buttons_to_tab("Materials", price_of_steel_information.get_value("materials"))
        self.workspace_filter_tab_widget.add_buttons_to_tab("Thicknesses", price_of_steel_information.get_value("thicknesses"))
        self.workspace_filter_tab_widget.add_buttons_to_tab("Paint", list(workspace_tags.get_value("paint_colors").keys()))
        self.workspace_filter_tab_widget.update_tab_button_visibility(0)

        self.filter_layout.addWidget(self.workspace_filter_tab_widget)

        self.lineEdit_search.editingFinished.connect(lambda: (self.pushButton_use_filter.setChecked(True), self.load_workspace()))
        self.lineEdit_search.setCompleter(QCompleter(self.get_all_workspace_item_names(), self))
        self.lineEdit_search.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self.pushButton_show_sub_assembly.clicked.connect(lambda: (self.pushButton_show_item_summary.setChecked(False), self.load_workspace()))
        self.pushButton_show_item_summary.clicked.connect(lambda: (self.pushButton_show_sub_assembly.setChecked(False), self.load_workspace()))

        self.horizontalLayout_23.setAlignment(Qt.AlignmentFlag.AlignRight)

        calendar = SelectRangeCalendar(self)
        calendar.clicked.connect(lambda: (self.pushButton_use_filter.setChecked(True), self.load_workspace()))
        self.groupBox_due_dates.toggled.connect(lambda: (self.pushButton_use_filter.setChecked(True), self.load_workspace()))
        self.verticalLayout_calendar_select_range.addWidget(calendar)

        self.workspace_filter["use_filter"] = self.pushButton_use_filter
        self.workspace_filter["search"] = self.lineEdit_search
        self.workspace_filter["materials"] = self.workspace_filter_tab_widget.get_buttons("Materials")
        self.workspace_filter["thicknesses"] = self.workspace_filter_tab_widget.get_buttons("Thicknesses")
        self.workspace_filter["flow_tags"] = self.workspace_filter_tab_widget.get_buttons("Flow Tags")
        self.workspace_filter["statuses"] = self.workspace_filter_tab_widget.get_buttons("Statuses")
        self.workspace_filter["paint"] = self.workspace_filter_tab_widget.get_buttons("Paint")
        self.workspace_filter["due_dates"] = self.groupBox_due_dates
        self.workspace_filter["calendar"] = calendar
        self.workspace_filter["show_recut"] = False

        self.pushButton_use_filter.toggled.connect(self.load_workspace)

        self.workspace_filter_tab_widget.filterButtonPressed.connect(lambda: (self.pushButton_use_filter.setChecked(True), self.load_workspace()))

    # OMNIGEN
    def load_quote_generator_ui(self) -> None:
        """
        The function "load_quote_generator_ui" refreshes nest directories, loads a cutoff drop-down, and
        loads previous nest files in a separate thread.
        """
        self.refresh_nest_directories()
        self.load_cuttoff_drop_down()
        self.load_previous_nests_files_thread()

    # OMNIGEN
    def load_cuttoff_drop_down(self) -> None:
        """
        The function loads cutoff sheets data and adds it to a dropdown menu in a GUI.
        """
        with contextlib.suppress(Exception):  # This is just incase the Cutoff tab has never been created
            cutoff_items = self.cutoff_widget.widgets[0]
            cutoff_items.clear()
            price_of_steel_inventory.load_data()
            cutoff_sheets = price_of_steel_inventory.get_value("Cutoff")
            grouped_data = parts_in_inventory.sort_by_multiple_tags(category=cutoff_sheets, tags_ids=["material"])
            for group in grouped_data:
                cutoff_items.addItem(f"\t             {group.replace(';', '')}")
                for sheet in list(grouped_data[group].keys()):
                    cutoff_items.addItem(sheet)

    # OMNIGEN
    def load_previous_nest_tree_view(self, data: dict[str, dict[str, Any]]) -> None:
        """
        The function `load_previous_nest_tree_view` populates a tree view with data from a dictionary,
        organizing the data into groups based on file names and displaying the file names and their
        corresponding modified dates.

        Args:
          data: The `data` parameter is a dictionary that contains information about previous nests.
        Each key-value pair in the dictionary represents a file name and its corresponding data. The
        file name is a string, and the data is a dictionary containing information such as the created
        date of the file.
        """
        self.tree_model_previous_nests.clear()
        self.tree_model_previous_nests.setHorizontalHeaderLabels(["Name", "Date Modified"])
        # icon_provider =
        root_item = self.tree_model_previous_nests.invisibleRootItem()
        groups_dictionary: dict[str, QStandardItem] = {}

        for file_name, file_data in data.items():
            match = re.match(r"(\w\D+) .+\.json", file_name)
            if not match:
                continue
            group_name = match[1]
            group_folder = groups_dictionary.get(group_name)
            if group_folder is None:
                group_folder = QStandardItem(group_name)
                group_folder.setIcon(QFileIconProvider().icon(QFileIconProvider().IconType.Folder))
                groups_dictionary[group_name] = group_folder
                root_item.appendRow(group_folder)

            file_name = QStandardItem(file_name)
            file_name.setIcon(QFileIconProvider().icon(QFileIconProvider().IconType.File))
            date_created = QStandardItem(datetime.fromtimestamp(file_data["created_date"]).strftime("%Y-%m-%d %H:%M:%S"))
            file_info = [file_name, date_created]
            group_folder.appendRow(file_info)

        self.treeView_previous_nests.setColumnWidth(0, 200)
        self.treeView_previous_nests.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        self.treeView_previous_nests.selectionModel().selectionChanged.connect(self.previous_nest_directory_item_selected)

    # OMNIGEN
    def refresh_nest_directories(self) -> None:
        """
        The function refreshes the nested directories in a GUI by clearing the layout, retrieving the
        directories from a settings file, creating a QToolBox widget, adding tree views for each
        directory, and setting icons for the items.
        """
        self.clear_layout(self.verticalLayout_24)
        self.quote_nest_directories_list_widgets.clear()
        nest_directories: list[str] = settings_file.get_value("quote_nest_directories")
        toolbox = QToolBox(self)
        toolbox.setLineWidth(0)
        toolbox.layout().setSpacing(0)
        self.verticalLayout_24.addWidget(toolbox)
        for i, nest_directory in enumerate(nest_directories):
            nest_directory_name: str = nest_directory.split("/")[-1]
            tree_view = PdfTreeView(nest_directory, self)
            tree_view.selectionModel().selectionChanged.connect(self.nest_directory_item_selected)
            # There is an issue where it still calls even tho its a folder
            # tree_view.doubleClicked.connect(self.process_selected_nests)

            self.quote_nest_directories_list_widgets[nest_directory] = tree_view
            toolbox.addItem(tree_view, nest_directory_name)
            toolbox.setItemIcon(i, QIcon("icons/folder.png"))
        self.nest_directory_item_selected()

    # OMNIGEN
    def load_nests(self) -> None:
        """
        This function loads nests and their corresponding information into a QToolBox widget and a
        table, and connects signals to update the table when cells are changed.
        """
        self.clear_layout(self.verticalLayout_sheets)
        self.comboBox_global_sheet_thickness.setEnabled(True)
        self.comboBox_global_sheet_material.setEnabled(True)
        self.doubleSpinBox_global_sheet_length.setEnabled(True)
        self.doubleSpinBox_global_sheet_width.setEnabled(True)
        self.sheet_nests_toolbox = MultiToolBox(self)
        self.sheet_nests_toolbox.layout().setSpacing(0)
        self.verticalLayout_sheets.addWidget(self.sheet_nests_toolbox)
        row_index: int = 0
        tab_index: int = 0
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name[0] == "_":
                widget = QWidget(self)
                widget.setMinimumHeight(260)
                widget.setMaximumHeight(260)
                grid_layout = QGridLayout(widget)
                labels = [
                    "Sheet Scrap Percentage:",
                    "Cost for Sheets:",
                    "Cutting Costs:",
                    "Sheet Cut Time:",
                    "Nest Cut Time:",
                    "Sheet Count:",
                    "Sheet Material:",
                    "Sheet Thickness:",
                    "Sheet Dimension (len x wid):",
                ]
                for i, label in enumerate(labels):
                    label = QLabel(label, self)
                    grid_layout.addWidget(label, i, 0)

                label_scrap_percentage = QLabel(f"{calculate_scrap_percentage(nest_name, self.quote_nest_information):,.2f}%", self)
                grid_layout.addWidget(label_scrap_percentage, 0, 2)

                label_sheet_cost = QLabel(f'${self.get_sheet_cost(nest_name):,.2f}')
                grid_layout.addWidget(label_sheet_cost, 1, 2)

                label_cutting_cost = QLabel(f'${self.get_cutting_cost(nest_name):,.2f}')
                grid_layout.addWidget(label_cutting_cost, 2, 2)

                sheet_cut_time = MachineCutTimeSpinBox(self)
                sheet_cut_time.setValue(float(self.quote_nest_information[nest_name]['single_sheet_machining_time']))
                sheet_cut_time.editingFinished.connect(partial(self.sheet_nest_item_change, tab_index, sheet_cut_time, nest_name, "single_sheet_machining_time"))
                sheet_cut_time.setToolTip(f'Original: {self.get_sheet_cut_time(nest_name)}')
                grid_layout.addWidget(sheet_cut_time, 3, 2)

                nest_cut_time = QLabel(self)
                nest_cut_time.setText(f'{self.get_total_cutting_time(nest_name)}')
                grid_layout.addWidget(nest_cut_time, 4, 2)

                spinBox_sheet_count = HumbleDoubleSpinBox(self)
                spinBox_sheet_count.setValue(self.quote_nest_information[nest_name]["quantity_multiplier"])
                spinBox_sheet_count.valueChanged.connect(
                    partial(
                        self.sheet_nest_item_change,
                        tab_index,
                        spinBox_sheet_count,
                        nest_name,
                        "quantity_multiplier",
                    )
                )

                grid_layout.addWidget(spinBox_sheet_count, 5, 2)

                comboBox_sheet_material = QComboBox(self)
                comboBox_sheet_material.wheelEvent = lambda event: event.ignore()
                comboBox_sheet_material.addItems(price_of_steel_information.get_value("materials"))
                comboBox_sheet_material.setCurrentText(self.quote_nest_information[nest_name]["material"])
                if self.quote_nest_information[nest_name]["material"] in {"304 SS", "409 SS", "Aluminium"}:
                    self.comboBox_laser_cutting.setCurrentText("Nitrogen")
                else:
                    self.comboBox_laser_cutting.setCurrentText("CO2")
                comboBox_sheet_material.activated.connect(
                    partial(
                        self.sheet_nest_item_change,
                        tab_index,
                        comboBox_sheet_material,
                        nest_name,
                        "material",
                    )
                )
                grid_layout.addWidget(comboBox_sheet_material, 6, 2)

                comboBox_sheet_thickness = QComboBox(self)
                comboBox_sheet_thickness.wheelEvent = lambda event: event.ignore()
                comboBox_sheet_thickness.addItems(price_of_steel_information.get_value("thicknesses"))
                comboBox_sheet_thickness.setCurrentText(self.quote_nest_information[nest_name]["gauge"])
                comboBox_sheet_thickness.activated.connect(
                    partial(
                        self.sheet_nest_item_change,
                        tab_index,
                        comboBox_sheet_thickness,
                        nest_name,
                        "gauge",
                    )
                )
                grid_layout.addWidget(comboBox_sheet_thickness, 7, 2)
                lineEdit_sheet_size_x = HumbleDoubleSpinBox(self)
                lineEdit_sheet_size_x.setDecimals(3)
                lineEdit_sheet_size_x.setSuffix(" in")
                try:
                    lineEdit_sheet_size_x.setValue(float(self.quote_nest_information[nest_name]["sheet_dim"].replace(" x ", "x").split("x")[0]))
                except AttributeError:
                    lineEdit_sheet_size_x.setValue(0.0)
                grid_layout.addWidget(lineEdit_sheet_size_x, 10, 0)
                label = QLabel("x", self)
                label.setFixedWidth(15)
                grid_layout.addWidget(label, 10, 1)
                lineEdit_sheet_size_y = HumbleDoubleSpinBox(self)
                lineEdit_sheet_size_y.setDecimals(3)
                lineEdit_sheet_size_y.setSuffix(" in")
                try:
                    lineEdit_sheet_size_y.setValue(float(self.quote_nest_information[nest_name]["sheet_dim"].replace(" x ", "x").split("x")[1]))
                except AttributeError:
                    lineEdit_sheet_size_y.setValue(0.0)
                grid_layout.addWidget(lineEdit_sheet_size_y, 10, 2)
                lineEdit_sheet_size_x.valueChanged.connect(
                    partial(
                        self.sheet_nest_item_change,
                        tab_index,
                        (lineEdit_sheet_size_x, lineEdit_sheet_size_y),
                        nest_name,
                        "sheet_dim",
                    )
                )
                lineEdit_sheet_size_y.valueChanged.connect(
                    partial(
                        self.sheet_nest_item_change,
                        tab_index,
                        (lineEdit_sheet_size_x, lineEdit_sheet_size_y),
                        nest_name,
                        "sheet_dim",
                    )
                )

                self.sheet_nests_toolbox.addItem(
                    widget,
                    f"{self.quote_nest_information[nest_name]['gauge']} {self.quote_nest_information[nest_name]['material']} {self.quote_nest_information[nest_name]['sheet_dim']} - {nest_name.split('/')[-1].replace('.pdf', '')}",
                )
                self.sheet_nests_toolbox.setItemIcon(
                    tab_index,
                    QIcon("icons/project_open.png"),
                )
                tab_index += 1
        self.load_quote_table()
        self.load_nest_summary()
        # self.sheet_nests_toolbox.open_all()
        self.sheet_nests_toolbox.close_all()
        self.tableWidget_quote_items.setEnabled(True)
        self.tableWidget_quote_items.resizeColumnsToContents()
        self.tableWidget_quote_items.setColumnWidth(1, 250)
        self.update_quote_price()
        self.update_sheet_prices()

    def load_nest_summary(self) -> None:
        """
        The function `load_nest_summary` creates a summary of sheet names, total sheet count, and total
        cut time and displays them in a grid layout.
        """
        self.clear_layout(self.gridLayout_nest_summary)
        headers = ["Sheet Name", "Total Sheet Count", "Total Cut Time"]
        for i, header in enumerate(headers):
            label = QLabel(header, self)
            self.gridLayout_nest_summary.addWidget(label, 0, i)
        for i, (sheet_name, sheet_data) in enumerate(self.get_nest_summary().items()):
            if " x " not in sheet_name:
                label_sheet_name = QLabel(sheet_name, self)
            else:
                label_sheet_name = QLabel(sheet_name, self)
            label_sheet_name.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if " x " not in sheet_name:
                label_sheet_name.setStyleSheet("border-top: 1px solid grey; border-bottom: 1px solid grey")
            self.gridLayout_nest_summary.addWidget(label_sheet_name, i+1, 0)

            if " x " not in sheet_name:
                label_sheet_count = QLabel(f"Total Cut Time:", self)
            else:
                label_sheet_count = QLabel(str(sheet_data['total_sheet_count']), self)
            label_sheet_count.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if " x " not in sheet_name:
                label_sheet_count.setStyleSheet("border-top: 1px solid grey; border-bottom: 1px solid grey")
            self.gridLayout_nest_summary.addWidget(label_sheet_count, i+1, 1)

            total_seconds = sheet_data['total_seconds']
            try:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)
                total_seconds_string = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
            except KeyError:
                total_seconds_string = "Null"


            if " x " not in sheet_name:
                label_sheet_cuttime = QLabel(f"{total_seconds_string}", self)
            else:
                label_sheet_cuttime = QLabel(total_seconds_string, self)
            label_sheet_cuttime.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            if " x " not in sheet_name:
                label_sheet_cuttime.setStyleSheet("border-top: 1px solid grey; border-bottom: 1px solid grey")
            self.gridLayout_nest_summary.addWidget(label_sheet_cuttime, i+1, 2)

    def get_nest_summary(self) -> dict:
        """
        The function `get_nest_summary` calculates the total sheet count and total machining time for
        each nest in a quote, and returns a summary dictionary sorted by material.

        Returns:
          a sorted dictionary containing the summary of nest information. The keys of the dictionary are
        the names of the nests, and the values are dictionaries containing the total sheet count and
        total seconds for each nest. The dictionary is sorted in descending order based on the keys.
        """
        summary = {}
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name[0] == "_":
                name = f"{self.quote_nest_information[nest_name]['material']} {self.quote_nest_information[nest_name]['gauge']} {self.quote_nest_information[nest_name]['sheet_dim']}"
                summary.setdefault(name, {"total_sheet_count": 0, "total_seconds": 0})
                summary.setdefault(f"{self.quote_nest_information[nest_name]['material']}",  {"total_sheet_count": 0, "total_seconds": 0})
                summary[name]['total_sheet_count'] += self.quote_nest_information[nest_name]["quantity_multiplier"]
                summary[name]['total_seconds'] += float(self.quote_nest_information[nest_name]['single_sheet_machining_time']) * self.quote_nest_information[nest_name]['quantity_multiplier']

                summary[f"{self.quote_nest_information[nest_name]['material']}"]['total_seconds'] += float(self.quote_nest_information[nest_name]['single_sheet_machining_time']) * self.quote_nest_information[nest_name]['quantity_multiplier']
                summary[f"{self.quote_nest_information[nest_name]['material']}"]['total_sheet_count'] += self.quote_nest_information[nest_name]["quantity_multiplier"]
        sorted_keys = natsorted(summary.keys(), reverse=True)
        sorted_dict = {key: summary[key] for key in sorted_keys}
        return sorted_dict

    # OMNIGEN
    def delete_quote_part(self, item_name: str, nest_name: str, refresh_quote_table: bool = True) -> None:
        """
        The function `delete_quote_part` deletes a specific item from a nested dictionary and performs
        additional actions if necessary.

        Args:
          item_name (str): The `item_name` parameter is a string that represents the name of the item to
        be deleted from the `quote_nest_information` dictionary.
          nest_name (str): The `nest_name` parameter is a string that represents the name of a nest in
        the `quote_nest_information` dictionary.
        """
        del self.quote_nest_information[nest_name][item_name]
        if len(self.quote_nest_information[nest_name]) == 0:
            # Deleting sheets
            for nest in self.quote_nest_information:
                if nest_name in nest and nest[0] == "_":
                    for i, button in enumerate(self.sheet_nests_toolbox.buttons):
                        if (
                            button.text()
                            == f"{self.quote_nest_information[nest]['gauge']} {self.quote_nest_information[nest]['material']} {self.quote_nest_information[nest]['sheet_dim']} - {nest.split('/')[-1].replace('.pdf', '')}"
                        ):
                            self.sheet_nests_toolbox.getWidget(i).setEnabled(False)
                            self.sheet_nests_toolbox.setItemText(i, "No more items for this nest")
                            self.sheet_nests_toolbox.close(i)
                    del self.quote_nest_information[nest]
                    break
            del self.quote_nest_information[nest_name]
        if refresh_quote_table:
            self.load_quote_table()
            if len(self.quote_nest_information) == 0:
                self.clear_layout(self.verticalLayout_sheets)

    # OMNIGEN
    def delete_selected_quote_parts(self) -> None:
        """
        The function `delete_selected_quote_parts` deletes selected quote parts from a table and updates
        the quote table.
        """
        selected_rows = list({item.row() for item in self.tableWidget_quote_items.selectedItems()})
        nest_name: str = ""
        item_name: str = ""
        for row in range(self.tableWidget_quote_items.rowCount()):
            try:
                nest_name = self.tableWidget_quote_items.item(row, 0).text()
            except AttributeError:
                item_name = self.tableWidget_quote_items.item(row, 1).text()
            if nest_name in list(self.quote_nest_information.keys()) and nest_name != "":
                nest_name = self.tableWidget_quote_items.item(row, 0).text()
                continue

            item_name = self.tableWidget_quote_items.item(row, 1).text()
            if item_name == "":
                continue

            if row in selected_rows:
                if nest_name == "":
                    nest_name = "/CUSTOM NEST"
                self.delete_quote_part(item_name=item_name, nest_name=f"{nest_name}.pdf", refresh_quote_table=False)

        self.load_quote_table()
        if len(self.quote_nest_information) == 0:
            self.clear_layout(self.verticalLayout_sheets)

    # OMNIGEN
    def delete_component(self, item_name: str) -> None:
        del self.quote_components_information[item_name]
        self.load_components_table()

    # OMNIGEN
    def delete_selected_components(self) -> None:
        selected_rows = list(set([item.row() for item in self.tableWidget_components_items.selectedItems()]))
        selected_items = [self.tableWidget_components_items.item(row, 1).text() for row in selected_rows]
        for item_name in selected_items:
            del self.quote_components_information[item_name]
        self.load_components_table()

    # OMNIGEN
    def load_quote_table(self) -> None:
        """
        This function loads a table with information about quotes, including images, item names,
        materials, gauges, and quantities.
        """
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        row_index: int = 0
        self.tableWidget_quote_items.setRowCount(0)
        for nest_name in list(self.quote_nest_information.keys()):
            if nest_name == "Components":
                continue
            if nest_name[0] != "_":
                self.tableWidget_quote_items.insertRow(row_index)
                item = QTableWidgetItem(nest_name.replace(".pdf", ""))
                item.setTextAlignment(4)
                font = QFont()
                font.setPointSize(15)
                item.setFont(font)
                self.tableWidget_quote_items.setItem(row_index, 0, item)
                self.tableWidget_quote_items.setSpan(row_index, 0, 1, self.tableWidget_quote_items.columnCount())
                self.set_table_row_color(self.tableWidget_quote_items, row_index, "#292929")
                row_index += 1
                for item in list(self.quote_nest_information[nest_name].keys()):
                    self.tableWidget_quote_items.insertRow(row_index)
                    self.tableWidget_quote_items.setRowHeight(row_index, 50)
                    label = ClickableLabel(self)
                    label.setToolTip("Click to make bigger.")
                    label.setFixedSize(50, 50)
                    pixmap = QPixmap(f"images/{self.quote_nest_information[nest_name][item]['image_index']}.jpeg")
                    does_part_exist: bool = True
                    if pixmap.isNull():
                        does_part_exist = False
                        pixmap = QPixmap("images/404.png")
                        label.clicked.connect(
                            partial(
                                self.open_image,
                                "images/404.png",
                                "Part does not exist",
                            )
                        )
                    else:
                        label.clicked.connect(
                            partial(
                                self.open_image,
                                f"images/{self.quote_nest_information[nest_name][item]['image_index']}.jpeg",
                                item,
                            )
                        )
                    scaled_pixmap = pixmap.scaled(label.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
                    label.setPixmap(scaled_pixmap)
                    self.tableWidget_quote_items.setCellWidget(row_index, 0, label)

                    self.tableWidget_quote_items.setItem(row_index, 1, QTableWidgetItem(item))
                    self.tableWidget_quote_items.item(row_index, 1).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    self.tableWidget_quote_items.setItem(
                        row_index,
                        2,
                        QTableWidgetItem(self.quote_nest_information[nest_name][item]["material"]),
                    )
                    self.tableWidget_quote_items.item(row_index, 2).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    self.tableWidget_quote_items.setItem(
                        row_index,
                        3,
                        QTableWidgetItem(self.quote_nest_information[nest_name][item]["gauge"]),
                    )
                    self.tableWidget_quote_items.item(row_index, 3).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    self.tableWidget_quote_items.setItem(
                        row_index,
                        4,
                        QTableWidgetItem(
                            str(int(self.quote_nest_information[nest_name][item]["quantity"]) * self.get_quantity_multiplier(item, nest_name))
                        ),
                    )
                    self.tableWidget_quote_items.item(row_index, 4).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    self.tableWidget_quote_items.setItem(
                        row_index,
                        5,
                        QTableWidgetItem(str(self.quote_nest_information[nest_name][item]["part_dim"])),
                    )
                    self.tableWidget_quote_items.item(row_index, 5).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    self.tableWidget_quote_items.item(row_index, 5).setToolTip(
                        f'Surface Area: {self.quote_nest_information[nest_name][item]["surface_area"]}'
                    )

                    # COGS
                    self.tableWidget_quote_items.setItem(
                        row_index,
                        6,
                        QTableWidgetItem("$0.00"),
                    )
                    self.tableWidget_quote_items.item(row_index, 6).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    # Bend Cost
                    try:
                        bend_cost: str = self.quote_nest_information[nest_name][item]["bend_cost"]
                    except KeyError:
                        bend_cost: str = "$0.00"
                    self.tableWidget_quote_items.setItem(
                        row_index,
                        7,
                        QTableWidgetItem(bend_cost),
                    )
                    self.tableWidget_quote_items.item(row_index, 7).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    # Labor Cost
                    try:
                        labor_cost: str = self.quote_nest_information[nest_name][item]["labor_cost"]
                    except KeyError:
                        labor_cost: str = "$0.00"
                    self.tableWidget_quote_items.setItem(
                        row_index,
                        8,
                        QTableWidgetItem(labor_cost),
                    )
                    self.tableWidget_quote_items.item(row_index, 8).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    # Unit Price
                    self.tableWidget_quote_items.setItem(
                        row_index,
                        9,
                        QTableWidgetItem("$0.00"),
                    )
                    self.tableWidget_quote_items.item(row_index, 9).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    # Price
                    self.tableWidget_quote_items.setItem(
                        row_index,
                        10,
                        QTableWidgetItem("$0.00"),
                    )
                    self.tableWidget_quote_items.item(row_index, 10).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    try:
                        shelf_number = self.quote_nest_information[nest_name][item]["shelf_number"]
                    except:
                        shelf_number = ""
                    # Shelf Number
                    self.tableWidget_quote_items.setItem(
                        row_index,
                        11,
                        QTableWidgetItem(shelf_number),
                    )
                    self.tableWidget_quote_items.item(row_index, 11).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

                    recut_button = RecutButton(self)
                    recut_button.setStyleSheet("margin: 5%;")
                    self.tableWidget_quote_items.setCellWidget(row_index, 12, recut_button)

                    send_part_to_inventory = QPushButton(self)
                    send_part_to_inventory.setText("Add Part to Inventory")
                    send_part_to_inventory.setStyleSheet("margin: 5%;")
                    send_part_to_inventory.setFixedWidth(150)
                    send_part_to_inventory.clicked.connect(partial(self.upload_part_to_inventory_thread, item, nest_name, send_part_to_inventory))
                    self.tableWidget_quote_items.setCellWidget(row_index, 13, send_part_to_inventory)

                    delete_button = DeletePushButton(
                        self,
                        tool_tip=f"Delete {item} from {nest_name} forever",
                        icon=QIcon(f"icons/trash.png"),
                    )
                    delete_button.clicked.connect(partial(self.delete_quote_part, item, nest_name, True))
                    delete_button.setStyleSheet("margin-top: 10px; margin-bottom: 10px; margin-right: 3px; margin-left: 3px;")
                    self.tableWidget_quote_items.setCellWidget(row_index, 14, delete_button)

                    if not does_part_exist:
                        self.set_table_row_color(self.tableWidget_quote_items, row_index, "#3F1E25")
                    row_index += 1
        self.tableWidget_quote_items.resizeColumnsToContents()
        self.scroll_position_manager.restore_scroll_position(tab_name="OmniGen_Quote", scroll=self.tableWidget_quote_items)
        self.update_quote_price()
        QApplication.restoreOverrideCursor()

    # OMNIGEN
    def load_components_table(self) -> None:
        self.tableWidget_components_items.blockSignals(True)
        self.tableWidget_components_items.setRowCount(0)
        for row_index, (item, item_data) in enumerate(self.quote_components_information.items()):
            self.tableWidget_components_items.insertRow(row_index)
            self.tableWidget_components_items.setRowHeight(row_index, 60)

            self.tableWidget_components_items.setItem(row_index, 0, QTableWidgetItem(""))
            self.tableWidget_components_items.item(row_index, 0).setData(Qt.ItemDataRole.DecorationRole, QPixmap(item_data['image_path']))
            self.tableWidget_components_items.setItem(row_index, 1, QTableWidgetItem(item))
            try:
                shelf_number = str(item_data['shelf_number'])
            except KeyError:
                shelf_number = ""
            self.tableWidget_components_items.setItem(row_index, 2, QTableWidgetItem(item_data['part_number']))
            self.tableWidget_components_items.item(row_index, 2).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.tableWidget_components_items.setItem(row_index, 3, QTableWidgetItem(shelf_number))
            self.tableWidget_components_items.item(row_index, 3).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.tableWidget_components_items.setItem(row_index, 4, QTableWidgetItem(str(item_data['description'])))
            self.tableWidget_components_items.setItem(row_index, 5, QTableWidgetItem(str(item_data['quantity'])))
            self.tableWidget_components_items.item(row_index, 5).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.tableWidget_components_items.setItem(row_index, 6, QTableWidgetItem(f'${item_data["unit_price"]:,.2f}'))
            self.tableWidget_components_items.item(row_index, 6).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            self.tableWidget_components_items.setItem(row_index, 7, QTableWidgetItem('$0.00'))
            self.tableWidget_components_items.item(row_index, 7).setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            delete_button = DeletePushButton(
                self,
                tool_tip=f"Delete {item} from forever",
                icon=QIcon(f"icons/trash.png"),
            )
            delete_button.clicked.connect(partial(self.delete_component, item))
            delete_button.setStyleSheet("margin-top: 10px; margin-bottom: 10px; margin-right: 3px; margin-left: 3px;")
            self.tableWidget_components_items.setCellWidget(row_index, 8, delete_button)
        self.scroll_position_manager.restore_scroll_position(tab_name="OmniGen_Components", scroll=self.tableWidget_components_items)
        self.tableWidget_components_items.blockSignals(False)
        self.update_components_prices()
        self.tableWidget_components_items.resizeColumnsToContents()
        self.tableWidget_components_items.setColumnWidth(0, 60)
        self.tableWidget_components_items.setColumnWidth(1, 250)

    def component_image_pasted(self, image_file_name: str, row: int) -> None:
        item_name = self.tableWidget_components_items.item(row, 1).text()
        self.quote_components_information[item_name]['image_path'] = image_file_name

    # OMNIGEN
    def update_components_prices(self) -> None:
        self.tableWidget_components_items.blockSignals(True)
        for row in range(self.tableWidget_components_items.rowCount()):
            quantity = float(self.tableWidget_components_items.item(row, 5).text())
            unit_price_item = float(self.tableWidget_components_items.item(row, 6).text().replace('$', '').replace(',', ''))
            price_item = self.tableWidget_components_items.item(row, 7)
            price_item.setText(f"${calculate_overhead(unit_price_item*quantity, self.spinBox_profit_margin_items.value() / 100, self.spinBox_overhead_items.value() / 100):,.2f}")
        self.tableWidget_components_items.blockSignals(False)
        self.update_quote_price()

    # OMNIGEN
    def get_components_prices(self) -> float:
        total_cost: float = 0.0
        self.tableWidget_components_items.blockSignals(True)
        for row in range(self.tableWidget_components_items.rowCount()):
            price_item = float(self.tableWidget_components_items.item(row, 7).text().replace('$', '').replace(',', ''))
            total_cost += price_item
        self.tableWidget_components_items.blockSignals(False)
        return total_cost

    # * /\ Load UI /\
    # * \/ CHECKERS \/
    def check_for_updates(self, on_start_up: bool = False) -> None:
        """
        It checks for updates on GitHub and displays a message dialog if there is a new update available

        Args:
          on_start_up (bool): bool = False. Defaults to False
        """
        try:
            try:
                response = requests.get("https://api.github.com/repos/thecodingjsoftware/Inventory-Manager/releases/latest")
            except ConnectionError:
                return
            version: str = response.json()["name"].replace(" ", "")
            if version != __version__:
                # message_dialog = self.show_message_dialog(
                #     title=__name__,
                #     message=f"There is a new update available.\n\nNew Version: {version}\n\nMake sure to make a backup\nbefore installing new version.",
                #     dialog_buttons=DialogButtons.ok_update,
                # )
                # if message_dialog == DialogButtons.update:
                subprocess.Popen("start update.exe", shell=True)
                # sys.exit()
            elif not on_start_up:
                self.show_message_dialog(
                    title=__name__,
                    message=f"There are currently no updates available.\n\nCurrent Version: {__version__}",
                )
        except Exception as e:
            if not on_start_up:
                self.show_error_dialog(title=__name__, message=f"Error\n\n{e}")

    def check_trusted_user(self) -> None:
        """
        If the user is not in the trusted_users list, then the user is not trusted
        """
        trusted_users = get_trusted_users()
        check_trusted_user = (user for user in trusted_users if not self.trusted_user)
        for user in check_trusted_user:
            self.trusted_user = self.username.lower() == user.lower()

        # if not self.trusted_user:
        # self.menuSort.setEnabled(False)
        # self.menuOpen_Category.setEnabled(False)

    # * /\ CHECKERS /\

    # * \/ Purchase Order \/
    def open_po(self, po_name: str = None) -> None:
        """
        It opens a dialog box with a list of items
        """
        if po_name is None:
            input_dialog = SelectItemDialog(
                title="Open PO",
                message="Select a PO to open",
                items=get_all_po(),
                button_names=DialogButtons.open_cancel,
            )
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
        """
        It opens a dialog box with a list of items
        """
        input_dialog = SelectItemDialog(
            title="Delete PO",
            message="Select a PO to delete.\n\nThis cannot be undone.",
            items=get_all_po(),
            button_names=DialogButtons.discard_cancel,
        )
        if input_dialog.exec():
            response = input_dialog.get_response()
            if response == DialogButtons.discard:
                try:
                    os.remove(f"PO's/templates/{input_dialog.get_selected_item()}.xlsx")
                    self.show_message_dialog(title="Success", message="Successfully removed template.")
                except AttributeError:
                    return
            elif response == DialogButtons.cancel:
                return

    def add_po_templates(self, po_file_paths: list[str], open_select_file_dialog: bool = False) -> None:
        """
        It takes a list of file paths, copies them to a new directory, and then shows a message dialog

        Args:
          po_file_paths (list[str]): list[str]
          open_select_file_dialog (bool): bool = False. Defaults to False
        """
        if open_select_file_dialog:
            po_file_paths, check = QFileDialog.getOpenFileNames(None, "Add Purchase Order Template", "", "Excel Files (*.xlsx)")
            if not po_file_paths:
                return
            for po_file_path in po_file_paths:
                try:
                    po_file: POTemplate = POTemplate(po_file_path)
                except Exception as error:
                    self.show_error_dialog(
                        title="Error",
                        message=f"Error parsing excel file. Please double check Order number and Vendor cell positions, or email me the excel file.\n\n{error}\n\n{po_file_path}",
                    )
                    return
                new_file_path = f"PO's/templates/{po_file.get_vendor().replace('.','')}.xlsx"
                shutil.copyfile(po_file_path, new_file_path)
            check_po_directories()
            self.show_message_dialog(title="Success", message="Successfully added new Purchase Order template.")
        if not open_select_file_dialog:
            for po_file_path in po_file_paths:
                try:
                    po_file: POTemplate = POTemplate(po_file_path)
                except Exception as error:
                    self.show_error_dialog(
                        title="Error",
                        message=f"Error parsing excel file. Please double check Order number and Vendor cell positions, or email me the excel file.\n\n{error}",
                    )
                    return
                new_file_path = f"PO's/templates/{po_file.get_vendor().replace('.','')}.xlsx"
                shutil.copyfile(po_file_path, new_file_path)
            check_po_directories()
            self.show_message_dialog(title="Success", message="Successfully added new Purchase Order template.")

        self.reload_po_menu()

    def reload_po_menu(self) -> None:
        """
        It creates a menu for each button in a list of buttons, and then adds an action to each menu for
        each item in a list of items
        """
        for po_button in self.po_buttons:
            po_menu = QMenu(self)
            for po in get_all_po():
                po_menu.addAction(po, partial(self.open_po, po))
            po_button.setMenu(po_menu)

    # * /\ Purchase Order /\
    def print_inventory(self) -> None:
        """
        It takes a file path as an argument, opens the file, generates an excel file, and saves it

        Returns:
          The return value is None.
        """
        try:
            file_name = f"excel files/{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}"
            excel_file = ExcelFile(inventory, f"{file_name}.xlsx")
            excel_file.generate()
            excel_file.save()

            input_dialog = MessageDialog(
                title="Success",
                message="Successfully generated inventory.\n\nWould you love to open it?",
                button_names=DialogButtons.open_cancel,
            )
            if input_dialog.exec():
                response = input_dialog.get_response()
                if response == DialogButtons.open:
                    try:
                        os.startfile(f"{os.path.dirname(os.path.realpath(sys.argv[0]))}/{file_name}.xlsx")
                    except AttributeError:
                        return
                elif response == DialogButtons.cancel:
                    return
        except Exception as error:
            self.show_error_dialog(
                title="Error",
                message=f"Error generating inventory excel file. Please review the error message below.\n\n{error}",
            )
            return

    # * \/ External Actions \/
    def open_website(self) -> None:
        """
        This function opens the website in the default browser.
        """
        webbrowser.open("http://10.0.0.92:5051", new=0)

    def open_item_history(self) -> None:
        """
        It opens the inventory history file in the data folder.
        """
        os.startfile(f"{os.path.dirname(os.path.realpath(sys.argv[0]))}/data/inventory history.xlsx")

    def open_folder(self, path: str) -> None:
        """
        It opens the folder in the default file browser

        Args:
          path: The path to the folder
        """
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.show_error_dialog("Error opening folder", f"{e}\n\nPlatform: {sys.platform}")

    def generate_error_log(self, message_dialog: MessageDialog) -> None:
        """
        It takes a screenshot of the error message dialog, saves it to a folder, writes the error
        message to a file, copies the app log to the folder, compresses the folder, and deletes the
        folder

        Args:
          message_dialog (MessageDialog): MessageDialog = The error message dialog that pops up when an
        error occurs.
        """
        output_directory: str = f"logs/ErrorLog_{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
        check_folders([output_directory])
        pixmap = QPixmap(message_dialog.grab())
        pixmap.save(f"{output_directory}/screenshot.png")
        with open(f"{output_directory}/error.log", "w", encoding="utf-8") as error_log:
            error_log.write(message_dialog.message)
        shutil.copyfile("logs/app.log", f"{output_directory}/app.log")
        compress_folder(foldername=output_directory, target_dir=output_directory)
        shutil.rmtree(output_directory)

    def play_celebrate_sound(self) -> None:
        """
        It starts a new thread that calls the function _play_celebrate_sound
        """
        threading.Thread(target=_play_celebrate_sound).start()

    def play_boot_sound(self) -> None:
        """
        It starts a new thread that calls the function _play_celebrate_sound
        """
        threading.Thread(target=_play_boot_sound).start()

    # * /\ External Actions /\
    # * \/ THREADS \/
    def sync_changes(self) -> None:
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Edit Inventory":
            self.status_button.setText(f'Synching - {datetime.now().strftime("%r")}', "lime")
            self.upload_file(
                [
                    f"{self.inventory_file_name}.json",
                ],
                False,
            )
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Parts in Inventory":
            self.status_button.setText(f'Synching - {datetime.now().strftime("%r")}', "lime")
            self.upload_file(
                [
                    f"{self.inventory_file_name} - Parts in Inventory.json",
                ],
                False,
            )
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Sheets in Inventory":
            self.status_button.setText(f'Synching - {datetime.now().strftime("%r")}', "lime")
            self.upload_file(
                [
                    f"{self.inventory_file_name} - Price of Steel.json",
                ],
                False,
            )
        elif self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            self.status_button.setText(f'Synching - {datetime.now().strftime("%r")}', "lime")
            if self.category == "Staging":
                self.upload_file(
                    [
                        "workspace - Admin.json",
                    ],
                    False,
                )
            else:
                self.upload_file(
                    [
                        "workspace - User.json",
                        "workspace - History.json",
                    ],
                    False,
                )

    # USER
    def download_workspace_file(self, file_to_download: str) -> None:
        self.status_button.setText(f'Downloading - {datetime.now().strftime("%r")}', "yellow")
        workspace_download_files = WorkspaceDownloadFiles(file_to_download)
        self.threads.append(workspace_download_files)
        workspace_download_files.signal.connect(self.download_workspace_file_response)
        workspace_download_files.start()

    # USER
    def download_workspace_file_response(self, response) -> None:
        if "Successfully downloaded" in response:
            self.status_button.setText(
                f"Successfully downloaded file - {datetime.now().strftime('%r')}",
                "lime",
            )
            file = response.split(";")[-1]
            file_name = os.path.basename(file)
            file_ext = file_name.split(".")[-1].upper()
            file_path = f"{os.path.dirname(os.path.realpath(__file__))}/data/workspace/{file_ext}/{file_name}"
            if file_ext in ["PNG", "JPEG", "JPG"]:
                self.open_image(path=file_path, title=file_name)
            if file_ext == "PDF":
                self.open_pdf(path=file_path)
        else:
            self.status_button.setText(f"Error - {response} - {datetime.now().strftime('%r')}", "red")

    # STAGING/EDITING
    def upload_workspace_files(self, files_to_upload: list[str]) -> None:
        self.status_button.setText(f'Uploading - {datetime.now().strftime("%r")}', "yellow")
        workspace_upload_thread = WorkspaceUploadThread(files_to_upload)
        self.threads.append(workspace_upload_thread)
        workspace_upload_thread.signal.connect(self.upload_workspace_files_response)
        workspace_upload_thread.start()

    # STAGING/EDITING
    def upload_workspace_files_response(self, response) -> None:
        if response == "Successfully uploaded":
            self.status_button.setText(
                f"Successfully uploaded files - {datetime.now().strftime('%r')}",
                "lime",
            )
        else:
            self.status_button.setText(f"Error - {response}", "red")

    # OMNIGEN
    def download_required_images(self, batch_data: dict) -> None:
        """
        This function downloads required images using a separate thread and emits a signal when the
        download is complete.

        Args:
          batch_data (dict): A dictionary containing information about the batch of data being
        processed. Each key in the dictionary represents an item in the batch, and the corresponding
        value is a dictionary containing information about that item.

        Returns:
          The function does not return anything explicitly, but it may return None implicitly if the
        condition in the if statement is True and the load_nests() method is called.
        """
        required_images = [batch_data[item]["image_index"] + ".jpeg" for item in list(batch_data.keys()) if item[0] != "_"]
        if not required_images:
            self.load_nests()
            return
        download_thread = DownloadImagesThread(required_images)
        download_thread.signal.connect(self.download_required_images_response)
        self.threads.append(download_thread)
        download_thread.start()

    # OMNIGEN
    def download_required_images_response(self, response: str) -> None:
        """
        This function loads nests if images are successfully downloaded and updates the status button
        text.

        Args:
          response (str): A string representing the response received after attempting to download
        required images.
        """
        if response == "Successfully downloaded":
            self.load_nests()
            with contextlib.suppress(AttributeError):
                self.status_button.setText(
                    f"Successfully loaded {len(self.get_all_selected_parts(self.tabs[self.category]))} parts",
                    "lime",
                )
        elif response == "":
            self.status_button.setText(f"Warning - No images found", "yellow")
        else:
            self.status_button.setText(f"Error - {response}", "red")

    # OMNIGEN
    def upload_batched_parts_images(self, batch_data) -> None:
        """
        This function uploads a batch of images by extracting their names from a dictionary and
        appending ".jpeg" to them before calling another function to upload the files.

        Args:
          batch_data: batch_data is a dictionary containing data for a batch of parts. The keys of the
        dictionary are the part names and the values are the corresponding data for each part.
        """
        images_to_upload: list[str] = [f"{item}.jpeg" for item in list(batch_data.keys()) if item[0] != "_"]
        self.upload_file(images_to_upload)

    def remove_quantity_thread_response(self, data) -> None:
        """
        It's a function that is called when a thread is finished. It's purpose is to update the GUI with
        the results of the thread.

        Args:
          data: str = "Done" or "count, total"
        """
        if data != "Done":
            count = int(data.split(", ")[0])
            total = int(data.split(", ")[1])
            __start: float = count / total
            __middle: float = __start + 0.001 if __start <= 1 - 0.001 else 1.0
            __end: float = __start + 0.0011 if __start <= 1 - 0.0011 else 1.0
            self.status_button.setText(f'Loading... {data.replace(", ", "/")}', color="white")
            self.status_button.setStyleSheet(
                """QPushButton#status_button {background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,stop:%(start)s #3daee9,stop:%(middle)s #3daee9,stop:%(end)s #1E363F)}"""
                % {"start": str(__start), "middle": str(__middle), "end": str(__end)}
            )
        else:
            self.status_button.setText("Done", "lime")
            inventory.load_data()
            self.centralwidget.setEnabled(True)
            self.listWidget_itemnames.setEnabled(True)
            self.pushButton_create_new.setEnabled(True)
            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(True)
            self.radioButton_category.setEnabled(True)
            self.radioButton_single.setEnabled(True)
            self.sort_inventory()
            self.sync_changes()

    def changes_response(self, response: str) -> None:
        """
        This function updates the status button text to indicate syncing, downloads all files, and
        updates the status button text again to indicate completion.

        Args:
          response (str): A string representing the response received from a server or API call.
        """
        if "download" in response:
            self.status_button.setText(f'Syncing - {datetime.now().strftime("%r")}', "yellow")
            self.downloading_changes = True
            self.download_all_files()
            self.status_button.setText(f'Synched - {datetime.now().strftime("%r")}', "lime")
        else:
            self.status_button.setText(f"Syncing Error - {response}", "red")

    def data_received(self, data) -> None:
        """
        This function handles the data received from the server and performs various actions based on
        the received data.

        Args:
          data: The data received by the function. It is of type string.
        """
        if data == "Successfully uploaded":
            self.status_button.setText(f'Synched - {datetime.now().strftime("%r")}', "lime")
        if self.downloading_changes and data == "Successfully downloaded":
            if self.tabWidget.tabText(self.tabWidget.currentIndex()) in [
                "Parts in Inventory",
                "Sheets in Inventory",
            ]:
                inventory.load_data()
                price_of_steel_inventory.load_data()
                parts_in_inventory.load_data()
                self.load_categories()
            if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "OmniGen":
                inventory.load_data()
                price_of_steel_inventory.load_data()
                parts_in_inventory.load_data()
                self.load_cuttoff_drop_down()
            self.downloading_changes = False

        if not self.finished_downloading_all_files:
            self.files_downloaded_count += 1
        if self.files_downloaded_count == 1 and not self.finished_downloading_all_files:
            self.finished_downloading_all_files = True
            inventory.load_data()
            price_of_steel_inventory.load_data()
            parts_in_inventory.load_data()
            self.load_categories()
            self.status_button.setText(f'Downloaded all files - {datetime.now().strftime("%r")}', "lime")
            self.centralwidget.setEnabled(True)
        if "timed out" in str(data).lower() or "fail" in str(data).lower():
            self.show_error_dialog(
                title="Time out",
                message=f"Server is either offline, try again or not connected to internet. Make sure VPN's are disabled, else contact server or netowrk administrator.\n\n{str(data)}",
            )
            self.status_button.setText("Cannot connect to server", "red")
        # QApplication.restoreOverrideCursor()

    def start_changes_thread(self, files_to_download: list[str]) -> None:
        """
        It creates a thread that will run a function that will download a list of files from a server

        Args:
          files_to_download (list[str]): list[str]
        """
        changes_thread = ChangesThread(self, files_to_download)  # 5 minutes
        changes_thread.signal.connect(self.changes_response)
        self.threads.append(changes_thread)
        changes_thread.start()

    def start_exchange_rate_thread(self) -> None:
        """
        It creates an instance of the ExchangeRate class and starts it
        """
        exchange_rate_thread = ExchangeRate()
        exchange_rate_thread.signal.connect(self.exchange_rate_received)
        self.threads.append(exchange_rate_thread)
        exchange_rate_thread.start()

    def exchange_rate_received(self, exchange_rate: float) -> None:
        """
        It takes the exchange rate from the API and updates the label on the GUI with the exchange rate
        and the time it was received

        Args:
          exchange_rate (float): float
        """
        self.label_exchange_price.setText(f"1.00 USD: {exchange_rate} CAD - {datetime.now().strftime('%r')}")
        self.label_total_unit_cost.setText(f"Total Unit Cost: ${inventory.get_total_unit_cost(self.category, self.get_exchange_rate()):,.2f}")
        settings_file.change_item(item_name="exchange_rate", new_value=exchange_rate)
        self.update_stock_costs()

    # NOTE SHEETS IN INVENTORY
    def send_sheet_report(self) -> None:
        thread = SendReportThread()
        self.start_thread(thread)

    def upload_file(self, files_to_upload: list[str], get_response: bool = True) -> None:
        """
        It creates a new thread, sets the cursor to wait, and starts the thread

        Args:
          files_to_upload (str): str - The file to upload
        """
        self.get_upload_file_response = get_response
        upload_thread = UploadThread(files_to_upload)
        # if get_response:
        # # QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self.start_thread(upload_thread)

    def download_file(self, files_to_download: list[str], get_response: bool = True) -> None:
        """
        It starts a thread that downloads a file from a server

        Args:
          files_to_download (list[str]): list[str]
        """
        self.get_upload_file_response = get_response
        download_thread = DownloadThread(files_to_download)
        # # QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self.start_thread(download_thread)

    def start_thread(self, thread) -> None:
        """
        It connects the signal from the thread to the data_received function, then appends the thread to
        the threads list, and finally starts the thread

        Args:
          thread: The thread to start
        """
        thread.signal.connect(self.data_received)
        self.threads.append(thread)
        thread.start()

    def download_all_files(self) -> None:
        """
        This function downloads three JSON files related to inventory and steel prices.
        """
        self.download_file(
            [
                f"{self.inventory_file_name} - Parts in Inventory.json",
                f"{self.inventory_file_name} - Price of Steel.json",
                f"{self.inventory_file_name}.json",
                "workspace_settings.json",
                "workspace - Admin.json",
                "workspace - User.json",
                "workspace - History.json",
            ],
            False,
        )

    # OMNIGEN
    def start_process_nest_thread(self, nests: list[str]) -> None:
        self.status_button.setText("Loadings Nests", "yellow")
        # QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self.pushButton_load_nests.setEnabled(False)
        load_nest_thread = LoadNests(self, nests)
        self.threads.append(load_nest_thread)
        load_nest_thread.signal.connect(self.response_from_load_nest_thread)
        load_nest_thread.start()

    # OMNIGEN
    def response_from_load_nest_thread(self, data) -> None:
        if "ERROR!" in data:
            self.status_button.setText("Encountered error processing pdfs", "red")
            self.pushButton_load_nests.setEnabled(True)
            self.show_error_dialog("oh no. Encountered error processing pdfs.", data)
            return
        if type(data) == dict:
            self.quote_nest_information.clear()
            self.quote_nest_information = data
            self.pushButton_load_nests.setEnabled(True)

        select_item_dialog = SelectItemDialog(
            button_names=DialogButtons.set_skip,
            title="Select Material",
            message="Select Material",
            items=price_of_steel_information.get_value("materials"),
        )

        if select_item_dialog.exec():
            response = select_item_dialog.get_response()
            if response == DialogButtons.set:
                self.comboBox_global_sheet_material.setCurrentText(select_item_dialog.get_selected_item())

            self.load_nests()
            self.status_button.setText(f"Successfully loaded {len(self.get_all_selected_nests())} nests", "lime")

            if response == DialogButtons.set:
                self.global_nest_material_change()
        # QApplication.restoreOverrideCursor()

    # OMNIGEN
    def upload_part_to_inventory_thread(self, item_name: str, nest_name: str, send_part_to_inventory: QPushButton) -> None:
        """
        The function uploads a part to the inventory and updates the UI accordingly.

        Args:
          item_name (str): The `item_name` parameter is a string that represents the name of the item
        being uploaded to the inventory.
          nest_name (str): The parameter "nest_name" is a string that represents the name of a nest.
          send_part_to_inventory (QPushButton): QPushButton object that represents the button used to
        send the part to the inventory.
        """
        send_part_to_inventory.setEnabled(False)
        self.save_quote_table_values()
        data = {item_name: self.quote_nest_information[nest_name][item_name]}
        # QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        date_time = datetime.now().strftime("%B%d%Y%I%M%S%f")

        with open(f"parts_batch_to_upload_part - {date_time}.json", "w") as f:
            json.dump(data, f, sort_keys=True, indent=4)
        upload_batch = UploadBatch(f"parts_batch_to_upload_part - {date_time}.json")
        upload_batch.signal.connect(self.upload_batch_to_inventory_response)
        self.threads.append(upload_batch)
        self.status_button.setText("Uploading Part", "yellow")
        upload_batch.start()
        self.upload_batched_parts_images(data)
        send_part_to_inventory.setEnabled(True)

    # OMNIGEN
    def upload_batch_to_inventory_thread(self, batch_data: dict, should_update_inventory: bool, should_generate_quote: bool) -> None:
        # QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        if should_update_inventory:
            with open("parts_batch_to_upload_workorder.json", "w") as file:
                json.dump(batch_data, file, sort_keys=True, indent=4)
            upload_batch = UploadBatch("parts_batch_to_upload_workorder.json")
        elif should_generate_quote:
            with open("parts_batch_to_upload_quote.json", "w") as file:
                json.dump(batch_data, file, sort_keys=True, indent=4)
            upload_batch = UploadBatch("parts_batch_to_upload_quote.json")
        else:
            with open("parts_batch_to_upload_packing_slip.json", "w") as file:
                json.dump(batch_data, file, sort_keys=True, indent=4)
            upload_batch = UploadBatch("parts_batch_to_upload_packing_slip.json")
        upload_batch.signal.connect(self.upload_batch_to_inventory_response)
        self.threads.append(upload_batch)
        self.status_button.setText("Uploading Batch", "yellow")
        upload_batch.start()

    # OMNIGEN
    def upload_batch_to_inventory_response(self, response: str, file_name: str) -> None:
        if response == "Batch sent successfully":
            self.status_button.setText("Batch was sent successfully", "lime")
            # self.show_message_dialog('Success', 'Batch was sent successfully')
        else:
            self.status_button.setText("Batch Failed to send", "red")
            self.show_error_dialog("Error", f"Something went wrong.\n\n{response}")
        # QApplication.restoreOverrideCursor()
        os.remove(file_name)

    def set_order_number_thread(self, order_number: int) -> None:
        """
        This function creates a new thread to set an order number and connects it to a response
        function.

        Args:
          order_number (int): An integer representing the order number that needs to be set.
        """
        set_order_number_thread = SetOrderNumberThread(order_number)
        set_order_number_thread.signal.connect(self.set_order_number_thread_response)
        self.threads.append(set_order_number_thread)
        set_order_number_thread.start()

    def get_order_number_thread(self) -> None:
        """
        This function creates and starts a thread to get an order number and connects its signal to a
        response function.
        """
        get_order_number_thread = GetOrderNumberThread()
        get_order_number_thread.signal.connect(self.get_order_number_thread_response)
        self.threads.append(get_order_number_thread)
        get_order_number_thread.start()

    def set_order_number_thread_response(self, response) -> None:
        """
        This function sets an order number and shows an error dialog if there is an error.

        Args:
          response: The response parameter is a string that indicates the result of a function call. If
        the response is not equal to "success", an error dialog will be displayed with the response
        message.
        """
        if response != "success":
            self.show_error_dialog("oh no. Encountered error when setting order number.", str(response))

    def get_order_number_thread_response(self, order_number: int) -> None:
        """
        This function takes an order number as input, converts it to an integer, and displays an error
        message if there is an exception.

        Args:
          order_number (int): The order number parameter is an integer that represents the unique
        identifier of an order.
        """
        try:
            self.order_number = int(order_number)
        except Exception:
            self.show_error_dialog("oh no. Encountered error when fetching order number.", str(order_number))

    # OMNIGEN
    def load_previous_nests_files_thread(self) -> None:
        """
        The function loads previous nest files in a separate thread and updates the status button with
        the current time.
        """
        self.status_button.setText(f'Fetching previous nests - {datetime.now().strftime("%r")}', "yellow")
        get_previous_nests_files_thread = GetPreviousNestsFilesThread()
        self.threads.append(get_previous_nests_files_thread)
        get_previous_nests_files_thread.signal.connect(self.load_previous_nests_files_response)
        get_previous_nests_files_thread.start()

    # OMNIGEN
    def load_previous_nests_files_response(self, data: dict) -> None:
        """
        The function loads previous nests files and updates the status button accordingly.

        Args:
          data (dict): The `data` parameter is a dictionary containing information about previous nests
        files.
        """
        if isinstance(data, dict):
            self.status_button.setText(
                f"Successfully fetched previous nests - {datetime.now().strftime('%r')}",
                "lime",
            )
            self.load_previous_nest_tree_view(data)
        else:
            self.status_button.setText(f"Error - {data}", "red")

    # OMNIGEN
    def load_previous_nests_data_thread(self, files_to_load: list[str]) -> None:
        """
        The function loads previous nests data from a list of files in a separate thread and updates the
        status button with the current time.

        Args:
          files_to_load (list[str]): The parameter `files_to_load` is a list of strings that represents
        the files that need to be loaded. Each string in the list should be the file name or file path
        of the file to be loaded.
        """
        self.status_button.setText(f'Fetching previous nests data - {datetime.now().strftime("%r")}', "yellow")
        get_previous_nests_data_thread = GetPreviousNestsDataThread(files_to_load)
        self.threads.append(get_previous_nests_data_thread)
        get_previous_nests_data_thread.signal.connect(self.load_previous_nests_data_response)
        get_previous_nests_data_thread.start()

    # OMNIGEN
    def load_previous_nests_data_response(self, data: dict[str, dict[str, Any]]) -> None:
        """
        The function loads previous nests data, groups it, sorts it, and updates the UI accordingly.

        Args:
          data (dict[str, dict[str, Any]]): The `data` parameter is a dictionary containing nested
        dictionaries. The keys of the outer dictionary are strings, and the values are inner
        dictionaries. The keys of the inner dictionaries are also strings, and the values can be of any
        type.
        """
        if isinstance(data, dict):
            self.status_button.setText(
                f"Successfully fetched previous nests data - {datetime.now().strftime('%r')}",
                "lime",
            )
            self.quote_nest_information.clear()
            self.quote_nest_information = data

            with contextlib.suppress(KeyError):
                # This checks if Components are even in the data
                self.quote_nest_information['Components']
                self.quote_components_information.clear()
                self.quote_components_information = data['Components']
                del self.quote_nest_information['Components']

            self.pushButton_load_previous_nests.setEnabled(True)
            self.load_nests()
            self.load_components_table()
        else:
            self.status_button.setText(f"Error - {data}", "red")

    # * /\ THREADS /\

    # * \/ BACKUP ACTIONS \/
    def load_backup(self, file_path: str = None) -> None:
        """
        It opens a file dialog, and if the user selects a file, it extracts the file and then loads the
        categories
        """
        if file_path is None:
            backup_file, check = QFileDialog.getOpenFileName(
                None,
                "Load backup",
                "backups/",
                "Zip Files (*.zip)",
            )
            if check:
                extract(file_to_extract=backup_file)
                self.load_categories()
                self.show_message_dialog(title="Success", message="Successfully loaded backup!")
        else:
            extract(file_to_extract=file_path)
            self.load_categories()
            self.show_message_dialog(title="Success", message="Successfully loaded backup!")

    def backup_database(self) -> None:
        """
        This function compresses the database file and shows a message dialog to the user
        """
        compress_database(path_to_file=f"data/{self.inventory_file_name}.json")
        self.show_message_dialog(
            title="Success",
            message="Backup was successful!\n\nNote! Loading a backup will not sync changes. Syncing is being done under the hood consistently, and there is no need for creating local backups anymore.",
        )

    # * /\ BACKUP ACTIONS /\
    def clear_layout(self, layout) -> None:
        """
        If the layout is not None, while the layout has items, take the first item, get the widget, if
        the widget is not None, delete it, otherwise clear the layout

        Args:
          layout: The layout to be cleared
        """
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
        """
        It sets the layout of the window to a left label, a highlighted message, and a right label.

        Args:
          left_label (str): str,
          highlighted_message (str): str = "Click Me"
          right_label (str): str = "",
          highlighted_message_width (int): int = The width of the highlighted message
          button_pressed_event: The function to be called when the button is pressed.
        """

        self.clear_layout(self.active_layout)
        self.tabs.clear()

        self.tab_widget = QTabWidget(self)
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_category)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        with contextlib.suppress(AttributeError):
            self.active_layout.addWidget(self.tab_widget)
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
        """
        If the event has a URL, accept it, otherwise ignore it.

        Args:
          event: This is the event object that is passed to the method.
        """
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """
        If the file is an Excel file, then accept the drop event and display a message. Otherwise,
        ignore the drop event.

        Args:
          event: The event object.
        """
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            return
        if event.mimeData().hasUrls:
            for url in event.mimeData().urls():
                if str(url.toLocalFile()).endswith(".xlsx") and self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Edit Inventory":
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
        """
        It loads the categories from the database and displays them in the list widget

        Args:
          event: QDragLeaveEvent
        """
        # self.load_categories()
        pass

    def dropEvent(self, event: QDropEvent) -> None:
        """
        If the event has URLs, set the drop action to copy, accept the event, get the local file paths
        from the URLs, add the PO files to the database, and reload the categories

        Args:
          event: The event object
        """
        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Workspace":
            return
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                if str(url.toLocalFile()).endswith(".xlsx") and self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Edit Inventory":
                    files = [str(url.toLocalFile()) for url in event.mimeData().urls()]
                    # self.load_categories()
                    self.add_po_templates(files)
                    break
                elif str(url.toLocalFile()).endswith(".zip"):
                    self.load_backup([str(url.toLocalFile()) for url in event.mimeData().urls()][0])
            event.ignore()

    def closeEvent(self, event) -> None:
        """
        The function saves the geometry of the window and then closes the window

        Args:
          event: the event that triggered the close_event() method
        """
        # compress_database(
        #     path_to_file=f"data/{self.inventory_file_name}.json",
        #     on_close=True,
        # )
        # for thread in self.threads:
        #     thread.quit()
        #     thread.wait()
        self.save_geometry()
        self.save_menu_tab_order()
        super().closeEvent(event)

    # * /\ OVERIDDEN UI EVENTS /\


def main() -> None:
    """
    It creates a QApplication, creates a MainWindow, shows the MainWindow, and then runs the
    QApplication
    """
    app = QApplication(sys.argv)



    set_theme(app, theme="dark")

    font = QFont()
    font.setFamily("Segoe UI")
    font.setWeight(400)
    app.setFont(font)
    app.processEvents()
    mainwindow = MainWindow()
    mainwindow.show()
    app.exec()

# cProfile.run('main()')
main()
