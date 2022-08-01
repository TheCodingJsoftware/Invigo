# sourcery skip: avoid-builtin-shadow
__author__ = "Jared Gross"
__copyright__ = "Copyright 2022, TheCodingJ's"
__credits__: "list[str]" = ["Jared Gross"]
__license__ = "MIT"
__name__ = "Inventory Manager"
__version__ = "v1.3.0"
__updated__ = "2022-08-01 15:35:03"
__maintainer__ = "Jared Gross"
__email__ = "jared@pinelandfarms.ca"
__status__ = "Production"

import contextlib
import itertools
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from functools import partial
from typing import Any

import requests
from forex_python.converter import CurrencyRates
from PyQt5 import QtTest, uic
from PyQt5.QtCore import QFile, QPoint, Qt, QTextStream, QTimer
from PyQt5.QtGui import QCursor, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QCompleter,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStyle,
    QTabWidget,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
    qApp,
)

import ui.BreezeStyleSheets.breeze_resources
from threads.changes_thread import ChangesThread
from threads.download_thread import DownloadThread
from threads.remove_quantity import RemoveQuantityThread
from threads.ui_threads import ProcessItemSelectedThread, SetStyleSheetThread
from threads.upload_thread import UploadThread
from ui.about_dialog import AboutDialog
from ui.add_item_dialog import AddItemDialog
from ui.custom_widgets import (
    ClickableLabel,
    CostLineEdit,
    DeletePushButton,
    DragableLayout,
    ExchangeRateComboBox,
    HeaderScrollArea,
    HumbleComboBox,
    HumbleDoubleSpinBox,
    HumbleSpinBox,
    ItemNameComboBox,
    NotesPlainTextEdit,
    PartNumberComboBox,
    POPushButton,
    PriorityComboBox,
    RichTextPushButton,
    ViewTree,
    set_default_dialog_button_stylesheet,
    set_status_button_stylesheet,
)
from ui.input_dialog import InputDialog
from ui.message_dialog import MessageDialog
from ui.select_item_dialog import SelectItemDialog
from ui.web_scrape_results_dialog import WebScrapeResultsDialog
from utils import excel_file
from utils.compress import compress_database, compress_folder
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.excel_file import ExcelFile
from utils.extract import extract
from utils.file_changes import FileChanges
from utils.json_file import JsonFile
from utils.json_object import JsonObject
from utils.po import check_po_directories, get_all_po
from utils.po_template import POTemplate
from utils.trusted_users import get_trusted_users
from web_scrapers.ebay_scraper import EbayScraper
from web_scrapers.exchange_rate import ExchangeRate


