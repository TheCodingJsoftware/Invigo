import contextlib
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QSpinBox, QTreeView,
                             QWidget)

from ui.custom_widgets import MultiToolBox
from utils.workspace.assembly import Assembly
from utils.workspace.workspace import Workspace


class GenerateWorkorderDialog(QDialog):
    def __init__(
        self,
        admin_workspace: Workspace,
        job_names: dict[str, int],
        parent,
    ) -> None:
        super(GenerateWorkorderDialog, self).__init__(parent)
        uic.loadUi("ui/generate_workorder_dialog.ui", self)
        self.admin_workspace = admin_workspace

        self.selected_assemblies: list[Assembly] = []
        self.models: list[QStandardItemModel] = []
        self.workorder: dict[Assembly, int] = {}
        self.job_names = job_names
        self.data: dict[int, Assembly] = {}
        self.assembly_count: int = 0

        self.setWindowTitle("Workorder Generator")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.group_toolbox = MultiToolBox(self)
        self.group_toolboxes = {}
        self.treeLayout.addWidget(self.group_toolbox)

        self.pushButton_generate.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.verticalLayout_workorders.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.load_layout()

    def load_layout(self) -> None:
        grouped_data = self.admin_workspace._get_all_groups()
        for group in grouped_data:
            treeview = self.create_treeview()
            self.group_toolbox.addItem(treeview, group, base_color=self.admin_workspace.get_group_color(group))
            self.group_toolboxes[group] = treeview
        self.group_toolbox.close_all()

        grouped_data = self.admin_workspace._get_grouped_data()
        for group in grouped_data:
            for assembly in grouped_data[group]:
                self.load_treeview(
                    self.group_toolboxes[group],
                    self.group_toolboxes[group].model(),
                    assembly,
                )

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
            if item.parent() is not None and self.are_all_children_checked(item.parent()):
                item.parent().setCheckState(Qt.CheckState.Checked)

    def get_topmost_checked_items_rows(self, model: QStandardItemModel) -> list[str]:
        topmost_checked_items: list[QStandardItem] = []
        for row in range(model.rowCount()):
            parent_item = model.item(row)
            if parent_item and parent_item.checkState() == Qt.CheckState.Checked:
                topmost_checked_items.append(model.item(row, 1))
            self.find_topmost_checked_items(parent_item, topmost_checked_items)
        return [item.text() for item in topmost_checked_items]

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
                self.selected_assemblies.append(self.data[int(row) - 1])  # Need to offset because ID starts at 1
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
            quantity_spin_box.setValue(0)
            quantity_spin_box.setMinimum(0)
            quantity_spin_box.setMaximum(99999999)

            def update_quantity(assembly: Assembly, quantity_spin_box: QSpinBox):
                self.workorder[assembly] = quantity_spin_box.value()

            quantity_spin_box.valueChanged.connect(partial(update_quantity, assembly, quantity_spin_box))

            h_layout.addWidget(QLabel(assembly.name, self))
            h_layout.addWidget(quantity_spin_box)

            self.verticalLayout_workorders.addWidget(widget)

    def get_selected_item(self) -> tuple[bool, bool, bool, bool]:
        return (
            self.pushButton_quote.isChecked(),
            self.pushButton_workorder.isChecked(),
            self.pushButton_update_inventory.isChecked(),
            self.pushButton_packingslip.isChecked(),
        )

    def clear_layout(self, layout) -> None:
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
