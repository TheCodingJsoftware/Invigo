import contextlib
from typing import Union

from PyQt6.QtCore import QThread, pyqtSignal

from utils.threads.download_images_thread import DownloadImagesThread
from utils.threads.download_job_thread import DownloadJobThread
from utils.threads.workspace_get_file_thread import WorkspaceDownloadFile
from utils.workspace.job import Job
from utils.workspace.job_manager import JobManager


class JobLoaderThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, job_manager: JobManager, folder_name: str) -> None:
        super().__init__()
        self.folder_name = folder_name
        self.job_manager = job_manager
        self.job = None
        self.threads: list[Union[DownloadImagesThread, DownloadJobThread, WorkspaceDownloadFile]] = []
        self.remaining_threads = 0

    def run(self):
        self.download_job_data_thread(self.folder_name)

    def get_all_images(self, job: Job) -> list[str]:
        images: set[str] = set()
        for assembly in job.get_all_assemblies():
            if assembly.assembly_image:
                images.add(assembly.assembly_image)
        for laser_cut_part in job.get_all_laser_cut_parts():
            images.add(laser_cut_part.image_index)
        for component in job.get_all_components():
            images.add(component.image_path)
        with contextlib.suppress(KeyError):  # Just in case
            images.remove("")
            images.remove("None")
        return list(images)

    def get_all_files(self, job: Job) -> list[str]:
        files: set[str] = set()
        for assembly in job.get_all_assemblies():
            for assembly_file in assembly.assembly_files:
                if not assembly_file.lower().endswith((".pdf", ".jpeg", ".jpg", ".png")):
                    files.add(assembly_file)
        for laser_cut_part in job.get_all_laser_cut_parts():
            for laser_cut_part_file in laser_cut_part.bending_files + laser_cut_part.welding_files + laser_cut_part.cnc_milling_files:
                if not laser_cut_part_file.lower().endswith((".pdf", ".jpeg", ".jpg", ".png")):
                    files.add(laser_cut_part_file)
        return list(files)

    def download_job_data_thread(self, folder_name: str) -> None:
        download_job_thread = DownloadJobThread(folder_name)
        self.threads.append(download_job_thread)
        self.remaining_threads += 1
        download_job_thread.signal.connect(self.download_job_data_response)
        download_job_thread.start()

    def download_job_data_response(self, data: dict, folder_name: str) -> None:
        print(f"download_job_data_response: {data} {folder_name}")
        if isinstance(data, dict):
            self.job = Job(data, self.job_manager)
            self.job.downloaded_from_server = True

            required_images = self.get_all_images(self.job)
            self.download_required_images_thread(required_images)
        self.thread_finished()

    def download_required_images_thread(self, image_paths: list[str]) -> None:
        if image_paths:
            download_images_thread = DownloadImagesThread(image_paths)
            self.threads.append(download_images_thread)
            self.remaining_threads += 1
            download_images_thread.signal.connect(self.download_images_response)
            download_images_thread.start()

    def download_images_response(self, response: str) -> None:
        print(f"download_images_response: {response}")
        all_files = self.get_all_files(self.job)
        self.download_required_files_thread(all_files)
        self.thread_finished()

    def download_required_files_thread(self, files: list[str]) -> None:
        if files:
            download_files_thread = WorkspaceDownloadFile(files, False)
            self.threads.append(download_files_thread)
            self.remaining_threads += 1
            download_files_thread.signal.connect(self.download_files_response)
            download_files_thread.start()

    def download_files_response(self, file_ext: str, file_name: str, open_when_done: bool):
        print(f"download_files_response: {file_ext}")
        self.thread_finished()

    def thread_finished(self):
        self.remaining_threads -= 1
        if self.remaining_threads == 0:
            self.signal.emit(self.job)
