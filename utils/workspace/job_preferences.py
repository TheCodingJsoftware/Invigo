from PyQt6.QtWidgets import QLineEdit, QPushButton

from utils.inventory.nest import Nest


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

    def job_nest_tool_box_toggled(
        self,
        job_name: str,
        global_sheet_settings_button: QPushButton,
        item_quoting_options_button: QPushButton,
        sheet_quoting_options_button: QPushButton,
        nest_summary_button: QPushButton,
        nests_button: QPushButton,
    ):
        self.closed_toolboxes[job_name] = {
            "is_global_sheet_settings_closed": global_sheet_settings_button.isChecked(),
            "is_item_quoting_options_closed": item_quoting_options_button.isChecked(),
            "is_sheet_quoting_options_closed": sheet_quoting_options_button.isChecked(),
            "is_nest_summary_closed": nest_summary_button.isChecked(),
            "is_nests_closed": nests_button.isChecked(),
        }

    def is_global_sheet_settings_closed(self, job_name: str) -> bool:
        try:
            return self.closed_toolboxes[job_name]["is_global_sheet_settings_closed"]
        except KeyError:
            return False

    def is_item_quoting_options_closed(self, job_name: str) -> bool:
        try:
            return self.closed_toolboxes[job_name]["is_item_quoting_options_closed"]
        except KeyError:
            return False

    def is_sheet_quoting_options_closed(self, job_name: str) -> bool:
        try:
            return self.closed_toolboxes[job_name]["is_sheet_quoting_options_closed"]
        except KeyError:
            return False

    def is_nest_summary_closed(self, job_name: str) -> bool:
        try:
            return self.closed_toolboxes[job_name]["is_nest_summary_closed"]
        except KeyError:
            return False

    def is_nests_closed(self, job_name: str) -> bool:
        try:
            return self.closed_toolboxes[job_name]["is_nests_closed"]
        except KeyError:
            return False

    def assembly_toolbox_toggled(
        self,
        name: QLineEdit,
        button: QPushButton,
        laser_cut_button: QPushButton,
        component_button: QPushButton,
        sub_assembly_button: QPushButton,
    ):
        self.closed_toolboxes[name.text()] = {
            "is_closed": button.isChecked(),
            "is_laser_cut_closed": laser_cut_button.isChecked(),
            "is_component_closed": component_button.isChecked(),
            "is_sub_assembly_closed": sub_assembly_button.isChecked(),
        }

    def nest_toggled(self, nest_name: str, nest_button: QPushButton):
        self.closed_toolboxes.setdefault(
            nest_name,
            {
                "is_closed": False,
                "is_setting_closed": False,
                "is_laser_cut_closed": False,
                "is_image_closed": False,
            },
        )
        self.closed_toolboxes[nest_name]["is_closed"] = nest_button.isChecked()

    def is_nest_closed(self, nest_name: str) -> bool:
        try:
            return self.closed_toolboxes[nest_name]["is_closed"]
        except KeyError:
            return True

    def nest_widget_toolbox_toggled(self, nest: Nest, setting_button: QPushButton, laser_cut_button: QPushButton, image_button: QPushButton):
        self.closed_toolboxes.setdefault(
            nest.get_name(),
            {
                "is_closed": False,
                "is_setting_closed": False,
                "is_laser_cut_closed": False,
                "is_image_closed": False,
            },
        )
        self.closed_toolboxes[nest.get_name()]["is_setting_closed"] = setting_button.isChecked()
        self.closed_toolboxes[nest.get_name()]["is_laser_cut_closed"] = laser_cut_button.isChecked()
        self.closed_toolboxes[nest.get_name()]["is_image_closed"] = image_button.isChecked()

    def is_nest_setting_closed(self, nest: Nest) -> bool:
        try:
            return self.closed_toolboxes[nest.get_name()]["is_setting_closed"]
        except KeyError:
            return False

    def is_nest_laser_cut_closed(self, nest: Nest) -> bool:
        try:
            return self.closed_toolboxes[nest.get_name()]["is_laser_cut_closed"]
        except KeyError:
            return False

    def is_nest_image_closed(self, nest: Nest) -> bool:
        try:
            return self.closed_toolboxes[nest.get_name()]["is_image_closed"]
        except KeyError:
            return False

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
