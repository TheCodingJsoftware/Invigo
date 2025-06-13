import os

from PyQt6.QtCore import QMimeData, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDrag, QMouseEvent
from PyQt6.QtWidgets import QMenu, QPushButton

from utils.workers.workspace.download_file import WorkspaceDownloadWorker


class FileButton(QPushButton):
    buttonClicked = pyqtSignal()
    deleteFileClicked = pyqtSignal()
    longDragThreshold = 30

    def __init__(self, file: str, parent=None):
        super().__init__(parent)
        self.setFixedWidth(50)
        self.setAcceptDrops(True)
        self.dragging = False
        self.file = file
        self.drag_start_position = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def mouseMoveEvent(self, event):
        if self.dragging:
            return
        try:
            distance = (event.pos() - self.drag_start_position).manhattanLength()
        except TypeError:
            return
        if distance >= self.longDragThreshold:
            if not os.path.exists(self.file):
                self.download_thread = WorkspaceDownloadFile([self.file], False)
                self.download_thread.start()

            self.dragging = True
            mime_data = QMimeData()
            url = QUrl.fromLocalFile(self.file)  # Replace with the actual file path
            mime_data.setUrls([url])
            drag = QDrag(self)
            drag.setMimeData(mime_data)

            drag.exec(Qt.DropAction.CopyAction)
            super().mousePressEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        self.dragging = False
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if not self.dragging and event.button() == Qt.MouseButton.LeftButton:
            self.buttonClicked.emit()
        self.dragging = False
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def showContextMenu(self, pos):
        context_menu = QMenu(self)
        delete_action = context_menu.addAction("Delete File")
        delete_action.triggered.connect(self.onDeleteFileClicked)
        context_menu.exec(self.mapToGlobal(pos))

    def onDeleteFileClicked(self):
        self.deleteFileClicked.emit()
