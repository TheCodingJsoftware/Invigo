import contextlib
import copy
import itertools
import os
import sys
import typing
from datetime import datetime, timedelta
from functools import partial

from natsort import natsorted
from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QAbstractItemModel, QAbstractTableModel, QDate, QDateTime, QEvent, QMargins, QMimeData, QModelIndex, QPoint, QRegularExpression, QSettings, QSize, QSortFilterProxyModel, Qt, QTime, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QClipboard, QColor, QCursor, QDrag, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QFileSystemModel, QIcon, QKeySequence, QMouseEvent, QPainter, QPalette, QPixmap, QRegularExpressionValidator, QStandardItem, QStandardItemModel, QTextCharFormat
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplashScreen,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionComboBox,
    QStylePainter,
    QTabBar,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBox,
    QToolButton,
    QTreeView,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.custom_widgets import ClickableLabel, DeletePushButton


class SavedPlanningJobItem(QGroupBox):
    load_job = pyqtSignal()
    open_webpage = pyqtSignal()
    delete_job = pyqtSignal()
    job_type_changed = pyqtSignal()

    def __init__(self, file_info: dict[str, str], parent: QWidget) -> None:
        super().__init__(parent)
        job_name = file_info.get("name")
        modified_date = datetime.fromtimestamp(file_info.get("modified_date")).strftime("%A, %B %d, %Y, %I:%M:%S %p")
        status = file_info.get("status")

        self.setTitle(job_name)

        job_type = QLabel("Job Type:", self)
        job_type.setFixedWidth(60)

        self.job_type_combobox = QComboBox(self)
        self.job_type_combobox.setEnabled(False)
        self.job_type_combobox.addItems(["Planning", "Quoting", "Quoted", "Workspace", "Archive"])
        self.job_type_combobox.wheelEvent = lambda event: None
        self.job_type_combobox.setCurrentText(status)
        self.job_type_combobox.currentTextChanged.connect(self.job_type_changed.emit)

        modified = QLabel(f"Modified: {modified_date}")

        load_job_button = QPushButton("Load Job", self)
        load_job_button.clicked.connect(self.load_job.emit)
        load_job_button.setToolTip("Loads the selected job into a new tab for detailed viewing and editing.")

        open_external = ClickableLabel(self)
        open_external.setTextFormat(Qt.TextFormat.RichText)
        open_external.setText('<a href="open-in-browser">Open in Browser</a>')
        open_external.clicked.connect(self.open_webpage.emit)
        open_external.setToolTip("Will open up the printout in your default web browser.")

        delete_button = DeletePushButton(self, f"Permanently delete {job_name}.\nThis action is irreversible.\nPlease exercise caution.", QIcon("icons/trash.png"))
        delete_button.setFixedWidth(25)
        delete_button.clicked.connect(self.delete_job.emit)

        layout = QVBoxLayout(self)

        h_layout_1 = QHBoxLayout()
        h_layout_1.addWidget(job_type)
        h_layout_1.addWidget(self.job_type_combobox)

        h_layout_2 = QHBoxLayout()
        h_layout_2.addWidget(load_job_button)
        h_layout_2.addWidget(open_external)

        h_layout_3 = QHBoxLayout()
        h_layout_3.addWidget(modified)
        h_layout_3.addWidget(delete_button)

        layout.addLayout(h_layout_1)
        layout.addLayout(h_layout_2)
        layout.addLayout(h_layout_3)

        self.setLayout(layout)
        self.setStyleSheet("QGroupBox{border: 1px solid #8C8C8C;}")
