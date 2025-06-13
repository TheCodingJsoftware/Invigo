import logging
import time

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port


class WorkerSignals(QObject):
    success = pyqtSignal(object)
    error = pyqtSignal(object, int)
    finished = pyqtSignal()


class BaseWorker(QRunnable):
    def __init__(self, name="BaseWorker"):
        super().__init__()
        self.signals = WorkerSignals()
        self.logger = logging.getLogger(name)

        self.SERVER_IP = get_server_ip_address()
        self.SERVER_PORT = get_server_port()
        self.DOMAIN = f"http://{self.SERVER_IP}:{self.SERVER_PORT}"

        self.logger.debug(f"{name} initialized with domain: {self.DOMAIN}")

    def run(self):
        start = time.perf_counter()
        try:
            self.logger.info("Worker started.")
            result = self.do_work()
            self.signals.success.emit(result)
        except Exception as e:
            self.logger.exception("Worker error:")
            self.signals.error.emit(e)
        finally:
            self.signals.finished.emit()
            self.logger.info(f"Worker finished in {time.perf_counter() - start:.2f}s")

    def handle_exception(self, e):
        self.signals.error.emit({"error": str(e)}, 500)
        self.logger.error(f"Exception in worker: {e}")

    def do_work(self):
        raise NotImplementedError("Subclasses must implement do_work()")
