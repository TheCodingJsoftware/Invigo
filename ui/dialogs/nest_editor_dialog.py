import contextlib
from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING

from natsort import natsorted
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.dialogs.nest_editor_dialog_UI import Ui_Form
from ui.icons import Icons
from ui.widgets.nest_editor_widget import NestEditorWidget
from utils.inventory.nest import Nest

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class NestEditorDialog(QDialog, Ui_Form):
    def __init__(
        self,
        nests: list[Nest],
        parent=None,
    ):
        super().__init__(parent)
        self.parent: MainWindow = parent
        self.setupUi(self)

        self.nests = natsorted(nests, key=lambda nest: nest.name)
        self.sheet_settings = self.parent.sheet_settings
        self.laser_cut_inventory = self.parent.laser_cut_inventory
        self.deep_copy_nests = deepcopy(self.nests)
        self.nest_widgets: dict[Nest, NestEditorWidget] = {}

        self.load_ui()

    def load_ui(self):
        self.setWindowTitle(f"Nest Editor ({len(self.nests)})")
        self.setWindowIcon(QIcon(Icons.invigo_icon))
        self.setWindowFlags(
            Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.Dialog
        )
        self.resize(1600, 1000)

        self.showMaximized()

        self.buttonBox.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self.accept
        )
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(
            self.reset
        )

        self.comboBox_nests_sheet_material.addItems(self.sheet_settings.get_materials())
        self.comboBox_nests_sheet_thickness.addItems(
            self.sheet_settings.get_thicknesses()
        )

        self.comboBox_cutting_method.currentTextChanged.connect(
            self.on_cutting_method_changed
        )
        self.comboBox_cutting_method.wheelEvent = lambda event: self.wheelEvent(event)

        self.comboBox_nests_sheet_material.currentTextChanged.connect(
            self.on_nest_sheet_material_changed
        )
        self.comboBox_nests_sheet_material.wheelEvent = lambda event: self.wheelEvent(
            event
        )

        self.comboBox_nests_sheet_thickness.currentTextChanged.connect(
            self.on_nest_sheet_thickness_changed
        )
        self.comboBox_nests_sheet_thickness.wheelEvent = lambda event: self.wheelEvent(
            event
        )

        self.doubleSpinBox_nests_sheet_length.valueChanged.connect(
            self.on_nest_sheet_length_changed
        )
        self.doubleSpinBox_nests_sheet_length.wheelEvent = (
            lambda event: self.wheelEvent(event)
        )

        self.doubleSpinBox_nests_sheet_width.valueChanged.connect(
            self.on_nest_sheet_width_changed
        )
        self.doubleSpinBox_nests_sheet_width.wheelEvent = lambda event: self.wheelEvent(
            event
        )

        self.verticalLayout_nests.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.pushButton_add_nest.clicked.connect(self.add_new_nest)

        self.load_nests()

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

    def reset(self):
        msg = QMessageBox(
            QMessageBox.Icon.Question,
            "Reset Nests",
            "Are you sure you want to reset the nests?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
            self,
        )
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.nests.clear()
            self.nests = deepcopy(self.deep_copy_nests)
            self.load_nests()

    def load_nests(self):
        self.clear_layout(self.verticalLayout_nests)
        self.nest_widgets.clear()
        for nest in self.nests:
            nest_widget = NestEditorWidget(nest, self)
            nest_widget.sheetSettingsChanged.connect(self.on_sheet_settings_changed)
            nest_widget.pushButton_delete.clicked.connect(
                partial(self.delete_nest, nest)
            )
            self.verticalLayout_nests.addWidget(nest_widget)
            self.nest_widgets[nest] = nest_widget
        self.update_nest_summary()

    def add_new_nest(self):
        new_nest = Nest({}, self.sheet_settings, self.laser_cut_inventory)
        self.nests.append(new_nest)
        nest_widget = NestEditorWidget(new_nest, self)
        nest_widget.sheetSettingsChanged.connect(self.on_sheet_settings_changed)
        nest_widget.pushButton_delete.clicked.connect(
            partial(self.delete_nest, new_nest)
        )
        self.verticalLayout_nests.addWidget(nest_widget)
        self.nest_widgets[new_nest] = nest_widget
        self.update_nest_summary()

    def on_cutting_method_changed(self, new_cutting_method: str):
        for nest in self.nests:
            self.nest_widgets[nest].comboBox_cutting_method.blockSignals(True)
            self.nest_widgets[nest].comboBox_cutting_method.setCurrentText(
                new_cutting_method
            )
            self.nest_widgets[nest].comboBox_cutting_method.blockSignals(False)
            self.nest_widgets[nest].cutting_method_changed(new_cutting_method)
        self.update_nest_summary()

    def on_nest_sheet_material_changed(self, new_material: str):
        for nest in self.nests:
            self.nest_widgets[nest].comboBox_sheet_material.blockSignals(True)
            self.nest_widgets[nest].comboBox_sheet_material.setCurrentText(new_material)
            self.nest_widgets[nest].comboBox_sheet_material.blockSignals(False)
            self.nest_widgets[nest].sheet_material_changed(new_material)
        self.update_nest_summary()

    def on_nest_sheet_thickness_changed(self, new_thickness: str):
        for nest in self.nests:
            self.nest_widgets[nest].comboBox_sheet_thickness.blockSignals(True)
            self.nest_widgets[nest].comboBox_sheet_thickness.setCurrentText(
                new_thickness
            )
            self.nest_widgets[nest].comboBox_sheet_thickness.blockSignals(False)
            self.nest_widgets[nest].sheet_thickness_changed(new_thickness)
        self.update_nest_summary()

    def on_nest_sheet_length_changed(self, new_length: float):
        for nest in self.nests:
            self.nest_widgets[nest].doubleSpinBox_sheet_length.blockSignals(True)
            self.nest_widgets[nest].doubleSpinBox_sheet_length.setValue(new_length)
            self.nest_widgets[nest].doubleSpinBox_sheet_length.blockSignals(False)
            self.nest_widgets[nest].sheet_length_changed(new_length)
        self.update_nest_summary()

    def on_nest_sheet_width_changed(self, new_width: float):
        for nest in self.nests:
            self.nest_widgets[nest].doubleSpinBox_sheet_width.blockSignals(True)
            self.nest_widgets[nest].doubleSpinBox_sheet_width.setValue(new_width)
            self.nest_widgets[nest].doubleSpinBox_sheet_width.blockSignals(False)
            self.nest_widgets[nest].sheet_width_changed(new_width)
        self.update_nest_summary()

    def on_sheet_settings_changed(self):
        self.update_nest_summary()

    def update_nest_summary(self):
        summary_data = {"sheets": {}, "material_total": {}}
        for nest in self.nests:
            if not nest.laser_cut_parts:
                continue
            summary_data["sheets"].setdefault(
                nest.sheet.get_name(), {"total_sheet_count": 0, "total_seconds": 0}
            )
            summary_data["material_total"].setdefault(
                nest.sheet.material, {"total_sheet_count": 0, "total_seconds": 0}
            )
            summary_data["sheets"][nest.sheet.get_name()]["total_sheet_count"] += (
                nest.sheet_count
            )
            summary_data["sheets"][nest.sheet.get_name()]["total_seconds"] += (
                nest.sheet_cut_time * nest.sheet_count
            )
            summary_data["material_total"][nest.sheet.material]["total_seconds"] += (
                nest.sheet_cut_time * nest.sheet_count
            )
            summary_data["material_total"][nest.sheet.material][
                "total_sheet_count"
            ] += nest.sheet_count

            self.treeWidget_nest_summary.clear()
            self.treeWidget_nest_summary.setHeaderLabels(
                ["Name", "Quantity", "Cut time"]
            )

            sorted_summary_keys = natsorted(summary_data.keys())
            sorted_summary = {key: summary_data[key] for key in sorted_summary_keys}

            for sheet, data in sorted_summary.get("sheets", {}).items():
                hours = int(data["total_seconds"] // 3600)
                minutes = int((data["total_seconds"] % 3600) // 60)
                seconds = int(data["total_seconds"] % 60)
                total_seconds_string = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
                item = QTreeWidgetItem(
                    [sheet, str(data["total_sheet_count"]), total_seconds_string]
                )
                self.treeWidget_nest_summary.addTopLevelItem(item)

            materials_item = QTreeWidgetItem(
                self.treeWidget_nest_summary, ["Materials Total"]
            )
            materials_item.setFirstColumnSpanned(True)
            for material, data in sorted_summary.get("material_total", {}).items():
                hours = int(data["total_seconds"] // 3600)
                minutes = int((data["total_seconds"] % 3600) // 60)
                seconds = int(data["total_seconds"] % 60)
                total_seconds_string = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
                item = QTreeWidgetItem(
                    [material, str(data["total_sheet_count"]), total_seconds_string]
                )
                materials_item.addChild(item)

            self.treeWidget_nest_summary.expandAll()
            self.treeWidget_nest_summary.resizeColumnToContents(0)
            self.treeWidget_nest_summary.resizeColumnToContents(1)

    def sync_changes(self):
        self.parent.sync_changes("nest_editor")

    def delete_nest(self, nest: Nest):
        self.nest_widgets[nest].deleteLater()
        self.clear_layout(self.nest_widgets[nest])
        self.nests.remove(nest)
        self.update_nest_summary()

    def clear_layout(self, layout: QVBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
