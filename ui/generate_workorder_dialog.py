import contextlib
import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QFile, Qt, QTextStream
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTreeView,
    QTreeWidget,
    QWidget,
)

from ui.custom_widgets import MultiToolBox, set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile
from utils.workspace.assembly import Assembly
from utils.workspace.workspace import Workspace

settings_file = JsonFile(file_name="settings")
admin_workspace = Workspace("workspace - Admin")

class GenerateWorkorderDialog(QDialog):
    """
    Select dialog
    """

    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.question,
        button_names: str = DialogButtons.generate_cancel,
        title: str = __name__,
        message: str = "",
        job_names: dict[str, int] = {},
    ) -> None:
        """
        It's a function that takes in a list of options and displays them in a list widget

        Args:
          parent: The parent widget of the dialog.
          icon_name (str): str = Icons.question,
          button_names (str): str = DialogButtons.ok_cancel,
          title (str): str = __name__,
          message (str): str = "",
          options (list): list = None,
        """
        super(GenerateWorkorderDialog, self).__init__(parent)
        uic.loadUi("ui/generate_workorder_dialog.ui", self)
        admin_workspace.load_data()

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message
        self.inputText: str = ""
        self.theme: str = "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        self.selected_assemblies: list[Assembly] = []
        self.models: list[QStandardItemModel] = []
        self.workorder: dict[Assembly, int] = {}
        self.job_names = job_names
        self.data: dict[int, Assembly] = {}
        self.assembly_count: int = 0

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowIcon(QIcon("icons/icon.png"))
        self.group_toolbox = MultiToolBox(self)
        self.group_toolboxes = {}
        self.treeLayout.addWidget(self.group_toolbox)

        self.lblTitle.setText(self.title)
        self.lblMessage.setText(self.message)

        self.load_dialog_buttons()

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        # self.resize(320, 250)

        self.load_theme()
        self.verticalLayout_workorders.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.load_layout()

    def load_layout(self) -> None:
        grouped_data = admin_workspace._get_all_groups()
        for group in grouped_data:
            treeview = self.create_treeview()
            self.group_toolbox.addItem(treeview, group, base_color=admin_workspace.get_group_color(group))
            self.group_toolboxes[group] = treeview
        self.group_toolbox.close_all()

        grouped_data = admin_workspace._get_grouped_data()
        for group in grouped_data:
            for assembly in grouped_data[group]:
                self.load_treeview(self.group_toolboxes[group], self.group_toolboxes[group].model(), assembly)

    def create_treeview(self) -> QTreeView:
        model = QStandardItemModel()
        self.models.append(model)
        tree_view = QTreeView()
        tree_view.setMinimumHeight(200)
        model.setHorizontalHeaderLabels(["NAME", "ID"])
        tree_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tree_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tree_view.setModel(model)
        tree_view.setHeaderHidden(True)
        tree_view.setColumnWidth(0, 1000)  # Adjust the width of the first column
        tree_view.expandAll()
        tree_view.model().itemChanged.connect(self.update_parent_state)
        tree_view.clicked.connect(self.get_selected_assemblies)
        return tree_view

    def load_treeview(self, tree_view: QTreeView, model: QStandardItemModel, assembly: Assembly):
        # for assembly in admin_workspace.data:
        parent_item = self.create_item_with_checkbox(assembly.name)
        self.data[self.assembly_count] = assembly
        self.assembly_count += 1
        model.appendRow([parent_item, QStandardItem(str(self.assembly_count))])
        if len(assembly.sub_assemblies) > 0:
            self.add_items_to_model(parent_item, assembly)

    def add_items_to_model(self, parent_item: QStandardItem, sub_assembly: Assembly):
        for _sub_assembly in sub_assembly.sub_assemblies:
            item_with_checkbox = self.create_item_with_checkbox(_sub_assembly.name)
            self.data[self.assembly_count] = _sub_assembly
            self.assembly_count += 1
            parent_item.appendRow([item_with_checkbox, QStandardItem(str(self.assembly_count))])
            if len(_sub_assembly.sub_assemblies) > 0:
                self.add_items_to_model(item_with_checkbox, _sub_assembly)

    def create_item_with_checkbox(self, name: str) -> QStandardItem:
        item = QStandardItem(name)
        item.setCheckable(True)
        return item

    def update_child_items(self, item: QStandardItem):
        check_state = item.checkState()
        for row in range(item.rowCount()):
            child_item = item.child(row)
            child_item.setCheckState(check_state)
            self.update_child_items(child_item)

    def are_all_children_checked(self, parent_item: QStandardItem) -> bool:
        for row in range(parent_item.rowCount()):
            child_item = parent_item.child(row)
            if child_item.checkState() == Qt.CheckState.Unchecked:
                return False
        return True

    def update_parent_state(self, item: QStandardItem):
        if item.checkState() == Qt.CheckState.Unchecked:
            if item is None or item.parent() is None:
                return
            parent_item = item.parent() if item.parent() is not None else item
            if self.are_all_children_checked(parent_item):
                parent_item.setCheckState(Qt.CheckState.Checked)
                item.setCheckState(Qt.CheckState.Checked)
            else:
                parent_item.setCheckState(Qt.CheckState.Unchecked)
                self.update_parent_state(parent_item)
        elif item.checkState() == Qt.CheckState.Checked:
            self.update_child_items(item)
            if item.parent() is not None:
                if self.are_all_children_checked(item.parent()):
                    item.parent().setCheckState(Qt.CheckState.Checked)

    def get_topmost_checked_items_rows(self, model: QStandardItemModel) -> list[str]:
        topmost_checked_items: list[QStandardItem] = []
        for row in range(model.rowCount()):
            parent_item = model.item(row)
            if parent_item and parent_item.checkState() == Qt.CheckState.Checked:
                topmost_checked_items.append(model.item(row, 1))
            self.find_topmost_checked_items(parent_item, topmost_checked_items)
        return  [item.text() for item in topmost_checked_items]

    def find_topmost_checked_items(self, parent_item: QStandardItem, topmost_checked_items: list[str]):
        for row in range(parent_item.rowCount()):
            child_item = parent_item.child(row)
            if child_item and child_item.checkState() == Qt.CheckState.Checked and child_item.parent().checkState() == Qt.CheckState.Unchecked:
                topmost_checked_items.append(parent_item.child(row, 1))
            self.find_topmost_checked_items(child_item, topmost_checked_items)

    def get_selected_assemblies(self) -> list[Assembly]:
        self.selected_assemblies.clear()
        for model in self.models:
            selected_rows: list[str] = self.get_topmost_checked_items_rows(model)
            for row in selected_rows:
                self.selected_assemblies.append(self.data[int(row)-1]) # Need to offset because ID starts at 1
        self.load_jobs()

    def get_workorder(self) -> dict[Assembly, int]:
        return self.workorder

    def load_jobs(self) -> None:
        self.clear_layout(self.verticalLayout_workorders)
        self.workorder.clear()
        for assembly in self.selected_assemblies:
            self.workorder[assembly] = 0
            widget = QWidget(self)
            h_layout = QHBoxLayout()
            h_layout.setSpacing(0)
            h_layout.setContentsMargins(0, 0, 0, 5)
            widget.setLayout(h_layout)
            quantity_spin_box = QSpinBox(self)
            quantity_spin_box.setValue(1)
            quantity_spin_box.setMinimum(1)
            quantity_spin_box.setMaximum(99999999)

            def update_quantity(assembly: Assembly, quantity_spin_box: QSpinBox):
                self.workorder[assembly] = quantity_spin_box.value()

            quantity_spin_box.valueChanged.connect(partial(update_quantity, assembly, quantity_spin_box))

            h_layout.addWidget(QLabel(assembly.name, self))
            h_layout.addWidget(quantity_spin_box)

            self.verticalLayout_workorders.addWidget(widget)
    def load_theme(self) -> None:
        """
        It loads the stylesheet.qss file from the theme folder
        """
        set_theme(self, theme="dark")

    def get_icon(self, path_to_icon: str) -> QSvgWidget:
        """
        It returns a QSvgWidget object that is initialized with a path to an SVG icon

        Args:
          path_to_icon (str): The path to the icon you want to use.

        Returns:
          A QSvgWidget object.
        """
        return QSvgWidget(f"icons/{path_to_icon}")

    def button_press(self, button) -> None:
        """
        The function is called when a button is pressed. It sets the response to the text of the button
        and then closes the dialog

        Args:
          button: The button that was clicked.
        """
        self.response = button.text()
        self.accept()

    def load_dialog_buttons(self) -> None:
        """
        It takes a string of button names, splits them into a list, and then creates a button for each
        name in the list
        """
        button_names = self.button_names.split(", ")
        for index, name in enumerate(button_names):
            if name == DialogButtons.generate:
                button = QPushButton(f"  {name}")
                button.setIcon(QIcon(f"icons/dialog_ok.svg"))
            elif os.path.isfile(f"icons/dialog_{name.lower()}.svg"):
                button = QPushButton(f"  {name}")
                button.setIcon(QIcon(f"icons/dialog_{name.lower()}.svg"))
            else:
                button = QPushButton(name)
            if index == 0:
                button.setObjectName("default_dialog_button")
                set_default_dialog_button_stylesheet(button)
            button.setFixedWidth(100)
            if name == DialogButtons.copy:
                button.setToolTip("Will copy this window to your clipboard.")
            elif name == DialogButtons.save and self.icon_name == Icons.critical:
                button.setToolTip("Will save this error log to the logs directory.")
            button.clicked.connect(partial(self.button_press, button))
            self.buttonsLayout.addWidget(button)

    def get_response(self) -> str:
        """
        This function returns the response of the class

        Returns:
          The response
        """
        return self.response.replace(" ", "")

    def get_selected_item(self) -> tuple[bool, bool, bool, bool]:
        """
        This function returns a tuple of boolean values indicating which push buttons are checked.

        Returns:
          A tuple containing three boolean values representing whether the corresponding push button
        (quote, work order, update inventory) is checked or not.
        """
        return (
            self.pushButton_quote.isChecked(),
            self.pushButton_workorder.isChecked(),
            self.pushButton_update_inventory.isChecked(),
            self.pushButton_packingslip.isChecked(),
        )

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