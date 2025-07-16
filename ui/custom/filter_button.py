from functools import partial

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QCheckBox, QPushButton, QVBoxLayout, QWidget

from ui.icons import Icons


class DropDownWidget(QWidget):
    checkbox_states_changed = pyqtSignal(dict)  # Signal with checkbox states dictionary

    def __init__(self, options: list[str]):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setLayout(QVBoxLayout())
        self.setObjectName("drop_down")
        self.options = options
        self.checkbox_states = {option: False for option in self.options}

        for option in self.options:
            checkbox = QCheckBox(option)
            checkbox.stateChanged.connect(partial(self.on_checkbox_state_changed, option))
            self.layout().addWidget(checkbox)

    def on_checkbox_state_changed(self, name: str, state: int):
        checked = not state == 0  # Check if the checkbox is checked
        self.checkbox_states[name] = checked
        self.checkbox_states_changed.emit(self.checkbox_states)


class FilterButton(QPushButton):
    checkbox_states_changed = pyqtSignal(dict)

    def __init__(self, title: str, options: list[str]):
        super().__init__(title)
        self.base_title = title
        self.options = options
        self.dropdown = DropDownWidget(self.options)
        self.dropdown.checkbox_states_changed.connect(self.on_checkbox_states_changed)
        self.clicked.connect(self.toggle_dropdown)
        self.update_title({})
        self.setIcon(QIcon(Icons.filter_icon))

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

    def on_checkbox_states_changed(self, states: dict):
        self.checkbox_states_changed.emit(states)
        self.update_title(states)

    def update_title(self, states: dict):
        checked_count = sum(states.values())
        self.setText(f"  {self.base_title} ({checked_count})")
