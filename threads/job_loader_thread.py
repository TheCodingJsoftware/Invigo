import contextlib

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from threads.download_images_thread import DownloadImagesThread
from threads.download_job_thread import DownloadJobThread
from threads.workspace_get_file_thread import WorkspaceDownloadFile
from utils.workspace.job import Job
from utils.workspace.job_manager import JobManager


class JobLoaderThread(QThread):
    signal = pyqtSignal(object)

    def __init__(self, job_manager: JobManager, folder_name: str) -> None:
        super().__init__()
        self.folder_name = folder_name
        self.job_manager = job_manager
        self.job: Job = None
        self.threads: list[DownloadImagesThread | DownloadJobThread | WorkspaceDownloadFile] = []

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
        return list(images)

    def get_all_files(self, job: Job):
        files: set[str] = set()
        for assembly in job.get_all_assemblies():
            for assembly_file in assembly.assembly_files:
                if not assembly_file.lower().endswith(('.pdf', '.jpeg', '.jpg', '.png')):
                    files.add(assembly_file)
        for laser_cut_part in job.get_all_laser_cut_parts():
            for laser_cut_part_file in laser_cut_part.bending_files + laser_cut_part.welding_files + laser_cut_part.cnc_milling_files:
                if not laser_cut_part_file.lower().endswith(('.pdf', '.jpeg', '.jpg', '.png')):
                    files.add(laser_cut_part_file)
        return list(files)

    def download_job_data_thread(self, folder_name: str) -> None:
        download_job_thread = DownloadJobThread(folder_name)
        self.threads.append(download_job_thread)
        download_job_thread.signal.connect(self.download_job_data_response)
        download_job_thread.start()
        download_job_thread.wait()

    def download_job_data_response(self, data: dict, folder_name: str) -> None:
        if isinstance(data, dict):
            job_name = folder_name.split("\\")[-1]
            self.job = Job(job_name, data, self.job_manager)
            self.job.downloaded_from_server = True

            required_images = self.get_all_images(self.job)

            self.download_required_images_thread(required_images)
        else:
            self.signal.emit(None)

    def download_required_images_thread(self, image_paths: list[str]) -> None:
        download_images_thread = DownloadImagesThread(image_paths)
        self.threads.append(download_images_thread)
        download_images_thread.signal.connect(self.download_images_response)
        download_images_thread.start()
        download_images_thread.wait()

    def download_images_response(self, response: str) -> None:
        if response == "Successfully downloaded":
            all_files = self.get_all_files(self.job)
            self.download_required_files_thread(all_files)
        else:
            self.signal.emit(None)

    def download_required_files_thread(self, files: list[str]) -> None:
        download_files_thread = WorkspaceDownloadFile(files, False)
        self.threads.append(download_files_thread)
        download_files_thread.signal.connect(self.download_files_response)
        download_files_thread.start()
        download_files_thread.wait()

    def download_files_response(self, file_ext: str, file_name: str, open_when_done: bool):
        if file_ext == "Successfully downloaded" or file_name == "Successfully downloaded":
            self.signal.emit(self.job)
        else:
            self.signal.emit(None)
