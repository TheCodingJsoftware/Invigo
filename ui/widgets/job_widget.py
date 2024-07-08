import contextlib
from functools import partial
from typing import TYPE_CHECKING

from natsort import natsorted
from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.group_widget import GroupWidget
from ui.custom_widgets import AssemblyMultiToolBox, MultiToolBox, QLineEdit
from ui.widgets.nest_widget import NestWidget
from utils import colors
from utils.colors import darken_color, lighten_color
from utils.inventory.nest import Nest
from utils.workspace.group import Group
from utils.workspace.job import Job, JobStatus, JobColor

if TYPE_CHECKING:
    from ui.custom.job_tab import JobTab


class JobWidget(QWidget):
    reloadJob = pyqtSignal(object)  # object -> JobWidget

    def __init__(self, job: Job, parent) -> None:
        super().__init__(parent)
        uic.loadUi("ui/widgets/job_widget.ui", self)

        self.parent: JobTab = parent
        self.job = job
        self.job_preferences = self.parent.job_preferences
        self.sheet_settings = self.parent.parent.sheet_settings
        self.paint_inventory = self.parent.parent.paint_inventory
        self.price_calculator = self.job.price_calculator

        self.group_widgets: list[GroupWidget] = []
        self.nest_widgets: list[NestWidget] = []
        self.nest_laser_cut_parts_assembly_comboboxes: list[QComboBox] = []

        self.load_ui()

    def load_ui(self):
        self.verticalLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.gridLayout_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_8.setAlignment(Qt.AlignmentFlag.AlignTop)


        self.item_quoting_options_layout = self.findChild(QVBoxLayout, "item_quoting_options_layout")
        self.item_quoting_options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.gridLayout_4 = self.findChild(QGridLayout, "gridLayout_4")
        self.gridLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.nest_summary_layout = self.findChild(QVBoxLayout, "nest_summary_layout")
        self.nest_summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.treeWidget_nest_summary = self.findChild(QTreeWidget, "treeWidget_nest_summary")

        self.pushButton_global_sheet_settings = self.findChild(QPushButton, "pushButton_global_sheet_settings")
        self.global_sheet_settings_widget = self.findChild(QWidget, "global_sheet_settings_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_global_sheet_settings, self.global_sheet_settings_widget)

        self.pushButton_item_quoting_options = self.findChild(QPushButton, "pushButton_item_quoting_options")
        self.item_quoting_options_widget = self.findChild(QWidget, "item_quoting_options_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_item_quoting_options, self.item_quoting_options_widget)

        self.pushButton_sheet_quoting_options = self.findChild(QPushButton, "pushButton_sheet_quoting_options")
        self.sheet_quoting_options_widget = self.findChild(QWidget, "sheet_quoting_options_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_sheet_quoting_options, self.sheet_quoting_options_widget)

        self.pushButton_nests = self.findChild(QPushButton, "pushButton_nests")
        self.nests_widget = self.findChild(QWidget, "nests_widget")
        self.nests_layout = self.findChild(QVBoxLayout, "nests_layout")
        self.nests_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_nests, self.nests_widget)

        self.pushButton_nest_summary = self.findChild(QPushButton, "pushButton_nest_summary")
        self.nest_summary_widget = self.findChild(QWidget, "nest_summary_widget")
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_nest_summary, self.nest_summary_widget)

        self.pushButton_global_sheet_settings.clicked.connect(
            partial(
                self.job_preferences.job_nest_tool_box_toggled,
                self.job.name,
                self.pushButton_global_sheet_settings,
                self.pushButton_item_quoting_options,
                self.pushButton_sheet_quoting_options,
                self.pushButton_nest_summary,
                self.pushButton_nests,
            )
        )
        self.pushButton_item_quoting_options.clicked.connect(
            partial(
                self.job_preferences.job_nest_tool_box_toggled,
                self.job.name,
                self.pushButton_global_sheet_settings,
                self.pushButton_item_quoting_options,
                self.pushButton_sheet_quoting_options,
                self.pushButton_nest_summary,
                self.pushButton_nests,
            )
        )
        self.pushButton_sheet_quoting_options.clicked.connect(
            partial(
                self.job_preferences.job_nest_tool_box_toggled,
                self.job.name,
                self.pushButton_global_sheet_settings,
                self.pushButton_item_quoting_options,
                self.pushButton_sheet_quoting_options,
                self.pushButton_nest_summary,
                self.pushButton_nests,
            )
        )
        self.pushButton_nests.clicked.connect(
            partial(
                self.job_preferences.job_nest_tool_box_toggled,
                self.job.name,
                self.pushButton_global_sheet_settings,
                self.pushButton_item_quoting_options,
                self.pushButton_sheet_quoting_options,
                self.pushButton_nest_summary,
                self.pushButton_nests,
            )
        )
        self.pushButton_nest_summary.clicked.connect(
            partial(
                self.job_preferences.job_nest_tool_box_toggled,
                self.job.name,
                self.pushButton_global_sheet_settings,
                self.pushButton_item_quoting_options,
                self.pushButton_sheet_quoting_options,
                self.pushButton_nest_summary,
                self.pushButton_nests,
            )
        )

        self.pushButton_global_sheet_settings.setChecked(self.job_preferences.is_global_sheet_settings_closed(self.job.name))
        self.global_sheet_settings_widget.setHidden(not self.job_preferences.is_global_sheet_settings_closed(self.job.name))
        self.pushButton_item_quoting_options.setChecked(self.job_preferences.is_item_quoting_options_closed(self.job.name))
        self.item_quoting_options_widget.setHidden(not self.job_preferences.is_item_quoting_options_closed(self.job.name))
        self.pushButton_sheet_quoting_options.setChecked(self.job_preferences.is_sheet_quoting_options_closed(self.job.name))
        self.sheet_quoting_options_widget.setHidden(not self.job_preferences.is_sheet_quoting_options_closed(self.job.name))
        self.pushButton_nest_summary.setChecked(self.job_preferences.is_nest_summary_closed(self.job.name))
        self.nest_summary_widget.setHidden(not self.job_preferences.is_nest_summary_closed(self.job.name))
        self.pushButton_nests.setChecked(self.job_preferences.is_nests_closed(self.job.name))
        self.nests_widget.setHidden(not self.job_preferences.is_nests_closed(self.job.name))

        # TODO: Save close close/opened nest

        self.scrollArea = self.findChild(QScrollArea, "scrollArea")

        self.pushButton_reload_job = self.findChild(QPushButton, "pushButton_reload_job")
        self.pushButton_reload_job.clicked.connect(self.reload_job)

        self.doubleSpinBox_order_number: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_order_number")
        self.doubleSpinBox_order_number.setValue(self.job.order_number)
        self.doubleSpinBox_order_number.wheelEvent = lambda event: None
        self.doubleSpinBox_order_number.valueChanged.connect(self.job_settings_changed)
        self.pushButton_get_order_number: QPushButton = self.findChild(QPushButton, "pushButton_get_order_number")

        def get_latest_order_number():
            self.doubleSpinBox_order_number.setValue(self.parent.parent.order_number)
            self.job_settings_changed()

        self.pushButton_get_order_number.clicked.connect(get_latest_order_number)

        self.comboBox_type: QComboBox = self.findChild(QComboBox, "comboBox_type")
        self.comboBox_type.setCurrentIndex(self.job.status.value - 1)
        self.comboBox_type.wheelEvent = lambda event: None
        self.comboBox_type.currentTextChanged.connect(self.job_settings_changed)
        self.dateEdit_shipped: QDateEdit = self.findChild(QDateEdit, "dateEdit_shipped")
        try:
            year, month, day = map(int, self.job.date_shipped.split("-"))
            self.dateEdit_shipped.setDate(QDate(year, month, day))
        except ValueError:
            self.dateEdit_shipped.setDate(QDate.currentDate())
        self.dateEdit_shipped.dateChanged.connect(self.job_settings_changed)
        self.dateEdit_shipped.wheelEvent = lambda event: None
        self.dateEdit_expected: QDateEdit = self.findChild(QDateEdit, "dateEdit_expected")
        try:
            year, month, day = map(int, self.job.date_expected.split("-"))
            self.dateEdit_expected.setDate(QDate(year, month, day))
        except ValueError:
            self.dateEdit_expected.setDate(QDate.currentDate())
        self.dateEdit_expected.dateChanged.connect(self.job_settings_changed)
        self.dateEdit_expected.wheelEvent = lambda event: None
        self.textEdit_ship_to: QTextEdit = self.findChild(QTextEdit, "textEdit_ship_to")
        self.textEdit_ship_to.setText(self.job.ship_to)
        self.textEdit_ship_to.textChanged.connect(self.job_settings_changed)

        self.groups_layout = self.findChild(QVBoxLayout, "groups_layout")
        self.groups_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.add_group_button = self.findChild(QPushButton, "add_group_button")
        self.add_group_button.clicked.connect(self.add_group)

        self.groups_toolbox = AssemblyMultiToolBox(self)
        self.groups_layout.addWidget(self.groups_toolbox)

        self.comboBox_laser_cutting = self.findChild(QComboBox, "comboBox_laser_cutting")
        self.comboBox_laser_cutting.wheelEvent = lambda event: None

        self.doubleSpinBox_cost_for_laser = self.findChild(QDoubleSpinBox, "doubleSpinBox_cost_for_laser")
        self.doubleSpinBox_cost_for_laser.setValue(self.price_calculator.cost_for_laser)
        self.doubleSpinBox_cost_for_laser.valueChanged.connect(self.cost_for_laser_changed)
        self.doubleSpinBox_cost_for_laser.wheelEvent = lambda event: None

        self.comboBox_materials = self.findChild(QComboBox, "comboBox_materials")
        self.comboBox_materials.wheelEvent = lambda event: None
        self.comboBox_materials.addItems(self.sheet_settings.get_materials())
        self.comboBox_materials.currentTextChanged.connect(partial(self.update_nest_sheets, "MATERIAL"))

        self.comboBox_thicknesses = self.findChild(QComboBox, "comboBox_thicknesses")
        self.comboBox_thicknesses.wheelEvent = lambda event: None
        self.comboBox_thicknesses.addItems(self.sheet_settings.get_thicknesses())
        self.comboBox_thicknesses.currentTextChanged.connect(partial(self.update_nest_sheets, "THICKNESS"))

        self.doubleSpinBox_length = self.findChild(QDoubleSpinBox, "doubleSpinBox_length")
        self.doubleSpinBox_length.wheelEvent = lambda event: None
        self.doubleSpinBox_length.valueChanged.connect(partial(self.update_nest_sheets, "LENGTH"))

        self.doubleSpinBox_width = self.findChild(QDoubleSpinBox, "doubleSpinBox_width")
        self.doubleSpinBox_width.wheelEvent = lambda event: None
        self.doubleSpinBox_width.valueChanged.connect(partial(self.update_nest_sheets, "WIDTH"))

        self.doubleSpinBox_items_overhead = self.findChild(QDoubleSpinBox, "doubleSpinBox_items_overhead")
        self.doubleSpinBox_items_overhead.wheelEvent = lambda event: None
        self.doubleSpinBox_items_overhead.setValue(self.price_calculator.item_overhead * 100)
        self.doubleSpinBox_items_overhead.valueChanged.connect(self.price_settings_changed)

        self.doubleSpinBox_items_profit_margin = self.findChild(QDoubleSpinBox, "doubleSpinBox_items_profit_margin")
        self.doubleSpinBox_items_profit_margin.wheelEvent = lambda event: None
        self.doubleSpinBox_items_profit_margin.setValue(self.price_calculator.item_profit_margin * 100)
        self.doubleSpinBox_items_profit_margin.valueChanged.connect(self.price_settings_changed)

        self.pushButton_item_to_sheet = self.findChild(QPushButton, "pushButton_item_to_sheet")
        self.pushButton_item_to_sheet.setChecked(self.price_calculator.match_item_cogs_to_sheet)
        self.pushButton_item_to_sheet.clicked.connect(self.match_item_to_sheet_toggled)

        self.doubleSpinBox_sheets_overhead = self.findChild(QDoubleSpinBox, "doubleSpinBox_sheets_overhead")
        self.doubleSpinBox_sheets_overhead.wheelEvent = lambda event: None
        self.doubleSpinBox_sheets_overhead.setValue(self.price_calculator.sheet_overhead * 100)
        self.doubleSpinBox_sheets_overhead.valueChanged.connect(self.price_settings_changed)

        self.doubleSpinBox_sheets_profit_margin = self.findChild(QDoubleSpinBox, "doubleSpinBox_sheets_profit_margin")
        self.doubleSpinBox_sheets_profit_margin.wheelEvent = lambda event: None
        self.doubleSpinBox_sheets_profit_margin.setValue(self.price_calculator.sheet_profit_margin * 100)
        self.doubleSpinBox_sheets_profit_margin.valueChanged.connect(self.price_settings_changed)

        self.nests_toolbox = MultiToolBox(self)
        self.nests_layout.addWidget(self.nests_toolbox)

        self.splitter = self.findChild(QSplitter, "splitter")

        if self.job.status == JobStatus.PLANNING and self.parent.parent.tabWidget.tabText(self.parent.parent.tabWidget.currentIndex()) == "Job Planner":
            self.splitter.setSizes([0, 1])
            # self.quoting_settings_widget.setEnabled(False)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)

        self.label_total_cost_for_parts = self.findChild(QLabel, "label_total_cost_for_parts")
        self.label_total_cost_for_parts.setHidden(self.job.status == JobStatus.PLANNING)
        self.label_total_cost_for_parts.setText(f"Total Cost for Parts: ${self.price_calculator.get_job_cost():,.2f}")

        self.label_total_cost_for_sheets = self.findChild(QLabel, "label_total_cost_for_sheets")
        self.label_total_cost_for_sheets.setHidden(self.job.status == JobStatus.PLANNING)
        self.label_total_cost_for_sheets.setText(f"Total Cost for Nested Sheets: ${self.price_calculator.get_total_cost_for_sheets():,.2f}")

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = JobColor.get_color(self.job.status)
        hover_color: str = lighten_color(base_color)
        pressed_color: str = darken_color(base_color)
        button.setObjectName("assembly_button_drop_menu")
        button.setStyleSheet(
            """
QPushButton#assembly_button_drop_menu {
    border: 1px solid rgba(71, 71, 71, 110);
    background-color: rgba(71, 71, 71, 110);
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-left-radius: 5px;
    border-bottom-right-radius: 5px;
    color: #EAE9FC;
    text-align: left;
}

QPushButton:hover#assembly_button_drop_menu {
    background-color: rgba(76, 76, 76, 110);
    border: 1px solid %(base_color)s;
}

QPushButton:pressed#assembly_button_drop_menu {
    background-color: %(base_color)s;
    color: #171717;
}

QPushButton:!checked#assembly_button_drop_menu {
    color: #8C8C8C;
}

QPushButton:!checked:pressed#assembly_button_drop_menu {
    color: #EAE9FC;
}

QPushButton:checked#assembly_button_drop_menu {
    color: #171717;
    border-color: %(base_color)s;
    background-color: %(base_color)s;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
}

QPushButton:checked:hover#assembly_button_drop_menu {
    background-color: %(hover_color)s;
}

QPushButton:checked:pressed#assembly_button_drop_menu {
    color: #171717;
    background-color: %(pressed_color)s;
}
"""
            % {
                "base_color": base_color,
                "hover_color": hover_color,
                "pressed_color": pressed_color,
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

    def job_settings_changed(self):
        self.job.order_number = self.doubleSpinBox_order_number.value()
        self.job.status = JobStatus(self.comboBox_type.currentIndex() + 1)
        self.job.date_shipped = self.dateEdit_shipped.date().toString("yyyy-MM-dd")
        self.job.date_expected = self.dateEdit_expected.date().toString("yyyy-MM-dd")
        self.job.ship_to = self.textEdit_ship_to.toPlainText()
        self.changes_made()

    def workspace_settings_changed(self):
        for group_widget in self.group_widgets:
            group_widget.workspace_settings_changed()

    def add_group(self, new_group: Group = None) -> GroupWidget:
        if not new_group:
            group = Group(f"Enter Group Name{len(self.job.groups)}", {}, self.job)
            group.color = colors.get_random_color()
            self.job.add_group(group)
            self.changes_made()
        else:
            group = new_group

        group_widget = GroupWidget(group, self)
        self.groups_toolbox.addItem(group_widget, group.name, group.color)

        toggle_button = self.groups_toolbox.getLastToggleButton()

        job_name_input: QLineEdit = self.groups_toolbox.getLastInputBox()
        job_name_input.textChanged.connect(partial(self.group_name_renamed, group, job_name_input))

        job_name_input.textChanged.connect(
            partial(
                self.job_preferences.group_toolbox_toggled,
                job_name_input,
                toggle_button,
            )
        )
        toggle_button.clicked.connect(
            partial(
                self.job_preferences.group_toolbox_toggled,
                job_name_input,
                toggle_button,
            )
        )

        duplicate_button = self.groups_toolbox.getLastDuplicateButton()
        duplicate_button.clicked.connect(partial(self.duplicate_group, group))

        delete_button = self.groups_toolbox.getLastDeleteButton()
        delete_button.clicked.connect(partial(self.delete_group, group_widget))

        self.group_widgets.append(group_widget)

        if self.job_preferences.is_group_closed(group.name):
            self.groups_toolbox.closeLastToolBox()

        return group_widget

    def load_group(self, group: Group):
        group_widget = self.add_group(group)
        for assembly in group.assemblies:
            group_widget.load_assembly(assembly)
        self.load_nests()
        self.update_nest_summary()

    def group_name_renamed(self, group: Group, new_group_name: QLineEdit):
        group.name = new_group_name.text()
        self.changes_made()

    def duplicate_group(self, group: Group):
        new_group = Group(f"{group.name} - (Copy)", group.to_dict(), self.job)
        new_group.color = colors.get_random_color()
        self.load_group(new_group)
        self.job.add_group(new_group)
        self.changes_made()

    def delete_group(self, group_widget: GroupWidget):
        self.group_widgets.remove(group_widget)
        self.groups_toolbox.removeItem(group_widget)
        self.job.remove_group(group_widget.group)
        self.changes_made()

    def reload_job(self):
        self.job_preferences.set_job_scroll_position(
            self.job.name,
            (
                self.scrollArea.horizontalScrollBar().value(),
                self.scrollArea.verticalScrollBar().value(),
            ),
        )
        self.reloadJob.emit(self)

    def load_nests(self):
        self.nests_toolbox.clear()
        self.nest_widgets.clear()
        self.nest_laser_cut_parts_assembly_comboboxes.clear()
        for nest in self.job.nests:
            nest_widget = NestWidget(nest, self)
            nest_widget.updateLaserCutPartSettings.connect(self.nest_settings_changed)
            self.nest_widgets.append(nest_widget)
            self.nests_toolbox.addItem(nest_widget, nest.get_name(), JobColor.get_color(self.job.status))
            button = self.nests_toolbox.getLastButton()
            button.clicked.connect(partial(self.job_preferences.nest_toggled, nest.get_name(), button))
            nest_widget.toolbox_button = button
        for i, nest in enumerate(self.job.nests):
            if self.job_preferences.is_nest_closed(nest.get_name()):
                self.nests_toolbox.close(i)
            else:
                self.nests_toolbox.open(i)

    def update_nest_parts_assemblies(self):
        for nest_widget in self.nest_widgets:
            nest_widget.update_parts_assembly()

    def update_nest_summary(self):
        summary_data = {"sheets": {}, "material_total": {}}
        for nest in self.job.nests:
            if not nest.laser_cut_parts:
                continue
            summary_data["sheets"].setdefault(nest.sheet.get_name(), {"total_sheet_count": 0, "total_seconds": 0})
            summary_data["material_total"].setdefault(nest.sheet.material, {"total_sheet_count": 0, "total_seconds": 0})
            summary_data["sheets"][nest.sheet.get_name()]["total_sheet_count"] += nest.sheet_count
            summary_data["sheets"][nest.sheet.get_name()]["total_seconds"] += nest.sheet_cut_time * nest.sheet_count
            summary_data["material_total"][nest.sheet.material]["total_seconds"] += nest.sheet_cut_time * nest.sheet_count
            summary_data["material_total"][nest.sheet.material]["total_sheet_count"] += nest.sheet_count

            self.treeWidget_nest_summary.clear()
            self.treeWidget_nest_summary.setHeaderLabels(["Name", "Quantity", "Cut time"])

            sorted_summary_keys = natsorted(summary_data.keys())
            sorted_summary = {key: summary_data[key] for key in sorted_summary_keys}

            for sheet, data in sorted_summary.get("sheets", {}).items():
                hours = int(data["total_seconds"] // 3600)
                minutes = int((data["total_seconds"] % 3600) // 60)
                seconds = int(data["total_seconds"] % 60)
                total_seconds_string = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
                item = QTreeWidgetItem([sheet, str(data["total_sheet_count"]), total_seconds_string])
                self.treeWidget_nest_summary.addTopLevelItem(item)

            materials_item = QTreeWidgetItem(self.treeWidget_nest_summary, ["Materials Total"])
            materials_item.setFirstColumnSpanned(True)
            for material, data in sorted_summary.get("material_total", {}).items():
                hours = int(data["total_seconds"] // 3600)
                minutes = int((data["total_seconds"] % 3600) // 60)
                seconds = int(data["total_seconds"] % 60)
                total_seconds_string = f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
                item = QTreeWidgetItem([material, str(data["total_sheet_count"]), total_seconds_string])
                materials_item.addChild(item)

            self.treeWidget_nest_summary.expandAll()
            self.treeWidget_nest_summary.resizeColumnToContents(0)
            self.treeWidget_nest_summary.resizeColumnToContents(1)

    def match_item_to_sheet_toggled(self):
        self.price_calculator.match_item_cogs_to_sheet = self.pushButton_item_to_sheet.isChecked()
        self.changes_made()

    def cost_for_laser_changed(self):
        self.price_calculator.cost_for_laser = self.doubleSpinBox_cost_for_laser.value()
        self.changes_made()

    def update_nest_sheets(self, action: str):
        for i, nest_widget in enumerate(self.nest_widgets):
            if action == "LENGTH":
                nest_widget.sheet.length = self.doubleSpinBox_length.value()
            elif action == "WIDTH":
                nest_widget.sheet.width = self.doubleSpinBox_width.value()
            elif action == "MATERIAL":
                nest_widget.sheet.material = self.comboBox_materials.currentText()
            elif action == "THICKNESS":
                nest_widget.sheet.thickness = self.comboBox_thicknesses.currentText()
            nest_widget.update_ui_values()
            nest_widget.update_nest_cost()
            self.nests_toolbox.setItemText(i, nest_widget.nest.get_name())
        self.price_calculator.update_laser_cut_parts_to_sheet_price()
        self.price_calculator.update_laser_cut_parts_cost()
        self.changes_made()

    def update_tables(self):
        for group_widget in self.group_widgets:
            group_widget.update_tables()

    def update_prices(self):
        self.price_calculator.update_laser_cut_parts_cost()
        self.price_calculator.update_laser_cut_parts_to_sheet_price()
        self.label_total_cost_for_parts.setText(f"Total Cost for Parts: ${self.price_calculator.get_job_cost():,.2f}")
        self.label_total_cost_for_sheets.setText(f"Total Cost for Nested Sheets: ${self.price_calculator.get_total_cost_for_sheets():,.2f}")
        for group_widget in self.group_widgets:
            group_widget.update_prices()

    def price_settings_changed(self):
        self.price_calculator.item_overhead = self.doubleSpinBox_items_overhead.value() / 100
        self.price_calculator.item_profit_margin = self.doubleSpinBox_items_profit_margin.value() / 100
        self.price_calculator.sheet_overhead = self.doubleSpinBox_sheets_overhead.value() / 100
        self.price_calculator.sheet_profit_margin = self.doubleSpinBox_sheets_profit_margin.value() / 100
        self.changes_made()

    def nest_settings_changed(self, nest: Nest):
        self.update_tables()
        self.changes_made()

    def changes_made(self):
        self.parent.job_changed(self.job)
        self.update_nest_parts_assemblies()
        self.update_prices()

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
