import contextlib
import math
import os
import shutil
from datetime import datetime, timedelta
from functools import partial

from PyQt6 import uic
from PyQt6.QtCore import QAbstractItemModel, QAbstractTableModel, QDate, QDateTime, QEvent, QMargins, QMimeData, QModelIndex, QPoint, QRegularExpression, QSettings, QSize, QSortFilterProxyModel, Qt, QTime, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QClipboard, QColor, QCursor, QDrag, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QFileSystemModel, QFont, QIcon, QKeySequence, QMouseEvent, QPainter, QPalette, QPixmap, QRegularExpressionValidator, QStandardItem, QStandardItemModel, QTextCharFormat
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QCheckBox, QComboBox, QDateEdit, QDoubleSpinBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget

from ui.add_component_dialog import AddComponentDialog
from ui.add_laser_cut_part_dialog import AddLaserCutPartDialog
from ui.custom.components_planning_table_widget import ComponentsPlanningTableWidget
from ui.custom.laser_cut_parts_planning_table_widget import LaserCutPartsPlanningTableWidget
from ui.custom_widgets import AssemblyMultiToolBox
from ui.image_viewer import QImageViewer
from ui.pdf_viewer import PDFViewer
from utils.calulations import calculate_overhead
from utils.colors import darken_color, lighten_color
from utils.inventory.category import Category
from utils.inventory.component import Component
from utils.inventory.components_inventory import ComponentsInventory
from utils.inventory.laser_cut_inventory import LaserCutInventory
from utils.inventory.laser_cut_part import LaserCutPart
from utils.threads.upload_thread import UploadThread
from utils.threads.workspace_get_file_thread import WorkspaceDownloadFile
from utils.threads.workspace_upload_file_thread import WorkspaceUploadThread
from utils.workspace.assembly import Assembly
from utils.workspace.group import Group
from utils.workspace.job_preferences import JobPreferences


class RecordingWidget(QWidget):
    def __init__(self, parent=None):
        super(RecordingWidget, self).__init__(parent)
        self.setFixedSize(20, 20)
        self.recording = True
        self.recording_color = QColor("red")
        self.nonrecording_color = QColor("#8C8C8C")
        self.current_color = self.nonrecording_color
        self.scale = 1.0
        self.scale_factor = 0.01
        self.scale_direction = 0.1
        self.animation_duration = 3000
        self.elapsed_time = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateAnimation)
        self.timer.start(1)  # Update every 20 milliseconds

    def set_recording(self, recording):
        self.recording = recording

    def updateAnimation(self):
        if self.recording:
            self.elapsed_time += self.timer.interval()
            if self.elapsed_time >= self.animation_duration:
                self.elapsed_time = 0

            progress = self.elapsed_time / self.animation_duration
            scale_progress = 1 - (2 * abs(progress - 0.5) * 0.3)
            self.scale = scale_progress

            self.current_color = self.interpolateColors(self.recording_color, QColor("darkred"), scale_progress)
        else:
            self.elapsed_time = 0
            self.scale = 1.0
            self.current_color = self.interpolateColors(self.nonrecording_color, self.recording_color, 1.0)

        self.update()

    def interpolateColors(self, start_color, end_color, progress):
        red = int(start_color.red() + progress * (end_color.red() - start_color.red()))
        green = int(start_color.green() + progress * (end_color.green() - start_color.green()))
        blue = int(start_color.blue() + progress * (end_color.blue() - start_color.blue()))

        return QColor(red, green, blue)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(self.current_color))

        # Calculate the center of the widget
        center = self.rect().center()

        # Calculate the radius of the circle based on the widget size
        radius = int(min(self.rect().width(), self.rect().height()) / 2)

        # Adjust the radius based on the scale
        radius = int(radius * self.scale)

        # Calculate the top-left corner of the circle bounding rectangle
        x = center.x() - radius
        y = center.y() - radius

        # Draw the circle
        painter.drawEllipse(x, y, 2 * radius, 2 * radius)
