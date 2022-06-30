__author__ = "Jared Gross"
__copyright__ = "Copyright 2022, TheCodingJ's"
__credits__: "list[str]" = ["Jared Gross"]
__license__ = "MIT"
__name__ = "Inventory Manager"
__version__ = "v1.1.3"
__updated__ = "2022-06-30 13:01:43"
__maintainer__ = "Jared Gross"
__email__ = "jared@pinelandfarms.ca"
__status__ = "Production"

import itertools
import logging
import math
import os
import shutil
import threading
import webbrowser
from datetime import datetime
from functools import partial
from operator import add

import requests
from forex_python.converter import CurrencyRates
from PyQt5 import QtTest, uic
from PyQt5.QtCore import QFile, Qt, QTextStream
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStyle,
    QTabWidget,
    QWidget,
    qApp,
)

import log_config
import ui.BreezeStyleSheets.breeze_resources
from threads.changes_thread import ChangesThread
from threads.download_thread import DownloadThread
from threads.upload_thread import UploadThread
from ui.about_dialog import AboutDialog
from ui.add_item_dialog import AddItemDialog
from ui.custom_widgets import (
    HumbleComboBox,
    HumbleDoubleSpinBox,
    HumbleSpinBox,
    RichTextPushButton,
    ViewTree,
)
from ui.input_dialog import InputDialog
from ui.message_dialog import MessageDialog
from ui.select_item_dialog import SelectItemDialog
from ui.web_scrape_results_dialog import WebScrapeResultsDialog
from utils.compress import compress_database, compress_folder
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.extract import extract
from utils.file_changes import FileChanges
from utils.json_file import JsonFile
from utils.json_object import JsonObject
from web_scrapers.ebay_scraper import EbayScraper
from web_scrapers.exchange_rate import ExchangeRate

settings_file = JsonFile(file_name="settings")
inventory = JsonFile(file_name="data/inventory")
geometry = JsonObject(JsonFile=settings_file, object_name="geometry")


