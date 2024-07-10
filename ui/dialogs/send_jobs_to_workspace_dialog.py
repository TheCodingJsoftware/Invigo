from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QTreeWidget, QTreeWidgetItem, QDoubleSpinBox, QLabel, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from datetime import datetime

from utils.workspace.job import JobStatus

class SendJobsToWorkspaceDialog(QDialog):
    def __init__(
        self,
        active_jobs_in_planning: dict,
        active_jobs_in_quoting: dict,
        job_templates: dict,
        parent=None,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/dialogs/send_jobs_to_workspace_dialog.ui", self)

        self.setWindowTitle("Send Jobs to Workspace")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.pushButton_add.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.job_tree_widget = QTreeWidget(self)
        self.jobs_layout.addWidget(self.job_tree_widget)
        self.verticalLayout_workorders.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.populate_tree_widget(
            active_jobs_in_planning, active_jobs_in_quoting, job_templates
        )

        self.job_tree_widget.itemChanged.connect(self.update_workorders_layout)

    def populate_tree_widget(
        self, active_jobs_in_planning, active_jobs_in_quoting, job_templates
    ):
        self.job_tree_widget.setColumnCount(3)
        self.job_tree_widget.setHeaderLabels(["Job Name", "Order Number", "Modified Date"])

        planning_item = QTreeWidgetItem(["Active Jobs in Planning"])
        quoting_item = QTreeWidgetItem(["Active Jobs in Quoting"])
        templates_item = QTreeWidgetItem(["Templates"])

        self.job_tree_widget.addTopLevelItem(planning_item)
        self.job_tree_widget.addTopLevelItem(quoting_item)
        self.job_tree_widget.addTopLevelItem(templates_item)

        self.add_jobs_to_item(planning_item, active_jobs_in_planning, True)
        self.add_jobs_to_item(quoting_item, active_jobs_in_quoting, True)
        self.add_jobs_to_item(templates_item, job_templates)

        # Expand all tree widgets by default
        self.job_tree_widget.expandAll()
        self.job_tree_widget.resizeColumnToContents(0)
        self.job_tree_widget.resizeColumnToContents(1)

    def add_jobs_to_item(self, parent_item, jobs, ignore_job_type=False):
        for job_name, job_data in jobs.items():
            job_name = job_name.split("\\")[-1]
            if not ignore_job_type and job_data.get("type") != JobStatus.TEMPLATE.value:
                continue
            try:
                modified_date = datetime.fromtimestamp(job_data.get("modified_date")).strftime("%A, %B %d, %Y, %I:%M:%S %p")
            except TypeError:
                modified_date = ""
            item = QTreeWidgetItem([
                job_name,
                str(job_data["order_number"]),
                modified_date,
            ])
            item.setCheckState(0, Qt.CheckState.Unchecked)  # Add checkbox to the first column
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            parent_item.addChild(item)

    def update_workorders_layout(self, item, column):
        if column == 0:  # Check state changed
            if item.checkState(0) == Qt.CheckState.Checked:
                self.add_workorder_widget(item.text(0))
            else:
                self.remove_workorder_widget(item.text(0))

    def add_workorder_widget(self, job_name):
        container = QWidget()
        layout = QHBoxLayout()

        label = QLabel(job_name)
        label_1 = QLabel("*")
        label_1.setFixedWidth(20)
        spin_box = QDoubleSpinBox()
        spin_box.setValue(1.0)
        spin_box.setDecimals(0)
        spin_box.setMinimum(1)

        layout.addWidget(label)
        layout.addWidget(spin_box)
        layout.addWidget(label_1)
        container.setLayout(layout)

        container.setObjectName(f"workorder_{job_name}")
        self.verticalLayout_workorders.addWidget(container)

    def remove_workorder_widget(self, job_name):
        for i in range(self.verticalLayout_workorders.count()):
            widget = self.verticalLayout_workorders.itemAt(i).widget()
            if widget and widget.objectName() == f"workorder_{job_name}":
                widget.deleteLater()
                break
