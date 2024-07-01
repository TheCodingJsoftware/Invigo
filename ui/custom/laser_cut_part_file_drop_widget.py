from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent
from PyQt6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QVBoxLayout,
                             QWidget)

from utils.laser_cut_inventory.laser_cut_part import LaserCutPart


class LaserCutPartFileDropWidget(QWidget):
    fileDropped = pyqtSignal(QHBoxLayout, object, str, list)  # Changed to object for LaserCutPart

    def __init__(
        self,
        laser_cut_part: LaserCutPart,
        files_layout: QHBoxLayout,
        file_category: str,
        parent,
    ):
        super(LaserCutPartFileDropWidget, self).__init__(parent)
        self.parent = parent
        self.setAcceptDrops(True)
        self.laser_cut_part = laser_cut_part
        self.files_layout = files_layout
        self.file_category = file_category

        self.default_style_sheet = "background-color: rgba(30,30,30, 0.6); border-radius: 5px; border: 1px solid rgb(15,15,15);"
        self.accept_style_sheet = "background-color: rgba(70,210,110, 0.6); border-radius: 5px; border: 1px solid rgba(70,210,110, 0.6);"
        self.fail_style_sheet = "background-color: rgba(210,70,60, 0.6); border-radius: 5px; border: 1px solid rgba(210,70,60, 0.6);"

        self.setMaximumWidth(100)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.label = QLabel("Drag Here", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setMaximumWidth(100)
        self.label.setMinimumHeight(65)
        self.label.setMinimumWidth(80)
        self.label.setStyleSheet(self.default_style_sheet)
        self.label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label.setToolTip("Click to select files from your computer")
        layout.addWidget(self.label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.label.setText("Drop Me")
            self.label.setStyleSheet(self.accept_style_sheet)
            event.accept()
        else:
            self.reset_label()
            event.ignore()

    def dragLeaveEvent(self, event: QDragEnterEvent):
        self.reset_label()
        event.accept()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [url.toLocalFile() for url in urls]
            allowed_extensions = [
                ".pdf",
                ".dxf",
                ".jpeg",
                ".geo",
                ".png",
                ".jpg",
                "sldprt",
            ]  # Allowed file extensions
            valid_files = all(file_path.lower().endswith(tuple(allowed_extensions)) for file_path in file_paths)
            if valid_files:
                self.fileDropped.emit(self.files_layout, self.laser_cut_part, self.file_category, file_paths)
                self.reset_label()
                event.accept()
            else:
                self.label.setText("Not allowed")
                self.label.setStyleSheet(self.fail_style_sheet)
                QTimer.singleShot(1000, self.reset_label)
                event.ignore()
        else:
            event.ignore()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            file_dialog.setNameFilter("Allowed Files (*.pdf *.dxf *.jpeg *.geo *.png *.jpg *.sldprt)")
            file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
            if file_dialog.exec():
                if file_paths := file_dialog.selectedFiles():
                    self.fileDropped.emit(self.files_layout, self.laser_cut_part, self.file_category, file_paths)

    def reset_label(self):
        self.label.setText("Drag Here")
        self.label.setStyleSheet(self.default_style_sheet)
