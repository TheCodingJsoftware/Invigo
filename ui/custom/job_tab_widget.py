from PyQt6.QtWidgets import QTabWidget


class JobTabWidget(QTabWidget):
    def __init__(self, parent) -> None:
        super(JobTabWidget, self).__init__(parent)
        self.setUsesScrollButtons(True)
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setMovable(True)
        self.setObjectName("job_planner_tab_widget")
        self.setStyleSheet("QTabWidget#job_planner_tab_widget > QWidget { border-bottom-left-radius: 0px; }")
