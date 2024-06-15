from datetime import datetime, timedelta

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QWidget,
)

from ui.custom_widgets import ClickableLabel, DeletePushButton


class SavedPlanningJobItem(QWidget):
    load_job = pyqtSignal()
    open_webpage = pyqtSignal()
    delete_job = pyqtSignal()
    job_type_changed = pyqtSignal()

    def __init__(self, file_info: dict[str, str], parent: QWidget) -> None:
        super().__init__(parent)
        uic.loadUi("ui/job_plan_widget.ui", self)

        modified_date = datetime.fromtimestamp(file_info.get("modified_date")).strftime("%A, %B %d, %Y, %I:%M:%S %p")
        status = file_info.get("status", "Planning")
        base_color = file_info.get("color")

        self.comboBox_job_status = self.findChild(QComboBox, "comboBox_job_status")
        self.pushButton_load_job = self.findChild(QPushButton, "pushButton_load_job")
        self.label_modified_date = self.findChild(QLabel, "label_modified_date")
        self.pushButton_open_in_browser = self.findChild(QPushButton, "pushButton_open_in_browser")
        self.pushButton_delete = self.findChild(QPushButton, "pushButton_delete")

        self.comboBox_job_status.setEnabled(False)
        self.comboBox_job_status.wheelEvent = lambda event: None
        self.comboBox_job_status.setCurrentText(status)
        self.comboBox_job_status.currentTextChanged.connect(self.job_type_changed.emit)

        self.label_modified_date.setText(f"Modified: {modified_date}")

        self.pushButton_load_job.clicked.connect(self.load_job.emit)

        self.pushButton_open_in_browser.clicked.connect(self.open_webpage.emit)

        self.pushButton_delete.clicked.connect(self.delete_job.emit)