def default_settings() -> None:
    """
    It checks if a setting exists in the settings file, and if it doesn't, it creates it with a default
    value
    """
    check_setting(setting="exchange_rate", default_value=1.0)
    check_setting(setting="dark_mode", default_value=True)
    check_setting(setting="sort_ascending", default_value=False)
    check_setting(setting="sort_descending", default_value=True)
    check_setting(setting="sort_quantity_in_stock", default_value=True)
    check_setting(setting="sort_priority", default_value=False)
    check_setting(setting="sort_alphabatical", default_value=False)
    check_setting(setting="server_ip", default_value="10.0.0.64")
    check_setting(setting="server_port", default_value=4000)
    check_setting(
        setting="geometry",
        default_value={"x": 200, "y": 200, "width": 600, "height": 400},
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
    check_setting(setting="trusted_users", default_value=["itsme", "jared", "joseph"])
    check_setting(setting="auto_backup_to_cloud", default_value=False)


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


check_folders(
    folders=["logs", "data", "backups", "excel files", "PO's", "PO's/templates"]
)

logging.basicConfig(
    filename="logs/app.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)


settings_file = JsonFile(file_name="settings")
default_settings()
inventory = JsonFile(
    file_name=f"data/{settings_file.get_value(item_name='inventory_file_name')}"
)
geometry = JsonObject(JsonFile=settings_file, object_name="geometry")


class MainWindow(QMainWindow):
    """The class MainWindow inherits from the class QMainWindow"""

    def __init__(self):
        """
        It loads the UI and starts a thread that checks for changes in a JSON file.
        """
        super().__init__()
        uic.loadUi("ui/main_menu.ui", self)
        self.username = os.getlogin().title()
        self.trusted_user: bool = False
        self.setWindowTitle(f"{__name__} - {__version__} - {self.username}")
        self.setWindowIcon(QIcon(Icons.icon))

        check_po_directories()
        self.check_for_updates(on_start_up=True)

        # VARIABLES
        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

        self.inventory_prices_objects: dict[
            QComboBox,
            dict[
                dict[str, QSpinBox],
                dict[str, QSpinBox],
                dict[str, QDoubleSpinBox],
                dict[str, QComboBox],
                dict[str, QLineEdit],
                dict[str, QLineEdit],
            ],
        ] = {}
        self.po_buttons: list[QPushButton] = []
        self.categories: list[str] = []
        self.scroll_areas: list[QScrollArea] = []
        self.highlight_color: str = "#3daee9"
        self.category: str = ""
        self.tabs: list[QVBoxLayout] = []
        self.last_item_selected_index: int = 0
        self.last_item_selected_text: str = None
        self.item_layouts: list[QHBoxLayout] = []
        self.group_layouts: dict[str, QVBoxLayout] = {}
        self.threads: tuple[
            ChangesThread | ExchangeRate | DownloadThread | UploadThread | EbayScraper,
            ...,
        ] = []
        self.get_upload_file_response: bool = True
        # {str("Header name"): int(Label fixed width)}
        self.headers: dict[dict[str, int]] = {
            "Part Name": 486,
            "Part Number": 120,
            "Quantity Per Unit": 100,
            "Quantity in Stock": 100,
            "Item Price": 100,
            "": 40,  # USD/CAD
            "Total Cost in Stock": 100,
            "Total Unit Cost": 100,
            "Priority": 60,
            "Notes": 170,
        }

        self.__load_ui()
        self.tool_box_menu_changed()
        self.start_changes_thread(
            f"data/{settings_file.get_value(item_name='inventory_file_name')}.json"
        )
        self.quantities_change()
        self.start_exchange_rate_thread()
        self.check_trusted_user()
        self.show()
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
        self.update_theme()

        # Dockable Widget
        self.dockWidget_create_add_remove.dockLocationChanged.connect(
            self.dock_location_changed
        )
        self.lineEdit_search_items.textChanged.connect(self.update_list_widget)
        self.radioButton_category.toggled.connect(self.quantities_change)
        self.radioButton_single.toggled.connect(self.quantities_change)

        if settings_file.get_value(item_name="change_quantities_by") == "Category":
            self.radioButton_category.setChecked(True)
            self.radioButton_single.setChecked(False)
        else:
            self.radioButton_category.setChecked(False)
            self.radioButton_single.setChecked(True)

        # Tool Box
        self.toolBox.setCurrentIndex(
            settings_file.get_value(item_name="last_toolbox_tab")
        )
        self.toolBox.currentChanged.connect(self.tool_box_menu_changed)

        # Status
        self.status_button = RichTextPushButton(
            self, '<p style="color:yellow;">Getting changes...</p>'
        )
        set_status_button_stylesheet(button=self.status_button, color="yellow")
        self.status_button.setObjectName("status_button")
        self.status_button.setFlat(True)
        self.status_button.setFixedHeight(20)
        self.status_button.setStatusTip(
            "View additions and removals from the inventory file."
        )
        self.verticalLayout_status.addWidget(self.status_button)

        # Tab widget
        self.load_categories()
        self.pushButton_create_new.clicked.connect(self.add_item)
        self.pushButton_add_quantity.clicked.connect(self.add_quantity)
        # self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_add_quantity.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/list_add.png")
        )
        self.pushButton_remove_quantity.clicked.connect(self.remove_quantity)
        # self.pushButton_remove_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/list_remove.png")
        )
        self.listWidget_itemnames.itemSelectionChanged.connect(
            self.listWidget_item_changed
        )

        # Action events
        # HELP
        self.actionAbout_Qt.triggered.connect(qApp.aboutQt)
        self.actionAbout_Qt.setIcon(
            self.style().standardIcon(QStyle.SP_TitleBarMenuButton)
        )
        self.actionCheck_for_Updates.triggered.connect(self.check_for_updates)
        self.actionCheck_for_Updates.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/refresh.png")
        )
        self.actionAbout.triggered.connect(self.show_about_dialog)
        self.actionAbout.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/about.png")
        )
        self.actionRelease_Notes.triggered.connect(partial(self.show_whats_new, True))
        self.actionRelease_Notes.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/release_notes.png")
        )
        self.actionWebsite.triggered.connect(self.open_website)
        self.actionWebsite.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/website.png")
        )
        # PRINT
        self.actionPrint_Inventory.triggered.connect(self.print_inventory)

        # SETTINGS
        self.actionDarkmode.setChecked(settings_file.get_value(item_name="dark_mode"))
        self.actionDarkmode.triggered.connect(self.toggle_dark_mode)

        self.actionAuto_back_up_to_cloud.setChecked(
            settings_file.get_value(item_name="auto_backup_to_cloud")
        )
        self.actionAuto_back_up_to_cloud.triggered.connect(
            self.toggle_auto_back_up_to_cloud
        )

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
        self.actionAlphabatical.setChecked(
            settings_file.get_value(item_name="sort_alphabatical")
        )
        self.actionAlphabatical.setEnabled(
            not settings_file.get_value(item_name="sort_alphabatical")
        )
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
        self.actionQuantity_in_Stock.setChecked(
            settings_file.get_value(item_name="sort_quantity_in_stock")
        )
        self.actionQuantity_in_Stock.setEnabled(
            not settings_file.get_value(item_name="sort_quantity_in_stock")
        )
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
        self.actionPriority.setEnabled(
            not settings_file.get_value(item_name="sort_priority")
        )
        self.actionAscending.triggered.connect(
            partial(
                self.action_group, "order", [self.actionAscending, self.actionDescending]
            )
        )
        self.actionAscending.setChecked(
            settings_file.get_value(item_name="sort_ascending")
        )
        self.actionAscending.setEnabled(
            not settings_file.get_value(item_name="sort_ascending")
        )
        self.actionDescending.triggered.connect(
            partial(
                self.action_group, "order", [self.actionAscending, self.actionDescending]
            )
        )
        self.actionDescending.setChecked(
            settings_file.get_value(item_name="sort_descending")
        )
        self.actionDescending.setEnabled(
            not settings_file.get_value(item_name="sort_descending")
        )
        self.actionSort.triggered.connect(self.sort_inventory)
        self.update_sorting_status_text()

        # PURCHASE ORDERS
        self.actionAdd_Purchase_Order.triggered.connect(
            partial(self.add_po_templates, [], True)
        )
        self.actionRemove_Purchase_Order.triggered.connect(self.delete_po)
        self.actionOpen_Purchase_Order.triggered.connect(partial(self.open_po, None))
        self.actionOpen_Folder.triggered.connect(partial(self.open_folder, "PO's"))
        # FILE
        self.menuOpen_Category.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/folder.png")
        )
        self.menuUpload_File.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/upload.png")
        )
        self.actionUploadInventory.triggered.connect(
            partial(
                self.upload_file,
                f"data/{settings_file.get_value(item_name='inventory_file_name')}.json",
            )
        )
        self.actionUploadInventory.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/upload.png")
        )
        self.menuDownload_File.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/download.png")
        )
        self.actionDownloadInventory.triggered.connect(
            partial(
                self.download_file,
                f"data/{settings_file.get_value(item_name='inventory_file_name')}.json",
            )
        )
        self.actionDownloadInventory.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/download.png")
        )
        self.actionCreate_Category.triggered.connect(self.create_new_category)
        self.actionCreate_Category.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/list_add.png")
        )
        self.actionDelete_Category.triggered.connect(self.delete_category)
        self.actionDelete_Category.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/list_remove.png")
        )
        self.actionClone_Category.triggered.connect(self.clone_category)
        self.actionClone_Category.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/tab_duplicate.png")
        )

        self.actionBackup.triggered.connect(self.backup_database)
        self.actionBackup.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/backup.png")
        )
        self.actionLoad_Backup.triggered.connect(partial(self.load_backup, None))
        self.actionExit.triggered.connect(self.close)
        self.actionExit.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/tab_close.png")
        )

        # SEARCH
        self.actionEbay.triggered.connect(self.search_ebay)

    def quick_load_category(self, index: int) -> None:
        """
        It sets the current tab to the index passed in, then calls the load_tab function

        Args:
          index (int): int - The index of the tab to load
        """
        self.tab_widget.setCurrentIndex(index)
        self.load_tab()

    #! Doesn't work
    def dock_location_changed(self, area: int) -> None:
        """
        If the dock location is not floating, save the dock location to the settings file

        Args:
          area (int): 0 -> Floating
        """
        if area != 0:
            """
            area: 0 -> Floating
            area: 1 -> Left
            area: 2 -> Right
            """
            settings_file.add_item("last_dock_location", area)

    def tool_box_menu_changed(self) -> None:
        """

        If the toolbox is not on the first tab, hide the dock widget
        """
        if self.toolBox.currentIndex() != 0:
            self.load_tree_view(inventory)
        else:
            self.dockWidget_create_add_remove.setVisible(self.tab_widget.tabText(0) != "")
            self.status_button.setHidden(False)
        settings_file.add_item("last_toolbox_tab", self.toolBox.currentIndex())

    def load_categories(self) -> None:
        """
        It loads the categories from the inventory file and creates a tab for each category.
        """
        self.set_layout_message("", "Loading...", "", 120)
        inventory = JsonFile(
            file_name=f"data/{settings_file.get_value(item_name='inventory_file_name')}"
        )
        # QApplication.setOverrideCursor(Qt.BusyCursor)
        self.clear_layout(self.verticalLayout)
        self.tabs.clear()
        self.scroll_areas.clear()
        self.categories = inventory.get_keys()
        self.menuOpen_Category.clear()
        for i, category in enumerate(self.categories):
            action = QAction(self)
            action.setIcon(
                QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/project_open.png")
            )
            action.triggered.connect(partial(self.quick_load_category, i))
            action.setText(category)
            self.menuOpen_Category.addAction(action)
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setStyleSheet(
            "QTabBar::tab::disabled {width: 0; height: 0; margin: 0; padding: 0; border: none;} "
        )
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_category)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        i: int = -1
        for i, category in enumerate(self.categories):
            tab = HeaderScrollArea(
                self.headers,
                self,
            )
            self.scroll_areas.append(tab)
            content_widget = QWidget()
            content_widget.setObjectName("tab")
            tab.setWidget(content_widget)
            tab.setWidgetResizable(True)
            layout = QVBoxLayout(content_widget)
            layout.setAlignment(Qt.AlignTop)
            self.tabs.append(layout)
            self.tab_widget.addTab(tab, category)

        if i == -1:
            tab = QScrollArea(self)
            self.scroll_areas.append(tab)
            content_widget = QWidget()
            content_widget.setObjectName("tab")
            tab.setWidget(content_widget)
            tab.setWidgetResizable(True)
            layout = QVBoxLayout(content_widget)
            layout.setAlignment(Qt.AlignTop)
            self.tabs.append(layout)
            self.tab_widget.addTab(tab, "")
            i += 1

        self.tab_widget.setCurrentIndex(settings_file.get_value("last_category_tab"))
        self.tab_widget.currentChanged.connect(self.load_tab)
        self.verticalLayout.addWidget(self.tab_widget)

        if self.toolBox.currentIndex() != 0:
            self.load_tree_view(inventory)

        self.dockWidget_create_add_remove.setVisible(self.tab_widget.tabText(0) != "")
        self.load_tab()

    def load_tab(self) -> None:
        """
        It loads the data from the inventory file and displays it in the GUI

        Returns:
          The return value is a list of QWidget objects.
        """
        tab_index: int = self.tab_widget.currentIndex()
        self.category = self.tab_widget.tabText(tab_index)
        self.inventory_prices_objects.clear()
        self.po_buttons.clear()
        self.item_layouts.clear()
        self.group_layouts.clear()
        # self.tab_widget.currentChanged.connect(self.load_tab)
        # self.tab_widget.tabBarDoubleClicked.connect(self.rename_category)
        self.pushButton_create_new.setEnabled(True)
        self.radioButton_category.setEnabled(True)
        self.radioButton_single.setEnabled(True)
        try:
            self.clear_layout(self.tabs[tab_index])
        except IndexError:
            return
        settings_file.add_item("last_category_tab", tab_index)
        tab: QVBoxLayout = self.tabs[tab_index]
        category_data = inventory.get_value(item_name=self.category)
        autofill_search_options = self.get_all_part_names() + self.get_all_part_numbers()
        completer = QCompleter(autofill_search_options)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.lineEdit_search_items.setCompleter(completer)

        self.update_list_widget()
        self.label_category_name.setText(f"Category: {self.category}")
        round_number = lambda x, n: eval(
            '"%.'
            + str(int(n))
            + 'f" % '
            + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
        )
        self.label_total_unit_cost.setText(
            f"Total Unit Cost: ${round_number(inventory.get_total_unit_cost(self.category, self.get_exchange_rate()),2)}"
        )
        try:
            self.label_units_possible.setText(
                f"Total Units Possible ≈ {inventory.get_exact_total_unit_count(self.category)} to {round_number(inventory.get_total_count(self.category, 'current_quantity')/inventory.get_total_count(self.category, 'unit_quantity'),2)}"
            )
        except ZeroDivisionError:
            self.label_units_possible.setText("Total Units Possible: 0")
        self.quantities_change()

        try:
            if not list(category_data.keys()):
                self.pushButton_create_new.setEnabled(True)
                self.pushButton_add_quantity.setEnabled(False)
                self.pushButton_remove_quantity.setEnabled(False)
                self.radioButton_category.setEnabled(False)
                self.radioButton_single.setEnabled(False)
                # QApplication.restoreOverrideCursor()
                return
        except AttributeError:
            self.set_layout_message(
                "You need to", "create", "a category", 120, self.create_new_category
            )
        # self.load_item(tab, tab_index, category_data)
        self._row_index: int = 0
        try:
            self._iter = iter(range(len(list(category_data.keys()))))
        except AttributeError:
            self.set_layout_message(
                "You need to", "create", "a category", 120, self.create_new_category
            )
            self.pushButton_create_new.setEnabled(False)
            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(False)
            self.radioButton_category.setEnabled(False)
            self.radioButton_single.setEnabled(False)
            # QApplication.restoreOverrideCursor()
            return
        self._timer = QTimer(
            interval=0, timeout=partial(self.load_item, tab, tab_index, category_data)
        )
        self._timer.start()
        # QApplication.setOverrideCursor(Qt.BusyCursor)

    def load_item(self, tab: QVBoxLayout, tab_index: int, category_data: dict) -> None:
        """
        It creates a bunch of widgets and adds them to a layout.

        Args:
          tab (QVBoxLayout): QVBoxLayout
          tab_index (int): int = 0
          category_data (dict): dict = {

        Returns:
          A list of all the items in the inventory.
        """
        MINIMUM_WIDTH: int = 170
        try:
            row_index = next(self._iter)
            # QApplication.setOverrideCursor(Qt.BusyCursor)
        except StopIteration:
            self._timer.stop()
            set_status_button_stylesheet(button=self.status_button, color="#3daee9")
            self.load_item_context_menu()
            # QApplication.restoreOverrideCursor()
        else:
            __start: float = (row_index + 1) / len(list(category_data.keys()))
            __middle: float = __start + 0.001 if __start <= 1 - 0.001 else 1.0
            __end: float = __start + 0.0011 if __start <= 1 - 0.0011 else 1.0
            self.status_button.setStyleSheet(
                """QPushButton#status_button {background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,stop:%(start)s #3daee9,stop:%(middle)s #3daee9,stop:%(end)s #222222)}"""
                % {"start": str(__start), "middle": str(__middle), "end": str(__end)}
            )
            item = list(category_data.keys())[row_index]

            part_number: str = self.get_value_from_category(
                item_name=item, key="part_number"
            )
            group = self.get_value_from_category(item_name=item, key="group")

            if group:
                try:
                    layout = self.group_layouts[group]
                except KeyError:
                    group_box = QGroupBox()
                    group_box.setObjectName("group")
                    group_box.setTitle(group)
                    group_layout = QVBoxLayout()
                    group_layout.setAlignment(Qt.AlignTop)
                    self.group_layouts[group] = group_layout
                    group_box.setLayout(group_layout)
                    tab.addWidget(group_box)
            else:
                # Might appear that this does nothing, your wrong.
                self.group_layouts["__main__"] = tab

            layout = QHBoxLayout()
            # Checking if the item is in the inventory.
            if (
                self.get_value_from_category(item_name=item, key="current_quantity")
                is None
            ):
                return

            self.item_layouts.append(layout)
            current_quantity: int = int(
                self.get_value_from_category(item_name=item, key="current_quantity")
            )
            unit_quantity: int = int(
                self.get_value_from_category(item_name=item, key="unit_quantity")
            )
            priority: int = self.get_value_from_category(item_name=item, key="priority")
            price: float = self.get_value_from_category(item_name=item, key="price")
            notes: str = self.get_value_from_category(item_name=item, key="notes")
            use_exchange_rate: bool = self.get_value_from_category(
                item_name=item, key="use_exchange_rate"
            )
            exchange_rate: float = self.get_exchange_rate() if use_exchange_rate else 1
            total_cost_in_stock: float = current_quantity * price * exchange_rate
            total_unit_cost: float = unit_quantity * price * exchange_rate
            latest_change_part_number: str = self.get_value_from_category(
                item_name=item, key="latest_change_part_number"
            )
            latest_change_unit_quantity: str = self.get_value_from_category(
                item_name=item, key="latest_change_unit_quantity"
            )
            latest_change_current_quantity: str = self.get_value_from_category(
                item_name=item, key="latest_change_current_quantity"
            )
            latest_change_price: str = self.get_value_from_category(
                item_name=item, key="latest_change_price"
            )
            latest_change_use_exchange_rate: str = self.get_value_from_category(
                item_name=item, key="latest_change_use_exchange_rate"
            )
            latest_change_priority: str = self.get_value_from_category(
                item_name=item, key="latest_change_priority"
            )
            latest_change_notes: str = self.get_value_from_category(
                item_name=item, key="latest_change_notes"
            )
            latest_change_name: str = self.get_value_from_category(
                item_name=item, key="latest_change_name"
            )

            col_index: int = 0

            # PART NAME
            item_name = ItemNameComboBox(
                parent=self,
                selected_item=item,
                items=self.get_all_part_names(),
                tool_tip=latest_change_name,
            )
            item_name.setContextMenuPolicy(Qt.CustomContextMenu)
            item_name.currentTextChanged.connect(
                partial(
                    self.name_change,
                    self.category,
                    item_name.currentText(),
                    item_name,
                )
            )
            layout.addWidget(item_name)

            col_index += 1

            # PART NUMBER
            line_edit_part_number = PartNumberComboBox(
                parent=self,
                selected_item=part_number,
                items=self.get_all_part_numbers(),
                tool_tip=latest_change_part_number,
            )
            line_edit_part_number.currentTextChanged.connect(
                partial(
                    self.part_number_change,
                    self.category,
                    item_name,
                    "part_number",
                    line_edit_part_number,
                )
            )
            layout.addWidget(line_edit_part_number)

            col_index += 1

            # UNIT QUANTITY
            spin_unit_quantity = HumbleSpinBox(self)
            spin_unit_quantity.setToolTip(latest_change_unit_quantity)
            spin_unit_quantity.setValue(unit_quantity)
            spin_unit_quantity.valueChanged.connect(
                partial(
                    self.unit_quantity_change,
                    self.category,
                    item_name,
                    "unit_quantity",
                    spin_unit_quantity,
                )
            )
            layout.addWidget(spin_unit_quantity)

            col_index += 1

            # ITEM QUANTITY
            spin_current_quantity = HumbleSpinBox(self)
            spin_current_quantity.setToolTip(latest_change_current_quantity)
            spin_current_quantity.setValue(current_quantity)
            if current_quantity <= 10:
                quantity_color = "red"
            elif current_quantity <= 20:
                quantity_color = "yellow"

            if current_quantity > 20:
                spin_current_quantity.setStyleSheet("")
            else:
                spin_current_quantity.setStyleSheet(
                    f"color: {quantity_color}; border-color: {quantity_color};"
                )
            spin_current_quantity.valueChanged.connect(
                partial(
                    self.current_quantity_change,
                    self.category,
                    item_name,
                    "current_quantity",
                    spin_current_quantity,
                )
            )
            layout.addWidget(spin_current_quantity)

            col_index += 1

            # PRICE
            spin_price = HumbleDoubleSpinBox(self)
            spin_price.setToolTip(latest_change_price)
            spin_price.setValue(price)
            spin_price.setSuffix(" USD" if use_exchange_rate else " CAD")
            spin_price.valueChanged.connect(
                partial(self.price_change, self.category, item_name, "price", spin_price)
            )
            layout.addWidget(spin_price)

            col_index += 1

            # EXCHANGE RATE
            combo_exchange_rate = ExchangeRateComboBox(
                parent=self,
                selected_item="USD" if use_exchange_rate else "CAD",
                tool_tip=latest_change_use_exchange_rate,
            )
            combo_exchange_rate.currentIndexChanged.connect(
                partial(
                    self.use_exchange_rate_change,
                    self.category,
                    item_name,
                    "use_exchange_rate",
                    combo_exchange_rate,
                )
            )
            layout.addWidget(combo_exchange_rate)

            col_index += 1

            # TOTAL COST
            spin_total_cost = CostLineEdit(
                parent=self,
                prefix="$",
                text=total_cost_in_stock,
                suffix=combo_exchange_rate.currentText(),
            )
            layout.addWidget(spin_total_cost)

            col_index += 1

            # TOTALE UNIT COST
            spin_total_unit_cost = CostLineEdit(
                parent=self,
                prefix="$",
                text=total_unit_cost,
                suffix=combo_exchange_rate.currentText(),
            )
            layout.addWidget(spin_total_unit_cost)

            self.inventory_prices_objects[item_name] = {
                "current_quantity": spin_current_quantity,
                "unit_quantity": spin_unit_quantity,
                "price": spin_price,
                "use_exchange_rate": combo_exchange_rate,
                "total_cost": spin_total_cost,
                "total_unit_cost": spin_total_unit_cost,
            }

            col_index += 1

            # PRIORITY
            combo_priority = PriorityComboBox(
                parent=self, selected_item=priority, tool_tip=latest_change_priority
            )
            if combo_priority.currentText() == "Medium":
                combo_priority.setStyleSheet("color: yellow; border-color: yellow;")
            elif combo_priority.currentText() == "High":
                combo_priority.setStyleSheet("color: red; border-color: red;")
            combo_priority.currentIndexChanged.connect(
                partial(
                    self.priority_change,
                    self.category,
                    item_name,
                    "priority",
                    combo_priority,
                )
            )
            layout.addWidget(combo_priority)

            col_index += 1

            # NOTES
            text_notes = NotesPlainTextEdit(
                parent=self, text=notes, tool_tip=latest_change_notes
            )
            text_notes.textChanged.connect(
                partial(self.notes_changed, self.category, item_name, "notes", text_notes)
            )
            layout.addWidget(text_notes)

            col_index += 1

            # PURCHASE ORDER
            po_menu = QMenu(self)
            for po in get_all_po():
                po_menu.addAction(po, partial(self.open_po, po))
            btn_po = POPushButton(parent=self)
            btn_po.setMenu(po_menu)
            layout.addWidget(btn_po)
            self.po_buttons.append(btn_po)

            col_index += 1

            # DELETE
            btn_delete = DeletePushButton(
                parent=self,
                tool_tip=f"Delete {item_name.currentText()} permanently from {self.category}",
                icon=QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/trash.png"),
            )
            btn_delete.clicked.connect(
                partial(self.delete_item, self.category, item_name)
            )
            layout.addWidget(btn_delete)

            try:
                self.group_layouts[group].addLayout(layout)
            except KeyError:
                tab.addLayout(layout)
            # QApplication.restoreOverrideCursor()

    def update_list_widget(self) -> None:
        """
        It takes the text from a lineEdit widget and searches for it in a dictionary. If the text is
        found, it adds the key to a listWidget

        Returns:
          the value of the item_name key in the category_data dictionary.
        """
        search_input: str = self.lineEdit_search_items.text()
        category_data = inventory.get_value(item_name=self.category)
        self.listWidget_itemnames.clear()
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        try:
            for item in list(category_data.keys()):
                if (
                    search_input.lower() in item.lower()
                    or search_input.lower() in category_data[item]["part_number"].lower()
                ):
                    self.listWidget_itemnames.addItem(item)
        except AttributeError:
            return

    def update_stock_costs(self) -> None:
        """
        It takes the current quantity of an item, multiplies it by the price of the item, and then
        multiplies that by the exchange rate
        """
        for item_name in list(self.inventory_prices_objects.keys()):
            spin_current_quantity = self.inventory_prices_objects[item_name][
                "current_quantity"
            ]
            spin_unit_quantity = self.inventory_prices_objects[item_name]["unit_quantity"]
            spin_price = self.inventory_prices_objects[item_name]["price"]
            combo_exchange_rate = self.inventory_prices_objects[item_name][
                "use_exchange_rate"
            ]
            spin_price.setSuffix(f" {combo_exchange_rate.currentText()}")
            spin_total_cost = self.inventory_prices_objects[item_name]["total_cost"]
            spin_total_unit_cost = self.inventory_prices_objects[item_name][
                "total_unit_cost"
            ]
            use_exchange_rate: bool = combo_exchange_rate.currentText() == "USD"
            exchange_rate: float = self.get_exchange_rate() if use_exchange_rate else 1
            round_number = lambda x, n: eval(
                '"%.'
                + str(int(n))
                + 'f" % '
                + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
            )
            spin_total_cost.setText(
                f"${round_number(spin_current_quantity.value() * spin_price.value() * exchange_rate, 2)} {combo_exchange_rate.currentText()}"
            )

            spin_total_unit_cost.setText(
                f"${round_number(spin_unit_quantity.value() * spin_price.value() * exchange_rate, 2)} {combo_exchange_rate.currentText()}"
            )

    def create_new_category(self, event=None) -> None:
        """
        It creates a new category

        Args:
          event: The event that triggered the function.

        Returns:
          The return value of the function is None.
        """
        input_dialog = InputDialog(
            title="Create category", message="Enter a name for a new category."
        )

        if input_dialog.exec_():
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
                inventory.add_item(item_name=input_text, value={})
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

        if select_item_dialog.exec_():
            response = select_item_dialog.get_response()
            if response == DialogButtons.discard:
                try:
                    inventory.remove_item(select_item_dialog.get_selected_item())
                except AttributeError:
                    return
                settings_file.add_item(item_name="last_category_tab", value=0)
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

        if select_item_dialog.exec_():
            response = select_item_dialog.get_response()
            if response == DialogButtons.clone:
                try:
                    for category in self.categories:
                        if (
                            f"Clone from: {select_item_dialog.get_selected_item()} Double click me rename me"
                            == category
                        ):
                            self.show_error_dialog(
                                "Invalid name",
                                f"'Clone from: {select_item_dialog.get_selected_item()} Double click me rename me'\nalready exists.\n\nCan't be the same as other names.",
                                dialog_buttons=DialogButtons.ok,
                            )
                            return
                    inventory.clone_key(select_item_dialog.get_selected_item())
                except AttributeError:
                    return
                self.load_categories()
            elif response == DialogButtons.cancel:
                return

    def rename_category(self, index):
        """
        It takes the index of the tab that was clicked, opens a dialog box, and if the user clicks ok,
        it renames the tab.

        Args:
          index: The index of the tab that was clicked.

        Returns:
          The return value of the function is the return value of the last expression evaluated, or None
        if no expression was evaluated.
        """
        if self.tab_widget.tabText(0) == "":
            return
        input_dialog = InputDialog(
            title="Rename category", message=f"Enter a new name for '{self.category}'."
        )

        if input_dialog.exec_():
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
                inventory.change_key_name(
                    key_name=self.tab_widget.tabText(index), new_name=input_text
                )
                self.load_categories()
            elif response == DialogButtons.cancel:
                return

    def open_group_menu(self, menu: QMenu) -> None:
        """
        It opens a menu at the current cursor position

        Args:
          menu (QMenu): QMenu
        """
        menu.exec_(QCursor.pos())

    def add_to_group(self, item_name: QComboBox, group: str) -> None:
        """
        It takes the name of a QComboBox and a string, and if the string is "Create", it opens a dialog
        box to create a new group, and if the string is not "Create", it changes the group of the item
        in the QComboBox to the string

        Args:
          item_name (QComboBox): QComboBox
          group (str): str = The group name
        """
        if group == "Create group":
            input_dialog = InputDialog(
                title="Create group", message="Enter a name for a new group."
            )

            if input_dialog.exec_():
                response = input_dialog.get_response()
                if response == DialogButtons.ok:
                    input_text = input_dialog.inputText
                    inventory.change_object_in_object_item(
                        self.category, item_name.currentText(), "group", input_text
                    )
                    self.load_categories()
                elif response == DialogButtons.cancel:
                    return
        else:
            inventory.change_object_in_object_item(
                self.category, item_name.currentText(), "group", group
            )
            self.load_categories()

    def remove_from_group(self, item_name: QComboBox, group: str) -> None:
        """
        It removes an item from a group

        Args:
          item_name (QComboBox): QComboBox
          group (str): str = The group name
        """
        inventory.change_object_in_object_item(
            self.category, item_name.currentText(), "group", None
        )
        self.load_categories()

    def load_item_context_menu(self) -> None:
        """
        It creates a context menu for each item in the inventory
        """
        for item_name in list(self.inventory_prices_objects.keys()):
            group = self.get_value_from_category(
                item_name=item_name.currentText(), key="group"
            )
            menu = QMenu(self)
            groups = QMenu(menu)
            groups.setTitle("Move to group")
            for i, group_name in enumerate(["Create group"] + self.get_all_groups()):
                if group == group_name or group_name == "__main__":
                    continue
                if i == 1:
                    groups.addSeparator()
                action = QAction(self)
                action.triggered.connect(
                    partial(self.add_to_group, item_name, group_name)
                )
                action.setText(group_name)
                groups.addAction(action)
            menu.addMenu(groups)
            remove_from_group = QAction("Remove from group", self)
            remove_from_group.triggered.connect(
                partial(self.remove_from_group, item_name, group)
            )
            menu.addAction(remove_from_group)
            item_name.customContextMenuRequested.connect(
                partial(self.open_group_menu, menu)
            )

    def name_change(self, category: str, old_name: str, name: QLineEdit) -> None:
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
        category_data = inventory.get_value(item_name=category)
        for item in list(category_data.keys()):
            if name.currentText() == item:
                self.show_error_dialog(
                    "Invalid name",
                    f"'{name.currentText()}'\nis an invalid item name.\n\nCan't be the same as other names.",
                    dialog_buttons=DialogButtons.ok,
                )
                name.setCurrentText(old_name)
                # name.selectAll()
                return

        inventory.change_object_in_object_item(
            category,
            old_name,
            "latest_change_name",
            f"Latest Change:\nfrom: \"{old_name}\"\nto: \"{name.currentText()}\"\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        name.setToolTip(
            f"Latest Change:\nfrom: \"{old_name}\"\nto: \"{name.currentText()}\"\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        inventory.change_item_name(category, old_name, name.currentText())
        name.disconnect()
        name.currentTextChanged.connect(
            partial(self.name_change, category, name.currentText(), name)
        )
        self.update_list_widget()

    def part_number_change(
        self, category: str, item_name: QComboBox, value_name: str, part_number: QLineEdit
    ) -> None:
        """
        It takes a category, item name, value name, and quantity, and changes the value of the item in
        the category to the quantity

        Args:
        category (str): str - The category of the item.
        item_name (QLineEdit): QLineEdit
        value_name (str): str = The name of the value you want to change.
        quantity (QLineEdit): QLineEdit
        """
        value_before = inventory.get_value(item_name=category)[item_name.currentText()][
            "part_number"
        ]
        inventory.change_object_in_object_item(
            category,
            item_name.currentText(),
            "latest_change_part_number",
            f"Latest Change:\nfrom: {value_before}\nto: {part_number.currentText()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        part_number.setToolTip(
            f"Latest Change:\nfrom: {value_before}\nto: {part_number.currentText()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        self.value_change(
            category, item_name.currentText(), value_name, part_number.currentText()
        )

    def current_quantity_change(
        self, category: str, item_name: QComboBox, value_name: str, quantity: QSpinBox
    ) -> None:
        """
        It takes a category, item name, value name, and quantity, and changes the value of the item in
        the category to the quantity

        Args:
        category (str): str - The category of the item.
        item_name (QLineEdit): QLineEdit
        value_name (str): str = The name of the value you want to change.
        quantity (QSpinBox): QSpinBox
        """
        data = inventory.get_data()
        value_before = inventory.get_value(item_name=category)[item_name.currentText()][
            "current_quantity"
        ]
        part_number: str = data[self.category][item_name.currentText()]["part_number"]
        inventory.change_object_in_object_item(
            category,
            item_name.currentText(),
            "latest_change_current_quantity",
            f"Latest Change:\nfrom: {value_before}\nto: {quantity.value()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        quantity.setToolTip(
            f"Latest Change:\nfrom: {value_before}\nto: {quantity.value()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        self.value_change(category, item_name.currentText(), value_name, quantity.value())
        for category in list(data.keys()):
            if category == self.category:
                continue
            for item in list(data[category].keys()):
                if part_number == data[category][item]["part_number"]:
                    data[category][item]["current_quantity"] = quantity.value()
                    data[category][item][
                        "latest_change_current_quantity"
                    ] = f"Latest Change:\nfrom: {value_before}\nto: {quantity.value()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
        inventory.save_data(data)
        inventory.load_data()
        if quantity.value() <= 10:
            quantity_color = "red"
        elif quantity.value() <= 20:
            quantity_color = "yellow"

        if quantity.value() > 20:
            quantity.setStyleSheet("")
        else:
            quantity.setStyleSheet(
                f"color: {quantity_color}; border-color: {quantity_color};"
            )
        self.update_stock_costs()

    def unit_quantity_change(
        self, category: str, item_name: QComboBox, value_name: str, quantity: QSpinBox
    ) -> None:
        """
        It takes a category, item name, value name, and quantity, and changes the value of the item in
        the category to the quantity

        Args:
          category (str): str - The category of the item.
          item_name (QLineEdit): QLineEdit
          value_name (str): str = The name of the value you want to change.
          quantity (QSpinBox): QSpinBox
        """
        value_before = inventory.get_value(item_name=category)[item_name.currentText()][
            "unit_quantity"
        ]
        inventory.change_object_in_object_item(
            category,
            item_name.currentText(),
            "latest_change_unit_quantity",
            f"Latest Change:\nfrom: {value_before}\nto: {quantity.value()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        quantity.setToolTip(
            f"Latest Change:\nfrom: {value_before}\nto: {quantity.value()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        self.value_change(category, item_name.currentText(), value_name, quantity.value())
        self.update_stock_costs()

    def price_change(
        self, category: str, item_name: QComboBox, value_name: str, price: QDoubleSpinBox
    ) -> None:
        """
        It takes a category, item name, value name, and price, and then calls the value_change function
        with the same arguments

        Args:
          category (str): str - The category of the item.
          item_name (QLineEdit): QLineEdit
          value_name (str): str = The name of the value you want to change.
          price (QDoubleSpinBox): QDoubleSpinBox
        """

        data = inventory.get_data()
        part_number: str = data[self.category][item_name.currentText()]["part_number"]
        value_before = inventory.get_value(item_name=category)[item_name.currentText()][
            "price"
        ]
        inventory.change_object_in_object_item(
            category,
            item_name.currentText(),
            "latest_change_price",
            f"Latest Change:\nfrom: {value_before}\nto: {price.value()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        price.setToolTip(
            f"Latest Change:\nfrom: {value_before}\nto: {price.value()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        self.value_change(category, item_name.currentText(), value_name, price.value())
        for category in list(data.keys()):
            if category == self.category:
                continue
            for item in list(data[category].keys()):
                if part_number == data[category][item]["part_number"]:
                    current_price: int = data[category][item]["price"]
                    data[category][item]["price"] = price.value()
                    data[category][item][
                        "latest_change_price"
                    ] = f"Latest Change:\nfrom: {current_price}\nto: {price.value()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}"
        inventory.save_data(data)
        inventory.load_data()
        self.update_stock_costs()
        round_number = lambda x, n: eval(
            '"%.'
            + str(int(n))
            + 'f" % '
            + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
        )
        self.label_total_unit_cost.setText(
            f"Total Unit Cost: ${round_number(inventory.get_total_unit_cost(self.category, self.get_exchange_rate()),2)}"
        )

    def use_exchange_rate_change(
        self, category: str, item_name: QComboBox, value_name: str, combo: QComboBox
    ) -> None:
        """
        It changes the exchange rate

        Args:
          category (str): str - The category of the item
          item_name (QLineEdit): QLineEdit
          value_name (str): str = The name of the value to change
          combo (QComboBox): QComboBox
        """
        value_before = inventory.get_value(item_name=category)[item_name.currentText()][
            "use_exchange_rate"
        ]
        usd = combo.currentText() == "USD"
        inventory.change_object_in_object_item(
            category,
            item_name.currentText(),
            "latest_change_use_exchange_rate",
            f"Latest Change:\nfrom: {'USD' if value_before else 'CAD'}\nto: {combo.currentText()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        combo.setToolTip(
            f"Latest Change:\nfrom: {'USD' if value_before else 'CAD'}\nto: {combo.currentText()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )

        self.value_change(
            category,
            item_name.currentText(),
            value_name,
            usd,
        )
        self.update_stock_costs()

    def priority_change(
        self, category: str, item_name: QComboBox, value_name: str, combo: QComboBox
    ) -> None:
        """
        It changes the priority of a task

        Args:
          category (str): str - The category of the item
          item_name (QLineEdit): QLineEdit
          value_name (str): str = The name of the value to change
          combo (QComboBox): QComboBox
        """

        value_before = inventory.get_value(item_name=category)[item_name.currentText()][
            "priority"
        ]
        inventory.change_object_in_object_item(
            category,
            item_name.currentText(),
            "latest_change_priority",
            f"Latest Change:\nfrom: {value_before}\nto: {combo.currentIndex()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        combo.setToolTip(
            f"Latest Change:\nfrom: {value_before}\nto: {combo.currentIndex()}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )

        self.value_change(
            category, item_name.currentText(), value_name, combo.currentIndex()
        )
        if combo.currentText() == "Medium":
            combo.setStyleSheet("color: yellow; border-color: yellow;")
        elif combo.currentText() == "High":
            combo.setStyleSheet("color: red; border-color: red")
        else:
            combo.setStyleSheet("")

    def notes_changed(
        self, category: str, item_name: QComboBox, value_name: str, note: QPlainTextEdit
    ) -> None:
        """
        It takes the category, item name, value name, and note as parameters and then calls the
        value_change function with the category, item name, value name, and note as parameters

        Args:
          category (str): str = The category of the item.
          item_name (QLineEdit): QLineEdit
          value_name (str): str = The name of the value that is being changed.
          note (QPlainTextEdit): QPlainTextEdit
        """
        value_before = inventory.get_value(item_name=category)[item_name.currentText()][
            "notes"
        ]
        inventory.change_object_in_object_item(
            category,
            item_name.currentText(),
            "latest_change_notes",
            f"Latest Change:\nfrom: \"{value_before}\"\nto: \"{note.toPlainText()}\"\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        note.setToolTip(
            f"Latest Change:\nfrom: \"{value_before}\"\nto: \"{note.toPlainText()}\"\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
        )
        self.value_change(
            category, item_name.currentText(), value_name, note.toPlainText()
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

        if add_item_dialog.exec_():
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
                unit_quantity: int = add_item_dialog.get_unit_quantity()
                current_quantity: int = add_item_dialog.get_current_quantity()
                price: float = add_item_dialog.get_item_price()
                notes: str = add_item_dialog.get_notes()
                part_number: str = add_item_dialog.get_part_number()
                use_exchange_rate: bool = add_item_dialog.get_exchange_rate()
                group: str = add_item_dialog.get_group()

                try:
                    inventory.add_item_in_object(self.category, name)
                    inventory.change_object_in_object_item(
                        self.category, name, "part_number", part_number
                    )
                except KeyError:
                    self.show_error_dialog(
                        "Invalid characters",
                        f"'{name}'\nis an invalid item name.",
                        dialog_buttons=DialogButtons.ok,
                    )
                    return
                inventory.change_object_in_object_item(
                    self.category, name, "unit_quantity", unit_quantity
                )
                inventory.change_object_in_object_item(
                    self.category, name, "current_quantity", current_quantity
                )
                inventory.change_object_in_object_item(
                    self.category, name, "price", price
                )
                inventory.change_object_in_object_item(
                    self.category, name, "use_exchange_rate", use_exchange_rate
                )
                inventory.change_object_in_object_item(
                    self.category, name, "priority", priority
                )
                inventory.change_object_in_object_item(
                    self.category, name, "notes", notes
                )
                if group != "None":
                    inventory.change_object_in_object_item(
                        self.category, name, "group", group
                    )
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
                self.load_tab()
            elif response == DialogButtons.cancel:
                return

    def delete_item(self, category: str, item_name: QComboBox) -> None:
        """
        It removes an item from the inventory

        Args:
          category (str): str
          item_name (QLineEdit): QLineEdit
        """
        inventory.remove_object_item(category, item_name.currentText())
        self.load_tab()

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
            # self.listWidget_itemnames.setStyleSheet(
            #     "QAbstractItemView::item{color: grey}"
            # )

            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(True)

            # self.pushButton_add_quantity.disconnect()
            self.pushButton_remove_quantity.disconnect()

            self.pushButton_remove_quantity.clicked.connect(
                self.remove_quantity_from_category
            )
            self.spinBox_quantity.setValue(0)
        else:
            self.pushButton_remove_quantity.setEnabled(False)
            # self.listWidget_itemnames.clearSelection()
            # self.listWidget_item_changed()
            # self.listWidget_itemnames.setEnabled(True)
            # self.listWidget_itemnames.setStyleSheet(
            #     "QAbstractItemView::item{color: white}"
            # )
            self.label.setText("Quantity:")
            self.pushButton_add_quantity.setText("Add Quantity")
            self.pushButton_remove_quantity.setText("Remove Quantity")
            settings_file.add_item(item_name="change_quantities_by", value="Item")
            self.pushButton_add_quantity.setEnabled(False)

    def remove_quantity_from_category(self) -> None:
        """
        It removes a quantity of items from a category
        """
        self.radioButton_category.setEnabled(False)
        self.radioButton_single.setEnabled(False)
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        self.pushButton_create_new.setEnabled(False)
        self.tab_widget.setEnabled(False)
        self.listWidget_itemnames.setEnabled(False)
        self.status_button.setText("This may take awhile, please wait...")
        remove_quantity_thread = RemoveQuantityThread(
            inventory,
            self.category,
            self.inventory_prices_objects,
            self.spinBox_quantity.value(),
        )
        remove_quantity_thread.signal.connect(self.remove_quantity_thread_response)
        self.threads.append(remove_quantity_thread)
        remove_quantity_thread.start()

        self.spinBox_quantity.setValue(0)

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
            self.status_button.setStyleSheet(
                """QPushButton#status_button {background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,stop:%(start)s #3daee9,stop:%(middle)s #3daee9,stop:%(end)s #222222)}"""
                % {"start": str(__start), "middle": str(__middle), "end": str(__end)}
            )
        else:
            self.radioButton_category.setEnabled(True)
            self.radioButton_single.setEnabled(True)
            self.tab_widget.setEnabled(True)
            self.listWidget_itemnames.setEnabled(True)
            self.pushButton_create_new.setEnabled(True)
            inventory.load_data()
            set_status_button_stylesheet(button=self.status_button, color="#33b833")
            self.highlight_color = "#BE2525"
            for item in list(self.inventory_prices_objects.keys()):
                spin_current_quantity = self.inventory_prices_objects[item][
                    "current_quantity"
                ]
                spin_current_quantity.setStyleSheet(
                    f"background-color: {self.highlight_color}; {'color: red; border-color: red;' if spin_current_quantity.value() <= 0 else 'color: white;'} border: 1px solid {self.highlight_color};"
                )
            self.status_button.setText("Done!")

            round_number = lambda x, n: eval(
                '"%.'
                + str(int(n))
                + 'f" % '
                + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
            )

            try:
                self.label_units_possible.setText(
                    f"Total Units Possible ≈ {inventory.get_exact_total_unit_count(self.category)} to {round_number(inventory.get_total_count(self.category, 'current_quantity')/inventory.get_total_count(self.category, 'unit_quantity'),2)}"
                )
            except ZeroDivisionError:
                self.label_units_possible.setText("Total Units Possible: 0")
            self.highlight_color = "#3daee9"
            QtTest.QTest.qWait(1750)
            for item in list(self.inventory_prices_objects.keys()):
                spin_current_quantity = self.inventory_prices_objects[item][
                    "current_quantity"
                ]
                self.inventory_prices_objects[item]["current_quantity"].setStyleSheet(
                    f"{'color: red; border-color: red;' if spin_current_quantity.value() <= 0 else ''}"
                )
            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(True)

    def add_quantity(self, item_name: str, old_quantity: int) -> None:
        """
        It adds the value of the spinbox to the quantity of the item selected in the listwidget

        Args:
          item_name (str): str = the name of the item
          old_quantity (int): int = the quantity of the item before the change
        """
        self.highlight_color = "#33b833"
        data = inventory.get_data()
        part_number: str = data[self.category][item_name]["part_number"]
        current_quantity: int = data[self.category][item_name]["current_quantity"]
        for object_item in list(self.inventory_prices_objects.keys()):
            if object_item.currentText() == item_name:
                self.inventory_prices_objects[object_item][
                    "current_quantity"
                ].disconnect()
                self.inventory_prices_objects[object_item]["current_quantity"].setValue(
                    int(current_quantity + self.spinBox_quantity.value())
                )
                self.value_change(
                    self.category,
                    item_name,
                    "current_quantity",
                    current_quantity + self.spinBox_quantity.value(),
                )
                self.inventory_prices_objects[object_item][
                    "current_quantity"
                ].valueChanged.connect(
                    partial(
                        self.current_quantity_change,
                        self.category,
                        item_name,
                        "current_quantity",
                        self.inventory_prices_objects[object_item]["current_quantity"],
                    )
                )

        for category in list(data.keys()):
            if category == self.category:
                continue
            for item in data[category].keys():
                if part_number == data[category][item]["part_number"]:
                    current_quantity: int = data[category][item]["current_quantity"]
                    self.value_change(
                        category=category,
                        item_name=item,
                        value_name="current_quantity",
                        new_value=current_quantity + self.spinBox_quantity.value(),
                    )
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        # self.load_tab()
        self.listWidget_itemnames.setCurrentRow(self.last_item_selected_index)
        self.listWidget_item_changed()

    def remove_quantity(self, item_name: str, old_quantity: int) -> None:
        """
        It removes the quantity of an item from the inventory

        Args:
          item_name (str): str = the name of the item
          old_quantity (int): int = the quantity of the item before the change
        """
        self.highlight_color = "#BE2525"
        data = inventory.get_data()
        part_number: str = data[self.category][item_name]["part_number"]
        current_quantity: int = data[self.category][item_name]["current_quantity"]
        for object_item in list(self.inventory_prices_objects.keys()):
            if object_item.currentText() == item_name:
                self.inventory_prices_objects[object_item][
                    "current_quantity"
                ].disconnect()
                self.inventory_prices_objects[object_item]["current_quantity"].setValue(
                    int(current_quantity - self.spinBox_quantity.value())
                )
                self.value_change(
                    self.category,
                    item_name,
                    "current_quantity",
                    current_quantity - self.spinBox_quantity.value(),
                )
                self.inventory_prices_objects[object_item][
                    "current_quantity"
                ].valueChanged.connect(
                    partial(
                        self.current_quantity_change,
                        self.category,
                        item_name,
                        "current_quantity",
                        self.inventory_prices_objects[object_item]["current_quantity"],
                    )
                )
        for category in list(data.keys()):
            if category == self.category:
                continue
            for item in data[category].keys():
                if part_number == data[category][item]["part_number"]:
                    current_quantity: int = data[category][item]["current_quantity"]
                    self.value_change(
                        category=category,
                        item_name=item,
                        value_name="current_quantity",
                        new_value=current_quantity - self.spinBox_quantity.value(),
                    )
        print(data[self.category][item_name]["current_quantity"])
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        # self.load_tab()
        self.listWidget_itemnames.setCurrentRow(self.last_item_selected_index)
        self.listWidget_item_changed()

    def listWidget_item_changed(self) -> None:
        """
        It's a function that changes the color of a QComboBox and QDoubleSpinBox when the user clicks on
        an item in a QListWidget.
        """

        tab_index: int = self.tab_widget.currentIndex()
        scroll_area: QVBoxLayout = self.scroll_areas[tab_index]

        try:
            selected_item: str = self.listWidget_itemnames.currentItem().text()
        except AttributeError:
            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(False)
            return
        category_data = inventory.get_value(item_name=self.category)
        try:
            quantity: int = category_data[selected_item]["current_quantity"]
            item_name: QComboBox = list(self.inventory_prices_objects.keys())[
                self.last_item_selected_index
            ]
            current_quantity: QDoubleSpinBox = self.inventory_prices_objects[item_name][
                "current_quantity"
            ]
        except (KeyError, IndexError):
            return
        item_name.setStyleSheet(f"")

        if current_quantity.value() <= 10:
            quantity_color = "red"
        elif current_quantity.value() <= 20:
            quantity_color = "yellow"

        if current_quantity.value() > 20:
            current_quantity.setStyleSheet("")
        else:
            current_quantity.setStyleSheet(
                f"color: {quantity_color}; border-color: {quantity_color};"
            )

        # self.last_item_selected_index = self.listWidget_itemnames.currentRow()
        try:
            self.last_item_selected_index = [
                item.currentText() for item in list(self.inventory_prices_objects.keys())
            ].index(self.listWidget_itemnames.currentItem().text())
        except ValueError:
            return

        item_name: QComboBox = list(self.inventory_prices_objects.keys())[
            self.last_item_selected_index
        ]
        current_quantity: QDoubleSpinBox = self.inventory_prices_objects[item_name][
            "current_quantity"
        ]
        scroll_area.verticalScrollBar().setValue(item_name.pos().y())
        if self.highlight_color == "#3daee9":
            item_name.setStyleSheet(
                f"background-color: {self.highlight_color}; border: 1px solid {self.highlight_color};"
            )
            if current_quantity.value() <= 10:
                quantity_color = "red"
            elif current_quantity.value() <= 20:
                quantity_color = "yellow"

            if current_quantity.value() > 20:
                current_quantity.setStyleSheet("")
            else:
                current_quantity.setStyleSheet(
                    f"color: {quantity_color}; border-color: {quantity_color};"
                )
        else:
            if current_quantity.value() <= 10:
                quantity_color = "red"
            elif current_quantity.value() <= 20:
                quantity_color = "yellow"

            current_quantity.setStyleSheet(
                f"background-color: {self.highlight_color}; border: 1px solid {self.highlight_color}; {'color: {quantity_color}; border-color: {quantity_color};' if current_quantity.value() <= 20 else ''}"
            )
            self.highlight_color = "#3daee9"
        if self.radioButton_single.isChecked():
            self.pushButton_add_quantity.setEnabled(True)
            self.pushButton_remove_quantity.setEnabled(True)

            self.pushButton_add_quantity.disconnect()
            self.pushButton_remove_quantity.disconnect()

            self.pushButton_remove_quantity.clicked.connect(
                partial(self.remove_quantity, selected_item, quantity)
            )
            self.pushButton_add_quantity.clicked.connect(
                partial(self.add_quantity, selected_item, quantity)
            )
        self.spinBox_quantity.setValue(0)

    def value_change(
        self, category: str, item_name: str, value_name: str, new_value
    ) -> None:
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
        # QApplication.setOverrideCursor(Qt.BusyCursor)
        # threading.Thread(
        #     target=inventory.change_object_in_object_item,
        #     args=(category, item_name, value_name, new_value),
        # ).start()
        inventory.change_object_in_object_item(
            object_name=category,
            item_name=item_name,
            value_name=value_name,
            new_value=new_value,
        )
        if value_name == "current_quantity":
            value_before = inventory.get_value(item_name=category)[item_name][
                "current_quantity"
            ]
            # threading.Thread(
            #     target=inventory.change_object_in_object_item,
            #     args=(
            #         category,
            #         item_name,
            #         "latest_change_current_quantity",
            #         f"Latest Change:\nfrom: {value_before}\nto: {new_value}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
            #     ),
            # ).start()
            inventory.change_object_in_object_item(
                category,
                item_name,
                "latest_change_current_quantity",
                f"Latest Change:\nfrom: {value_before}\nto: {new_value}\n{self.username}\n{datetime.now().strftime('%B %d %A %Y %I:%M:%S %p')}",
            )
        # QApplication.restoreOverrideCursor()
        self.pushButton_add_quantity.setEnabled(add_quantity_state)
        self.pushButton_remove_quantity.setEnabled(remove_quantity_state)

        round_number = lambda x, n: eval(
            '"%.'
            + str(int(n))
            + 'f" % '
            + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
        )
        try:
            self.label_units_possible.setText(
                f"Total Units Possible ≈ {inventory.get_exact_total_unit_count(self.category)} to {round_number(inventory.get_total_count(self.category, 'current_quantity')/inventory.get_total_count(self.category, 'unit_quantity'),2)}"
            )
        except ZeroDivisionError:
            self.label_units_possible.setText("Total Units Possible: 0")

    def toggle_auto_back_up_to_cloud(self) -> None:
        """
        It adds an item to a settings file
        """
        settings_file.add_item(
            item_name="auto_backup_to_cloud",
            value=self.actionAuto_back_up_to_cloud.isChecked(),
        )

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
            if actions[0].isChecked() and settings_file.get_value(
                item_name="sort_descending"
            ):
                actions[1].setChecked(False)
                actions[0].setEnabled(False)
                actions[1].setEnabled(True)
            if actions[1].isChecked() and settings_file.get_value(
                item_name="sort_ascending"
            ):
                actions[0].setChecked(False)
                actions[1].setEnabled(False)
                actions[0].setEnabled(True)
        elif group_name == "sorting":
            if actions[0].isChecked() and (  # Quantity in Stock
                settings_file.get_value(item_name="sort_priority")
                or settings_file.get_value(item_name="sort_alphabatical")
            ):
                actions[1].setChecked(False)
                actions[2].setChecked(False)
                actions[0].setEnabled(False)
                actions[1].setEnabled(True)
                actions[2].setEnabled(True)
            elif actions[1].isChecked() and (  # Priority
                settings_file.get_value(item_name="sort_quantity_in_stock")
                or settings_file.get_value(item_name="sort_alphabatical")
            ):
                actions[0].setChecked(False)
                actions[2].setChecked(False)
                actions[0].setEnabled(True)
                actions[1].setEnabled(False)
                actions[2].setEnabled(True)
            elif actions[2].isChecked() and (  # Alphabatical
                settings_file.get_value(item_name="sort_priority")
                or settings_file.get_value(item_name="sort_quantity_in_stock")
            ):
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

        inventory.sort(
            self.category, sorting_method, not self.actionAscending.isChecked()
        )
        self.load_tab()

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
                part_numbers.extend(
                    data[category][item]["part_number"]
                    for item in list(data[category].keys())
                )
            except KeyError:
                continue
        part_numbers = list(set(part_numbers))
        return part_numbers

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

    def get_all_groups(self) -> list[str]:
        """
        This function returns a list of all the groups in the layout

        Returns:
          A list of all the keys in the group_layouts dictionary.
        """
        return list(self.group_layouts.keys())

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
            return inventory.get_data()[self.category][item_name][key]
        except KeyError:
            return "No changes yet." if "latest" in key else None

    def save_geometry(self) -> None:
        """
        It saves the geometry of the window to the settings file
        """
        geometry.set_value(item_name="x", value=max(self.pos().x(), 0))
        geometry.set_value(item_name="y", value=max(self.pos().y(), 0))
        geometry.set_value(item_name="width", value=self.size().width())
        geometry.set_value(item_name="height", value=self.size().height())

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

    def show_message_dialog(
        self, title: str, message: str, dialog_buttons: str = DialogButtons.ok
    ) -> str:
        """
        It creates a message dialog, shows it, and returns the response

        Args:
          title (str): str = The title of the dialog
          message (str): str = The message to display in the dialog
          dialog_buttons (str): str = DialogButtons.ok

        Returns:
          The response is being returned.
        """
        message_dialog = MessageDialog(
            self, Icons.information, dialog_buttons, title, message
        )
        message_dialog.show()

        response: str = ""

        if message_dialog.exec_():
            response = message_dialog.get_response()

        return response

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
        message_dialog = MessageDialog(
            self, Icons.critical, dialog_buttons, title, message
        )
        message_dialog.show()

        response: str = ""

        if message_dialog.exec_():
            response = message_dialog.get_response()

        if response == DialogButtons.copy:
            pixmap = QPixmap(self.message_dialog.grab())
            QApplication.clipboard().setPixmap(pixmap)
        elif response == DialogButtons.save:
            self.generate_error_log(message_dialog=message_dialog)
        return response

    def show_file_changes(
        self, title: str, message: str, dialog_buttons: str = DialogButtons.ok
    ) -> None:
        """
        It creates a message dialog, shows it, and returns the response

        Args:
          title (str): str = The title of the dialog
          message (str): str = The message to display in the dialog
          dialog_buttons (str): str = DialogButtons.ok

        Returns:
          The response is being returned.
        """
        message_dialog = MessageDialog(
            self, Icons.information, dialog_buttons, title, message
        )
        message_dialog.show()

        response: str = ""

        if message_dialog.exec_():
            response = message_dialog.get_response()

        return response

    def search_ebay(self) -> None:
        """
        It opens a dialog box, and if the user clicks ok, it starts a thread that scrapes ebay for the
        user's input.

        Returns:
          The response is a DialogButtons enum.
        """
        input_dialog = InputDialog(title="Search Ebay", message="Search for anything")
        if input_dialog.exec_():
            response = input_dialog.get_response()
            if response == DialogButtons.ok:
                input_text = input_dialog.inputText
                ebay_scraper_thread = EbayScraper(item_to_search=input_text)
                # QApplication.setOverrideCursor(Qt.BusyCursor)
                ebay_scraper_thread.signal.connect(self.show_web_scrape_results)
                self.threads.append(ebay_scraper_thread)
                ebay_scraper_thread.start()
            elif response == DialogButtons.cancel:
                return

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
            if input_dialog.exec_():
                response = input_dialog.get_response()
                if response == DialogButtons.open:
                    try:
                        po_template = POTemplate(
                            f"{os.path.abspath(os.getcwd())}/PO's/templates/{input_dialog.get_selected_item()}.xlsx"
                        )
                        po_template.generate()
                        os.startfile(po_template.get_output_path())
                    except AttributeError:
                        return
                elif response == DialogButtons.cancel:
                    return
        else:
            po_template = POTemplate(
                f"{os.path.abspath(os.getcwd())}/PO's/templates/{po_name}.xlsx"
            )
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
        if input_dialog.exec_():
            response = input_dialog.get_response()
            if response == DialogButtons.discard:
                try:
                    os.remove(f"PO's/templates/{input_dialog.get_selected_item()}.xlsx")
                    self.show_message_dialog(
                        title="Success", message="Successfully removed template."
                    )
                except AttributeError:
                    return
            elif response == DialogButtons.cancel:
                return

    def add_po_templates(
        self, po_file_paths: list[str], open_select_file_dialog: bool = False
    ) -> None:
        """
        It takes a list of file paths, copies them to a new directory, and then shows a message dialog

        Args:
          po_file_paths (list[str]): list[str]
          open_select_file_dialog (bool): bool = False. Defaults to False
        """
        if open_select_file_dialog:
            po_file_paths, check = QFileDialog.getOpenFileNames(
                None, "Add Purchase Order Template", "", "Excel Files (*.xlsx)"
            )
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
                new_file_path = (
                    f"PO's/templates/{po_file.get_vendor().replace('.','')}.xlsx"
                )
                shutil.copyfile(po_file_path, new_file_path)
            check_po_directories()
            self.show_message_dialog(
                title="Success", message="Successfully added new Purchase Order template."
            )
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
                new_file_path = (
                    f"PO's/templates/{po_file.get_vendor().replace('.','')}.xlsx"
                )
                shutil.copyfile(po_file_path, new_file_path)
            check_po_directories()
            self.show_message_dialog(
                title="Success", message="Successfully added new Purchase Order template."
            )

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

    def print_inventory(self) -> None:
        """
        It takes a file path as an argument, opens the file, generates an excel file, and saves it

        Returns:
          The return value is None.
        """
        try:
            file_name = (
                f"excel files/{datetime.now().strftime('%B %d %A %Y %I-%M-%S %p')}"
            )
            excel_file = ExcelFile(inventory, f"{file_name}.xlsx")
            excel_file.generate()
            excel_file.save()

            input_dialog = MessageDialog(
                title="Success",
                message="Successfully generated inventory.\n\nWould you love to open it?",
                button_names=DialogButtons.open_cancel,
            )
            if input_dialog.exec_():
                response = input_dialog.get_response()
                if response == DialogButtons.open:
                    try:
                        os.startfile(
                            f"{os.path.dirname(os.path.realpath(sys.argv[0]))}/{file_name}.xlsx"
                        )
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

    def show_web_scrape_results(self, data) -> None:
        """
        Shows results of webscrape

        Args:
          data: a list of dictionaries
        """
        # QApplication.restoreOverrideCursor()
        results = WebScrapeResultsDialog(
            title="Results", message="Ebay search results", data=data
        )
        if results.exec_():
            response = results.get_response()
            if response == DialogButtons.ok:
                return

    def generate_error_log(self, message_dialog: MessageDialog) -> None:
        """
        It takes a screenshot of the error message dialog, saves it to a folder, writes the error
        message to a file, copies the app log to the folder, compresses the folder, and deletes the
        folder

        Args:
          message_dialog (MessageDialog): MessageDialog = The error message dialog that pops up when an
        error occurs.
        """
        output_directory: str = (
            f"logs/ErrorLog_{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
        )
        check_folders([output_directory])
        pixmap = QPixmap(message_dialog.grab())
        pixmap.save(f"{output_directory}/screenshot.png")
        with open(f"{output_directory}/error.log", "w", encoding="utf-8") as error_log:
            error_log.write(message_dialog.message)
        shutil.copyfile("logs/app.log", f"{output_directory}/app.log")
        compress_folder(foldername=output_directory, target_dir=output_directory)
        shutil.rmtree(output_directory)

    def toggle_dark_mode(self) -> None:
        """
        It toggles the dark mode setting in the settings file and updates the theme
        """
        settings_file.change_item(
            item_name="dark_mode", new_value=not settings_file.get_value("dark_mode")
        )

        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

        self.update_theme()

    def update_theme(self) -> None:
        """
        It reads the stylesheet.qss file from the theme folder and sets it as the stylesheet for the
        application
        """
        file = QFile(f"ui/BreezeStyleSheets/dist/qrc/{self.theme}/stylesheet.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        self.setStyleSheet(stream.readAll())

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
            self.actionAlphabatical.setStatusTip(
                f"Sort from {sorting_from_alphabet} to {sorting_to_alphabet}"
            )
            self.actionPriority.setStatusTip(
                f"Sort from {sorting_from_priority} to {sorting_to_priority}"
            )
            self.actionQuantity_in_Stock.setStatusTip(
                f"Sort from {sorting_from_number} to {sorting_to_number}"
            )
        else:
            self.actionAlphabatical.setStatusTip(
                f"Sort from {sorting_to_alphabet} to {sorting_from_alphabet}"
            )
            self.actionPriority.setStatusTip(
                f"Sort from {sorting_to_priority} to {sorting_from_priority}"
            )
            self.actionQuantity_in_Stock.setStatusTip(
                f"Sort from {sorting_to_number} to {sorting_from_number}"
            )

        if self.actionAlphabatical.isChecked():
            if self.actionAscending.isChecked():
                self.actionSort.setStatusTip(
                    f"Sort from {sorting_from_alphabet} to {sorting_to_alphabet}"
                )
            else:
                self.actionSort.setStatusTip(
                    f"Sort from {sorting_to_alphabet} to {sorting_from_alphabet}"
                )
            self.actionAscending.setStatusTip(
                f"Sort from {sorting_from_alphabet} to {sorting_to_alphabet}"
            )
            self.actionDescending.setStatusTip(
                f"Sort from {sorting_to_alphabet} to {sorting_from_alphabet}"
            )
        elif self.actionQuantity_in_Stock.isChecked():
            if self.actionAscending.isChecked():
                self.actionSort.setStatusTip(
                    f"Sort from {sorting_from_number} to {sorting_to_number}"
                )
            else:
                self.actionSort.setStatusTip(
                    f"Sort from {sorting_to_number} to {sorting_from_number}"
                )
            self.actionAscending.setStatusTip(
                f"Sort from {sorting_from_number} to {sorting_to_number}"
            )
            self.actionDescending.setStatusTip(
                f"Sort from {sorting_to_number} to {sorting_from_number}"
            )
        elif self.actionPriority.isChecked():
            if self.actionAscending.isChecked():
                self.actionSort.setStatusTip(
                    f"Sort from {sorting_from_priority} to {sorting_to_priority}"
                )
            else:
                self.actionSort.setStatusTip(
                    f"Sort from {sorting_to_priority} to {sorting_from_priority}"
                )
            self.actionAscending.setStatusTip(
                f"Sort from {sorting_from_priority} to {sorting_to_priority}"
            )
            self.actionDescending.setStatusTip(
                f"Sort from {sorting_to_priority} to {sorting_from_priority}"
            )

    def check_for_updates(self, on_start_up: bool = False) -> None:
        """
        It checks for updates on GitHub and displays a message dialog if there is a new update available

        Args:
          on_start_up (bool): bool = False. Defaults to False
        """
        try:
            try:
                response = requests.get(
                    "https://api.github.com/repos/thecodingjsoftware/Inventory-Manager/releases/latest"
                )
            except ConnectionError:
                return
            version: str = response.json()["name"].replace(" ", "")
            if version != __version__:
                message_dialog = self.show_message_dialog(
                    title=__name__,
                    message=f"There is a new update available.\n\nNew Version: {version}\n\nMake sure to make a backup\nbefore installing new version.",
                    dialog_buttons=DialogButtons.ok_update,
                )
                if message_dialog == DialogButtons.update:
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

    def show_whats_new(self, show: bool = False) -> None:
        """
        If the latest version of the program is newer than the last time the program was opened, show
        the changelog.
        """

        try:
            response = requests.get(
                "https://api.github.com/repos/thecodingjsoftware/Inventory-Manager/releases/latest"
            )
            version: str = response.json()["name"].replace(" ", "")
            if version == __version__ or show:
                build_date = time.strptime(__updated__, "%Y-%m-%d %H:%M:%S")
                current_date = time.strptime(
                    settings_file.get_value(item_name="last_opened"),
                    "%Y-%m-%d %H:%M:%S.%f",
                )
                if current_date < build_date or show:
                    with open("CHANGELOG.md", "r") as change_log_file:
                        self.show_message_dialog(
                            title="Whats new?", message=change_log_file.read()
                        )
                    settings_file.add_item(
                        item_name="last_opened", value=str(datetime.now())
                    )
        except:
            return

    def open_website(self) -> None:
        """
        This function opens the website in the default browser.
        """
        webbrowser.open("https://piney-manufacturing-inventory.herokuapp.com", new=0)

    def changes_response(self, data) -> None:
        """
        It compares two files, and if they are different, it displays a message in a label

        Args:
          data: The data that is returned from the server.
        """
        try:
            file_change = FileChanges(
                from_file=f"data/{settings_file.get_value(item_name='inventory_file_name')} - Compare.json",
                to_file=f"data/{settings_file.get_value(item_name='inventory_file_name')}.json",
            )
            self.status_button.disconnect()
            if file_change.get_changes() == "":
                self.status_button.clicked.connect(
                    partial(
                        self.show_file_changes, title="Changes", message="No changes."
                    )
                )
                set_status_button_stylesheet(button=self.status_button, color="green")
            else:
                self.status_button.clicked.connect(
                    partial(
                        self.show_file_changes,
                        title="Changes",
                        message=file_change.get_changes(),
                    )
                )
                set_status_button_stylesheet(button=self.status_button, color="yellow")
                if self.actionAuto_back_up_to_cloud.isChecked():
                    self.upload_file(
                        f"data/{settings_file.get_value(item_name='inventory_file_name')}.json",
                        False,
                    )
            if settings_file.get_value(item_name="last_toolbox_tab") == 0:
                self.status_button.setHidden(False)
                self.status_button.setText(file_change.which_file_changed())
            else:
                self.status_button.setHidden(True)
            os.remove(
                f"data/{settings_file.get_value(item_name='inventory_file_name')} - Compare.json"
            )
        except (TypeError, FileNotFoundError) as error:
            self.status_button.setText(
                f'<p style="color:red;"><b>{settings_file.get_value(item_name="inventory_file_name").title()}</b> - Failed to get changes. - {datetime.now().strftime("%r")}</p>'
            )
            set_status_button_stylesheet(button=self.status_button, color="red")

            self.status_button.disconnect()
            self.status_button.clicked.connect(
                partial(
                    self.show_error_dialog,
                    title="Error",
                    message=f"Could not get changes.\n\n{str(error)}",
                )
            )
            logging.critical(error)

    def data_received(self, data) -> None:
        """
        If the data received is "Successfully uploaded" or "Successfully downloaded", then show a
        message dialog with the title and message

        Args:
          data: the data received from the server
        """
        # QApplication.restoreOverrideCursor()
        if data == "Successfully uploaded" and self.get_upload_file_response:
            self.show_message_dialog(
                title=data,
                message=f"{data}\n\nFile successfully sent.\nWill take roughly 5 minutes to update database",
            )
            logging.info(f"Server: {data}")
        elif data == "Successfully downloaded" and self.get_upload_file_response:
            self.show_message_dialog(
                title=data,
                message=f"{data}\n\nFile successfully downloaded.",
            )
            logging.info(f"Server: {data}")
            inventory.load_data()
            self.load_categories()
        elif str(data) == "timed out" and self.get_upload_file_response:
            self.show_error_dialog(
                title="Time out",
                message="Server is either offline or try again. \n\nMake sure VPN's are disabled, else\n\ncontact server administrator.\n\n",
            )
        elif self.get_upload_file_response:
            self.show_error_dialog(
                title="error",
                message=str(data),
            )

    def start_changes_thread(self, file_to_download: str) -> None:
        """
        It creates a thread that will run a function that will check for changes in a file every 60
        seconds

        Args:
          file_to_download (str): str = the file to download
        """
        changes_thread = ChangesThread(file_to_download, 60)  # 1 minute
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

        round_number = lambda x, n: eval(
            '"%.'
            + str(int(n))
            + 'f" % '
            + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
        )
        self.label_exchange_price.setText(
            f"1.00 USD: {exchange_rate} CAD - {datetime.now().strftime('%r')}"
        )
        self.label_total_unit_cost.setText(
            f"Total Unit Cost: ${round_number(inventory.get_total_unit_cost(self.category, self.get_exchange_rate()),2)}"
        )
        settings_file.change_item(item_name="exchange_rate", new_value=exchange_rate)
        self.update_stock_costs()

    def upload_file(self, file_to_upload: str, get_response: bool = True) -> None:
        """
        It creates a new thread, sets the cursor to wait, and starts the thread

        Args:
          file_to_upload (str): str - The file to upload
        """
        self.get_upload_file_response = get_response
        upload_thread = UploadThread(file_to_upload)
        # if get_response:
        # QApplication.setOverrideCursor(Qt.BusyCursor)
        self.start_thread(upload_thread)

    def download_file(self, file_to_download: str) -> None:
        """
        It creates a new thread, sets the cursor to wait, and starts the thread

        Args:
          file_to_download (str): str = The file to download
        """
        self.get_upload_file_response = True
        download_thread = DownloadThread(file_to_download)
        # QApplication.setOverrideCursor(Qt.BusyCursor)
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
                self.show_message_dialog(
                    title="Success", message="Successfully loaded backup!"
                )
        else:
            extract(file_to_extract=file_path)
            self.load_categories()
            self.show_message_dialog(
                title="Success", message="Successfully loaded backup!"
            )

    def backup_database(self) -> None:
        """
        This function compresses the database file and shows a message dialog to the user
        """
        compress_database(
            path_to_file=f"data/{settings_file.get_value(item_name='inventory_file_name')}.json"
        )
        self.show_message_dialog(title="Success", message="Backup was successful!")

    def show_not_trusted_user(self) -> None:
        """
        It shows a message dialog with a title and a message
        """
        self.toolBox.currentChanged.disconnect()
        self.toolBox.setCurrentIndex(1)
        self.toolBox.currentChanged.connect(self.show_not_trusted_user)
        self.show_message_dialog(
            title="Permission error",
            message="You don't have permission to change inventory items.\n\nnot sorry \n\n(:",
        )

    def check_trusted_user(self) -> None:
        """
        If the user is not in the trusted_users list, then the user is not trusted
        """
        trusted_users = get_trusted_users()
        check_trusted_user = (user for user in trusted_users if not self.trusted_user)
        for user in check_trusted_user:
            self.trusted_user = self.username.lower() == user.lower()

        if not self.trusted_user:
            self.inventory_page.setEnabled(False)
            self.load_tree_view(inventory)
            self.toolBox.currentChanged.disconnect()
            self.toolBox.setCurrentIndex(1)
            settings_file.add_item("last_toolbox_tab", 1)
            self.toolBox.currentChanged.connect(self.show_not_trusted_user)
            self.toolBox.setItemToolTip(
                0,
                "You don't have permission to change inventory items.\n\nnot sorry \n\n(:",
            )
            self.menuSort.setEnabled(False)
            self.menuUpload_File.setEnabled(False)
            self.menuOpen_Category.setEnabled(False)

    def load_tree_view(self, inventory: JsonFile):
        """
        > This function loads the inventory into the tree view

        Args:
          inventory: The inventory object that is being displayed.
        """
        self.dockWidget_create_add_remove.setVisible(False)
        self.status_button.setHidden(True)
        self.clear_layout(self.search_layout)
        tree_view = ViewTree(data=inventory.get_data())
        self.search_layout.addWidget(tree_view, 0, 0)

    def clear_layout(self, layout) -> None:
        """
        If the layout is not None, while the layout has items, take the first item, get the widget, if
        the widget is not None, delete it, otherwise clear the layout

        Args:
          layout: The layout to be cleared
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def open_folder(self, path: str) -> None:
        """
        It opens the folder in the default file browser

        Args:
          path: The path to the folder
        """
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

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
        self.clear_layout(self.verticalLayout)
        self.tabs.clear()

        self.tab_widget = QTabWidget(self)
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_category)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.verticalLayout.addWidget(self.tab_widget)
        tab = QScrollArea(self)
        content_widget = QWidget()
        tab.setWidget(content_widget)
        grid_layout = QGridLayout(content_widget)
        tab.setWidgetResizable(True)
        self.tabs.append(grid_layout)
        self.tab_widget.addTab(tab, "")

        lbl1 = QLabel(left_label)
        lbl1.setStyleSheet("font:30px")
        if not left_label:
            lbl1.setFixedWidth(650)
            lbl1.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        else:
            lbl1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font_size = QFont()
        font_size.setPointSize(25)
        btn = QPushButton(highlighted_message)
        btn.setFont(font_size)
        btn.setObjectName("default_dialog_button")
        if button_pressed_event is not None:
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.clicked.connect(button_pressed_event)
        btn.setStyleSheet(
            "QPushButton#default_dialog_button{text-align: center; vertical-align: center }"
        )
        set_default_dialog_button_stylesheet(btn)
        btn.setFixedSize(highlighted_message_width, 45)
        lbl2 = QLabel(right_label)
        if not right_label:
            lbl2.setFixedWidth(650)
            lbl2.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        else:
            lbl2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        lbl2.setStyleSheet("font:30px")

        tab_index: int = self.tab_widget.currentIndex()
        tab = self.tabs[tab_index]
        tab.addWidget(lbl1, 0, 0)
        tab.addWidget(btn, 0, 1)
        tab.addWidget(lbl2, 0, 2)
        self.dockWidget_create_add_remove.setVisible(self.tab_widget.tabText(0) != "")

    def dragEnterEvent(self, event) -> None:
        """
        If the event has a URL, accept it, otherwise ignore it.

        Args:
          event: This is the event object that is passed to the method.
        """
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        """
        If the file is an Excel file, then accept the drop event and display a message. Otherwise,
        ignore the drop event.

        Args:
          event: The event object.
        """
        if event.mimeData().hasUrls:
            for url in event.mimeData().urls():
                if str(url.toLocalFile()).endswith(".xlsx"):
                    event.setDropAction(Qt.CopyAction)
                    event.accept()
                    self.set_layout_message(
                        "", "Add", "a new Purchase Order template", 80, None
                    )
                elif str(url.toLocalFile()).endswith(".zip"):
                    event.setDropAction(Qt.CopyAction)
                    event.accept()
                    self.set_layout_message("", "Load", "backup", 80, None)
                else:
                    event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        """
        It loads the categories from the database and displays them in the list widget

        Args:
          event: QDragLeaveEvent
        """
        self.load_categories()

    def dropEvent(self, event) -> None:
        """
        If the event has URLs, set the drop action to copy, accept the event, get the local file paths
        from the URLs, add the PO files to the database, and reload the categories

        Args:
          event: The event object
        """
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                if str(url.toLocalFile()).endswith(".xlsx"):
                    files = [str(url.toLocalFile()) for url in event.mimeData().urls()]
                    self.load_categories()
                    self.add_po_templates(files)
                    break
                elif str(url.toLocalFile()).endswith(".zip"):
                    self.load_backup(
                        [str(url.toLocalFile()) for url in event.mimeData().urls()][0]
                    )
            event.ignore()

    def closeEvent(self, event) -> None:
        """
        The function saves the geometry of the window and then closes the window

        Args:
          event: the event that triggered the close_event() method
        """
        # compress_database(
        #     path_to_file=f"data/{settings_file.get_value(item_name='inventory_file_name')}.json",
        #     on_close=True,
        # )
        self.save_geometry()
        super().closeEvent(event)


def main() -> None:
    """
    It creates a QApplication, creates a MainWindow, shows the MainWindow, and then runs the
    QApplication
    """
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


# if __name__ == "__main__":
main()
