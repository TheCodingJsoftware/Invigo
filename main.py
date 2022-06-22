# sourcery skip: avoid-builtin-shadow
__author__ = "Jared Gross"
__copyright__ = "Copyright 2022, TheCodingJ's"
__credits__: "list[str]" = ["Jared Gross"]
__license__ = "MIT"
__name__ = "Inventory Manager"
__version__ = "v0.0.3"
__updated__ = "2022-06-21 21:31:00"
__maintainer__ = "Jared Gross"
__email__ = "jared@pinelandfarms.ca"
__status__ = "Production"

import logging
import os
import shutil
from datetime import datetime
from functools import partial

import requests
from PyQt5 import uic
from PyQt5.QtCore import QFile, Qt, QTextStream
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QDoubleSpinBox,
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
from about_dialog import AboutDialog
from add_item_dialog import AddItemDialog
from changes_thread import ChangesThread
from download_thread import DownloadThread
from input_dialog import InputDialog
from message_dialog import MessageDialog
from select_item_dialog import SelectItemDialog
from upload_thread import UploadThread
from utils.compress import compress_database, compress_folder
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.file_changes import FileChanges
from utils.json_file import JsonFile
from utils.json_object import JsonObject

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
        self.setWindowTitle(f"{__name__} {__version__}")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.check_for_updates(on_start_up=True)
        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

        # VARIABLES
        self.categories = []
        self.category: str = ""
        self.tabs = []
        self.last_item_selected: int = 0
        self.threads = []

        self.__load_ui()
        self.start_changes_thread("data/inventory.json")
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

        # Tool Box
        self.toolBox.setCurrentIndex(
            settings_file.get_value(item_name="last_toolbox_tab")
        )
        self.toolBox.currentChanged.connect(self.tool_box_menu_changed)

        # Tab widget
        self.load_categories()
        self.pushButton_create_new.clicked.connect(self.add_item)
        self.pushButton_add_quantity.clicked.connect(self.add_quantity)
        self.pushButton_add_quantity.setEnabled(False)
        self.pushButton_add_quantity.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/list_add.png")
        )
        self.pushButton_remove_quantity.clicked.connect(self.remove_quantity)
        self.pushButton_remove_quantity.setEnabled(False)
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
        self.actionExit.triggered.connect(self.close)
        self.actionExit.setIcon(
            QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/tab_close.png")
        )

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
        else:
            self.dockWidget_create_add_remove.setVisible(True)
        settings_file.add_item("last_toolbox_tab", self.toolBox.currentIndex())

    def load_categories(self) -> None:
        """
        It loads the categories from the inventory file and creates a tab for each category.
        """
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
        self.tab_widget.setMovable(True)
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
        self.tab_widget.setTabToolTip(i + 1, "Add a new category")
        self.tab_widget.setTabIcon(
            i + 1, QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/list_add.png")
        )
        self.tab_widget.setTabToolTip(i + 2, "Delete an existing category")
        self.tab_widget.setTabIcon(
            i + 2, QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/list_remove.png")
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
        if self.category == "Create category":
            self.tab_widget.setCurrentIndex(settings_file.get_value("last_category_tab"))
            self.create_new_category()
            return
        if self.category == "Delete category":
            self.tab_widget.setCurrentIndex(settings_file.get_value("last_category_tab"))
            self.delete_category()
            return
        self.pushButton_create_new.setEnabled(True)
        try:
            self.clear_layout(self.tabs[tab_index])
        except IndexError:
            return
        settings_file.add_item("last_category_tab", tab_index)
        tab = self.tabs[tab_index]
        category_data = inventory.get_value(item_name=self.category)
        self.update_list_widget()
        self.label_category_name.setText(f"Category: {self.category}")

        # ! Some signals that are being used might be to performant heavy... may have to use on lost focus or something
        try:
            if list(category_data.keys()):  # type: ignore
                headers = ["Name", "Quantity", "Price", "Priority", "Notes"]

                row_index: int = 0

                for i, header in enumerate(headers):
                    lbl_header = QLabel(header)
                    tab.addWidget(lbl_header, 0, i)

            for row_index, item in enumerate(list(category_data.keys()), start=1):  # type: ignore
                quantity: int = category_data[item]["quantity"]
                priority: int = category_data[item]["priority"]
                price: float = category_data[item]["price"]
                notes: str = category_data[item]["notes"]

                col_index: int = 0

                item_name = QLineEdit()
                item_name.setText(item)
                item_name.textEdited.connect(
                    partial(self.name_change, self.category, item_name.text(), item_name)
                )
                tab.addWidget(item_name, row_index, col_index)

                col_index += 1

                spin_quantity = QSpinBox()
                spin_quantity.setValue(quantity)
                spin_quantity.valueChanged.connect(
                    partial(
                        self.quantity_change,
                        self.category,
                        item_name,
                        "quantity",
                        spin_quantity,
                    )
                )
                tab.addWidget(spin_quantity, row_index, col_index)

                col_index += 1

                spin_price = QDoubleSpinBox()
                spin_price.setValue(price)
                spin_price.valueChanged.connect(
                    partial(
                        self.price_change, self.category, item_name, "price", spin_price
                    )
                )
                tab.addWidget(spin_price, row_index, col_index)

                col_index += 1

                combo_priority = QComboBox()
                combo_priority.addItems(["Default", "Low", "Medium", "High"])
                combo_priority.setCurrentIndex(priority)
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
                text_notes.setMaximumWidth(300)
                text_notes.setMaximumHeight(60)
                text_notes.setPlainText(notes)
                text_notes.textChanged.connect(
                    partial(
                        self.notes_changed, self.category, item_name, "notes", text_notes
                    )
                )
                tab.addWidget(text_notes, row_index, col_index)

                col_index += 1

                btn_delete = QPushButton()
                btn_delete.setToolTip(
                    f"Delete {item_name.text()} permanently from {self.category}"
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
                if search_input.lower() in item.lower():
                    self.listWidget_itemnames.addItem(item)
        except AttributeError:
            return

    def create_new_category(self) -> None:
        """
        It creates a new category

        Returns:
          The response is being returned.
        """
        self.input_dialog = InputDialog(
            title="Create category", message="Enter a name for a new category."
        )

        if self.input_dialog.exec_():
            response = self.input_dialog.get_response()

        if response == DialogButtons.ok:
            input_text = self.input_dialog.inputText
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
        self.select_item_dialog = SelectItemDialog(
            button_names=DialogButtons.delete_cancel,
            title="Delete category",
            message="Select a category to delete.\n\nThis action is permanent and cannot\nbe undone.",
            items=self.categories,
        )

        if self.select_item_dialog.exec_():
            response = self.select_item_dialog.get_response()

        if response == DialogButtons.delete:
            try:
                inventory.remove_item(self.select_item_dialog.get_selected_item())
            except AttributeError:
                return
            self.tab_widget.setCurrentIndex(0)
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
            if name.text() == item:
                self.show_error_dialog(
                    "Invalid name",
                    f"'{name.text()}' is an invalid item name.\n\nCan't be the same as other names.",
                    dialog_buttons=DialogButtons.ok,
                )
                name.setText(old_name)
                name.selectAll()
                return
        inventory.change_item_name(category, old_name, name.text())
        name.disconnect()
        name.textEdited.connect(partial(self.name_change, category, name.text(), name))
        self.update_list_widget()

    def quantity_change(
        self, category: str, item_name: QLineEdit, value_name: str, quantity: QSpinBox
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
        self.value_change(category, item_name.text(), value_name, quantity.value())

    def price_change(
        self, category: str, item_name: QLineEdit, value_name: str, price: QDoubleSpinBox
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
        self.value_change(category, item_name.text(), value_name, price.value())

    def priority_change(
        self, category: str, item_name: QLineEdit, value_name: str, combo: QComboBox
    ) -> None:
        """
        It changes the priority of a task

        Args:
          category (str): str - The category of the item
          item_name (QLineEdit): QLineEdit
          value_name (str): str = The name of the value to change
          combo (QComboBox): QComboBox
        """
        self.value_change(category, item_name.text(), value_name, combo.currentIndex())

    def notes_changed(
        self, category: str, item_name: QLineEdit, value_name: str, note: QPlainTextEdit
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
        self.value_change(category, item_name.text(), value_name, note.toPlainText())

    def add_item(self) -> None:
        """
        It adds an item to a category

        Returns:
          The response from the dialog.
        """
        self.add_item_dialog = AddItemDialog(
            title="Add item",
            message=f"Adding an item to {self.category}.\n\nPress 'Add' when finished.",
        )

        if self.add_item_dialog.exec_():
            response = self.add_item_dialog.get_response()

        if response == DialogButtons.add:
            name: str = self.add_item_dialog.get_name()
            category_data = inventory.get_value(item_name=self.category)
            for item in list(category_data.keys()):
                if name == item:
                    self.show_error_dialog(
                        "Invalid name",
                        f"'{name}' is an invalid item name.\n\nCan't be the same as other names.",
                        dialog_buttons=DialogButtons.ok,
                    )
                    return
            priority: int = self.add_item_dialog.get_priority()
            quantity: int = self.add_item_dialog.get_quantity()
            price: float = self.add_item_dialog.get_price()
            notes: str = self.add_item_dialog.get_notes()
            inventory.add_item_in_object(self.category, name)
            inventory.change_object_in_object_item(
                self.category, name, "quantity", quantity
            )
            inventory.change_object_in_object_item(self.category, name, "price", price)
            inventory.change_object_in_object_item(
                self.category, name, "priority", priority
            )
            inventory.change_object_in_object_item(self.category, name, "notes", notes)
            self.load_tab()
        elif response == DialogButtons.cancel:
            return

    def delete_item(self, category: str, item_name: QLineEdit) -> None:
        """
        It removes an item from the inventory

        Args:
          category (str): str
          item_name (QLineEdit): QLineEdit
        """
        inventory.remove_object_item(category, item_name.text())
        self.load_tab()

    def add_quantity(self, item_name: str, old_quantity: int) -> None:
        """
        It adds the value of the spinbox to the quantity of the item selected in the listwidget

        Args:
          item_name (str): str = the name of the item
          old_quantity (int): int = the quantity of the item before the change
        """
        category_data = inventory.get_value(item_name=self.category)
        quantity: int = category_data[item_name]["quantity"]
        self.value_change(
            self.category,
            item_name,
            "quantity",
            quantity + self.spinBox_quantity.value(),
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
        category_data = inventory.get_value(item_name=self.category)
        quantity: int = category_data[item_name]["quantity"]
        self.value_change(
            self.category,
            item_name,
            "quantity",
            quantity - self.spinBox_quantity.value(),
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
        selected_item: str = self.listWidget_itemnames.currentItem().text()
        category_data = inventory.get_value(item_name=self.category)
        try:
            quantity: int = category_data[selected_item]["quantity"]
        except KeyError:
            return
        self.last_item_selected = self.listWidget_itemnames.currentRow()

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
        self.spinBox_quantity.setValue(1)

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
        inventory.change_object_in_object_item(
            object_name=category,
            item_name=item_name,
            value_name=value_name,
            new_value=new_value,
        )

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
        self.dialog = AboutDialog(
            __name__,
            __version__,
            __updated__,
            "https://github.com/TheCodingJsoftware/Inventory-Manager",
        )
        self.dialog.show()

    def show_message_dialog(
        self, title: str, message: str, dialog_buttons: DialogButtons = DialogButtons.ok
    ) -> str:
        """
        It creates a message dialog, shows it, and returns the response

        Args:
          title (str): str = The title of the dialog
          message (str): str = The message to display in the dialog
          dialog_buttons (DialogButtons): DialogButtons = DialogButtons.ok

        Returns:
          The response is being returned.
        """
        self.message_dialog = MessageDialog(
            self, Icons.information, dialog_buttons, title, message
        )
        self.message_dialog.show()

        response: str = ""

        if self.message_dialog.exec_():
            response = self.message_dialog.get_response()

        return response

    def show_error_dialog(
        self,
        title: str,
        message: str,
        dialog_buttons: DialogButtons = DialogButtons.ok_save_copy_cancel,
    ) -> str:
        """
        It creates a dialog box with a message and a title, and returns the response

        Args:
          title (str): str = The title of the dialog
          message (str): str = The message to be displayed in the dialog.
          dialog_buttons (DialogButtons): DialogButtons = DialogButtons.ok_save_copy_cancel,

        Returns:
          The response from the dialog.
        """
        self.message_dialog = MessageDialog(
            self, Icons.critical, dialog_buttons, title, message
        )
        self.message_dialog.show()

        response: str = ""

        if self.message_dialog.exec_():
            response = self.message_dialog.get_response()

        if response == DialogButtons.copy:
            pixmap = QPixmap(self.message_dialog.grab())
            QApplication.clipboard().setPixmap(pixmap)
        elif response == DialogButtons.save:
            self.generate_error_log(message_dialog=self.message_dialog)
        return response

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
                self.show_message_dialog(
                    title=__name__,
                    message=f"There is a new update available.\n\nNew Version: {version}",
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
            if settings_file.get_value(item_name="last_toolbox_tab") == 0:
                self.lblStatus.setText(file_change.which_file_changed().title())
            else:
                self.lblStatus.setText("")
            os.remove("data/inventory - Compare.json")
        except Exception as e:
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

    def backup_database(self) -> None:
        """
        This function compresses the database file and shows a message dialog to the user
        """
        compress_database(path_to_file="data/inventory.json")
        self.show_message_dialog(title="Success", message="Backup was successful!")

    def close_event(self, event):
        """
        The function saves the geometry of the window and then closes the window

        Args:
          event: the event that triggered the close_event() method
        """
        self.save_geometry()
        super().close_event(event)

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
    check_setting(setting="dark_mode", default_value=False)
    check_setting(setting="server_ip", default_value="10.0.0.64")
    check_setting(setting="server_port", default_value=4000)
    check_setting(
        setting="geometry",
        default_value={"x": 200, "y": 200, "width": 600, "height": 400},
    )
    check_setting(setting="last_category_tab", default_value=0)
    check_setting(setting="last_toolbox_tab", default_value=0)


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
