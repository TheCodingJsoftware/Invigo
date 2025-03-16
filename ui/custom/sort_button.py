from functools import partial

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from ui.icons import Icons
from utils.workspace.workspace_filter import SortingMethod


class DropDownWidget(QWidget):
    sorting_method_selected = pyqtSignal(
        SortingMethod
    )  # Signal for the selected sorting method

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setLayout(QVBoxLayout())
        self.setObjectName("drop_down")

        for option in SortingMethod:
            button = QPushButton(self)
            button.setText(option.value)
            button.clicked.connect(partial(self.on_sorting_method_selected, option))
            self.layout().addWidget(button)

    def on_sorting_method_selected(self, method: str):
        self.sorting_method_selected.emit(method)
        self.hide()


class SortButton(QPushButton):
    sorting_method_selected = pyqtSignal(SortingMethod)

    def __init__(self):
        super().__init__("Sort: A ➜ Z")
        self.base_title = "Sort"
        self.dropdown = DropDownWidget()
        self.dropdown.sorting_method_selected.connect(self.on_sorting_method_selected)
        self.clicked.connect(self.toggle_dropdown)

        icon = QIcon(Icons.sort_fill_icon)
        self.setIcon(icon)

    def show_dropdown(self):
        button_rect = self.rect()
        global_pos = self.mapToGlobal(button_rect.bottomLeft())
        self.dropdown.move(global_pos)
        self.dropdown.show()

    def hide_dropdown(self):
        self.dropdown.hide()

    def toggle_dropdown(self):
        if self.dropdown.isVisible():
            self.hide_dropdown()
        else:
            self.show_dropdown()

    def on_sorting_method_selected(self, method: SortingMethod):
        self.sorting_method_selected.emit(method)
        self.setText(f"{self.base_title}: {method.value}")
