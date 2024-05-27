from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox

from threads.job_sorter_thread import JobSorterThread


class JobSorterDialog(QDialog):
    def __init__(
        self,
        parent,
    ) -> None:
        super(JobSorterDialog, self).__init__(parent)
        uic.loadUi("ui/job_sorter_dialog.ui", self)
        self.parent = parent

        self.excel_file_path: str = ""
        self.directory_to_sort: str = ""
        self.output_directory: str = ""
        self.threads = []

        self.setWindowTitle("Job Sorter")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.pushButton_set_excel_file_path.clicked.connect(self.set_excel_file_path)
        self.pushButton_set_sorting_directory.clicked.connect(self.set_sorting_directory)
        self.pushButton_set_output_directory.clicked.connect(self.set_output_directory)
        self.lineEdit_path_to_data_file.textChanged.connect(self.paths_changes)
        self.lineEdit_directory_to_sort.textChanged.connect(self.paths_changes)
        self.lineEdit_output_directory.textChanged.connect(self.paths_changes)
        self.lineEdit_job_name.textChanged.connect(self.paths_changes)

        self.pushButton_sort.clicked.connect(self.sort)

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
            msg = QMessageBox(QMessageBox.Icon.Information, "Done", f"Jobs sorted into {self.output_directory}/{self.job_name}", QMessageBox.StandardButton.Ok, self)
            msg.exec()
        else:
            msg = QMessageBox(QMessageBox.Icon.Critical, "Error", str(response), QMessageBox.StandardButton.Ok, self)
            msg.exec()

    def paths_changes(self) -> None:
        self.excel_file_path: str = self.lineEdit_path_to_data_file.text()
        self.directory_to_sort: str = self.lineEdit_directory_to_sort.text()
        self.output_directory: str = self.lineEdit_output_directory.text()
        self.job_name: str = self.lineEdit_job_name.text()
        self.pushButton_sort.setEnabled(bool(self.excel_file_path and self.directory_to_sort and self.output_directory and self.job_name))

    def set_excel_file_path(self) -> None:
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Excel Files (*.xlsx)")
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
