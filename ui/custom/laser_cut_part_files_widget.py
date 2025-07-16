import os
from functools import partial
from typing import Literal, Optional, Union

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtWidgets import QHBoxLayout, QMessageBox, QScrollArea, QWidget

from config.environments import Environment
from ui.custom.file_button import FileButton
from ui.windows.image_viewer import QImageViewer
from ui.windows.pdf_viewer import PDFViewer
from utils.inventory.laser_cut_part import LaserCutPart
from utils.workers.workspace.download_file import WorkspaceDownloadWorker
from utils.workspace.workspace_assemply_group import WorkspaceAssemblyGroup
from utils.workspace.workspace_laser_cut_part_group import WorkspaceLaserCutPartGroup


class LaserCutPartFilesWidget(QWidget):
    def __init__(
        self,
        item: Union[WorkspaceLaserCutPartGroup, WorkspaceAssemblyGroup, LaserCutPart],
        file_types: list[
            Union[
                Literal["bending_files"],
                Literal["welding_files"],
                Literal["cnc_milling_files"],
                Literal["assembly_files"],
            ]
        ],
        parent=None,
    ):
        super().__init__(parent)
        self.item = item
        self.file_types = file_types

        self.create_layout()

    def create_layout(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        files_widget = QWidget()
        files_widget.setObjectName("files_widget")

        files_layout = QHBoxLayout(files_widget)
        files_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        files_layout.setContentsMargins(0, 0, 6, 0)
        files_layout.setSpacing(6)

        scroll_area = QScrollArea()
        scroll_area.setWidget(files_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(100)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        for file_type in self.file_types:
            if isinstance(self.item, WorkspaceAssemblyGroup):
                file_list: list[str] = self.item.get_all_files()
            elif isinstance(self.item, WorkspaceLaserCutPartGroup):
                file_list = self.item.get_files(file_type)
            elif isinstance(self.item, LaserCutPart):
                file_list = getattr(self.item, file_type)
            for file in file_list:
                self.add_laser_cut_part_drag_file_widget(file_type, files_layout, file)

    def add_laser_cut_part_drag_file_widget(
        self,
        file_category: str,
        files_layout: QHBoxLayout,
        file_path: str,
    ):
        file_button = FileButton(f"{Environment.DATA_PATH}\\{file_path}", self)
        file_button.buttonClicked.connect(partial(self.laser_cut_part_file_clicked, file_path))
        file_name = os.path.basename(file_path)
        file_ext = file_name.split(".")[-1].upper()
        file_button.setText(file_ext)
        file_button.setToolTip(file_path)
        file_button.setToolTipDuration(0)
        files_layout.addWidget(file_button)

    def laser_cut_part_file_clicked(self, file_path: str):
        def open_pdf(files: list[str]):
            if file_path.lower().endswith(".pdf"):
                if isinstance(self.item, WorkspaceLaserCutPartGroup):
                    self.open_pdf(
                        self.item.get_all_files_with_ext(".pdf"),
                        file_path,
                    )
                elif isinstance(self.item, WorkspaceAssemblyGroup):
                    self.open_pdf(
                        self.item.get_files(".pdf"),
                        file_path,
                    )

        self.download_file_thread = WorkspaceDownloadWorker([file_path], True)
        self.download_file_thread.signals.success.connect(self.file_downloaded)
        self.download_file_thread.signals.success.connect(open_pdf)
        QThreadPool.globalInstance().start(self.download_file_thread)

    def file_downloaded(self, response: tuple[str, str, bool]):
        file_ext, file_name, open_when_done = response
        if file_ext is None:
            msg = QMessageBox(
                QMessageBox.Icon.Critical,
                "Error",
                f"Failed to download file: {file_name}",
                QMessageBox.StandardButton.Ok,
                self,
            )
            msg.show()
            return
        if open_when_done:
            if file_ext in {"PNG", "JPG", "JPEG"}:
                local_path = f"data/workspace/{file_ext}/{file_name}"
                self.open_image(local_path, file_name)

    def open_pdf(self, files, file_path: str):
        pdf_viewer = PDFViewer(files, file_path, self)
        pdf_viewer.show()

    def open_image(self, path: str, title: str):
        image_viewer = QImageViewer(self, path, title)
        image_viewer.show()
