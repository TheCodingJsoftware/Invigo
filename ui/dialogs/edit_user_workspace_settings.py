import os

from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QDoubleSpinBox, QLineEdit, QListWidget, QMessageBox, QPushButton

from utils.settings import Settings
from utils.workspace.workspace_settings import WorkspaceSettings


class EditUserWorkspaceSettingsDialog(QDialog):
    def __init__(self, workspace_settings: WorkspaceSettings, parent):
        super().__init__(parent)
        uic.loadUi("ui/dialogs/edit_user_workspace_settings.ui", self)
        self.parent = parent

        self.workspace_settings = workspace_settings

        self.setWindowTitle("Edit user workspace settings")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.settings_file = Settings()

        self.lineEdit_username = self.findChild(QLineEdit, "lineEdit_username")
        self.lineEdit_username.setText(os.getlogin())

        self.pushButton_view_parts = self.findChild(QPushButton, "pushButton_view_parts")
        self.pushButton_view_parts.setChecked(self.settings_file.get_value("user_workspace_settings").get("view_parts", True))
        self.pushButton_view_assemblies = self.findChild(QPushButton, "pushButton_view_assemblies")
        self.pushButton_view_assemblies.setChecked(self.settings_file.get_value("user_workspace_settings").get("view_assemblies", True))

        self.listWidget_process_tags = self.findChild(QListWidget, "listWidget_process_tags")
        self.listWidget_process_tags.addItems(self.workspace_settings.get_all_tags())
        for row in range(self.listWidget_process_tags.count()):
            item = self.listWidget_process_tags.item(row)
            if item.text() in self.settings_file.get_value("user_workspace_settings").get("visible_process_tags", []):
                item.setSelected(True)

        self.pushButton_apply = self.findChild(QPushButton, "pushButton_apply")

        self.pushButton_apply.clicked.connect(self.save_and_apply)
        self.pushButton_cancel = self.findChild(QPushButton, "pushButton_cancel")
        self.pushButton_cancel.clicked.connect(self.reject)

    def save_and_apply(self):
        selected_tags = []
        for row in range(self.listWidget_process_tags.count()):
            item = self.listWidget_process_tags.item(row)
            if item.isSelected():
                selected_tags.append(item.text())

        if not (self.pushButton_view_parts.isChecked() or self.pushButton_view_assemblies.isChecked()):
            msg = QMessageBox(QMessageBox.Icon.Information, "Workspace User Settings", "You need to select at least one visible view mode.", QMessageBox.StandardButton.Ok, self)
            msg.exec()
            return

        if not selected_tags:
            msg = QMessageBox(QMessageBox.Icon.Information, "Workspace User Settings", "You need to select at least one visible process tag.", QMessageBox.StandardButton.Ok, self)
            msg.exec()
            return

        settings = {
            "view_parts": self.pushButton_view_parts.isChecked(),
            "view_assemblies": self.pushButton_view_assemblies.isChecked(),
            "visible_process_tags": selected_tags,
        }
        self.settings_file.set_value("user_workspace_settings", settings)
        self.accept()
