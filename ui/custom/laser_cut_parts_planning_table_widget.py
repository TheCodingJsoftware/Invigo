from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView

from ui.custom_widgets import CustomTableWidget


class LaserCutPartsPlanningTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super(LaserCutPartsPlanningTableWidget, self).__init__(parent)
        self.image_column = 0
        self.part_name_column = 1
        self.bending_files_column = 2
        self.welding_files_column = 3
        self.cnc_milling_files_column = 4
        self.material_column = 5
        self.thickness_column = 6
        self.quantity_column = 7
        self.painting_column = 8
        self.paint_settings_column = 9
        self.flow_tag_column = 10
        self.expected_time_to_complete_column = 11
        self.notes_column = 12
        self.shelf_number_column = 13

        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.set_editable_column_index([self.part_name_column, self.quantity_column, self.notes_column, self.shelf_number_column])

        headers: dict[str, int] = {
            "Picture": self.image_column,
            "Part Name": self.part_name_column,
            "Bending Files": self.bending_files_column,
            "Welding Files": self.welding_files_column,
            "CNC/Milling Files": self.cnc_milling_files_column,
            "Material": self.material_column,
            "Thickness": self.thickness_column,
            "Quantity": self.quantity_column,
            "Painting": self.painting_column,
            "Paint Settings": self.paint_settings_column,
            "Flow Tag": self.flow_tag_column,
            "Expected time\nto complete": self.expected_time_to_complete_column,
            "Notes": self.notes_column,
            "Shelf #": self.shelf_number_column,
        }

        self.setColumnCount(len(list(headers.keys())))
        self.setHorizontalHeaderLabels(headers)
        self.setStyleSheet("border-color: transparent;")
