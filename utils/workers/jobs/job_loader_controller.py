import contextlib
import logging

from PyQt6.QtCore import QObject, QThreadPool, pyqtSignal

from utils.workers.download_images import DownloadImagesWorker
from utils.workers.jobs.get_job import GetJobWorker
from utils.workers.workspace.download_file import WorkspaceDownloadWorker
from utils.workspace.job import Job
from utils.workspace.job_manager import JobManager


class JobLoaderController(QObject):
    finished = pyqtSignal(object)  # Emit Job when done

    def __init__(self, job_manager: JobManager, job_id: int):
        super().__init__()
        self.logger = logging.getLogger("JobLoaderController")
        self.job_id = job_id
        self.job_manager = job_manager
        self.job: Job | None = None
        self.thread_pool = QThreadPool.globalInstance()

        # New logic: track known tasks and their completion
        self.expected_tasks = {"job", "images", "files"}
        self.completed_tasks = set()

        self.logger.info(f"Initialized for job id: {self.job_id}")

    def start(self):
        self.logger.info("Starting job loading process")
        self.download_job_data()

    def download_job_data(self):
        self.logger.info("Downloading job data...")
        worker = GetJobWorker(self.job_id)
        worker.signals.success.connect(self.handle_job_data)
        worker.signals.error.connect(lambda *args: self.task_finished("job"))
        worker.signals.finished.connect(lambda: self.task_finished("job"))
        self.thread_pool.start(worker)

    def handle_job_data(self, response: tuple[dict, str]):
        self.job = Job(response, self.job_manager)
        self.job.downloaded_from_server = True
        images = self.get_all_images(self.job)
        self.logger.info(f"Found {len(images)} image(s) to download")
        if images:
            self.download_images(images)
        else:
            self.task_finished("images")

    def download_images(self, image_paths: list[str]):
        self.logger.info(f"Starting image download: {image_paths}")
        worker = DownloadImagesWorker(image_paths)
        worker.signals.success.connect(self.handle_images_downloaded)
        worker.signals.error.connect(lambda *args: self.task_finished("images"))
        worker.signals.finished.connect(lambda: self.task_finished("images"))
        self.thread_pool.start(worker)

    def handle_images_downloaded(self, _):
        self.logger.info("Images downloaded successfully")
        files = self.get_all_files(self.job)
        self.logger.info(f"Found {len(files)} file(s) to download")
        if files:
            self.download_files(files)
        else:
            self.task_finished("files")

    def download_files(self, files: list[str]):
        self.logger.info(f"Starting file download: {files}")
        worker = WorkspaceDownloadWorker(files, open_when_done=False)
        worker.signals.success.connect(
            lambda *_: self.logger.info("Files downloaded successfully")
        )
        worker.signals.error.connect(lambda *args: self.task_finished("files"))
        worker.signals.finished.connect(lambda: self.task_finished("files"))
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

    def task_finished(self, task_name: str):
        if task_name in self.completed_tasks:
            self.logger.warning(f"Task '{task_name}' already finished once. Ignoring.")
            return
        self.completed_tasks.add(task_name)
        remaining = self.expected_tasks - self.completed_tasks
        self.logger.debug(
            f"Marked task '{task_name}' as finished. Remaining: {remaining}"
        )

        if self.completed_tasks == self.expected_tasks:
            self.logger.info("All expected tasks complete. Emitting final signal.")
            self.finished.emit(self.job)
