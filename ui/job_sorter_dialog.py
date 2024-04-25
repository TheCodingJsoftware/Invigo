import os.path
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QFile, Qt, QTextStream
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QDialog, QFileDialog, QPushButton, QRadioButton

from threads.job_sorter_thread import JobSorterThread
from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile


class JobSorterDialog(QDialog):
    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.information,
        button_names: str = DialogButtons.ok_cancel,
        title: str = __name__,
        message: str = "",
        options: list = None,
    ) -> None:
        super(JobSorterDialog, self).__init__(parent)
        uic.loadUi("ui/job_sorter_dialog.ui", self)
        self.parent = parent

        self.icon_name = icon_name
        self.button_names = button_names
        self.title = title
        self.message = message
        self.inputText: str = ""
        self.excel_file_path: str = ""
        self.directory_to_sort: str = ""
        self.output_directory: str = ""
        self.threads = []

        self.setWindowIcon(QIcon("icons/icon.png"))

        self.setWindowTitle(self.title)
        self.lblMessage.setText(self.message)

        svg_icon = self.get_icon(icon_name)
        svg_icon.setFixedSize(62, 50)
        self.iconHolder.addWidget(svg_icon)

        self.pushButton_set_excel_file_path.clicked.connect(self.set_excel_file_path)
        self.pushButton_set_sorting_directory.clicked.connect(self.set_sorting_directory)
        self.pushButton_set_output_directory.clicked.connect(self.set_output_directory)
        self.lineEdit_path_to_data_file.textChanged.connect(self.paths_changes)
        self.lineEdit_directory_to_sort.textChanged.connect(self.paths_changes)
        self.lineEdit_output_directory.textChanged.connect(self.paths_changes)
        self.lineEdit_job_name.textChanged.connect(self.paths_changes)

        self.pushButton_sort.clicked.connect(self.sort)

        self.resize(600, 200)

        self.load_theme()

    def sort(self) -> None:
        job_sorter_thread = JobSorterThread(
            self.parent,
            self.job_name,
            self.excel_file_path,
            self.directory_to_sort,
            self.output_directory,
        )
        self.threads.append(job_sorter_thread)
        job_sorter_thread.signal.connect(self.thread_response)
        job_sorter_thread.start()

    def thread_response(self, response) -> None:
        if response == "Done":
            self.parent.show_message_dialog(
                title="Done",
                message=f"Jobs sorted into {self.output_directory}/{self.job_name}",
            )
        else:
            self.parent.show_error_dialog(title="Error", message=str(response))

    def paths_changes(self) -> None:
        self.excel_file_path: str = self.lineEdit_path_to_data_file.text()
        self.directory_to_sort: str = self.lineEdit_directory_to_sort.text()
        self.output_directory: str = self.lineEdit_output_directory.text()
        self.job_name: str = self.lineEdit_job_name.text()
        self.pushButton_sort.setEnabled(bool(self.excel_file_path and self.directory_to_sort and self.output_directory and self.job_name))

    def set_excel_file_path(self) -> None:
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Excel Files (*.xlsx *.xls)")
        file_dialog.setWindowTitle("Select Excel File")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_file = file_dialog.selectedFiles()[0]
            self.excel_file_path = selected_file
            self.lineEdit_path_to_data_file.setText(selected_file)

    def set_sorting_directory(self) -> None:
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("Select Folder")
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_folder = file_dialog.selectedFiles()[0]
            self.directory_to_sort = selected_folder
            self.lineEdit_directory_to_sort.setText(selected_folder)

    def set_output_directory(self) -> None:
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("Select Folder")
        file_dialog.setFileMode(QFileDialog.FileMode.Directory)

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_folder = file_dialog.selectedFiles()[0]
            self.output_directory = selected_folder
            self.lineEdit_output_directory.setText(selected_folder)

    def load_theme(self) -> None:
        set_theme(self, theme="dark")

    def get_icon(self, path_to_icon: str) -> QSvgWidget:
        return QSvgWidget(f"icons/{path_to_icon}")
