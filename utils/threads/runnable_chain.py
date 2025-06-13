from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal


class RunnableChain(QObject):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps: list[tuple[QRunnable, callable]] = []
        self.current_index = 0

    def add(self, worker: QRunnable, callback: callable):
        self.steps.append((worker, callback))
        return self

    def start(self):
        self._run_next()

    def _run_next(self):
        if self.current_index >= len(self.steps):
            self.finished.emit()
            return

        worker, callback = self.steps[self.current_index]

        # Assume each worker has `.signals.signal`
        def wrapper(*args):
            callback(*args, self._run_next)

        worker.signals.signal.connect(wrapper)

        QThreadPool.globalInstance().start(worker)
        self.current_index += 1
