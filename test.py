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
import ast
import operator as op

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        input_box = QLineEdit(self)
        input_box.returnPressed.connect(partial(self.value_change, input_box))

    def value_change(self, input_box: QLineEdit):
        try:
            input_box.setText(str(self.eval_expr(input_box.text())))
        except SyntaxError:
            return

    def eval_expr(self, expr):
        return self.eval_(ast.parse(expr, mode='eval').body)

    def eval_(self, node):
        if isinstance(node, ast.Num): # <number>
            return node.n
        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return operators[type(node.op)](self.eval_(node.left), self.eval_(node.right))
        elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
            return operators[type(node.op)](self.eval_(node.operand))
        else:
            raise TypeError(node)

app = QApplication(sys.argv)
set_theme(app, theme="dark")

# apply_stylesheet(app, theme='dark_blue.xml')
window = MainWindow()
window.show()
app.exec_()
