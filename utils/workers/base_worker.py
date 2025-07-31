import contextlib
import getpass
import logging
import socket
import time

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from utils.ip_utils import get_server_ip_address, get_server_port, get_server_protocol


class WorkerSignals(QObject):
    success = pyqtSignal(object)
    error = pyqtSignal(object, int)
    finished = pyqtSignal()


class BaseWorker(QRunnable):
    def __init__(self, name="BaseWorker"):
        super().__init__()
        self.signals = WorkerSignals()
        self.logger = logging.getLogger(name)

        self.PROTOCOL = get_server_protocol()
        self.SERVER_IP = get_server_ip_address()
        self.SERVER_PORT = get_server_port()
        self.DOMAIN = f"{self.PROTOCOL}://{self.SERVER_IP}:{self.SERVER_PORT}"

        self.headers = {
            "X-Client-Name": getpass.getuser(),
            "X-Client-Address": socket.gethostname(),
        }

    def run(self) -> None:
        start = time.perf_counter()
        try:
            self.logger.info(f"[{self.__class__.__name__}] started.")
            result = self.do_work()
            with contextlib.suppress(RuntimeError):
                self.signals.success.emit(result)
        except Exception as e:
            self.logger.exception("Worker error:")
            self.handle_exception(e)
        finally:
            with contextlib.suppress(RuntimeError):
                self.signals.finished.emit()
            self.logger.info(f"[{self.__class__.__name__}] finished in {time.perf_counter() - start:.2f}s")

    def handle_exception(self, e):
        self.signals.error.emit({"error": str(e)}, 500)
        self.logger.error(f"[{self.__class__.__name__}] Exception in worker: {e}")

    def do_work(self):
        raise NotImplementedError("Subclasses must implement do_work()")
