from datetime import datetime

from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QLabel, QPushButton, QWidget


class SavedPlanningJobItem(QWidget):
    load_job = pyqtSignal()
    open_webpage = pyqtSignal()
    delete_job = pyqtSignal()
    job_type_changed = pyqtSignal()

    def __init__(self, file_info: dict[str, str], parent: QWidget) -> None:
        super().__init__(parent)
        uic.loadUi("ui/widgets/job_plan_widget.ui", self)

        modified_date = datetime.fromtimestamp(file_info.get("modified_date")).strftime(
            "%A, %B %d, %Y, %I:%M:%S %p"
        )
        job_type = file_info.get("type", 0)

        self.comboBox_job_status = self.findChild(QComboBox, "comboBox_job_status")
        self.pushButton_load_job = self.findChild(QPushButton, "pushButton_load_job")
        self.label_modified_date = self.findChild(QLabel, "label_modified_date")
        self.pushButton_open_in_browser = self.findChild(
            QPushButton, "pushButton_open_in_browser"
        )
        self.pushButton_delete = self.findChild(QPushButton, "pushButton_delete")

        self.comboBox_job_status.wheelEvent = lambda event: None
        self.comboBox_job_status.setCurrentIndex(job_type - 1)
        self.comboBox_job_status.currentTextChanged.connect(self.job_type_changed.emit)

        self.label_modified_date.setText(f"Modified: {modified_date}")

        self.pushButton_load_job.clicked.connect(self.load_job.emit)

        self.pushButton_open_in_browser.clicked.connect(self.open_webpage.emit)

        self.pushButton_delete.clicked.connect(self.delete_job.emit)
