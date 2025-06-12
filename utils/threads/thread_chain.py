from PyQt6.QtCore import QObject, QThread, pyqtSignal


class ThreadChain(QObject):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.steps: list[tuple[QThread, callable]] = []
        self.thread_refs: list[QThread] = []

    def add(self, thread: QThread, callback: callable):
        self.steps.append((thread, callback))
        self.thread_refs.append(thread)
        return self

    def start(self):
        self._start_next()

    def _start_next(self):
        if not self.steps:
            self.finished.emit()
            return

        thread, callback = self.steps.pop(0)
        thread.signal.connect(lambda *args: callback(*args, self._start_next))
        thread.finished.connect(thread.deleteLater)
        thread.start()
