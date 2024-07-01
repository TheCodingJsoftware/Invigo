from PyQt6.QtWidgets import QLineEdit, QPushButton


class JobPreferences:
    def __init__(self):
        # NOTE The closing logic does not make alot of sense, this is because assembly-multitoolbox and multitoolbox do not work in the same way. Deal with it.
        self.closed_toolboxes: dict[str, bool] = {}
        self.job_scroll_positions: dict[str, tuple[int, int]] = {}
        self.scroll_position: int = 0

    def set_job_scroll_position(self, name: str, position_x_y: tuple[int, int]):
        self.job_scroll_positions[name] = position_x_y

    def get_job_scroll_position(self, name: str) -> tuple[int, int]:
        try:
            return self.job_scroll_positions[name]
        except KeyError:
            return (0, 0)

    def group_toolbox_toggled(self, name: QLineEdit, button: QPushButton):
        self.closed_toolboxes[name.text()] = button.isChecked()

    def assembly_toolbox_toggled(self, name: QLineEdit, button: QPushButton, laser_cut_button: QPushButton, component_button: QPushButton, sub_assembly_button: QPushButton):
        self.closed_toolboxes[name.text()] = {
            "is_closed": button.isChecked(),
            "is_laser_cut_closed": laser_cut_button.isChecked(),
            "is_component_closed": component_button.isChecked(),
            "is_sub_assembly_closed": sub_assembly_button.isChecked(),
        }

    def is_group_closed(self, name: str) -> bool:
        try:
            return self.closed_toolboxes[name]
        except KeyError:
            return True

    def is_assembly_closed(self, name: str) -> bool:
        try:
            return self.closed_toolboxes[name]["is_closed"]
        except KeyError:
            return True

    # NOTE multitoolbox's closing logic is different from assembly-multitoolbox, hence the oppositve return values
    def is_assembly_laser_cut_closed(self, name: str) -> bool:
        try:
            return self.closed_toolboxes[name]["is_laser_cut_closed"]
        except KeyError:
            return False

    def is_assembly_component_closed(self, name: str) -> bool:
        try:
            return self.closed_toolboxes[name]["is_component_closed"]
        except KeyError:
            return False

    def is_assembly_sub_assembly_closed(self, name: str) -> bool:
        try:
            return self.closed_toolboxes[name]["is_sub_assembly_closed"]
        except KeyError:
            return False
