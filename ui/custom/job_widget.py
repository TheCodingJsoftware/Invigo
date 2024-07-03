import contextlib
from functools import partial
from typing import TYPE_CHECKING

from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QGridLayout,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.custom.group_widget import GroupWidget
from ui.custom_widgets import AssemblyMultiToolBox, MultiToolBox, QLineEdit
from ui.widgets.nest_widget import NestWidget
from utils import colors
from utils.colors import darken_color, lighten_color
from utils.quote.nest import Nest
from utils.workspace.group import Group
from utils.workspace.job import Job, JobStatus

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

        self.group_widgets: list[GroupWidget] = []
        self.nest_widgets: list[NestWidget] = []

        self.load_ui()

    def load_ui(self):
        #         self.groups_widget = self.findChild(QWidget, "groups_widget")
        #         self.groups_widget.setStyleSheet(
        #             """
        # QWidget#groups_widget {
        # border: 1px solid #3daee9;
        # border-bottom-left-radius: 10px;
        # border-bottom-right-radius: 10px;
        # border-top-right-radius: 0px;
        # border-top-left-radius: 0px;
        # }"""
        #         )
        self.verticalLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.gridLayout_2.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.verticalLayout_8.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.item_quoting_options_layout = self.findChild(
            QVBoxLayout, "item_quoting_options_layout"
        )
        self.item_quoting_options_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.gridLayout_4 = self.findChild(QGridLayout, "gridLayout_4")
        self.gridLayout_4.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.nest_summary_layout = self.findChild(QVBoxLayout, "nest_summary_layout")
        self.nest_summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.pushButton_global_sheet_settings = self.findChild(
            QPushButton, "pushButton_global_sheet_settings"
        )
        self.global_sheet_settings_widget = self.findChild(
            QWidget, "global_sheet_settings_widget"
        )
        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_global_sheet_settings, self.global_sheet_settings_widget
        )

        self.pushButton_item_quoting_options = self.findChild(
            QPushButton, "pushButton_item_quoting_options"
        )
        self.item_quoting_options_widget = self.findChild(
            QWidget, "item_quoting_options_widget"
        )
        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_item_quoting_options, self.item_quoting_options_widget
        )

        self.pushButton_sheet_quoting_options = self.findChild(
            QPushButton, "pushButton_sheet_quoting_options"
        )
        self.sheet_quoting_options_widget = self.findChild(
            QWidget, "sheet_quoting_options_widget"
        )
        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_sheet_quoting_options, self.sheet_quoting_options_widget
        )

        self.pushButton_nests = self.findChild(QPushButton, "pushButton_nests")
        self.nests_widget = self.findChild(QWidget, "nests_widget")
        self.nests_layout = self.findChild(QVBoxLayout, "nests_layout")
        self.nests_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_nests, self.nests_widget
        )

        self.pushButton_nest_summary = self.findChild(
            QPushButton, "pushButton_nest_summary"
        )
        self.nest_summary_widget = self.findChild(QWidget, "nest_summary_widget")
        self.nest_summary_layout = self.findChild(QVBoxLayout, "nest_summary_layout")
        self.apply_stylesheet_to_toggle_buttons(
            self.pushButton_nest_summary, self.nest_summary_widget
        )

        self.scrollArea = self.findChild(QScrollArea, "scrollArea")

        self.pushButton_reload_job = self.findChild(
            QPushButton, "pushButton_reload_job"
        )
        self.pushButton_reload_job.clicked.connect(self.reload_job)

        self.doubleSpinBox_order_number: QDoubleSpinBox = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_order_number"
        )
        self.doubleSpinBox_order_number.setValue(self.job.order_number)
        self.doubleSpinBox_order_number.wheelEvent = lambda event: None
        self.doubleSpinBox_order_number.valueChanged.connect(self.job_settings_changed)
        self.pushButton_get_order_number: QPushButton = self.findChild(
            QPushButton, "pushButton_get_order_number"
        )

        def get_latest_order_number():
            self.doubleSpinBox_order_number.setValue(self.parent.parent.order_number)
            self.job_settings_changed()

        self.pushButton_get_order_number.clicked.connect(get_latest_order_number)

        self.comboBox_type: QComboBox = self.findChild(QComboBox, "comboBox_type")
        self.comboBox_type.setCurrentIndex(self.job.job_status.value - 1)
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
        self.dateEdit_expected: QDateEdit = self.findChild(
            QDateEdit, "dateEdit_expected"
        )
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

        self.comboBox_laser_cutting = self.findChild(
            QComboBox, "comboBox_laser_cutting"
        )
        self.comboBox_laser_cutting.wheelEvent = lambda event: None

        self.doubleSpinBox_cost_for_laser = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_cost_for_laser"
        )
        self.doubleSpinBox_cost_for_laser.wheelEvent = lambda event: None

        self.comboBox_materials = self.findChild(QComboBox, "comboBox_materials")
        self.comboBox_materials.wheelEvent = lambda event: None
        self.comboBox_materials.addItems(self.sheet_settings.get_materials())
        self.comboBox_materials.currentTextChanged.connect(
            partial(self.update_nest_sheets, "MATERIAL")
        )

        self.comboBox_thicknesses = self.findChild(QComboBox, "comboBox_thicknesses")
        self.comboBox_thicknesses.wheelEvent = lambda event: None
        self.comboBox_thicknesses.addItems(self.sheet_settings.get_thicknesses())
        self.comboBox_thicknesses.currentTextChanged.connect(
            partial(self.update_nest_sheets, "THICKNESS")
        )

        self.doubleSpinBox_length = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_length"
        )
        self.doubleSpinBox_length.wheelEvent = lambda event: None
        self.doubleSpinBox_length.valueChanged.connect(
            partial(self.update_nest_sheets, "LENGTH")
        )

        self.doubleSpinBox_width = self.findChild(QDoubleSpinBox, "doubleSpinBox_width")
        self.doubleSpinBox_width.wheelEvent = lambda event: None
        self.doubleSpinBox_width.valueChanged.connect(
            partial(self.update_nest_sheets, "WIDTH")
        )

        self.doubleSpinBox_items_overhead = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_items_overhead"
        )
        self.doubleSpinBox_items_overhead.wheelEvent = lambda event: None

        self.doubleSpinBox_items_profit_margin = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_items_profit_margin"
        )
        self.doubleSpinBox_items_profit_margin.wheelEvent = lambda event: None

        self.pushButton_item_to_sheet = self.findChild(
            QPushButton, "pushButton_item_to_sheet"
        )
        self.pushButton_item_to_sheet.wheelEvent = lambda event: None

        self.doubleSpinBox_sheets_overhead = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_sheets_overhead"
        )
        self.doubleSpinBox_sheets_overhead.wheelEvent = lambda event: None

        self.doubleSpinBox_sheets_profit_margin = self.findChild(
            QDoubleSpinBox, "doubleSpinBox_sheets_profit_margin"
        )
        self.doubleSpinBox_sheets_profit_margin.wheelEvent = lambda event: None

        self.nests_toolbox = MultiToolBox(self)
        self.nests_layout.addWidget(self.nests_toolbox)

        self.splitter = self.findChild(QSplitter, "splitter")

        if (
            self.job.job_status == JobStatus.PLANNING
            and self.parent.parent.tabWidget.tabText(
                self.parent.parent.tabWidget.currentIndex()
            )
            == "Job Planner"
        ):
            self.splitter.setSizes([0, 1])
            self.quoting_settings_widget.setEnabled(False)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 5)

    def apply_stylesheet_to_toggle_buttons(self, button: QPushButton, widget: QWidget):
        base_color = self.job.get_color()
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
        self.job.job_status = JobStatus(self.comboBox_type.currentIndex() + 1)
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
        job_name_input.textChanged.connect(
            partial(self.group_name_renamed, group, job_name_input)
        )

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
        for nest in self.job.nests:
            nest_widget = NestWidget(nest, self)
            nest_widget.updateLaserCutPartSettings.connect(self.nest_settings_changed)
            self.nest_widgets.append(nest_widget)
            self.nests_toolbox.addItem(nest_widget, nest.get_name(), self.job.color)
        self.nests_toolbox.close_all()

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
            self.nests_toolbox.setItemText(i, nest_widget.nest.get_name())

    def nest_settings_changed(self, nest: Nest):
        self.update_tables()

    def changes_made(self):
        self.parent.job_changed(self.job)

    def update_tables(self):
        for group_widget in self.group_widgets:
            group_widget.update_tables()

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
