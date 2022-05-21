# sourcery skip: avoid-builtin-shadow
__author__ = "Jared Gross"
__copyright__ = "Copyright 2022, TheCodingJ's"
__credits__: "list[str]" = ["Jared Gross"]
__license__ = "MIT"
__name__ = "Inventory Manager"
__version__ = "v0.0.1"
__updated__ = "2022-05-20 22:01:07"
__maintainer__ = "Jared Gross"
__email__ = "jared@pinelandfarms.ca"
__status__ = "Production"

import logging
import os
import shutil
import socket
import sys
import urllib
import urllib.request
from datetime import datetime, timedelta
from functools import partial

import requests
from PyQt5 import QtSvg, uic
from PyQt5.QtCore import (
    QCoreApplication,
    QFile,
    QProcess,
    QRunnable,
    QSettings,
    Qt,
    QTextStream,
    QThreadPool,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QFont, QIcon, QImage, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
    qApp,
)

import log_config
import ui.BreezeStyleSheets.breeze_resources
from about_dialog import AboutDialog
from add_item_dialog import AddItemDialog
from download_thread import DownloadThread
from input_dialog import InputDialog
from message_dialog import MessageDialog
from select_item_dialog import SelectItemDialog
from upload_thread import UploadThread
from utils.compress import compress_database, compress_folder
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile
from utils.json_object import JsonObject

settings_file = JsonFile(file_name="settings")
inventory = JsonFile(file_name="data/inventory")
geometry = JsonObject(JsonFile=settings_file, object_name="geometry")


