from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QDragEnterEvent, QDragLeaveEvent, QDropEvent, QMouseEvent, QPixmap
from PyQt6.QtWidgets import QLabel, QWidget

from ui.theme import theme_var


class AssemblyImage(QLabel):
    clicked = pyqtSignal()
    imagePathDropped = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = ...):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.setFixedHeight(120)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip("Press to enlarge")
        self.setText("Drop an Image.\nRight click to Paste\nfrom clipboard.\n(PNG, JPG, JPEG)")
        self.setAcceptDrops(True)
        self.setWordWrap(True)
        self.setStyleSheet(f"background-color:  {theme_var('overlay')}")
        self.image_dropped: bool = False
        self.path_to_image: str = ""

    def set_new_image(self, path_to_image):
        pixmap = QPixmap(path_to_image)
        pixmap = pixmap.scaledToHeight(100, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(pixmap)
        self.setStyleSheet(f"background-color:  {theme_var('overlay')}")
        self.path_to_image = path_to_image
        self.image_dropped = True

    def clear_image(self):
        self.setPixmap(QPixmap())
        self.setText("Drop an Image.\nRight click to Paste\nfrom clipboard.\n(PNG, JPG, JPEG)")
        self.setStyleSheet(f"background-color:  {theme_var('overlay')}")
        self.path_to_image = ""
        self.image_dropped = False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()  # Emit the clicked signal

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasImage():
            event.acceptProposedAction()
        elif event.mimeData().hasUrls():
            self.setText("Drop Me")
            self.setStyleSheet(f"background-color: {theme_var('primary-green')}; color: {theme_var('on-primary-green')}")
            event.acceptProposedAction()
            event.accept()

    def dropEvent(self, event: QDropEvent):
        if urls := event.mimeData().urls():
            image_path = urls[0].toLocalFile()
            if image_path.lower().endswith((".png", ".jpg", ".jpeg")):
                self.setPixmap(QPixmap(image_path).scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio))
                self.imagePathDropped.emit(image_path)
                event.accept()
            else:
                self.setText("Not allowed")
                self.setStyleSheet(f"background-color: {theme_var('error')}; color: {theme_var('on-error')}")
                event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.setText("Drop an Image.\nRight click to Paste\nfrom clipboard.\n(PNG, JPG, JPEG)")
        self.setStyleSheet(f"background-color:  {theme_var('overlay')}")
        event.accept()
        if self.image_dropped:
            self.set_new_image(self.path_to_image)