class MainWindow(QMainWindow):
    """The class MainWindow inherits from the class QMainWindow"""

    def __init__(self):
        """
        It loads the UI and starts a thread that checks for changes in a JSON file.
        """
        super().__init__()
        uic.loadUi("ui/main_menu.ui", self)
        self.setWindowTitle(f"{__name__} {__version__} - {os.getlogin()}")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.check_for_updates(on_start_up=True)
        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )
        self.inventory_prices_objects = {}

        # VARIABLES
        self.categories = []
        self.highlight_color: str = "#4380A0"
        self.category: str = ""
        self.tabs = []
        self.last_item_selected: int = 0
        self.threads = []

        self.__load_ui()
        self.tool_box_menu_changed()
        self.start_changes_thread("data/inventory.json")
        self.start_exchange_rate_thread()
        self.show()

    def __load_ui(self) -> None:
        """
        It loads the UI
        """
        self.update_theme()
        self.setGeometry(
            geometry.get_value("x"),
            geometry.get_value("y"),
            geometry.get_value("width"),
            geometry.get_value("height"),
        )

        # Dockable Widget
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

        # Status
        self.status_button = RichTextPushButton(
            self, '<p style="color:yellow;">Getting changes...</p>'
        )
        self.status_button.setFlat(True)
        self.status_button.setStatusTip(
            "View additions and removals from the inventory file."
        )
        self.verticalLayout_status.addWidget(self.status_button)

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

        # SETTINGS
        self.actionDarkmode.setChecked(settings_file.get_value(item_name="dark_mode"))
        self.actionDarkmode.triggered.connect(self.toggle_dark_mode)

        # FILE
        self.menuOpen_Category.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/folder.png")
        )
        self.menuUpload_File.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/upload.png")
        )
        self.actionUploadInventory.triggered.connect(
            partial(self.upload_file, "data/inventory.json")
        )
        self.actionUploadInventory.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/upload.png")
        )
        self.menuDownload_File.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/download.png")
        )
        self.actionDownloadInventory.triggered.connect(
            partial(self.download_file, "data/inventory.json")
        )
        self.actionDownloadInventory.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/download.png")
        )
        self.actionBackup.triggered.connect(self.backup_database)
        self.actionBackup.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/backup.png")
        )
        self.actionLoad_Backup.triggered.connect(self.load_backup)
        self.actionExit.triggered.connect(self.close)
        self.actionExit.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/tab_close.png")
        )

        # SEARCH
        self.actionEbay.triggered.connect(self.search_ebay)

    def quick_load_category(self, index: int):
        """
        It sets the current tab to the index passed in, then calls the load_tab function

        Args:
          index (int): int - The index of the tab to load
        """
        self.tab_widget.setCurrentIndex(index)
        self.load_tab()

    def tool_box_menu_changed(self):
        """
        If the toolbox is not on the first tab, hide the dock widget
        """
        if self.toolBox.currentIndex() != 0:
            self.dockWidget_create_add_remove.setVisible(False)
            self.status_button.setHidden(True)
            self.clear_layout(self.search_layout)
            tree_view = ViewTree(inventory.get_data())
            self.search_layout.addWidget(tree_view, 0, 0)
        else:
            self.dockWidget_create_add_remove.setVisible(True)
            self.status_button.setHidden(False)
        settings_file.add_item("last_toolbox_tab", self.toolBox.currentIndex())

    def load_categories(self) -> None:
        """
        It loads the categories from the inventory file and creates a tab for each category.
        """
        inventory = JsonFile(file_name="data/inventory")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.clear_layout(self.verticalLayout)
        self.tabs.clear()
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
        self.tab_widget.tabBarDoubleClicked.connect(self.rename_category)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        i: int = -1
        for i, category in enumerate(self.categories):
            tab = QScrollArea(self)
            content_widget = QWidget()
            tab.setWidget(content_widget)
            grid_layout = QGridLayout(content_widget)
            tab.setWidgetResizable(True)
            self.tabs.append(grid_layout)
            self.tab_widget.addTab(tab, category)

        if i == -1:
            tab = QScrollArea(self)
            content_widget = QWidget()
            tab.setWidget(content_widget)
            grid_layout = QGridLayout(content_widget)
            tab.setWidgetResizable(True)
            self.tabs.append(grid_layout)
            self.tab_widget.addTab(tab, "")
            i += 1

        tab = QWidget(self)
        self.tab_widget.addTab(tab, "Create category")
        tab = QWidget(self)
        self.tab_widget.addTab(tab, "Delete category")
        if self.tab_widget.tabText(0) != "":
            tab = QWidget(self)
            self.tab_widget.addTab(tab, "Clone category")
        self.tab_widget.setTabToolTip(i + 1, "Add a new category")
        self.tab_widget.setTabIcon(
            i + 1, QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/list_add.png")
        )
        self.tab_widget.setTabToolTip(i + 2, "Delete an existing category")
        self.tab_widget.setTabIcon(
            i + 2, QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/list_remove.png")
        )

        if self.tab_widget.tabText(0) != "":
            self.tab_widget.setTabToolTip(i + 3, "Clone an existing category")
            self.tab_widget.setTabIcon(
                i + 3,
                QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/tab_duplicate.png"),
            )
        self.tab_widget.setCurrentIndex(settings_file.get_value("last_category_tab"))
        self.tab_widget.currentChanged.connect(self.load_tab)
        self.verticalLayout.addWidget(self.tab_widget)
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
        MINIMUM_WIDTH: int = 170

        if self.category == "Create category":
            self.tab_widget.setCurrentIndex(settings_file.get_value("last_category_tab"))
            self.create_new_category()
            return
        if self.category == "Delete category":
            self.tab_widget.setCurrentIndex(settings_file.get_value("last_category_tab"))
            self.delete_category()
            return
        if self.category == "Clone category":
            self.tab_widget.setCurrentIndex(settings_file.get_value("last_category_tab"))
            self.clone_category()
            return
        self.pushButton_create_new.setEnabled(True)
        self.radioButton_category.setEnabled(True)
        self.radioButton_single.setEnabled(True)
        try:
            self.clear_layout(self.tabs[tab_index])
        except IndexError:
            return
        settings_file.add_item("last_category_tab", tab_index)
        tab = self.tabs[tab_index]
        category_data = inventory.get_value(item_name=self.category)
        self.update_list_widget()
        self.label_category_name.setText(f"Category: {self.category}")
        self.quantities_change()

        # ! Some signals that are being used might be to performant heavy... may have to use on lost focus or something
        try:
            if list(category_data.keys()):  # type: ignore
                headers = [
                    "Name",
                    "Part Number",
                    "Quantity Per Unit",
                    "Quantity in Stock",
                    "Item Price",
                    "",
                    "Total Cost in Stock",
                    "Priority",
                    "Notes",
                ]

                row_index: int = 0

                for i, header in enumerate(headers):
                    lbl_header = QLabel(header)
                    lbl_header.setFixedHeight(30)
                    tab.addWidget(lbl_header, 0, i)

            for row_index, item in enumerate(list(category_data.keys()), start=1):  # type: ignore
                current_quantity: int = category_data[item]["current_quantity"]
                unit_quantity: int = category_data[item]["unit_quantity"]
                priority: int = category_data[item]["priority"]
                price: float = category_data[item]["price"]
                notes: str = category_data[item]["notes"]
                part_number: str = category_data[item]["part_number"]
                use_exchange_rate: bool = category_data[item]["use_exchange_rate"]
                exchange_rate: float = (
                    self.get_exchange_rate() if use_exchange_rate else 1
                )
                total_cost_in_stock: float = current_quantity * price * exchange_rate

                col_index: int = 0

                item_name = QComboBox()
                item_name.addItems(self.get_all_part_names())
                item_name.wheelEvent = lambda event: None
                item_name.setEditable(True)
                item_name.setCurrentText(item)
                item_name.currentTextChanged.connect(
                    partial(
                        self.name_change,
                        self.category,
                        item_name.currentText(),
                        item_name,
                    )
                )
                item_name.setMinimumWidth(MINIMUM_WIDTH)
                tab.addWidget(item_name, row_index, col_index)

                col_index += 1

                line_edit_part_number = QComboBox()
                line_edit_part_number.addItems(self.get_all_part_numbers())
                line_edit_part_number.wheelEvent = lambda event: None
                line_edit_part_number.setEditable(True)
                line_edit_part_number.setCurrentText(part_number)
                line_edit_part_number.setFixedWidth(120)
                line_edit_part_number.currentTextChanged.connect(
                    partial(
                        self.part_number_change,
                        self.category,
                        item_name,
                        "part_number",
                        line_edit_part_number,
                    )
                )
                tab.addWidget(line_edit_part_number, row_index, col_index)

                col_index += 1

                spin_unit_quantity = HumbleSpinBox()
                spin_unit_quantity.setFixedWidth(100)
                spin_unit_quantity.setMaximum(99999999)
                spin_unit_quantity.setMinimum(-99999999)
                spin_unit_quantity.setAccelerated(True)
                spin_unit_quantity.setValue(int(unit_quantity))
                spin_unit_quantity.valueChanged.connect(
                    partial(
                        self.unit_quantity_change,
                        self.category,
                        item_name,
                        "unit_quantity",
                        spin_unit_quantity,
                    )
                )
                tab.addWidget(spin_unit_quantity, row_index, col_index)

                col_index += 1

                spin_current_quantity = HumbleSpinBox()
                spin_current_quantity.setFixedWidth(100)
                spin_current_quantity.setMaximum(99999999)
                spin_current_quantity.setMinimum(-99999999)
                spin_current_quantity.setAccelerated(True)
                spin_current_quantity.setValue(int(current_quantity))
                if current_quantity <= 0:
                    spin_current_quantity.setStyleSheet("color: red")
                spin_current_quantity.valueChanged.connect(
                    partial(
                        self.current_quantity_change,
                        self.category,
                        item_name,
                        "current_quantity",
                        spin_current_quantity,
                    )
                )
                tab.addWidget(spin_current_quantity, row_index, col_index)

                col_index += 1

                spin_price = HumbleDoubleSpinBox()
                spin_price.setFixedWidth(100)
                spin_price.setMaximum(99999999)
                spin_price.setMinimum(-99999999)
                spin_price.setAccelerated(True)
                spin_price.setValue(price)
                spin_price.setPrefix("$")
                spin_price.setSuffix(" USD" if use_exchange_rate else " CAD")
                spin_price.valueChanged.connect(
                    partial(
                        self.price_change, self.category, item_name, "price", spin_price
                    )
                )
                tab.addWidget(spin_price, row_index, col_index)

                col_index += 1

                combo_exchange_rate = QComboBox()
                combo_exchange_rate.wheelEvent = lambda event: None
                combo_exchange_rate.setFixedWidth(50)
                combo_exchange_rate.addItems(["CAD", "USD"])
                combo_exchange_rate.setCurrentText("USD" if use_exchange_rate else "CAD")
                combo_exchange_rate.currentIndexChanged.connect(
                    partial(
                        self.use_exchange_rate_change,
                        self.category,
                        item_name,
                        "use_exchange_rate",
                        combo_exchange_rate,
                    )
                )
                tab.addWidget(combo_exchange_rate, row_index, col_index)

                col_index += 1

                spin_total_cost = QLineEdit()
                spin_total_cost.setFixedWidth(100)
                spin_total_cost.setReadOnly(True)
                round_number = lambda x, n: eval(
                    '"%.'
                    + str(int(n))
                    + 'f" % '
                    + repr(int(x) + round(float("." + str(float(x)).split(".")[1]), n))
                )
                spin_total_cost.setText(
                    f"${str(round_number(total_cost_in_stock, 2))} {combo_exchange_rate.currentText()}"
                )
                tab.addWidget(spin_total_cost, row_index, col_index)

                self.inventory_prices_objects[item_name] = {
                    "current_quantity": spin_current_quantity,
                    "price": spin_price,
                    "use_exchange_rate": combo_exchange_rate,
                    "total_cost": spin_total_cost,
                }

                col_index += 1

                combo_priority = QComboBox()
                combo_priority.wheelEvent = lambda event: None
                combo_priority.setFixedWidth(60)
                combo_priority.addItems(["Default", "Low", "Medium", "High"])
                combo_priority.setCurrentIndex(priority)
                if combo_priority.currentText() == "Medium":
                    combo_priority.setStyleSheet("color: yellow")
                elif combo_priority.currentText() == "High":
                    combo_priority.setStyleSheet("color: red")
                combo_priority.currentIndexChanged.connect(
                    partial(
                        self.priority_change,
                        self.category,
                        item_name,
                        "priority",
                        combo_priority,
                    )
                )
                tab.addWidget(combo_priority, row_index, col_index)

                col_index += 1

                text_notes = QPlainTextEdit()
                text_notes.setMinimumWidth(100)
                text_notes.setMaximumWidth(200)
                text_notes.setFixedHeight(60)
                text_notes.setPlainText(notes)
                text_notes.textChanged.connect(
                    partial(
                        self.notes_changed, self.category, item_name, "notes", text_notes
                    )
                )
                tab.addWidget(text_notes, row_index, col_index)

                col_index += 1

                btn_po = QPushButton("PO")
                btn_po.setToolTip(f"Open a new purchase order")
                btn_po.setFixedSize(36, 26)
                btn_po.clicked.connect(self.open_po)
                tab.addWidget(btn_po, row_index, col_index)

                col_index += 1

                btn_delete = QPushButton()
                btn_delete.setToolTip(
                    f"Delete {item_name.currentText()} permanently from {self.category}"
                )
                btn_delete.setFixedSize(26, 26)
                btn_delete.setIcon(
                    QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/trash.png")
                )
                btn_delete.clicked.connect(
                    partial(self.delete_item, self.category, item_name)
                )
                tab.addWidget(btn_delete, row_index, col_index)
        except AttributeError:
            lbl = QLabel("You need to create a category.")
            self.pushButton_create_new.setEnabled(False)
            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(False)
            self.radioButton_category.setEnabled(False)
            self.radioButton_single.setEnabled(False)
            tab.addWidget(lbl, 0, 0)
            QApplication.restoreOverrideCursor()
            return
        QApplication.restoreOverrideCursor()

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
            spin_price = self.inventory_prices_objects[item_name]["price"]
            combo_exchange_rate = self.inventory_prices_objects[item_name][
                "use_exchange_rate"
            ]
            spin_price.setSuffix(f" {combo_exchange_rate.currentText()}")
            spin_total_cost = self.inventory_prices_objects[item_name]["total_cost"]
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

    def create_new_category(self) -> None:
        """
        It creates a new category

        Returns:
          The response is being returned.
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
            button_names=DialogButtons.delete_cancel,
            title="Delete category",
            message="Select a category to delete.\n\nThis action is permanent and cannot\nbe undone.",
            items=self.categories,
        )

        if select_item_dialog.exec_():
            response = select_item_dialog.get_response()
            if response == DialogButtons.delete:
                try:
                    inventory.remove_item(select_item_dialog.get_selected_item())
                except AttributeError:
                    return
                self.tab_widget.setCurrentIndex(0)
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
                    inventory.clone_key(select_item_dialog.get_selected_item())
                except AttributeError:
                    return
                self.tab_widget.setCurrentIndex(0)
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
        input_dialog = InputDialog(
            title="Rename category", message="Enter a new name for a category."
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
                inventory.change_key_name(
                    key_name=self.tab_widget.tabText(index), new_name=input_text
                )
                self.load_categories()
            elif response == DialogButtons.cancel:
                return

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
                    f"'{name.currentText()}' is an invalid item name.\n\nCan't be the same as other names.",
                    dialog_buttons=DialogButtons.ok,
                )
                name.setCurrentText(old_name)
                # name.selectAll()
                return
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
        self.value_change(category, item_name.currentText(), value_name, quantity.value())
        if quantity.value() <= 0:
            quantity.setStyleSheet("color: red")
        else:
            quantity.setStyleSheet("color: white")
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
        self.value_change(category, item_name.currentText(), value_name, quantity.value())

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
        self.value_change(category, item_name.currentText(), value_name, price.value())
        self.update_stock_costs()

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
        self.value_change(
            category,
            item_name.currentText(),
            value_name,
            combo.currentText() == "USD",
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
        self.value_change(
            category, item_name.currentText(), value_name, combo.currentIndex()
        )
        if combo.currentText() == "Medium":
            combo.setStyleSheet("color: yellow")
        elif combo.currentText() == "High":
            combo.setStyleSheet("color: red")
        else:
            combo.setStyleSheet("color: white")

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
            title="Add item",
            message=f"Adding an item to {self.category}.\n\nPress 'Add' when finished.",
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
                            f"'{name}' is an invalid item name.\n\nCan't be the same as other names.",
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

                inventory.add_item_in_object(self.category, name)

                inventory.change_object_in_object_item(
                    self.category, name, "part_number", part_number
                )
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
            self.label.setText("Quantity:")
            self.pushButton_add_quantity.setText("Add Quantity")
            self.pushButton_remove_quantity.setText("Remove Quantity")
            settings_file.add_item(item_name="change_quantities_by", value="Item")
            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(False)
            # self.listWidget_itemnames.clearSelection()
            # self.listWidget_item_changed()
            # self.listWidget_itemnames.setEnabled(True)
            # self.listWidget_itemnames.setStyleSheet(
            #     "QAbstractItemView::item{color: white}"
            # )

    def remove_quantity_from_category(self) -> None:
        """
        It takes the quantity of an item in a category, and subtracts that quantity to all items in the
        inventory that have the same part number as the item in the category
        """
        category_data = inventory.get_value(item_name=self.category)
        part_numbers = []
        for item in list(category_data.keys()):
            unit_quantity: int = category_data[item]["unit_quantity"]
            current_quantity: int = category_data[item]["current_quantity"]
            part_numbers.append(category_data[item]["part_number"])
            self.value_change(
                category=self.category,
                item_name=item,
                value_name="current_quantity",
                new_value=current_quantity
                - (unit_quantity * self.spinBox_quantity.value()),
            )
        part_numbers = list(set(part_numbers))
        data = inventory.get_data()
        for category in list(data.keys()):
            if category == self.category:
                continue
            for item, part_number in itertools.product(
                list(data[category].keys()), part_numbers
            ):
                if part_number == data[category][item]["part_number"]:
                    unit_quantity: int = data[category][item]["unit_quantity"]
                    current_quantity: int = data[category][item]["current_quantity"]
                    self.value_change(
                        category=category,
                        item_name=item,
                        value_name="current_quantity",
                        new_value=current_quantity
                        - (unit_quantity * self.spinBox_quantity.value()),
                    )
        self.load_tab()
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(True)

    def add_quantity(self, item_name: str, old_quantity: int) -> None:
        """
        It adds the value of the spinbox to the quantity of the item selected in the listwidget

        Args:
          item_name (str): str = the name of the item
          old_quantity (int): int = the quantity of the item before the change
        """
        self.highlight_color = "#45A54D"
        category_data = inventory.get_value(item_name=self.category)
        current_quantity: int = category_data[item_name]["current_quantity"]
        part_number: str = category_data[item_name]["part_number"]
        self.value_change(
            self.category,
            item_name,
            "current_quantity",
            current_quantity + self.spinBox_quantity.value(),
        )
        data = inventory.get_data()
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
        self.load_tab()
        self.listWidget_itemnames.setCurrentRow(self.last_item_selected)

    def remove_quantity(self, item_name: str, old_quantity: int) -> None:
        """
        It removes the quantity of an item from the inventory

        Args:
          item_name (str): str = the name of the item
          old_quantity (int): int = the quantity of the item before the change
        """
        self.highlight_color = "#A34444"
        category_data = inventory.get_value(item_name=self.category)
        current_quantity: int = category_data[item_name]["current_quantity"]
        part_number: str = category_data[item_name]["part_number"]
        self.value_change(
            self.category,
            item_name,
            "current_quantity",
            current_quantity - self.spinBox_quantity.value(),
        )
        data = inventory.get_data()
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
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        self.load_tab()
        self.listWidget_itemnames.setCurrentRow(self.last_item_selected)

    def listWidget_item_changed(self) -> None:
        """
        It's a function that is called when an item is selected from a list widget. It then enables two
        buttons and connects them to two other functions

        Returns:
          The return value of the function is None.
        """
        try:
            selected_item: str = self.listWidget_itemnames.currentItem().text()
        except AttributeError:
            self.pushButton_add_quantity.setEnabled(False)
            self.pushButton_remove_quantity.setEnabled(False)
            return
        category_data = inventory.get_value(item_name=self.category)
        try:
            quantity: int = category_data[selected_item]["current_quantity"]
        except KeyError:
            return
        self.last_item_selected = self.listWidget_itemnames.currentRow()
        for item in list(self.inventory_prices_objects.keys()):
            if item.currentText() == selected_item:
                if self.highlight_color == "#4380A0":
                    item.setStyleSheet(f"background-color: {self.highlight_color}")
                else:
                    if (
                        self.inventory_prices_objects[item]["current_quantity"].value()
                        <= 0
                    ):
                        self.inventory_prices_objects[item][
                            "current_quantity"
                        ].setStyleSheet(
                            f"background-color: {self.highlight_color}; color: red"
                        )
                    else:
                        self.inventory_prices_objects[item][
                            "current_quantity"
                        ].setStyleSheet(
                            f"background-color: {self.highlight_color}; color: white"
                        )
                    self.highlight_color = "#4380A0"

                # QtTest.QTest.qWait(1000)
            elif self.theme == "dark":
                if self.highlight_color == "#4380A0":
                    item.setStyleSheet("background-color: #1d2023")

                if self.inventory_prices_objects[item]["current_quantity"].value() <= 0:
                    self.inventory_prices_objects[item]["current_quantity"].setStyleSheet(
                        "background-color: #1d2023; color: red"
                    )

                else:
                    self.inventory_prices_objects[item]["current_quantity"].setStyleSheet(
                        "background-color: #1d2023; color: white"
                    )

            else:
                if self.highlight_color == "#4380A0":
                    item.setStyleSheet("background-color: #eff0f1")
                if self.inventory_prices_objects[item]["current_quantity"].value() <= 0:
                    self.inventory_prices_objects[item]["current_quantity"].setStyleSheet(
                        "background-color: #eff0f1; color: red"
                    )

                else:
                    self.inventory_prices_objects[item]["current_quantity"].setStyleSheet(
                        "background-color: #eff0f1; color: white"
                    )
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
        It changes the value of a value in an item in an object

        Args:
          category (str): str = The category of the item you want to change.
          item_name (str): str = The name of the item you want to change.
          value_name (str): str = The name of the value you want to change.
          new_value: The new value to be assigned to the value_name
        """
        add_quantity_state: bool = self.pushButton_add_quantity.isEnabled()
        remove_quantity_state: bool = self.pushButton_remove_quantity.isEnabled()
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_remove_quantity.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        inventory.change_object_in_object_item(
            object_name=category,
            item_name=item_name,
            value_name=value_name,
            new_value=new_value,
        )
        QApplication.restoreOverrideCursor()
        self.pushButton_add_quantity.setEnabled(add_quantity_state)
        self.pushButton_remove_quantity.setEnabled(remove_quantity_state)

    def get_all_part_numbers(self) -> list:
        """
        It takes the data from the inventory module, loops through the data, and returns a list of all
        the part numbers

        Returns:
          A list of all the part numbers in the inventory.
        """
        data = inventory.get_data()
        part_numbers = []
        for category in list(data.keys()):
            part_numbers.extend(
                data[category][item]["part_number"]
                for item in list(data[category].keys())
            )

        part_numbers = list(set(part_numbers))
        return part_numbers

    def get_all_part_names(self) -> list:
        """
        It takes the data from the inventory module, loops through the data, and returns a list of all
        the part names

        Returns:
          A list of all the part names in the inventory.
        """
        data = inventory.get_data()
        part_names = []
        for category in list(data.keys()):
            if category == self.category:
                continue
            part_names.extend(iter(list(data[category].keys())))
        part_names = list(set(part_names))
        return part_names

    def get_exchange_rate(self) -> float:
        """
        It returns the exchange rate from the settings file

        Returns:
          The exchange rate from the settings file.
        """
        return settings_file.get_value(item_name="exchange_rate")

    def save_geometry(self) -> None:
        """
        It saves the geometry of the window to the settings file
        """
        geometry.set_value("x", value=self.pos().x())
        geometry.set_value("y", value=self.pos().y())
        geometry.set_value("width", value=self.size().width())
        geometry.set_value("height", value=self.size().height())

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
                QApplication.setOverrideCursor(Qt.WaitCursor)
                ebay_scraper_thread.signal.connect(self.show_web_scrape_results)
                self.threads.append(ebay_scraper_thread)
                ebay_scraper_thread.start()
            elif response == DialogButtons.cancel:
                return

    def open_po(self) -> None:
        input_dialog = SelectItemDialog(
            title="Open PO", message="Waiting for PO templates", items=[]
        )
        input_dialog.show()

    def show_web_scrape_results(self, data) -> None:
        QApplication.restoreOverrideCursor()
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

    def check_for_updates(self, on_start_up: bool = False) -> None:
        """
        It checks for updates on GitHub and displays a message dialog if there is a new update available

        Args:
          on_start_up (bool): bool = False. Defaults to False
        """
        try:
            response = requests.get(
                "https://api.github.com/repos/thecodingjsoftware/Inventory-Manager/releases/latest"
            )
            version: str = response.json()["name"].replace(" ", "")
            if version != __version__:
                message_dialog = self.show_message_dialog(
                    title=__name__,
                    message=f"There is a new update available.\n\nNew Version: {version}\n\nMake sure to make a backup\nbefore installing new version.",
                    dialog_buttons=DialogButtons.ok_download,
                )
                if message_dialog == DialogButtons.download:
                    webbrowser.open(
                        f"https://github.com/TheCodingJsoftware/Inventory-Manager/releases/tag/{version}"
                    )
            elif not on_start_up:
                self.show_message_dialog(
                    title=__name__,
                    message=f"There are currently no updates available.\n\nCurrent Version: {__version__}",
                )
        except Exception as e:
            if not on_start_up:
                self.show_error_dialog(title=__name__, message=f"Error\n\n{e}")

    def changes_response(self, data) -> None:
        """
        It compares two files, and if they are different, it displays a message in a label

        Args:
          data: The data that is returned from the server.
        """
        try:
            file_change = FileChanges(
                from_file="data/inventory - Compare.json", to_file="data/inventory.json"
            )
            self.status_button.disconnect()
            if file_change.get_changes() == "":
                self.status_button.clicked.connect(
                    partial(
                        self.show_file_changes, title="Changes", message="No changes."
                    )
                )
            else:
                self.status_button.clicked.connect(
                    partial(
                        self.show_file_changes,
                        title="Changes",
                        message=file_change.get_changes(),
                    )
                )
            if settings_file.get_value(item_name="last_toolbox_tab") == 0:
                self.status_button.setHidden(False)
                self.status_button.setText(file_change.which_file_changed())
            else:
                self.status_button.setHidden(True)
            os.remove("data/inventory - Compare.json")
        except (TypeError, FileNotFoundError) as e:
            self.status_button.setText(
                f'<p style="color:red;"><b>Inventory</b> - Failed to get changes. - {datetime.now().strftime("%r")}</p>'
            )
            self.status_button.disconnect()
            self.status_button.clicked.connect(
                partial(
                    self.show_error_dialog,
                    title="Error",
                    message=f"Could not get changes.\n\n{str(e)}",
                )
            )
            logging.critical(e)

    def data_received(self, data) -> None:
        """
        If the data received is "Successfully uploaded" or "Successfully downloaded", then show a
        message dialog with the title and message

        Args:
          data: the data received from the server
        """
        QApplication.restoreOverrideCursor()
        if data == "Successfully uploaded":
            self.show_message_dialog(
                title=data,
                message=f"{data}\n\nFile successfully sent.\nWill take roughly 5 minutes to update database",
            )
            logging.info(f"Server: {data}")
        elif data == "Successfully downloaded":
            self.show_message_dialog(
                title=data,
                message=f"{data}\n\nFile successfully downloaded.",
            )
            logging.info(f"Server: {data}")
            inventory.load_data()
            self.load_categories()
        elif str(data) == "timed out":
            self.show_error_dialog(
                title="Time out",
                message="Server is either offline or try again. \n\nMake sure VPN's are disabled, else\n\ncontact server administrator.\n\n",
            )
        else:
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
        self.label_exchange_price.setText(
            f"1.00 USD: {exchange_rate} CAD - {datetime.now().strftime('%r')}"
        )
        settings_file.change_item(item_name="exchange_rate", new_value=exchange_rate)
        self.update_stock_costs()

    def upload_file(self, file_to_upload: str) -> None:
        """
        It creates a new thread, sets the cursor to wait, and starts the thread

        Args:
          file_to_upload (str): str - The file to upload
        """
        upload_thread = UploadThread(file_to_upload)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.start_thread(upload_thread)

    def download_file(self, file_to_download: str) -> None:
        """
        It creates a new thread, sets the cursor to wait, and starts the thread

        Args:
          file_to_download (str): str = The file to download
        """
        download_thread = DownloadThread(file_to_download)
        QApplication.setOverrideCursor(Qt.WaitCursor)
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

    def load_backup(self) -> None:
        """
        It opens a file dialog, and if the user selects a file, it extracts the file and then loads the
        categories
        """
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
                title="Success", message="Successfully loaded backup."
            )

    def backup_database(self) -> None:
        """
        This function compresses the database file and shows a message dialog to the user
        """
        compress_database(path_to_file="data/inventory.json")
        self.show_message_dialog(title="Success", message="Backup was successful!")

    def closeEvent(self, event):
        """
        The function saves the geometry of the window and then closes the window

        Args:
          event: the event that triggered the close_event() method
        """
        self.save_geometry()
        super().closeEvent(event)

    def clear_layout(self, layout):
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


