from typing import Union

from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QCheckBox, QDialog, QDoubleSpinBox, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from utils.settings import Settings
from utils.workspace.job import Job, JobStatus


class SendJobsToWorkspaceDialog(QDialog):
    def __init__(
        self,
        active_jobs_in_planning: dict[str, dict[str, Union[Job, float, str, int]]],
        active_jobs_in_quoting: dict[str, dict[str, Union[Job, float, str, int]]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/dialogs/send_jobs_to_workspace_dialog.ui", self)

        self.setWindowTitle("Send Jobs to Workspace")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.settings_file = Settings()
        self.tables_font = QFont()
        self.tables_font.setFamily(self.settings_file.get_value("tables_font")["family"])
        self.tables_font.setPointSize(self.settings_file.get_value("tables_font")["pointSize"])
        self.tables_font.setWeight(self.settings_file.get_value("tables_font")["weight"])
        self.tables_font.setItalic(self.settings_file.get_value("tables_font")["italic"])

        self.job_tree_widget = QTreeWidget(self)
        self.job_tree_widget.setStyleSheet("QTreeWidget { border: none; }")

        self.jobs_layout = self.findChild(QVBoxLayout, "jobs_layout")
        self.jobs_layout.addWidget(self.job_tree_widget)

        self.verticalLayout_workorders = self.findChild(QVBoxLayout, "verticalLayout_workorders")
        self.verticalLayout_workorders.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.populate_tree_widget(active_jobs_in_planning, active_jobs_in_quoting)

        self.job_tree_widget.itemChanged.connect(self.update_workorders_layout)

    def populate_tree_widget(self, active_jobs_in_planning, active_jobs_in_quoting):
        self.job_tree_widget.setColumnCount(2)
        self.job_tree_widget.setHeaderLabels(["Job Name", "Order Number"])

        if active_jobs_in_planning:
            planning_item = QTreeWidgetItem(["Active Jobs in Planning"])
            planning_item.setFont(0, self.tables_font)
            self.job_tree_widget.addTopLevelItem(planning_item)
            self.add_jobs_to_item(planning_item, active_jobs_in_planning, True)

        if active_jobs_in_quoting:
            quoting_item = QTreeWidgetItem(["Active Jobs in Quoting"])
            quoting_item.setFont(0, self.tables_font)
            self.job_tree_widget.addTopLevelItem(quoting_item)
            self.add_jobs_to_item(quoting_item, active_jobs_in_quoting, True)

        # Expand all tree widgets by default
        self.job_tree_widget.expandAll()
        self.job_tree_widget.resizeColumnToContents(0)
        self.job_tree_widget.resizeColumnToContents(1)

    def add_jobs_to_item(
        self,
        parent_item: QTreeWidgetItem,
        jobs: Union[
            dict[str, dict[str, Union[Job, float, str, int]]],
            dict[str, dict[str, Union[float, str, int]]],
        ],
        ignore_job_type=False,
    ):
        for job_name, job_data in jobs.items():
            job_name = job_name.split("\\")[-1]
            if not ignore_job_type and job_data.get("type") != JobStatus.TEMPLATE.value:
                continue
            item = QTreeWidgetItem(
                [
                    job_name,
                    str(int(job_data["order_number"])),
                ]
            )
            item.setFont(0, self.tables_font)
            item.setFont(1, self.tables_font)
            item.setFont(2, self.tables_font)
            item.setCheckState(0, Qt.CheckState.Unchecked)  # Add checkbox to the first column
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            parent_item.addChild(item)

    def update_workorders_layout(self, item: QTreeWidgetItem, column: int):
        if column == 0:  # Check state changed
            if item.checkState(0) == Qt.CheckState.Checked:
                self.add_workorder_widget(item.text(0))
            else:
                self.remove_workorder_widget(item.text(0))

    def add_workorder_widget(self, job_name: str):
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(job_name)
        label_1 = QLabel("*")
        label_1.setFixedWidth(20)
        spin_box = QDoubleSpinBox()
        spin_box.setValue(1.0)
        spin_box.setDecimals(0)
        spin_box.setMinimum(1)

        group_assemblies_checkbox = QCheckBox("Split up Assemblies")

        layout.addWidget(label)
        layout.addWidget(label_1)
        layout.addWidget(spin_box)
        layout.addWidget(group_assemblies_checkbox)

        layout.setStretch(0, 2)
        layout.setStretch(1, 0)
        layout.setStretch(2, 1)
        layout.setStretch(3, 0)

        container.setLayout(layout)

        container.setObjectName(job_name)
        self.verticalLayout_workorders.addWidget(container)

    def remove_workorder_widget(self, job_name: str):
        for i in range(self.verticalLayout_workorders.count()):
            widget = self.verticalLayout_workorders.itemAt(i).widget()
            if widget and widget.objectName() == job_name:
                widget.deleteLater()
                break

    def get_selected_jobs(self) -> dict[str, list[tuple[str, float, bool]]]:
        selected_jobs = {"planning": [], "quoting": []}

        def collect_selected_jobs(item: QTreeWidgetItem, category: str):
            if item.checkState(0) == Qt.CheckState.Checked:
                for i in range(self.verticalLayout_workorders.count()):
                    widget = self.verticalLayout_workorders.itemAt(i).widget()
                    if widget and widget.objectName() == item.text(0):
                        spin_box = widget.findChild(QDoubleSpinBox)
                        group_assemblies_checkbox = widget.findChild(QCheckBox)
                        quantity = int(spin_box.value()) if spin_box else 1
                        group_assemblies = group_assemblies_checkbox.isChecked() if group_assemblies_checkbox else False
                        selected_jobs[category].append((item.text(0), quantity, group_assemblies))
                        break
            for i in range(item.childCount()):
                collect_selected_jobs(item.child(i), category)

        for i in range(self.job_tree_widget.topLevelItemCount()):
            top_item = self.job_tree_widget.topLevelItem(i)
            if top_item.text(0) == "Active Jobs in Planning":
                collect_selected_jobs(top_item, "planning")
            elif top_item.text(0) == "Active Jobs in Quoting":
                collect_selected_jobs(top_item, "quoting")

        return selected_jobs
