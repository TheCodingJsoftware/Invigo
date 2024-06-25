import contextlib
import math
import os
from datetime import datetime
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QKeySequence, QPixmap
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QMenu, QMessageBox, QPushButton, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from ui.add_component_dialog import AddComponentDialog
from ui.custom_widgets import AssemblyMultiToolBox, ClickableLabel, CustomTableWidget, DeletePushButton, MachineCutTimeSpinBox, MultiToolBox, QLineEdit, RecutButton
from ui.group_widget import GroupWidget
from ui.image_viewer import QImageViewer
from utils import colors
from utils.calulations import calculate_overhead
from utils.components_inventory.component import Component
from utils.components_inventory.components_inventory import ComponentsInventory
from utils.inventory.category import Category
from utils.laser_cut_inventory.laser_cut_inventory import LaserCutInventory
from utils.laser_cut_inventory.laser_cut_part import LaserCutPart
from utils.workspace.group import Group
from utils.workspace.job import Job, JobStatus


class JobWidget(QWidget):
    reloadJob = pyqtSignal(Job)
    def __init__(self, job: Job, parent) -> None:
        super(JobWidget, self).__init__(parent)
        uic.loadUi("ui/job_widget.ui", self)

        self.parent = parent
        self.job = job

        self.group_widgets: list[GroupWidget] = []

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
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        self.pushButton_reload_job = self.findChild(QPushButton, "pushButton_reload_job")
        self.pushButton_reload_job.clicked.connect(self.reload_job)

        self.doubleSpinBox_order_number: QDoubleSpinBox = self.findChild(QDoubleSpinBox, "doubleSpinBox_order_number")
        self.doubleSpinBox_order_number.setValue(self.job.order_number)
        self.doubleSpinBox_order_number.wheelEvent = lambda event: None
        self.doubleSpinBox_order_number.valueChanged.connect(self.job_settings_changed)
        self.pushButton_get_order_number: QPushButton = self.findChild(QPushButton, "pushButton_get_order_number")

        # def get_latest_order_number():
        #     self.doubleSpinBox_order_number.setValue(self.parent.parent.order_number)
        #     self.job_settings_changed()

        # self.pushButton_get_order_number.clicked.connect(get_latest_order_number)
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

    def job_settings_changed(self):
        self.job.order_number = self.doubleSpinBox_order_number.value()
        self.job.job_status = JobStatus(self.comboBox_type.currentIndex() + 1)
        self.job.date_shipped = self.dateEdit_shipped.date().toString("yyyy-M-d")
        self.job.date_expected = self.dateEdit_expected.date().toString("yyyy-M-d")
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

        job_name_input: QLineEdit = self.groups_toolbox.getLastInputBox()
        job_name_input.textChanged.connect(partial(self.group_name_renamed, group, job_name_input))

        duplicate_button = self.groups_toolbox.getLastDuplicateButton()
        duplicate_button.clicked.connect(partial(self.duplicate_group, group))

        delete_button = self.groups_toolbox.getLastDeleteButton()
        delete_button.clicked.connect(partial(self.delete_group, group_widget))

        self.group_widgets.append(group_widget)

        return group_widget

    def load_group(self, group: Group):
        group_widget = self.add_group(group)
        for assembly in group.assemblies:
            group_widget.load_assembly(assembly)
        self.groups_toolbox.close_all()

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
        self.reloadJob.emit(self.job)

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