def default_settings() -> None:
    """
    It checks if a setting exists in the settings file, and if it doesn't, it creates it with a default
    value
    """
    check_setting(setting="exchange_rate", default_value=1.0)
    check_setting(setting="dark_mode", default_value=True)
    check_setting(setting="server_ip", default_value="10.0.0.64")
    check_setting(setting="server_port", default_value=4000)
    check_setting(
        setting="geometry",
        default_value={"x": 200, "y": 200, "width": 600, "height": 400},
    )
    check_setting(setting="last_category_tab", default_value=0)
    check_setting(setting="last_toolbox_tab", default_value=0)
    check_setting(setting="change_quantities_by", default_value="Category")


def check_setting(setting: str, default_value) -> None:
    """
    If the setting is not in the settings file, add it with the default value

    Args:
      setting (str): The name of the setting to check.
      default_value: The default value of the setting.
    """
    if settings_file.get_value(item_name=setting) is None:
        settings_file.add_item(item_name=setting, value=default_value)


def check_folders(folders: list) -> None:
    """
    If the folder doesn't exist, create it

    Args:
      folders (list): list = ["data", "data/images", "data/images/thumbnails", "data/images/fullsize",
    "data/images/fullsize/temp"]
    """
    for folder in folders:
        if not os.path.exists(f"{os.path.dirname(os.path.realpath(__file__))}/{folder}"):
            os.makedirs(f"{os.path.dirname(os.path.realpath(__file__))}/{folder}")


def main() -> None:
    """
    It creates a QApplication, creates a MainWindow, shows the MainWindow, and then runs the
    QApplication
    """
    default_settings()
    check_folders(folders=["logs", "data", "backups"])
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


# if __name__ == "__main__":
main()
