from functools import partial

from natsort import natsorted
from PyQt6 import uic
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QMessageBox, QPushButton, QSplitter, QVBoxLayout

from utils.threads.workspace_get_file_thread import WorkspaceDownloadFile


class PDFViewer(QMainWindow):
    def __init__(self, pdf_files: list[str], file_path: str, parent):
        super(PDFViewer, self).__init__(parent)
        uic.loadUi("ui/pdf_viewer.ui", self)

        self.files = pdf_files
        self.buttons: list[QPushButton] = []
        self.download_file_thread: WorkspaceDownloadFile = None

        self.webView = QWebEngineView(self)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PluginsEnabled, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PdfViewerEnabled, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.AllowRunningInsecureContent, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.AutoLoadImages, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.ErrorPageEnabled, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.FullScreenSupportEnabled, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.PrintElementBackgrounds, True)
        self.webView.settings().setAttribute(self.webView.settings().WebAttribute.WebGLEnabled, True)
        # self.webView.page().loadFinished.connect(self.hide_thumbnails)

        self.webview_layout = self.findChild(QVBoxLayout, "webview_layout")
        self.webview_layout.addWidget(self.webView)

        self.load_pdf_buttons()

        self.files_layout = self.findChild(QVBoxLayout, "files_layout")
        self.files_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.splitter = self.findChild(QSplitter, "splitter")
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        self.pdf_button_pressed(file_path)
        # self.resize(1200, 850)

    def pdf_button_pressed(self, path: str):
        file_name = path.split("\\")[-1].replace(".pdf", "")
        for button in self.buttons:
            if button.text() != file_name:
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False)
            else:
                button.blockSignals(True)
                button.setChecked(True)
                button.blockSignals(False)
        self.webView.setUrl(QUrl("file:///" + path.replace("\\", "/")))
        self.setWindowTitle(path)

    def get_pdf_files(self) -> list[str]:
        pdf_files: set[str] = {file for file in self.files if file.lower().endswith(".pdf")}
        return list(pdf_files)

    def load_pdf_file(self, file_path: str):
        self.download_file_thread = WorkspaceDownloadFile([file_path], True)
        self.download_file_thread.signal.connect(self.file_downloaded)
        self.download_file_thread.start()

    def file_downloaded(self, file_ext: str, file_name: str, open_when_done: bool):
        if file_ext is None:
            msg = QMessageBox(QMessageBox.Icon.Critical, "Error", f"Failed to download file: {file_name}", QMessageBox.StandardButton.Ok, self)
            msg.show()
            return
        if open_when_done:
            local_path = f"data\\workspace\\{file_ext}\\{file_name}"
            self.pdf_button_pressed(local_path)

    def load_pdf_buttons(self):
        all_pdfs = natsorted(self.get_pdf_files())
        for file in all_pdfs:
            file_name = file.split("\\")[-1].replace(".pdf", "")
            button = QPushButton(file_name, self)
            button.setCheckable(True)
            self.buttons.append(button)
            button.clicked.connect(partial(self.load_pdf_file, file))
            self.files_layout.addWidget(button)

    def hide_thumbnails(self):
        self.webView.page().runJavaScript(
            """
            var checkExist = setInterval(function() {
                var sideBar = document.querySelector('embed[type="application/pdf"]');
                if (sideBar) {
                    sideBar.setAttribute('style', 'width:100% !important');
                    clearInterval(checkExist);
                }
            }, 100);
        """
        )
