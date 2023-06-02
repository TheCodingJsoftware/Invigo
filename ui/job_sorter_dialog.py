import os.path
from functools import partial

from PyQt5 import QtSvg, uic
from PyQt5.QtCore import QFile, Qt, QTextStream
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QPushButton, QRadioButton, QFileDialog

from threads.job_sorter_thread import JobSorterThread
from ui.custom_widgets import set_default_dialog_button_stylesheet
from ui.theme import set_theme
from utils.dialog_buttons import DialogButtons
from utils.dialog_icons import Icons
from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class JobSorterDialog(QDialog):
    """
    Select dialog
    """

    def __init__(
        self,
        parent=None,
        icon_name: str = Icons.information,
        button_names: str = DialogButtons.ok_cancel,
        title: str = __name__,
        message: str = "",
        options: list = None,
    ) -> None:
        """
        It's a function that takes in a list of options and displays them in a list widget

        Args:
          parent: The parent widget of the dialog.
          icon_name (str): str = Icons.question,
          button_names (str): str = DialogButtons.ok_cancel,
          title (str): str = __name__,
          message (str): str = "",
          options (list): list = None,
        """
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
        self.theme: str = "dark"

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
        job_sorter_thread = JobSorterThread(self.parent, self.job_name, self.excel_file_path, self.directory_to_sort, self.output_directory)
        self.threads.append(job_sorter_thread)
        job_sorter_thread.signal.connect(self.thread_response)
        job_sorter_thread.start()

    def thread_response(self, response) -> None:
        if response == "Done":
            self.parent.show_message_dialog(title="Done", message=f"Jobs sorted into {self.output_directory}/{self.job_name}")
        else:
            self.parent.show_error_dialog(title="Error", message=str(response))

    def paths_changes(self) -> None:
        self.excel_file_path: str = self.lineEdit_path_to_data_file.text()
        self.directory_to_sort: str = self.lineEdit_directory_to_sort.text()
        self.output_directory: str = self.lineEdit_output_directory.text()
        self.job_name: str = self.lineEdit_job_name.text()
        self.pushButton_sort.setEnabled(
            True if self.excel_file_path and self.directory_to_sort and self.output_directory and self.job_name else False
        )

    def set_excel_file_path(self) -> None:
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Excel Files (*.xlsx *.xls)")
        file_dialog.setWindowTitle("Select Excel File")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec_() == QFileDialog.Accepted:
            selected_file = file_dialog.selectedFiles()[0]
            self.excel_file_path = selected_file
            self.lineEdit_path_to_data_file.setText(selected_file)

    def set_sorting_directory(self) -> None:
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("Select Folder")
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec_() == QFileDialog.Accepted:
            selected_folder = file_dialog.selectedFiles()[0]
            self.directory_to_sort = selected_folder
            self.lineEdit_directory_to_sort.setText(selected_folder)

    def set_output_directory(self) -> None:
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("Select Folder")
        file_dialog.setFileMode(QFileDialog.Directory)

        if file_dialog.exec_() == QFileDialog.Accepted:
            selected_folder = file_dialog.selectedFiles()[0]
            self.output_directory = selected_folder
            self.lineEdit_output_directory.setText(selected_folder)

    def load_theme(self) -> None:
        """
        It loads the stylesheet.qss file from the theme folder
        """
        set_theme(self, theme="dark")

    def get_icon(self, path_to_icon: str) -> QtSvg.QSvgWidget:
        """
        It returns a QSvgWidget object that is initialized with a path to an SVG icon

        Args:
          path_to_icon (str): The path to the icon you want to use.

        Returns:
          A QSvgWidget object.
        """
        return QtSvg.QSvgWidget(f"ui/BreezeStyleSheets/dist/pyqt6/{self.theme}/{path_to_icon}")
