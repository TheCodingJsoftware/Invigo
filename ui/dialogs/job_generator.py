import logging
import traceback
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, QThreadPool, QTimer
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QDialog, QTreeWidget, QTreeWidgetItem

from ui.custom_widgets import HumbleDoubleSpinBox
from ui.dialogs.job_generator_UI import Ui_Form
from ui.icons import Icons
from ui.theme import theme_var
from utils.colors import get_on_color_from_primary
from utils.workers.jobs.get_all_jobs import GetAllJobsWorker
from utils.workers.jobs.get_job import GetJobWorker
from utils.workers.runnable_chain import RunnableChain
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job, JobIcon

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class JobGeneratorDialog(QDialog, Ui_Form):
    def __init__(
        self,
        parent: "MainWindow",
    ):
        super().__init__(parent)
        self.setupUi(self)
        self._parent_widget = parent
        self.jobs: list[Job] = []
        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(3)
        self.tree_widget.setHeaderLabels(["Job/Assembly Name", "Status", "Quantity"])
        self.tree_widget.setSortingEnabled(True)
        self.jobs_layout.addWidget(self.tree_widget)
        self.tree_widget_items: dict[int, dict[str, HumbleDoubleSpinBox | Job | Assembly | QTreeWidgetItem]] = {}
        self.pushButton_cancel.clicked.connect(self.reject)
        self.pushButton_merge.clicked.connect(self.accept)
        self.lineEdit_job_name.textChanged.connect(self.on_job_name_changed)
        self.get_all_jobs()

        self.resize(650, 800)

    def load_ui(self):
        self.tree_widget.clear()

        for job in self.jobs:
            job_item = QTreeWidgetItem()
            job_item.setText(0, job.name)
            job_item.setText(1, job.status.name)
            job_item.setFlags(job_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            job_item.setData(0, Qt.ItemDataRole.BackgroundRole, None)
            job_item.setCheckState(0, Qt.CheckState.Unchecked)
            job_item.setIcon(0, JobIcon.get_icon(job.status))
            self.tree_widget_items[id(job_item)] = {
                "item": job_item,
                "job": job,
            }

            self.tree_widget.addTopLevelItem(job_item)

            for assembly in job.assemblies:
                assembly_item = QTreeWidgetItem()
                assembly_item.setText(0, assembly.name)
                assembly_item.setFlags(assembly_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                assembly_item.setCheckState(0, Qt.CheckState.Unchecked)

                spin_box = HumbleDoubleSpinBox(self.tree_widget)
                spin_box.setDecimals(0)
                spin_box.setToolTip(f"Original: {assembly.meta_data.quantity}")
                spin_box.setMinimum(1)
                spin_box.setMaximum(9999)  # or some other logical limit
                spin_box.setValue(assembly.meta_data.quantity)

                # Insert spin box into column 2
                job_item.addChild(assembly_item)
                self.tree_widget.setItemWidget(assembly_item, 2, spin_box)

                self.tree_widget_items[id(assembly_item)] = {
                    "job": job,
                    "item": assembly_item,
                    "assembly": assembly,
                    "spinbox": spin_box,
                }

                for col in range(self.tree_widget.columnCount()):
                    assembly_item.setForeground(col, QColor(job.color))
            for col in range(self.tree_widget.columnCount()):
                job_item.setForeground(col, QColor(job.color))

        self.tree_widget.expandAll()

        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
        self.tree_widget.resizeColumnToContents(2)

        self.tree_widget.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        QTimer.singleShot(1, self._update_spinboxes)

        # Connect to handle changes
        self.tree_widget.itemChanged.connect(self.on_item_check_changed)

    def merge(self) -> Job | None:
        # Get checked job items
        checked_jobs = [
            info["item"] for info in self.tree_widget_items.values() if "job" in info and info["item"].parent() is None and info["item"].checkState(0) == Qt.CheckState.Checked
        ]

        if not checked_jobs:
            return None

        # Create new Job
        merged_job = Job({}, self._parent_widget.job_manager)
        merged_job.name = self.lineEdit_job_name.text().strip()

        for job_item in checked_jobs:
            for i in range(job_item.childCount()):
                assembly_item = job_item.child(i)
                if assembly_item.checkState(0) == Qt.CheckState.Checked:
                    info = self.tree_widget_items.get(id(assembly_item))
                    if info:
                        assembly_ref: Assembly = info["assembly"]
                        spinbox: HumbleDoubleSpinBox = info["spinbox"]

                        cloned_assembly = Assembly(assembly_ref.to_dict(), merged_job)
                        cloned_assembly.meta_data.quantity = int(spinbox.value())
                        merged_job.add_assembly(cloned_assembly)

        return merged_job

    def on_job_name_changed(self, text: str):
        self.pushButton_merge.setEnabled(bool(text.strip()))

    def on_item_check_changed(self, item: QTreeWidgetItem, column: int):
        self.tree_widget.blockSignals(True)

        if item.parent() is None:
            # It's a job (parent)
            state = item.checkState(0)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, state)
        else:
            # It's an assembly (child)
            parent = item.parent()
            any_checked = any(parent.child(i).checkState(0) == Qt.CheckState.Checked for i in range(parent.childCount()))
            if any_checked:
                parent.setCheckState(0, Qt.CheckState.Checked)
            else:
                parent.setCheckState(0, Qt.CheckState.Unchecked)

        self._update_spinboxes()

        self.tree_widget.blockSignals(False)

    def _update_spinboxes(self):
        for i in range(self.tree_widget.topLevelItemCount()):
            job_item = self.tree_widget.topLevelItem(i)
            for j in range(job_item.childCount()):
                assembly_item = job_item.child(j)
                info = self.tree_widget_items.get(id(assembly_item))
                if info and "spinbox" in info:
                    spinbox = info["spinbox"]
                    # Show if checked, hide otherwise
                    spinbox.setHidden(assembly_item.checkState(0) != Qt.CheckState.Checked)

    def get_all_jobs(self):
        get_all_jobs_worker = GetAllJobsWorker()
        get_all_jobs_worker.signals.success.connect(self.on_get_all_jobs_result)
        QThreadPool.globalInstance().start(get_all_jobs_worker)

    def on_get_all_jobs_result(self, result):
        self.chain = RunnableChain(self._parent_widget)

        for job in result:
            get_job_worker = GetJobWorker(job["id"])
            self.chain.add(get_job_worker, self.on_get_job_result)

        self.chain.finished.connect(self.load_ui)
        self.chain.start()

    def on_get_job_result(self, result, next_step: Callable):
        try:
            job = Job(result, self._parent_widget.job_manager)
            self.jobs.append(job)
        except Exception as e:
            # include traceback
            logging.error(f"Error loading job: {e}\n{traceback.format_exc()}")
        next_step()
