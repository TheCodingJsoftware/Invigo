from datetime import datetime

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

from ui.icons import Icons
from ui.widgets.job_plan_widget_UI import Ui_Form


class SavedPlanningJobItem(QWidget, Ui_Form):
    load_job = pyqtSignal()
    open_webpage = pyqtSignal()
    delete_job = pyqtSignal()
    job_type_changed = pyqtSignal()

    def __init__(self, job_data: dict[str, str], parent: QWidget):
        super().__init__(parent)
        self.setupUi(self)

        modified_date = datetime.fromisoformat(job_data.get("updated_at")).strftime(
            "%A, %B %d, %Y, %I:%M:%S %p"
        )
        job_type = job_data.get("job_data", {}).get("type", 1)

        self.pushButton_open_in_browser.setIcon(Icons.printer_icon)
        self.pushButton_delete.setIcon(Icons.delete_icon)
        self.pushButton_delete.setObjectName("delete_button")

        self.comboBox_job_status.wheelEvent = lambda event: self.parent().wheelEvent(
            event
        )
        self.comboBox_job_status.setCurrentIndex(job_type - 1)
        self.comboBox_job_status.currentTextChanged.connect(self.job_type_changed.emit)

        self.label_modified_date.setText(f"Modified: {modified_date}")

        self.pushButton_load_job.clicked.connect(self.load_job.emit)
        self.pushButton_load_job.setObjectName("load_job")

        self.pushButton_open_in_browser.clicked.connect(self.open_webpage.emit)

        self.pushButton_delete.clicked.connect(self.delete_job.emit)
