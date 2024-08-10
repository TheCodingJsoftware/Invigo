import contextlib
from datetime import datetime, timedelta
from typing import Union, TYPE_CHECKING

from ui.custom.time_double_spin_box import TimeSpinBox
from utils.workspace.flowtag_data import FlowtagData
from utils.workspace.tag import Tag

from PyQt6.QtWidgets import QWidget, QLabel, QGridLayout


if TYPE_CHECKING:
    from ui.custom.assembly_planning_widget import AssemblyPlanningWidget


class FlowtagDataWidget(QWidget):
    def __init__(self, flowtag_data: FlowtagData, parent=None):
        super().__init__(parent)
        self.parent: AssemblyPlanningWidget = parent
        self.flowtag_data = flowtag_data
        self.grid_layout = QGridLayout()
        self.grid_layout.setVerticalSpacing(1)
        self.grid_layout.setHorizontalSpacing(0)
        self.setLayout(self.grid_layout)
        self.load_ui()

    def load_ui(self):
        self.clear_layout(self.grid_layout)  # Clear any existing layout

        row = 0
        for tag, tag_data in self.flowtag_data.tags_data.items():
            tag_label = QLabel(tag.name)
            tag_label.setFixedWidth(120)
            self.grid_layout.addWidget(tag_label, row, 0)

            label = QLabel("Exp. Dur.:")
            label.setFixedWidth(80)
            self.grid_layout.addWidget(label, row, 1)

            time_spin_box = TimeSpinBox(self)
            time_spin_box.setValue(tag_data["expected_time_to_complete"])
            time_spin_box.dateTimeChanged.connect(
                lambda value, t=tag: self.update_expected_time_to_complete(t, value)
            )

            self.grid_layout.addWidget(time_spin_box, row, 2)

            row += 1
        self.update_widget_size()

    def update_expected_time_to_complete(self, tag: Tag, value: float):
        self.flowtag_data.set_tag_data(tag, "expected_time_to_complete", value)
        self.changes_made()

    def changes_made(self):
        self.parent.changes_made()

    def update_widget_size(self):
        self.setFixedSize(400, len(self.flowtag_data.tags_data) * 40)

    def clear_layout(self, layout: QGridLayout):
        with contextlib.suppress(AttributeError):
            if layout is not None:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.deleteLater()
                    else:
                        self.clear_layout(item.layout())