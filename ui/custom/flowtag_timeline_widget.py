import contextlib
from datetime import datetime, timedelta
from typing import Union, TYPE_CHECKING

from utils.workspace.flowtag_timeline import FlowtagTimeline
from utils.workspace.tag import Tag

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import QSlider, QWidget, QHBoxLayout, QLabel, QVBoxLayout, QGridLayout

from superqt import QRangeSlider

if TYPE_CHECKING:
    from ui.widgets.job_widget import JobWidget


class FlowtagTimelineWidget(QWidget):
    def __init__(self, flowtag_timeline: FlowtagTimeline, parent=None):
        super().__init__(parent)
        self.parent: JobWidget = parent

        self.flowtag_timeline = flowtag_timeline
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.sliders: list[dict[str, Union[QRangeSlider, QLabel]]] = []
        self.load_tag_timelines()

    def set_range(self, start: QDate, end: QDate):
        for slider in self.sliders:
            slider['slider'].setMaximum(start.daysTo(end))

    def load_tag_timelines(self):
        self.clear_layout(self.grid_layout)
        self.sliders.clear()
        self.flowtag_timeline.load_data(self.flowtag_timeline.to_dict())

        job_start_date = datetime.strptime(self.flowtag_timeline.job.starting_date, "%Y-%m-%d")
        job_end_date = datetime.strptime(self.flowtag_timeline.job.ending_date, "%Y-%m-%d")
        job_duration = (job_end_date - job_start_date).days

        row = 0
        for tag, tag_data in self.flowtag_timeline.tags_data.items():
            slider = QRangeSlider(Qt.Orientation.Horizontal)
            slider.setTickPosition(QSlider.TickPosition.NoTicks)
            slider.setMaximum(job_duration)

            tag_start_date = datetime.strptime(tag_data["starting_date"], "%Y-%m-%d")
            tag_end_date = datetime.strptime(tag_data["ending_date"], "%Y-%m-%d")
            start_value = (tag_start_date - job_start_date).days
            end_value = (tag_end_date - tag_start_date).days  # Adjusted to be relative to the start_value

            tag_name_label = QLabel(f"{tag.name} ({end_value - start_value} days)")

            start_label = QLabel(f"{start_value}")
            end_label = QLabel(f"{end_value}")

            slider.setValue((start_value, end_value))

            slider.valueChanged.connect(lambda value, tag=tag, slider=slider, start_label=start_label, end_label=end_label, tag_name_label=tag_name_label: self.update_labels(value, tag, slider, start_label, end_label, tag_name_label))

            self.grid_layout.addWidget(tag_name_label, row, 0)
            self.grid_layout.addWidget(start_label, row, 1)
            self.grid_layout.addWidget(slider, row, 2)
            self.grid_layout.addWidget(end_label, row, 3)

            self.sliders.append({'tag': tag, 'slider': slider, 'start_label': start_label, 'end_label': end_label, 'tag_name_label': tag_name_label})
            row += 1

    def update_labels(self, value: tuple[int, int], tag: Tag, slider: QRangeSlider, start_label: QLabel, end_label: QLabel, tag_name_label: QLabel):
        start_label.setText(str(value[0]))
        end_label.setText(str(value[1]))

        start_date = datetime.strptime(self.flowtag_timeline.job.starting_date, "%Y-%m-%d")
        tag_start_date = start_date + timedelta(days=value[0])
        tag_end_date = tag_start_date + timedelta(days=value[1])

        self.flowtag_timeline.tags_data[tag]["starting_date"] = tag_start_date.strftime("%Y-%m-%d")
        self.flowtag_timeline.tags_data[tag]["ending_date"] = tag_end_date.strftime("%Y-%m-%d")

        tag_name_label.setText(f"{tag.name} ({value[1] - value[0]} days)")
        self.changes_made()

    def changes_made(self):
        self.parent.parent.job_changed(self.parent.job)
        self.parent.update_nest_parts_assemblies()
        self.parent.update_prices()

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

