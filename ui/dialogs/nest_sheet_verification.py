from functools import partial

from PyQt6 import uic
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QAbstractItemView, QDialog

from utils.dialog_buttons import DialogButtons
from utils.sheet_settings.sheet_settings import SheetSettings


class NestSheetVerification(QDialog):
    def __init__(
        self,
        message,
        thickness,
        material,
        sheet_settings: SheetSettings,
        parent=None,
    ) -> None:
        super().__init__(parent)
        uic.loadUi("ui/dialogs/nest_sheet_verification.ui", self)

        self.sheet_settings = sheet_settings
        self.sheet_settings.load_data()
        self.message = message
        self.response: str = DialogButtons.cancel

        self.setWindowTitle("Sheet Nest Verification")
        self.setWindowIcon(QIcon("icons/icon.png"))

        self.pushButton_set.clicked.connect(partial(self.button_press, DialogButtons.set))
        self.pushButton_skip.clicked.connect(partial(self.button_press, DialogButtons.skip))
        self.pushButton_cancel.clicked.connect(self.reject)

        self.listWidget_thicknesses.addItems(self.sheet_settings.get_thicknesses())
        self.listWidget_thicknesses.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        try:
            self.listWidget_thicknesses.setCurrentRow(self.sheet_settings.get_thicknesses().index(thickness))
        except ValueError:
            self.message += f'\n\nNOTICE: "{thickness}" is not in the global thickness list in "sheet_settings.json"; to add it go to Sheet Settings > Add Thickness'

        self.listWidget_materials.addItems(self.sheet_settings.get_materials())
        self.listWidget_materials.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        try:
            self.listWidget_materials.setCurrentRow(self.sheet_settings.get_materials().index(material))
        except ValueError:
            self.message += f'\n\nNOTICE: "{material}" is not in the global material list in "sheet_settings.json"; to add it go to > Sheet Settings > Add Material'

        self.lblMessage.setText(self.message)

    def button_press(self, text) -> None:
        self.response = text
        self.accept()

    def get_selected_material(self) -> str:
        try:
            return self.listWidget_materials.currentItem().text()
        except AttributeError:
            return None

    def get_selected_thickness(self) -> str:
        try:
            return self.listWidget_thicknesses.currentItem().text()
        except AttributeError:
            return None
