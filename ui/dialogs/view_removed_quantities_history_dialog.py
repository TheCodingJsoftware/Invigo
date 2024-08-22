from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QTableWidgetItem

from ui.dialogs.view_removed_quantities_history_dialog_UI import Ui_Form
from ui.icons import Icons
from utils.history_file import HistoryFile


class ViewRemovedQuantitiesHistoryDialog(QDialog, Ui_Form):
    def __init__(
        self,
        parent,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.setWindowTitle("History")
        self.setWindowIcon(QIcon(Icons.invigo_icon))

        # CATOGRY HISTORY
        self.categoryHistoryTable.clear()
        self.categoryHistoryTable.setRowCount(0)
        self.categoryHistoryTable.setHorizontalHeaderLabels(("Date;Description;").split(";"))
        self.categoryHistoryTable.setColumnWidth(0, 270)
        self.categoryHistoryTable.setColumnWidth(1, 600)
        history_file = HistoryFile()
        for i, date, description in zip(
            range(len(history_file.get_data_from_category()["Date"])),
            history_file.get_data_from_category()["Date"],
            history_file.get_data_from_category()["Description"],
        ):
            self.categoryHistoryTable.insertRow(self.categoryHistoryTable.rowCount())
            self.categoryHistoryTable.setItem(i, 0, QTableWidgetItem(date))
            self.categoryHistoryTable.setItem(i, 1, QTableWidgetItem(description))
        # SINGLE ITEM HISTORY
        self.singleItemHistoryTable.clear()
        self.singleItemHistoryTable.setRowCount(0)
        self.singleItemHistoryTable.setHorizontalHeaderLabels(("Date;Description;").split(";"))
        self.singleItemHistoryTable.setColumnWidth(0, 270)
        self.singleItemHistoryTable.setColumnWidth(1, 600)
        for i, date, description in zip(
            range(len(history_file.get_data_from_single_item()["Date"])),
            history_file.get_data_from_single_item()["Date"],
            history_file.get_data_from_single_item()["Description"],
        ):
            self.singleItemHistoryTable.insertRow(self.singleItemHistoryTable.rowCount())
            self.singleItemHistoryTable.setItem(i, 0, QTableWidgetItem(date))
            self.singleItemHistoryTable.setItem(i, 1, QTableWidgetItem(description))
