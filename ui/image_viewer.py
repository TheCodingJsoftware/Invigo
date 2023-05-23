
from PyQt5 import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class QImageViewer(QMainWindow):
    '''This is a class for a main window that displays images.'''
    def __init__(self, parent, path: str, title: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 600)

        self.image_label = QLabel()
        self.image_label.setBackgroundRole(QPalette.Base)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(True)

        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        self.setCentralWidget(self.scroll_area)

        pixmap = QPixmap(path)
        pixmap = pixmap.scaled(pixmap.width(), pixmap.height(), Qt.KeepAspectRatio, Qt.FastTransformation)
        self.image_label.setPixmap(pixmap)
        self.image_label.adjustSize()
        self.scroll_area.setWidgetResizable(True)
        self.setMouseTracking(True)

    def keyPressEvent(self, event):
        self.close()
