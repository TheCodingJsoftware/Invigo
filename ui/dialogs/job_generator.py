import logging
import traceback
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtWidgets import QDialog, QDoubleSpinBox, QTreeWidget, QTreeWidgetItem

from ui.dialogs.job_generator_UI import Ui_Form
from utils.workers.jobs.get_all_jobs import GetAllJobsWorker
from utils.workers.jobs.get_job import GetJobWorker
from utils.workers.runnable_chain import RunnableChain
from utils.workspace.job import Job

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
        self.tree_widget.setHeaderLabels(["Name", "Status", "Quantity"])
        self.tree_widget.setSortingEnabled(True)
        self.jobs_layout.addWidget(self.tree_widget)
        self.get_all_jobs()

    def load_ui(self):
        self.tree_widget.clear()

        for job in self.jobs:
            job_item = QTreeWidgetItem()
            job_item.setText(0, job.name)
            job_item.setText(1, job.status.name)
            job_item.setFlags(job_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            job_item.setCheckState(0, Qt.CheckState.Unchecked)

            self.tree_widget.addTopLevelItem(job_item)

            for assembly in job.assemblies:
                assembly_item = QTreeWidgetItem()
                assembly_item.setText(0, assembly.name)
                assembly_item.setFlags(
                    assembly_item.flags() | Qt.ItemFlag.ItemIsUserCheckable
                )
                assembly_item.setCheckState(0, Qt.CheckState.Unchecked)

                spin_box = QDoubleSpinBox(self.tree_widget)
                spin_box.setDecimals(0)
                spin_box.setMinimum(1)
                spin_box.setMaximum(9999)  # or some other logical limit
                spin_box.setValue(assembly.quantity)

                # Insert spin box into column 2
                job_item.addChild(assembly_item)
                self.tree_widget.setItemWidget(assembly_item, 2, spin_box)

        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
        self.tree_widget.resizeColumnToContents(2)

        # Connect to handle changes
        self.tree_widget.itemChanged.connect(self.on_item_check_changed)

    def on_item_check_changed(self, item: QTreeWidgetItem, column: int):
        if item.parent() is None:
            # It's a job (parent)
            state = item.checkState(0)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, state)

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