class MainWindow(QMainWindow):
    """
    Main program
    """

    def __init__(self):
        super().__init__()
        uic.loadUi("ui/main_menu.ui", self)
        self.setWindowTitle(__name__)
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

        self.__load_ui()
        self.show()

    def __load_ui(self) -> None:
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
        self.pushButton_remove_quantity.clicked.connect(self.remove_quantity)
        self.pushButton_remove_quantity.setEnabled(False)
        self.listWidget_itemnames.itemSelectionChanged.connect(
            self.listWidget_item_changed
        )

        # Action events
        # HELP
        self.actionCheck_for_Updates.triggered.connect(self.check_for_updates)
        self.actionAbout_Qt.triggered.connect(qApp.aboutQt)
        self.actionAbout.triggered.connect(self.show_about_dialog)

        # SETTINGS
        self.actionDarkmode.setChecked(settings_file.get_value(item_name="dark_mode"))
        self.actionDarkmode.triggered.connect(self.toggle_dark_mode)

        # FILE
        # TODO MAKE THESE QMENUS
        self.actionUploadInventory.triggered.connect(
            partial(self.upload_file, "data/inventory.json")
        )
        self.actionDownloadInventory.triggered.connect(
            partial(self.download_file, "data/inventory.json")
        )
        for i, category in enumerate(self.categories):
            action = QAction(self)
            action.triggered.connect(partial(self.quick_load_category, i))
            action.setText(category)
            self.menuOpen_Category.addAction(action)
        self.actionBackup.triggered.connect(self.backup_database)
        self.actionExit.triggered.connect(self.close)

    def quick_load_category(self, index: int):
        self.tab_widget.setCurrentIndex(index)
        self.load_tab()

    def tool_box_menu_changed(self):
        if self.toolBox.currentIndex() != 0:
            self.dockWidget_create_add_remove.setVisible(False)
        else:
            self.dockWidget_create_add_remove.setVisible(True)
        settings_file.add_item("last_toolbox_tab", self.toolBox.currentIndex())

    def load_categories(self) -> None:
        self.clearLayout(self.verticalLayout)
        self.tabs.clear()
        self.categories = inventory.get_keys()
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
            self.clearLayout(self.tabs[tab_index])
        except IndexError:
            return
        settings_file.add_item("last_category_tab", tab_index)
        tab = self.tabs[tab_index]
        category_data = inventory.get_value(item_name=self.category)
        self.update_list_widget()
        self.label_category_name.setText(f"Category: {self.category}")

        # ! Some signals that are being used might be to performant heavy... may have to use on lost focus or something
        try:
            if list(category_data.keys()):
                headers = ["Name", "Quantity", "Price", "Priority", "Notes"]

                row_index: int = 0

                for i, header in enumerate(headers):
                    lbl_header = QLabel(header)
                    tab.addWidget(lbl_header, 0, i)

            for row_index, item in enumerate(list(category_data.keys()), start=1):
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
                btn_delete.setToolTip(f"Delete {item_name.text()} from {self.category}")
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
            return

    def update_list_widget(self):
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

    def create_new_category(self):
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

    def delete_category(self):
        self.select_item_dialog = SelectItemDialog(
            button_names=DialogButtons.delete_cancel,
            title="Delete category",
            message="Select a category to delete.",
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
        self.value_change(category, item_name.text(), value_name, quantity.value())

    def price_change(
        self, category: str, item_name: QLineEdit, value_name: str, price: QDoubleSpinBox
    ) -> None:
        self.value_change(category, item_name.text(), value_name, price.value())

    def priority_change(
        self, category: str, item_name: QLineEdit, value_name: str, combo: QComboBox
    ) -> None:
        self.value_change(category, item_name.text(), value_name, combo.currentIndex())

    def notes_changed(
        self, category: str, item_name: QLineEdit, value_name: str, note: QPlainTextEdit
    ) -> None:
        self.value_change(category, item_name.text(), value_name, note.toPlainText())

    def add_item(self) -> None:
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
        inventory.remove_object_item(category, item_name.text())
        self.load_tab()

    def add_quantity(self, item_name: str, old_quantity: int) -> None:
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
        inventory.change_object_in_object_item(
            object_name=category,
            item_name=item_name,
            value_name=value_name,
            new_value=new_value,
        )

    def save_geometry(self):
        geometry.set_value("x", value=self.pos().x())
        geometry.set_value("y", value=self.pos().y())
        geometry.set_value("width", value=self.size().width())
        geometry.set_value("height", value=self.size().height())

    def show_about_dialog(self) -> None:
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
        output_directory: str = (
            f"logs/ErrorLog_{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
        )
        check_folders([output_directory])
        pixmap = QPixmap(message_dialog.grab())
        pixmap.save(f"{output_directory}/screenshot.png")
        with open(f"{output_directory}/error.log", "w") as error_log:
            error_log.write(message_dialog.message)
        shutil.copyfile("logs/app.log", f"{output_directory}/app.log")
        compress_folder(foldername=output_directory, target_dir=output_directory)
        shutil.rmtree(output_directory)

    def toggle_dark_mode(self) -> None:
        settings_file.change_item(
            item_name="dark_mode", new_value=not settings_file.get_value("dark_mode")
        )

        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

        self.update_theme()

    def update_theme(self) -> None:
        file = QFile(f"ui/BreezeStyleSheets/dist/qrc/{self.theme}/stylesheet.qss")
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        self.setStyleSheet(stream.readAll())

    def check_for_updates(self, on_start_up: bool = False) -> None:
        try:
            response = requests.get(
                "https://api.github.com/repos/thecodingjsoftware/Inventory-Manager/releases/latest"
            )
            version: str = response.json()["name"].replace(" ", "")
            if version != __version__:
                self.show_message_dialog(
                    title=__name__, message="There is a new update available"
                )
            elif not on_start_up:
                self.show_message_dialog(
                    title=__name__, message="There are currently no updates available."
                )
        except Exception as e:
            if not on_start_up:
                self.show_message_dialog(title=__name__, message=f"Error\n\n{e}")

    def data_received(self, data) -> None:
        if data == "Successfully uploaded":
            self.show_message_dialog(
                title=data,
                message=f"{data}\n\nDatabase successfully uploaded.\nWill take roughly 5 minutes to update database",
            )
            logging.info(f"Server: {data}")
        elif data == "Successfully downloaded":
            self.show_message_dialog(
                title=data,
                message=f"{data}\n\nDatabase successfully downloaded.",
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

    def upload_file(self, file_to_upload: str) -> None:
        self.threads = []
        upload_thread = UploadThread(file_to_upload)
        self.start_thread(upload_thread)

    def download_file(self, file_to_download: str) -> None:
        self.threads = []
        download_thread = DownloadThread(file_to_download)
        self.start_thread(download_thread)

    def start_thread(self, thread) -> None:
        thread.signal.connect(self.data_received)
        self.threads.append(thread)
        thread.start()

    def backup_database(self) -> None:
        compress_database(path_to_file="data/inventory.json")
        self.show_message_dialog(title="Success", message="Backup was successful!")

    def closeEvent(self, event):
        self.save_geometry()
        super().closeEvent(event)

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())


def default_settings() -> None:
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
    if settings_file.get_value(item_name=setting) is None:
        settings_file.add_item(item_name=setting, value=default_value)


def check_folders(folders: list) -> None:
    for folder in folders:
        if not os.path.exists(f"{os.path.dirname(os.path.realpath(__file__))}/{folder}"):
            os.makedirs(f"{os.path.dirname(os.path.realpath(__file__))}/{folder}")


def main() -> None:
    default_settings()
    check_folders(folders=["logs", "data", "backups"])
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


# if __name__ == "__main__":
main()
