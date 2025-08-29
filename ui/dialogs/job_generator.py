import logging
import traceback
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, QThreadPool, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QDialog, QTreeWidget, QTreeWidgetItem

from ui.custom_widgets import HumbleDoubleSpinBox
from ui.dialogs.job_generator_UI import Ui_Form
from utils.settings import Settings
from utils.workers.jobs.get_all_jobs import GetAllJobsWorker
from utils.workers.jobs.get_job import GetJobWorker
from utils.workers.runnable_chain import RunnableChain
from utils.workspace.assembly import Assembly
from utils.workspace.job import Job, JobIcon

if TYPE_CHECKING:
    pass


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
        self.tree_widget.itemChanged.connect(self.on_item_check_changed)
        self.tree_widget.setColumnCount(3)
        self.tree_widget.setHeaderLabels(["Job/Assembly Name", "Status", "Quantity"])
        self.tree_widget.setSortingEnabled(True)
        self.jobs_layout.addWidget(self.tree_widget)
        self.tree_widget_items: dict[int, dict[str, HumbleDoubleSpinBox | Job | Assembly | QTreeWidgetItem]] = {}
        self.pushButton_cancel.clicked.connect(self.reject)
        self.pushButton_merge.clicked.connect(self.accept)
        self.lineEdit_job_name.textChanged.connect(self.on_job_name_changed)
        self.lineEdit_search.textChanged.connect(self.on_search_changed)
        self.assembly_states: dict[int, dict[str, float | Qt.CheckState]] = {}
        self.settings = Settings()
        self.checkBox_bring_along_subassemblies.setChecked(self.settings.get_value("bring_along_sub_assemblies"))
        self.checkBox_bring_along_subassemblies.clicked.connect(self.save_checkbox_state)
        self.search_text = ""
        self.get_all_jobs()

        self.resize(800, 800)

    def save_checkbox_state(self):
        self.settings.set_value("bring_along_sub_assemblies", self.checkBox_bring_along_subassemblies.isChecked())

    def reload_tree(self):
        self.tree_widget.blockSignals(True)
        self.tree_widget.clear()
        self.tree_widget_items.clear()

        for job in self.jobs:
            if self.search_text:
                if not any(self.search_text.lower() in assembly.name.lower() for assembly in job.assemblies):
                    continue

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
                if self.search_text.lower() and self.search_text.lower() not in assembly.name.lower() and not self._has_matching_subassembly(assembly):
                    continue
                self._add_assembly_recursive(job, job_item, assembly, job.color)

            for col in range(self.tree_widget.columnCount()):
                job_item.setForeground(col, QColor(job.color))

        self.tree_widget.expandAll()
        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)
        self.tree_widget.resizeColumnToContents(2)
        self.tree_widget.sortByColumn(1, Qt.SortOrder.DescendingOrder)

        QTimer.singleShot(1, self._update_spinboxes)
        self.tree_widget.blockSignals(False)

    def _add_assembly_recursive(self, job: Job, parent_item: QTreeWidgetItem, assembly: Assembly, color: str):
        if self.search_text and self.search_text not in assembly.name.lower() and not self._has_matching_subassembly(assembly):
            return

        assembly_item = QTreeWidgetItem()
        assembly_item.setText(0, assembly.name)
        assembly_item.setFlags(assembly_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

        cached = self.assembly_states.get(id(assembly), {})
        check_state = cached.get("check_state", Qt.CheckState.Unchecked)
        quantity = cached.get("quantity", assembly.meta_data.quantity)

        assembly_item.setCheckState(0, check_state)

        spin_box = HumbleDoubleSpinBox(self.tree_widget)
        spin_box.setDecimals(0)
        spin_box.setToolTip(f"Original: {assembly.meta_data.quantity}")
        spin_box.setMinimum(1)
        spin_box.setMaximum(9999999)
        spin_box.setValue(quantity)
        spin_box.valueChanged.connect(lambda val, asm=assembly: self._on_spinbox_value_changed(asm, val))

        parent_item.addChild(assembly_item)
        self.tree_widget.setItemWidget(assembly_item, 2, spin_box)

        self.tree_widget_items[id(assembly_item)] = {
            "job": job,
            "item": assembly_item,
            "assembly": assembly,
            "spinbox": spin_box,
        }

        for col in range(self.tree_widget.columnCount()):
            assembly_item.setForeground(col, QColor(color))

        for sub in assembly.sub_assemblies:
            self._add_assembly_recursive(job, assembly_item, sub, color)

    def _has_matching_subassembly(self, assembly: Assembly) -> bool:
        if self.search_text.lower() in assembly.name.lower():
            return True
        return any(self._has_matching_subassembly(sub) for sub in assembly.sub_assemblies)

    def on_search_changed(self, text: str):
        self.search_text = text.strip().lower()
        self.reload_tree()

    def merge(self) -> Job | None:
        if not self.assembly_states:
            return None

        merged_job = Job({}, self._parent_widget.job_manager)
        merged_job.name = self.lineEdit_job_name.text().strip()

        for job in self.jobs:
            for assembly in job.assemblies:
                self._merge_selected_assemblies(merged_job, assembly)

        if not merged_job.assemblies:
            return None

        return merged_job

    def _merge_selected_assemblies(self, merged_job: Job, assembly: Assembly):
        state = self.assembly_states.get(id(assembly))
        if state and state.get("check_state") == Qt.CheckState.Checked:
            cloned = Assembly(assembly.to_dict(), merged_job)
            cloned.meta_data.quantity = state.get("quantity", assembly.meta_data.quantity)
            if not self.checkBox_bring_along_subassemblies.isChecked():
                cloned.sub_assemblies.clear()
            merged_job.add_assembly(cloned)

        for sub in assembly.sub_assemblies:
            self._merge_selected_assemblies(merged_job, sub)

    def on_job_name_changed(self, text: str):
        self.pushButton_merge.setEnabled(bool(text.strip()))

    def on_item_check_changed(self, item: QTreeWidgetItem, column: int):
        self.tree_widget.blockSignals(True)

        info = self.tree_widget_items.get(id(item))
        if not info or "assembly" not in info:
            self.tree_widget.blockSignals(False)
            return

        assembly = info["assembly"]
        state = item.checkState(0)
        self.assembly_states[id(assembly)] = {
            "check_state": state,
            "quantity": int(info["spinbox"].value())
        }

        self._update_spinboxes()
        self.tree_widget.blockSignals(False)

    def _on_spinbox_value_changed(self, assembly: Assembly, value: float):
        if id(assembly) not in self.assembly_states:
            self.assembly_states[id(assembly)] = {}
        self.assembly_states[id(assembly)]["quantity"] = int(value)

    def _update_spinboxes(self):
        def recurse(item: QTreeWidgetItem):
            info = self.tree_widget_items.get(id(item))
            if info and "spinbox" in info:
                spinbox = info["spinbox"]
                spinbox.setHidden(item.checkState(0) != Qt.CheckState.Checked)

            for i in range(item.childCount()):
                recurse(item.child(i))

        for i in range(self.tree_widget.topLevelItemCount()):
            recurse(self.tree_widget.topLevelItem(i))

    def get_all_jobs(self):
        get_all_jobs_worker = GetAllJobsWorker()
        get_all_jobs_worker.signals.success.connect(self.on_get_all_jobs_result)
        QThreadPool.globalInstance().start(get_all_jobs_worker)

    def on_get_all_jobs_result(self, result):
        self.chain = RunnableChain(self._parent_widget)

        for job in result:
            get_job_worker = GetJobWorker(job["id"])
            self.chain.add(get_job_worker, self.on_get_job_result)

        self.chain.finished.connect(self.reload_tree)
        self.chain.start()

    def on_get_job_result(self, result, next_step: Callable):
        try:
            job = Job(result, self._parent_widget.job_manager)
            self.jobs.append(job)
        except Exception as e:
            # include traceback
            logging.error(f"Error loading job: {e}\n{traceback.format_exc()}")
        next_step()
