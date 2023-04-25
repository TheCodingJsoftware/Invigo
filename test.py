import json
import sys
import time
from datetime import datetime
from functools import partial

from PyQt5 import QtTest, uic
from PyQt5.QtCore import QAbstractListModel, QFile, QPoint, Qt, QTextStream, QTimer
from PyQt5.QtGui import QColor, QCursor, QFont, QIcon, QImage, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
    QWidgetItem,
    qApp,
)

from ui.theme import set_theme

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
from functools import partial

from ui.custom_widgets import (
    ClickableLabel,
    CostLineEdit,
    CurrentQuantitySpinBox,
    DeletePushButton,
    DragableLayout,
    ExchangeRateComboBox,
    HeaderScrollArea,
    HumbleComboBox,
    HumbleDoubleSpinBox,
    HumbleSpinBox,
    ItemCheckBox,
    ItemNameComboBox,
    NotesPlainTextEdit,
    PartNumberComboBox,
    POPushButton,
    PriorityComboBox,
    RichTextPushButton,
    ViewTree,
    set_default_dialog_button_stylesheet,
    set_status_button_stylesheet,
)

qt_creator_file = "test.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.margins = (15, 15, 5, 5)  # top, bottom, left, right
        self.margin_format = f"margin-top: {self.margins[0]}%; margin-bottom: {self.margins[1]}%; margin-left: {self.margins[2]}%; margin-right: {self.margins[3]}%;"
        # LOAD TABLE
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setShowGrid(True)
        self.tableWidget.setColumnCount(12)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setSelectionBehavior(0)
        self.tableWidget.setSelectionMode(0)
        self.tableWidget.setHorizontalHeaderLabels(
            (
                "Part Name;Part Number;Quantity Per Unit;Quantity in Stock;Item Price;USD/CAD;Total Cost in Stock;Total Unit Cost;Priority;Notes;PO;DEL;"
            ).split(";")
        )
        self.verticalLayout_2.addWidget(self.tableWidget)
        with open(r"data\testt.json", "r") as f:
            self.data = json.load(f)
        self.load_item()

    def load_item(self):

        for i in range(len(list(self.data["Polar G2"].keys()))):
            self.tableWidget.insertRow(i)
            self.tableWidget.setRowHeight(i, 60)
            item: str = list(self.data["Polar G2"].keys())[i]

            self.tableWidget.setItem(i, 0, QTableWidgetItem(item))
            # PART NUMBER

            self.tableWidget.setItem(
                i, 1, QTableWidgetItem(self.data["Polar G2"][item]["part_number"])
            )
            # UNIT QUANTITY
            unit_quantity = self.data["Polar G2"][item]["unit_quantity"]

            self.tableWidget.setItem(
                i, 2, QTableWidgetItem(str(self.data["Polar G2"][item]["unit_quantity"]))
            )
            # ITEM QUANTITY
            current_quantity = self.data["Polar G2"][item]["current_quantity"]

            self.tableWidget.setItem(
                i,
                3,
                QTableWidgetItem(str(self.data["Polar G2"][item]["current_quantity"])),
            )
            # PRICE
            price = self.data["Polar G2"][item]["price"]

            self.tableWidget.setItem(
                i, 4, QTableWidgetItem(str(self.data["Polar G2"][item]["price"]))
            )
            # EXCHANGE RATE
            combo_exchange_rate = ExchangeRateComboBox(
                parent=self,
                selected_item="USD" if True else "CAD",
                tool_tip="latest_change_use_exchange_rate",
            )
            combo_exchange_rate.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 5, combo_exchange_rate)
            # TOTAL COST
            total_cost_in_stock: float = current_quantity * price
            if total_cost_in_stock < 0:
                total_cost_in_stock = 0

            self.tableWidget.setItem(i, 6, QTableWidgetItem(str(total_cost_in_stock)))
            # TOTALE UNIT COST
            total_unit_cost: float = unit_quantity * price

            self.tableWidget.setItem(i, 7, QTableWidgetItem(str(total_unit_cost)))
            # PRIORITY
            priority = self.data["Polar G2"][item]["priority"]
            combo_priority = PriorityComboBox(
                parent=self,
                selected_item=priority,
                tool_tip="latest_change_priority",
            )
            if combo_priority.currentText() == "Medium":
                combo_priority.setStyleSheet("color: yellow; border-color: yellow;")
            elif combo_priority.currentText() == "High":
                combo_priority.setStyleSheet("color: red; border-color: red;")
            combo_priority.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 8, combo_priority)
            # NOTES
            notes = self.data["Polar G2"][item]["notes"]

            self.tableWidget.setItem(i, 9, QTableWidgetItem(notes))
            # PURCHASE ORDER
            po_menu = QMenu(self)
            btn_po = POPushButton(parent=self)
            btn_po.setMenu(po_menu)
            btn_po.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 10, btn_po)
            # DELETE
            btn_delete = DeletePushButton(
                parent=self,
                tool_tip=f"Delete {item} permanently from Polar G2",
                icon=QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/dark/trash.png"),
            )
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            btn_delete.clicked.connect(partial(self.delete, item))
            btn_delete.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 11, btn_delete)

        # self.tableWidget.resizeRowsToContents()
        self.tableWidget.resizeColumnsToContents()

    def delete(self, name):
        print(name)


app = QApplication(sys.argv)
set_theme(app, theme="dark")

# apply_stylesheet(app, theme='dark_blue.xml')
window = MainWindow()
window.show()
app.exec_()
