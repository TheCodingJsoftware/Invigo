from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QMainWindow, QScrollArea, QSizePolicy


class QImageViewer(QMainWindow):
    """This is a class for a main window that displays images."""

    def __init__(self, parent, path: str, title: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 600)

        self.image_label = QLabel()
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(self.scroll_area)

        pixmap = QPixmap(path)
        pixmap = pixmap.scaled(pixmap.width(), pixmap.height(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()
        self.scroll_area.setWidgetResizable(True)
        self.setMouseTracking(True)

    def keyPressEvent(self, event):
        self.close()
