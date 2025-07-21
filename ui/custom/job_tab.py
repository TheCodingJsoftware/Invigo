import contextlib
from functools import partial
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.custom.job_tab_widget import JobTabWidget
from ui.theme import theme_var
from ui.widgets.job_widget import JobWidget
from utils.workspace.job import Job, JobStatus

if TYPE_CHECKING:
    from ui.windows.main_window import MainWindow


class PopoutWidget(QWidget):
    def __init__(self, tab_data: dict[str, str], layout_to_popout: QVBoxLayout, parent=None):
        super().__init__(parent)
        self._parent_widget: MainWindow = parent
        self.tab_data = tab_data

        self.tab_name = self.tab_data["object_name"]
        self.tab_icon = self.tab_data["icon"]

        self.original_layout = layout_to_popout
        self.original_layout_parent: "JobTab" = self.original_layout.parentWidget()
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle(self.tab_name)
        self.setLayout(self.original_layout)
        self.setObjectName("popout_widget")

    def closeEvent(self, event):
        if self.original_layout_parent:
            self.original_layout_parent.setLayout(self.original_layout)
            self.original_layout_parent.pushButton_popout.setIcon(QIcon("icons/open_in_new.png"))
            self.original_layout_parent.pushButton_popout.clicked.disconnect()
            self.original_layout_parent.pushButton_popout.clicked.connect(self.original_layout_parent.popout)
        super().closeEvent(event)


