from PyQt6.QtWidgets import QDialog, QInputDialog, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QDoubleSpinBox


class OrderPendingQuantityDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cancel_order = False
        self.setWindowTitle("Add Quantity")

        # Main vertical layout
        v_layout = QVBoxLayout(self)

        # Label
        self.label = QLabel()
        v_layout.addWidget(self.label)

        h_layout = QHBoxLayout()
        self.input_quantity = QDoubleSpinBox()
        self.input_quantity.setMaximum(float("inf"))
        h_layout.addWidget(QLabel("Quantity to Add:"))
        h_layout.addWidget(self.input_quantity)

        v_layout.addLayout(h_layout)

        h_layout = QHBoxLayout()
        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.accept)
        h_layout.addWidget(self.ok_button)

        self.cancel_pending_button = QPushButton("Cancel Pending")
        self.cancel_pending_button.clicked.connect(self.cancel_pending)
        h_layout.addWidget(self.cancel_pending_button)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        h_layout.addWidget(self.close_button)

        v_layout.addLayout(h_layout)

    def set_quantity_input(self, part_name, order_pending_quantity):
        self.label.setText(f'Do you want to add the incoming quantity for:\n\n{part_name}.\n\nPress "OK" to update quantity.')
        self.input_quantity.setValue(order_pending_quantity)

    def cancel_pending(self):
        self.cancel_order = True
        self.accept()