import os.path
from functools import partial

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QFileDialog, QPushButton

from config.environments import Environment
from ui.dialogs.select_files_to_download_dialog_UI import Ui_Form
from ui.icons import Icons


class SelectFilesToDownloadDialog(QDialog, Ui_Form):
    def __init__(
        self,
        files: list[str],
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.files = self.sort_files_by_extension(files)

        self.setWindowTitle("Download files")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        self.lblMessage.setText("Select the files you want to download.")

        self.load_quick_select_buttons()

        self.listWidget_files.addItems(self.files)
        self.listWidget_files.selectAll()

        self.pushButton_download.clicked.connect(self.accept)
        self.pushButton_cancel.clicked.connect(self.reject)

        self.lineEdit_download_path.setText(os.path.join(Environment.DATA_PATH, "data", "workspace"))
        self.lineEdit_download_path.textChanged.connect(self.lineEdit_download_path_changed)

        self.pushButton_selected_directory.clicked.connect(self.select_directory)
        self.pushButton_selected_directory.setIcon(Icons.open_folder_icon)

    def lineEdit_download_path_changed(self):
        self.pushButton_download.setEnabled(bool(self.lineEdit_download_path.text()))

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select directory")
        if directory:
            self.lineEdit_download_path.setText(directory)

    def sort_files_by_extension(self, files: list[str]) -> list[str]:
        return sorted(files, key=lambda file: os.path.splitext(file)[1].upper())

    def button_press(self, button: QPushButton):
        extension = button.text().strip().lower()
        for index in range(self.listWidget_files.count()):
            item = self.listWidget_files.item(index)
            if item.text().lower().endswith(f".{extension}"):
                item.setSelected(button.isChecked())

    def load_quick_select_buttons(self):
        for file_extension in self.get_file_extensions():
            button = QPushButton(file_extension)
            button.setCheckable(True)
            button.setChecked(True)
            button.setFlat(True)
            button.setFixedWidth(100)
            button.clicked.connect(partial(self.button_press, button))
            self.quick_select_layout.addWidget(button)

    def get_file_extensions(self) -> list[str]:
        file_extensions: set[str] = set()
        for file in self.files:
            file_extensions.add(file.split(".")[-1].upper())
        return list(file_extensions)

    def get_download_directory(self) -> str:
        return self.lineEdit_download_path.text()

    def get_selected_items(self) -> list[str]:
        try:
            return [item.text() for item in self.listWidget_files.selectedItems()]
        except AttributeError:
            return None
