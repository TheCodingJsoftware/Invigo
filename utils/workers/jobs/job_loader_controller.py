import contextlib

from PyQt6.QtCore import QObject, QThreadPool, pyqtSignal

from utils.workers.download_images import DownloadImagesWorker
from utils.workers.jobs.download_job import DownloadJobWorker
from utils.workers.workspace.download_file import WorkspaceDownloadWorker
from utils.workspace.job import Job
from utils.workspace.job_manager import JobManager


class JobLoaderController(QObject):
    finished = pyqtSignal(object)  # Emit Job when done

    def __init__(self, job_manager: JobManager, folder_name: str):
        super().__init__()
        self.folder_name = folder_name
        self.job_manager = job_manager
        self.job: Job | None = None
        self.thread_pool = QThreadPool.globalInstance()
        self.remaining_tasks = 0

    def start(self):
        self.download_job_data()

    def download_job_data(self):
        worker = DownloadJobWorker(self.folder_name)
        worker.signals.success.connect(self.handle_job_data)
        worker.signals.error.connect(self.task_error)
        worker.signals.finished.connect(self.task_finished)
        self.remaining_tasks += 1
        self.thread_pool.start(worker)

    def handle_job_data(self, data: dict):
        self.job = Job(data, self.job_manager)
        self.job.downloaded_from_server = True
        images = self.get_all_images(self.job)
        if images:
            self.download_images(images)
        else:
            self.task_finished()

    def download_images(self, image_paths: list[str]):
        worker = DownloadImagesWorker(image_paths)
        worker.signals.success.connect(self.handle_images_downloaded)
        worker.signals.error.connect(self.task_error)
        worker.signals.finished.connect(self.task_finished)
        self.remaining_tasks += 1
        self.thread_pool.start(worker)

    def handle_images_downloaded(self, _):
        files = self.get_all_files(self.job)
        if files:
            self.download_files(files)
        else:
            self.task_finished()

    def download_files(self, files: list[str]):
        worker = WorkspaceDownloadWorker(files, open_when_done=False)
        worker.signals.success.connect(lambda *_: None)
        worker.signals.error.connect(self.task_error)
        worker.signals.finished.connect(self.task_finished)
        self.remaining_tasks += 1
        self.thread_pool.start(worker)

    def get_all_images(self, job: Job) -> list[str]:
        images = set()
        for a in job.get_all_assemblies():
            if a.assembly_image:
                images.add(a.assembly_image)
        for lcp in job.get_all_laser_cut_parts():
            images.add(lcp.image_index)
        for c in job.get_all_components():
            images.add(c.image_path)
        with contextlib.suppress(KeyError):
            images.discard("")
            images.discard("None")
        return list(images)

    def get_all_files(self, job: Job) -> list[str]:
        files = set()
        for a in job.get_all_assemblies():
            for f in a.assembly_files:
                if not f.lower().endswith((".pdf", ".jpeg", ".jpg", ".png")):
                    files.add(f)
        for lcp in job.get_all_laser_cut_parts():
            for f in lcp.bending_files + lcp.welding_files + lcp.cnc_milling_files:
                if not f.lower().endswith((".pdf", ".jpeg", ".jpg", ".png")):
                    files.add(f)
        return list(files)

    def task_error(self, error, code):
        print(f"Error {code}: {error}")
        self.task_finished()

    def task_finished(self):
        self.remaining_tasks -= 1
        if self.remaining_tasks <= 0:
            self.finished.emit(self.job)
