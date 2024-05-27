from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class PDFViewer(QWidget):
    def __init__(self, path: str, parent: QWidget):
        super(PDFViewer, self).__init__(parent)

        self.path = path

        self.setWindowTitle("PDF Viewer")
        self.setGeometry(0, 28, 1000, 750)

        layout = QVBoxLayout()

        self.webView = QWebEngineView(self)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PluginsEnabled, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PdfViewerEnabled, True)

        layout.addWidget(self.webView)

        self.setLayout(layout)

        self.webView.setUrl(QUrl("file:///" + self.path.replace("\\", "/")))
