from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QMainWindow, QScrollArea, QSizePolicy


class QImageViewer(QMainWindow):
    def __init__(self, parent, path: str, title: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 600)

        self.image_label = QLabel()
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(self.scroll_area)

        self.original_pixmap = QPixmap(path)
        self.update_pixmap()

        self.scroll_area.setWidgetResizable(True)
        self.setMouseTracking(True)
        self.showMaximized()

    def update_pixmap(self):
        # Scale the pixmap while keeping the aspect ratio
        pixmap = self.original_pixmap.scaled(
            self.scroll_area.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_pixmap()

    def keyPressEvent(self, event):
        self.close()
