from typing import Callable

from PyQt6.QtCore import QObject, QThreadPool, pyqtSignal

from utils.workers.base_worker import BaseWorker


class RunnableChain(QObject):
    finished = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.steps: list[tuple[BaseWorker, Callable]] = []
        self.current_index = 0

    def add(self, worker: BaseWorker, callback: Callable):
        self.steps.append((worker, callback))
        return self

    def start(self):
        self._run_next()

    def _run_next(self):
        if self.current_index >= len(self.steps):
            self.finished.emit()
            return

        worker, callback = self.steps[self.current_index]
        self.current_index += 1

        # Connect to BaseWorker's success signal
        def wrapper(result):
            callback(result, self._run_next)

        worker.signals.success.connect(wrapper)

        # Optional: Log or handle errors without stopping the chain
        def error_handler(err, code):
            print(f"[RunnableChain] Step {self.current_index - 1} failed: {err} (status {code})")
            self._run_next()

        worker.signals.error.connect(error_handler)

        QThreadPool.globalInstance().start(worker)