class JobTab(QWidget):
    saveJob = pyqtSignal(Job)
    printJob = pyqtSignal(Job)
    reloadJob = pyqtSignal(JobWidget)

    def __init__(self, tab_data: dict[str, str], parent):
        super().__init__(parent)
        self._parent_widget: MainWindow = parent
        self.tab_data = tab_data

        self.tab_name = self.tab_data["object_name"]
        self.tab_icon = self.tab_data["icon"]

        self.job_manager = self._parent_widget.job_manager
        self.job_preferences = self._parent_widget.job_preferences

        self.job_widgets: list[JobWidget] = []
        self.current_job: Job | None = None
        self.default_job_status: JobStatus | None = None

        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_current_job)

        self.shortcut_open_printout = QShortcut(QKeySequence("Ctrl+P"), self)
        self.shortcut_open_printout.activated.connect(self.open_printout)

        self.load_ui()

    def load_ui(self):
        self.jobs_layout = QVBoxLayout(self)
        self.jobs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.jobs_layout.setContentsMargins(0, 0, 9, 0)

        self.job_tab = JobTabWidget(self)
        self.job_tab.tabCloseRequested.connect(self.close_tab)
        self.job_tab.tabBarDoubleClicked.connect(self.rename_tab)
        self.job_tab.currentChanged.connect(self.tab_changed)
        self.jobs_layout.addWidget(self.job_tab)

        self.add_job_button = QPushButton("Add Job", self)
        self.add_job_button.setStyleSheet("border-radius: 0px; padding: 2px;")
        self.add_job_button.clicked.connect(self.add_job)
        self.job_tab.setCornerWidget(self.add_job_button, Qt.Corner.TopRightCorner)

        self.setLayout(self.jobs_layout)

    def workspace_settings_changed(self):
        for job_widget in self.job_widgets:
            job_widget.workspace_settings_changed()

    def add_job(self, new_job: Optional[Job] = None) -> JobWidget:
        if not new_job:
            job = Job({}, self.job_manager)
            job.name = f"Enter Job Name{len(self.job_widgets)}"
            job.status = self.default_job_status
            job.order_number = self._parent_widget.order_number
        else:
            job = new_job

        job_widget = JobWidget(job, self)
        job_widget.reloadJob.connect(self.reloadJob.emit)

        self.job_tab.addTab(job_widget, job.name)

        self.job_widgets.append(job_widget)

        if self.job_tab.count() == 1:
            self.job_tab.setTabsClosable(False)
        else:
            self.job_tab.setTabsClosable(True)
        self.job_tab.setCurrentIndex(self.job_tab.count() - 1)
        self.tab_changed()
        return job_widget

    def reload_job(self, job: Job):
        current_index = self.job_tab.currentIndex()
        if current_index != -1:
            old_widget = self.job_tab.widget(current_index)
            new_widget = JobWidget(job, self)
            new_widget.reloadJob.connect(self.reloadJob.emit)

            for assembly in job.assemblies:
                new_widget.load_assembly(assembly)

            self.job_tab.removeTab(current_index)
            self.job_tab.insertTab(current_index, new_widget, job.name)
            self.job_tab.setCurrentIndex(current_index)

            self.job_widgets[current_index] = new_widget

            old_widget.deleteLater()

            self.set_job_widget_scroll_position_with_delay(job, new_widget)
            self.current_job = job

    def load_job(self, job: Job):
        job_widget = self.add_job(job)
        for assembly in job.assemblies:
            job_widget.load_assembly(assembly)
        self.current_job = job
        self.job_tab.setCurrentIndex(self.get_tab_index(job))
        self.set_job_widget_scroll_position_with_delay(job, job_widget)

    def set_job_widget_scroll_position(self, job: Job, job_widget: JobWidget):
        x, y = self.job_preferences.get_job_scroll_position(job.name)
        job_widget.scrollArea.verticalScrollBar().setValue(y)
        job_widget.scrollArea.horizontalScrollBar().setValue(x)

    def set_job_widget_scroll_position_with_delay(self, job: Job, job_widget: JobWidget):
        self.timer = QTimer(self)  # For setting scroll in job widget
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(partial(self.execute_set_job_widget_scroll_position, job, job_widget))
        self.timer.start(500)

    def execute_set_job_widget_scroll_position(self, job: Job, job_widget: JobWidget):
        self.set_job_widget_scroll_position(job, job_widget)
        self.timer = None  # Clean up the timer

    def get_tab_index(self, job: Job) -> int:
        return next(
            (i for i, job_widget in enumerate(self.job_widgets) if job_widget.job == job),
            0,
        )

    def tab_changed(self):
        if not self.get_active_job():
            return
        if self.current_job and self.current_job.unsaved_changes:
            msg = QMessageBox(
                QMessageBox.Icon.Information,
                "Unsaved changes",
                f"There are unsaved changes in {self._parent_widget.last_selected_menu_tab}, {self.current_job.name}.",
            )
            msg.exec()
        self.current_job = self.get_active_job()
        self.update_job_save_status(self.current_job)

    def get_active_tab(self) -> str:
        return self.job_tab.tabText(self.job_tab.currentIndex())

    def get_job(self, job_name: str) -> Optional[Job]:
        return next(
            (job_widget.job for job_widget in self.job_widgets if job_widget.job.name == job_name),
            None,
        )

    def get_active_jobs(self) -> list[Job]:
        return [job_widget.job for job_widget in self.job_widgets]

    def get_active_job(self) -> Job | None:
        return next(
            (job_widget.job for job_widget in self.job_widgets if job_widget.job.name == self.get_active_tab()),
            None,
        )

    def get_active_job_widget(self) -> JobWidget:
        active_job = self.job_widgets[self.get_tab_index(self.current_job)]
        return next(
            (self.job_tab.widget(tab_index) for tab_index in range(self.job_tab.count()) if self.job_tab.widget(tab_index) == active_job),
            None,
        )

    def rename_tab(self, tab_index: int):
        active_tab = self.get_active_tab()
        new_name, ok = QInputDialog.getText(self, "Rename Job", "Enter new job name:", text=active_tab)
        if ok and new_name:
            self.current_job.name = new_name
            self.job_tab.setTabText(tab_index, new_name)
            self.current_job.changes_made()
            self.update_job_save_status(self.current_job)

    def duplicate_job(self, job: Job):
        new_job = Job(job.to_dict(), self)
        new_job.name = job.name
        self.load_job(new_job)

    def close_current_tab(self):
        self.job_tab.removeTab(self.job_tab.currentIndex())

    def close_tab(self, tab_index: int):
        job_to_delete = self.job_widgets[tab_index]
        self.job_widgets.remove(job_to_delete)
        self.job_tab.removeTab(tab_index)
        if self.job_tab.count() == 1:
            self.job_tab.setTabsClosable(False)
        else:
            self.job_tab.setTabsClosable(True)

    def popout(self):
        self.popout_widget = PopoutWidget(self.tab_data, self.layout(), self._parent_widget)
        self.popout_widget.show()
        self.pushButton_popout.setIcon(QIcon("icons/dock_window.png"))
        self.pushButton_popout.clicked.disconnect()
        self.pushButton_popout.clicked.connect(self.popout_widget.close)

    def sync_changes(self):
        self.job_manager.sync_changes(self.tab_name)

    def save_current_job(self):
        self.current_job.unsaved_changes = False
        self.saveJob.emit(self.current_job)
        self.update_job_save_status(self.current_job)

    def open_printout(self):
        # This saves the job before printing
        self.current_job.unsaved_changes = False
        self.printJob.emit(self.current_job)
        self.update_job_save_status(self.current_job)

    def job_changed(self, job: Job):
        job.changes_made()
        self.update_job_save_status(job)

    def update_job_save_status(self, job: Job):
        SAVED_JOB_STYLE = f"background-color: {theme_var('primary-green')}; color: {theme_var('on-primary-green')}; padding: 5px; border-radius: 5px;"
        UNSAVED_JOB_STYLE = f"background-color: {theme_var('primary-yellow')}; color: {theme_var('on-primary-yellow')}; padding: 5px; border-radius: 5px;"

        if self._parent_widget.tab_text(self._parent_widget.stackedWidget.currentIndex()) == "job_planner_tab":
            if job.unsaved_changes:
                self._parent_widget.label_job_save_status.setText("You have unsaved changes")
                self._parent_widget.label_job_save_status.setStyleSheet(UNSAVED_JOB_STYLE)
            else:
                self._parent_widget.label_job_save_status.setText("Job is saved")
                self._parent_widget.label_job_save_status.setStyleSheet(SAVED_JOB_STYLE)
        elif self._parent_widget.tab_text(self._parent_widget.stackedWidget.currentIndex()) == "job_quoter_tab":
            if job.unsaved_changes:
                self._parent_widget.label_job_save_status_2.setText("You have unsaved changes")
                self._parent_widget.label_job_save_status_2.setStyleSheet(UNSAVED_JOB_STYLE)
            else:
                self._parent_widget.label_job_save_status_2.setText("Job is saved")
                self._parent_widget.label_job_save_status_2.setStyleSheet(SAVED_JOB_STYLE)

    def update_tables(self):
        for job_widget in self.job_widgets:
            job_widget.update_tables()

    def clear_layout(self, layout: QVBoxLayout | QHBoxLayout | QWidget):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())
