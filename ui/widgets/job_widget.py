import contextlib
from datetime import datetime
from functools import partial
from typing import TYPE_CHECKING, Optional, Union

from natsort import natsorted
from PyQt6.QtCore import QDateTime, Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QPushButton, QTreeWidgetItem, QVBoxLayout, QWidget

from ui.custom.assembly_planning_widget import AssemblyPlanningWidget
from ui.custom.assembly_quoting_widget import AssemblyQuotingWidget
from ui.custom.job_flowtag_timeline_widget import JobFlowtagTimelineWidget
from ui.custom_widgets import AssemblyMultiToolBox, MultiToolBox, QLineEdit
from ui.dialogs.add_assembly_dialog import AddAssemblyDialog
from ui.icons import Icons
from ui.theme import theme_var
from ui.widgets.job_widget_UI import Ui_Form
from ui.widgets.nest_widget import NestWidget
from utils import colors
from utils.colors import get_contrast_text_color, lighten_color
from utils.inventory.nest import Nest
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job, JobColor, JobStatus

if TYPE_CHECKING:
    from ui.custom.job_tab import JobTab


class JobWidget(QWidget, Ui_Form):
    reloadJob = pyqtSignal(object)  # object -> JobWidget

    def __init__(self, job: Job, parent):
        super().__init__(parent)
        self.setupUi(self)

        self.parent: JobTab = parent
        self.job = job
        self.price_calculator = self.job.price_calculator
        self.job_preferences = self.parent.job_preferences
        self.main_window = self.parent.parent
        self.sheet_settings = self.main_window.sheet_settings
        self.paint_inventory = self.main_window.paint_inventory
        self.main_window_tab_widget = self.main_window.stackedWidget

        self.assembly_widgets: list[Union[AssemblyPlanningWidget, AssemblyQuotingWidget]] = []

        self.nest_widgets: list[NestWidget] = []
        self.nest_laser_cut_parts_assembly_comboboxes: list[QComboBox] = []

        self.load_ui()

    def load_ui(self):
        self.verticalLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.gridLayout_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_8.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.item_quoting_options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.gridLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.nest_summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.nests_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.apply_stylesheet_to_toggle_buttons(self.pushButton_global_sheet_settings, self.global_sheet_settings_widget)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_item_quoting_options, self.item_quoting_options_widget)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_sheet_quoting_options, self.sheet_quoting_options_widget)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_nest_summary, self.nest_summary_widget)
        self.apply_stylesheet_to_toggle_buttons(self.pushButton_nests, self.nests_widget)

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

        self.pushButton_reload_job.clicked.connect(self.reload_job)
        self.pushButton_reload_job.setIcon(Icons.refresh_icon)

        self.doubleSpinBox_order_number.setValue(self.job.order_number)
        self.doubleSpinBox_order_number.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.doubleSpinBox_order_number.valueChanged.connect(self.job_settings_changed)

        self.doubleSpinBox_po_number.setValue(self.job.PO_number)
        self.doubleSpinBox_po_number.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.doubleSpinBox_po_number.valueChanged.connect(self.job_settings_changed)

        def get_latest_order_number():
            self.doubleSpinBox_order_number.setValue(self.parent.parent.order_number)
            self.job_settings_changed()

        self.pushButton_get_order_number.clicked.connect(get_latest_order_number)

        self.comboBox_type.setCurrentIndex(self.job.status.value - 1)
        self.comboBox_type.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.comboBox_type.currentTextChanged.connect(self.job_settings_changed)

        try:
            self.dateEdit_start.setDateTime(QDateTime(datetime.strptime(self.job.starting_date, "%Y-%m-%d %I:%M %p")))
        except ValueError:
            self.dateEdit_start.setDateTime(QDateTime().currentDateTime())
            self.job.starting_date = self.dateEdit_start.dateTime().toString("yyyy-MM-dd h:mm AP")

        self.dateEdit_start.dateChanged.connect(self.job_settings_changed)
        self.dateEdit_start.wheelEvent = lambda event: self.parent.wheelEvent(event)

        try:
            self.dateEdit_end.setDateTime(QDateTime(datetime.strptime(self.job.ending_date, "%Y-%m-%d %I:%M %p")))
        except ValueError:
            current_date = QDateTime.currentDateTime()
            new_date = current_date.addDays(7)
            self.dateEdit_end.setDateTime(new_date)
            self.job.ending_date = self.dateEdit_end.dateTime().toString("yyyy-MM-dd h:mm AP")

        self.label_16.setText(f"Process's timeline: ({self.job.starting_date} - {self.job.ending_date})")
        self.dateEdit_end.dateChanged.connect(self.job_settings_changed)
        self.dateEdit_end.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.textEdit_ship_to.setText(self.job.ship_to)
        self.textEdit_ship_to.textChanged.connect(self.job_settings_changed)

        self.assemblies_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.pushButton_add_new_assembly.clicked.connect(self.add_assembly)

        self.pushButton_add_existing_assembly.clicked.connect(self.add_existing_assembly)

        self.assemblies_toolbox = AssemblyMultiToolBox(self)
        self.assemblies_layout.addWidget(self.assemblies_toolbox)

        self.comboBox_laser_cutting.wheelEvent = lambda event: self.parent.wheelEvent(event)

        self.doubleSpinBox_cost_for_laser.setValue(self.price_calculator.cost_for_laser)
        self.doubleSpinBox_cost_for_laser.valueChanged.connect(self.cost_for_laser_changed)
        self.doubleSpinBox_cost_for_laser.wheelEvent = lambda event: self.parent.wheelEvent(event)

        self.comboBox_materials.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.comboBox_materials.addItems(self.sheet_settings.get_materials())
        self.comboBox_materials.currentTextChanged.connect(partial(self.update_nest_sheets, "MATERIAL"))

        self.comboBox_thicknesses.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.comboBox_thicknesses.addItems(self.sheet_settings.get_thicknesses())
        self.comboBox_thicknesses.currentTextChanged.connect(partial(self.update_nest_sheets, "THICKNESS"))

        self.doubleSpinBox_length.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.doubleSpinBox_length.valueChanged.connect(partial(self.update_nest_sheets, "LENGTH"))

        self.doubleSpinBox_width.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.doubleSpinBox_width.valueChanged.connect(partial(self.update_nest_sheets, "WIDTH"))

        self.doubleSpinBox_items_overhead.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.doubleSpinBox_items_overhead.setValue(self.price_calculator.item_overhead * 100)
        self.doubleSpinBox_items_overhead.valueChanged.connect(self.price_settings_changed)

        self.checkBox_components_use_overhead.toggled.connect(self.price_settings_changed)
        self.checkBox_components_use_overhead.setChecked(self.price_calculator.components_use_overhead)

        self.checkBox_components_use_profit_margin.toggled.connect(self.price_settings_changed)
        self.checkBox_components_use_profit_margin.setChecked(self.price_calculator.components_use_profit_margin)

        self.doubleSpinBox_items_profit_margin.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.doubleSpinBox_items_profit_margin.setValue(self.price_calculator.item_profit_margin * 100)
        self.doubleSpinBox_items_profit_margin.valueChanged.connect(self.price_settings_changed)

        self.pushButton_item_to_sheet.setChecked(self.price_calculator.match_item_cogs_to_sheet)
        self.pushButton_item_to_sheet.clicked.connect(self.match_item_to_sheet_toggled)

        self.doubleSpinBox_sheets_overhead.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.doubleSpinBox_sheets_overhead.setValue(self.price_calculator.sheet_overhead * 100)
        self.doubleSpinBox_sheets_overhead.valueChanged.connect(self.price_settings_changed)

        self.doubleSpinBox_sheets_profit_margin.wheelEvent = lambda event: self.parent.wheelEvent(event)
        self.doubleSpinBox_sheets_profit_margin.setValue(self.price_calculator.sheet_profit_margin * 100)
        self.doubleSpinBox_sheets_profit_margin.valueChanged.connect(self.price_settings_changed)

        self.nests_toolbox = MultiToolBox(self)
        self.nests_layout.addWidget(self.nests_toolbox)

        self.processes_widget.setVisible(self.parent.parent.tab_text(self.parent.parent.stackedWidget.currentIndex()) == "job_planner_tab")

        if self.parent.parent.tab_text(self.parent.parent.stackedWidget.currentIndex()) == "job_planner_tab":
            self.splitter.setSizes([0, 1])
            # self.quoting_settings_widget.setEnabled(False)

        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)

        self.label_total_cost_for_parts.setHidden(self.parent.parent.tab_text(self.parent.parent.stackedWidget.currentIndex()) == "job_planner_tab")
        self.label_total_cost_for_parts.setText(f"Total Cost for Parts: ${self.price_calculator.get_job_cost():,.2f}")

        self.label_total_cost_for_sheets.setHidden(self.parent.parent.tab_text(self.parent.parent.stackedWidget.currentIndex()) == "job_planner_tab")
        self.label_total_cost_for_sheets.setText(f"Total Cost for Nested Sheets: ${self.price_calculator.get_total_cost_for_sheets():,.2f}")

        self.flowtag_timeline = JobFlowtagTimelineWidget(self.job.flowtag_timeline, self)
        self.verticalLayout_flowtag_timeline.addWidget(self.flowtag_timeline)

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = JobColor.get_color(self.job.status)
        hover_color = lighten_color(base_color)
        inverted_color = get_contrast_text_color(base_color)
        button.setObjectName("assembly_button_drop_menu")
        button.setStyleSheet(
            f"""
QPushButton#assembly_button_drop_menu {{
    border: 1px solid {theme_var('surface')};
    background-color: {theme_var('surface')};
    border-radius: {theme_var('border-radius')};
    color: {theme_var('on-surface')};
    text-align: left;
}}
/* CLOSED */
QPushButton:!checked#assembly_button_drop_menu {{
    color: {theme_var('on-surface')};
    border: 1px solid {theme_var('outline')};
}}

QPushButton:!checked:hover#assembly_button_drop_menu {{
    background-color: {theme_var('outline-variant')};
}}
QPushButton:!checked:pressed#assembly_button_drop_menu {{
    background-color: {theme_var('surface')};
}}
/* OPENED */
QPushButton:checked#assembly_button_drop_menu {{
    color: %(inverted_color)s;
    border-color: %(base_color)s;
    background-color: %(base_color)s;
    border-top-left-radius: {theme_var('border-radius')};
    border-top-right-radius: {theme_var('border-radius')};
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
}}

QPushButton:checked:hover#assembly_button_drop_menu {{
    background-color: %(hover_color)s;
}}

QPushButton:checked:pressed#assembly_button_drop_menu {{
    background-color: %(pressed_color)s;
}}
"""
            % {
                "base_color": base_color,
                "hover_color": hover_color,
                "pressed_color": base_color,
                "inverted_color": inverted_color,
            }
        )
        widget.setObjectName("assembly_widget_drop_menu")
        widget.setStyleSheet(
            f"""QWidget#assembly_widget_drop_menu{{
            border: 1px solid %(base_color)s;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            background-color: {theme_var('background')};
            }}"""
            % {"base_color": base_color}
        )

    def job_settings_changed(self):
        self.job.order_number = int(self.doubleSpinBox_order_number.value())
        self.job.PO_number = int(self.doubleSpinBox_po_number.value())
        self.job.status = JobStatus(self.comboBox_type.currentIndex() + 1)
        self.job.starting_date = self.dateEdit_start.dateTime().toString("yyyy-MM-dd h:mm AP")
        self.job.ending_date = self.dateEdit_end.dateTime().toString("yyyy-MM-dd h:mm AP")
        self.flowtag_timeline.set_range(self.dateEdit_start.dateTime(), self.dateEdit_end.dateTime())
        self.job.ship_to = self.textEdit_ship_to.toPlainText()
        self.label_16.setText(f"Process's timeline: ({self.job.starting_date} - {self.job.ending_date})")
        self.changes_made()

    def workspace_settings_changed(self):
        for assembliy_widget in self.assembly_widgets:
            assembliy_widget.workspace_settings_changed()

    def get_assemblies_dialog(self) -> Optional[list[Assembly]]:
        dialog = AddAssemblyDialog(self.parent.get_active_jobs(), self)
        if dialog.exec():
            return dialog.get_selected_assemblies()
        return None

    def get_all_assembly_widgets(self) -> list[Union[AssemblyPlanningWidget, AssemblyQuotingWidget]]:
        widgets: list[Union[AssemblyPlanningWidget, AssemblyQuotingWidget]] = []
        widgets.extend(self.assembly_widgets)
        for assembly_widget in self.assembly_widgets:
            widgets.extend(assembly_widget.get_all_sub_assembly_widgets())
        return widgets

    def add_existing_assembly(self):
        if assemblies_to_add := self.get_assemblies_dialog():
            for assembly in assemblies_to_add:
                new_assembly = Assembly(assembly.to_dict(), self.job)
                self.job.add_assembly(new_assembly)
                self.load_assembly(new_assembly)
            self.update_prices()

    def add_assembly(self, new_assembly: Optional[Assembly] = None) -> Union[AssemblyPlanningWidget, AssemblyQuotingWidget]:
        if not new_assembly:
            assembly = Assembly({}, self.job)
            assembly.name = f"Enter Assembly Name{len(self.job.assemblies)}"
            assembly.color = colors.get_random_color()
            self.job.add_assembly(assembly)
            self.changes_made()
        else:
            assembly = new_assembly

        if self.main_window.tab_text(self.main_window_tab_widget.currentIndex()) == "job_planner_tab":
            assembly_widget = AssemblyPlanningWidget(assembly, self)
        elif self.main_window.tab_text(self.main_window_tab_widget.currentIndex()) == "job_quoter_tab":
            assembly_widget = AssemblyQuotingWidget(assembly, self)

        self.assemblies_toolbox.addItem(assembly_widget, assembly.name, assembly.color)

        toggle_button = self.assemblies_toolbox.getLastToggleButton()

        name_input: QLineEdit = self.assemblies_toolbox.getLastInputBox()
        name_input.textChanged.connect(partial(self.assembly_name_renamed, assembly, name_input))

        name_input.textChanged.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                assembly_widget.pushButton_laser_cut_parts,
                assembly_widget.pushButton_components,
                assembly_widget.pushButton_sub_assemblies,
            )
        )
        toggle_button.clicked.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                assembly_widget.pushButton_laser_cut_parts,
                assembly_widget.pushButton_components,
                assembly_widget.pushButton_sub_assemblies,
            )
        )

        duplicate_button = self.assemblies_toolbox.getLastDuplicateButton()
        duplicate_button.clicked.connect(partial(self.duplicate_assembly, assembly))

        delete_button = self.assemblies_toolbox.getLastDeleteButton()
        delete_button.clicked.connect(partial(self.delete_assembly, assembly_widget))

        assembly_widget.pushButton_laser_cut_parts.clicked.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                assembly_widget.pushButton_laser_cut_parts,
                assembly_widget.pushButton_components,
                assembly_widget.pushButton_sub_assemblies,
            )
        )
        assembly_widget.pushButton_components.clicked.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                assembly_widget.pushButton_laser_cut_parts,
                assembly_widget.pushButton_components,
                assembly_widget.pushButton_sub_assemblies,
            )
        )
        assembly_widget.pushButton_sub_assemblies.clicked.connect(
            partial(
                self.job_preferences.assembly_toolbox_toggled,
                name_input,
                toggle_button,
                assembly_widget.pushButton_laser_cut_parts,
                assembly_widget.pushButton_components,
                assembly_widget.pushButton_sub_assemblies,
            )
        )

        self.assembly_widgets.append(assembly_widget)

        if self.job_preferences.is_assembly_closed(assembly.name):
            self.assemblies_toolbox.closeLastToolBox()
        else:
            self.assemblies_toolbox.openLastToolBox()

        assembly_widget.pushButton_laser_cut_parts.setChecked(self.job_preferences.is_assembly_laser_cut_closed(assembly.name))
        assembly_widget.laser_cut_widget.setHidden(not self.job_preferences.is_assembly_laser_cut_closed(assembly.name))
        assembly_widget.pushButton_components.setChecked(self.job_preferences.is_assembly_component_closed(assembly.name))
        assembly_widget.component_widget.setHidden(not self.job_preferences.is_assembly_component_closed(assembly.name))
        assembly_widget.pushButton_sub_assemblies.setChecked(self.job_preferences.is_assembly_sub_assembly_closed(assembly.name))
        assembly_widget.sub_assemblies_widget.setHidden(not self.job_preferences.is_assembly_sub_assembly_closed(assembly.name))

        self.update_context_menu()
        return assembly_widget

    def load_assembly(self, sub_assembly: Assembly):
        assembly_widget = self.add_assembly(sub_assembly)
        for sub_assembly in sub_assembly.sub_assemblies:
            sub_assembly.job = self.job
            assembly_widget.load_sub_assembly(sub_assembly)
        self.load_nests()
        self.update_nest_summary()

    def assembly_name_renamed(self, assembly: Assembly, new_group_name: QLineEdit):
        assembly.name = new_group_name.text()
        self.update_context_menu()
        self.changes_made()

    def duplicate_assembly(self, assembly: Assembly):
        new_assembly = Assembly(assembly.to_dict(), self.job)
        new_assembly.name = f"{assembly.name} - (Copy)"
        new_assembly.color = colors.get_random_color()
        self.load_assembly(new_assembly)
        self.job.add_assembly(new_assembly)
        self.update_context_menu()
        self.changes_made()

    def delete_assembly(self, assembly_widget: Union[AssemblyPlanningWidget, AssemblyQuotingWidget]):
        self.assembly_widgets.remove(assembly_widget)
        self.assemblies_toolbox.removeItem(assembly_widget)
        self.job.remove_assembly(assembly_widget.assembly)
        self.update_context_menu()
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
        for group_widget in self.assembly_widgets:
            group_widget.update_tables()

    def update_prices(self):
        if self.main_window.tab_text(self.main_window_tab_widget.currentIndex()) == "job_quoter_tab":
            self.price_calculator.update_laser_cut_parts_cost()
            self.price_calculator.update_laser_cut_parts_to_sheet_price()
            self.label_total_cost_for_parts.setText(f"Total Cost for Parts: ${self.price_calculator.get_job_cost():,.2f}")
            self.label_total_cost_for_sheets.setText(f"Total Cost for Nested Sheets: ${self.price_calculator.get_total_cost_for_sheets():,.2f}")
            for assembly_widget in self.assembly_widgets:
                if isinstance(assembly_widget, AssemblyQuotingWidget):
                    assembly_widget.update_prices()

    def price_settings_changed(self):
        self.price_calculator.item_overhead = self.doubleSpinBox_items_overhead.value() / 100
        self.price_calculator.item_profit_margin = self.doubleSpinBox_items_profit_margin.value() / 100
        self.price_calculator.sheet_overhead = self.doubleSpinBox_sheets_overhead.value() / 100
        self.price_calculator.sheet_profit_margin = self.doubleSpinBox_sheets_profit_margin.value() / 100
        self.price_calculator.components_use_overhead = self.checkBox_components_use_overhead.isChecked()
        self.price_calculator.components_use_profit_margin = self.checkBox_components_use_profit_margin.isChecked()
        self.changes_made()

    def nest_settings_changed(self, nest: Nest):
        self.update_tables()
        self.changes_made()

    def update_context_menu(self):
        for assembly_widget in self.assembly_widgets:
            assembly_widget.reload_context_menu()

    def changes_made(self):
        with contextlib.suppress(AttributeError):  # Happens when reloading when no flowtags set.
            self.flowtag_timeline.load_tag_timelines()
        self.parent.job_changed(self.job)
        self.update_nest_parts_assemblies()
        self.update_prices()

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
