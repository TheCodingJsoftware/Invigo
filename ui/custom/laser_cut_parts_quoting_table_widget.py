from PyQt6.QtWidgets import QAbstractItemView

from ui.custom_widgets import CustomTableWidget


class LaserCutPartsQuotingTableWidget(CustomTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.row_height = 70

        self.picture_column = 0
        self.part_name_column = 1
        self.material_column = 2
        self.thickness_column = 3
        self.quantity_column = 4
        self.part_dim_column = 5

        self.painting_column = 6
        self.paint_settings_column = 7
        self.paint_cost_column = 8

        self.cost_of_goods_column = 9
        self.bend_cost_column = 10
        self.labor_cost_column = 11
        self.unit_price_column = 12
        self.price_column = 13
        self.shelf_number_column = 14
        self.recut_column = 15
        self.add_to_inventory_column = 16

        self.set_editable_column_index(
            [
                self.quantity_column,
                self.bend_cost_column,
                self.labor_cost_column,
                self.shelf_number_column,
            ]
        )
        self.setShowGrid(True)
        self.setSortingEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        headers: dict[str, int] = {
            "Picture": self.picture_column,
            "Part name": self.part_name_column,
            "Material": self.material_column,
            "Thickness": self.thickness_column,
            "Qty": self.quantity_column,
            "Part Dim": self.part_dim_column,
            "Painting": self.painting_column,
            "Paint Settings": self.paint_settings_column,
            "Paint Cost": self.paint_cost_column,
            "Cost of\nGoods": self.cost_of_goods_column,
            "Bend Cost": self.bend_cost_column,
            "Labor Cost": self.labor_cost_column,
            "Unit Price": self.unit_price_column,
            "Price": self.price_column,
            "Shelf #": self.shelf_number_column,
            "Recut": self.recut_column,
            "Add to Inventory": self.add_to_inventory_column,
        }
        self.setColumnCount(len(list(headers.keys())))
        self.setHorizontalHeaderLabels(headers)
