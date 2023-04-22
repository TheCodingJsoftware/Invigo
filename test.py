import sys
import json
from datetime import datetime
import time
from functools import partial
from ui.theme import set_theme
from PyQt5 import QtTest, uic
from PyQt5.QtCore import QFile, QPoint, Qt, QTextStream, QTimer, QAbstractListModel
from PyQt5.QtGui import QCursor, QFont, QIcon, QPixmap, QImage
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
    QWidgetItem,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
    qApp,
)
from PyQt5.QtGui import QPalette, QColor
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
from ui.custom_widgets import (
    ClickableLabel,
    CostLineEdit,
    CurrentQuantitySpinBox,
    DeletePushButton,
    DragableLayout,
    ExchangeRateComboBox,
    HeaderScrollArea,
    ItemCheckBox,
    HumbleComboBox,
    HumbleDoubleSpinBox,
    HumbleSpinBox,
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

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.margins = (15, 15, 5, 5) # top, bottom, left, right
        self.margin_format = f'margin-top: {self.margins[0]}%; margin-bottom: {self.margins[1]}%; margin-left: {self.margins[2]}%; margin-right: {self.margins[3]}%;'
        # LOAD TABLE
        self.tableWidget = QTableWidget(self)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.setColumnCount(12)
        self.tableWidget.setSelectionBehavior(1)
        self.tableWidget.setSelectionMode(1)
        self.tableWidget.setHorizontalHeaderLabels(
            ("Part Name;Part Number;Quantity Per Unit;Quantity in Stock;Item Price;USD/CAD;Total Cost in Stock;Total Unit Cost;Priority;Notes;PO;DEL;").split(";")
        )
        self.verticalLayout_2.addWidget(self.tableWidget)
        with open(r'data\testt.json', 'r') as f:
            data = json.load(f)
        self._iter = iter(range(len(list(data['Polar G2'].keys()))))
        self._timer = QTimer(
            interval=0, timeout=partial(self.load_item, data)
        )
        self._timer.start()
    def load_item(self, data) -> None:
        # PART NAME
        try:
            i = next(self._iter)
            self.tableWidget.setEnabled(False)
            # QApplication.setOverrideCursor(Qt.BusyCursor)
        except StopIteration:
            self._timer.stop()
            self.tableWidget.resizeRowsToContents()
            self.tableWidget.resizeColumnsToContents()
            self.tableWidget.setEnabled(True)
        else:
            self.tableWidget.insertRow(i)
            self.tableWidget.setRowHeight(i, 60)
            item: str = list(data['Polar G2'].keys())[i]
            item_name = ItemNameComboBox(
                parent=self,
                selected_item=item,
                items=[item],
                tool_tip='latest_change_name',
            )
            item_name.setContextMenuPolicy(Qt.CustomContextMenu)
            item_name.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 0, item_name)
            # PART NUMBER
            line_edit_part_number = PartNumberComboBox(
                parent=self,
                selected_item=data['Polar G2'][item]['part_number'],
                items=[data['Polar G2'][item]['part_number']],
                tool_tip='latest_change_part_number',
            )
            line_edit_part_number.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 1, line_edit_part_number)
            # UNIT QUANTITY
            unit_quantity=data['Polar G2'][item]['unit_quantity']
            spin_unit_quantity = HumbleDoubleSpinBox(self)
            spin_unit_quantity.setValue(unit_quantity)
            spin_unit_quantity.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 2, spin_unit_quantity)
            # ITEM QUANTITY
            current_quantity=data['Polar G2'][item]['current_quantity']
            spin_current_quantity = CurrentQuantitySpinBox(self)
            spin_current_quantity.setToolTip('latest_change_current_quantity')
            spin_current_quantity.setValue(int(current_quantity))
            if current_quantity <= 10:
                quantity_color = "red"
            elif current_quantity <= 20:
                quantity_color = "yellow"

            if current_quantity > 20:
                spin_current_quantity.setStyleSheet(self.margin_format)
            else:
                spin_current_quantity.setStyleSheet(
                    f"color: {quantity_color}; border-color: {quantity_color}; {self.margin_format}"
                )
            self.tableWidget.setCellWidget(i, 3, spin_current_quantity)
            # PRICE
            price = data['Polar G2'][item]['price']
            spin_price = HumbleDoubleSpinBox(self)
            spin_price.setValue(price)
            spin_price.setPrefix("$")
            spin_price.setSuffix(" USD" if True else " CAD")
            spin_price.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 4, spin_price)
            # EXCHANGE RATE
            combo_exchange_rate = ExchangeRateComboBox(
                parent=self,
                selected_item="USD" if True else "CAD",
                tool_tip='latest_change_use_exchange_rate',
            )
            combo_exchange_rate.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 5, combo_exchange_rate)
            # TOTAL COST
            total_cost_in_stock: float = current_quantity * price
            if total_cost_in_stock < 0:
                total_cost_in_stock = 0
            spin_total_cost = CostLineEdit(
                parent=self,
                prefix="$",
                text=total_cost_in_stock,
                suffix=combo_exchange_rate.currentText(),
            )
            spin_total_cost.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 6, spin_total_cost)
            # TOTALE UNIT COST
            total_unit_cost: float = unit_quantity * price
            spin_total_unit_cost = CostLineEdit(
                parent=self,
                prefix="$",
                text=total_unit_cost,
                suffix=combo_exchange_rate.currentText(),
            )
            spin_total_unit_cost.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 7, spin_total_unit_cost)
            # PRIORITY
            priority=data['Polar G2'][item]['priority']
            combo_priority = PriorityComboBox(
                parent=self, selected_item=priority, tool_tip='latest_change_priority'
            )
            if combo_priority.currentText() == "Medium":
                combo_priority.setStyleSheet("color: yellow; border-color: yellow;")
            elif combo_priority.currentText() == "High":
                combo_priority.setStyleSheet("color: red; border-color: red;")
            combo_priority.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 8, combo_priority)
            # NOTES
            notes=data['Polar G2'][item]['notes']
            text_notes = NotesPlainTextEdit(
                parent=self, text=notes, tool_tip='latest_change_notes'
            )
            text_notes.setStyleSheet('margin-top: 1%; margin-bottom: 1%; margin-left: 1%; margin-right: 1%;')
            self.tableWidget.setCellWidget(i, 9, text_notes)
            # PURCHASE ORDER
            po_menu = QMenu(self)
            btn_po = POPushButton(parent=self)
            btn_po.setMenu(po_menu)
            btn_po.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 10, btn_po)
            # DELETE
            btn_delete = DeletePushButton(
                parent=self,
                tool_tip=f"Delete {item_name.currentText()} permanently from Polar G2",
                icon=QIcon(f"ui/BreezeStyleSheets/dist/pyqt6/dark/trash.png"),
            )
            btn_delete.setStyleSheet(self.margin_format)
            self.tableWidget.setCellWidget(i, 11, btn_delete)
app = QApplication(sys.argv)
set_theme(app, theme='dark')

# apply_stylesheet(app, theme='dark_blue.xml')
window = MainWindow()
window.show()
app.exec_()