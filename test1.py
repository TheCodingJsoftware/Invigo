from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)


class StatusWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        # Create the QLineEdit widgets for status text
        status_edit_1 = QLineEdit(self)
        status_edit_2 = QLineEdit(self)
        status_edit_3 = QLineEdit(self)

        # Create the QRadioButton widgets
        radio_button_1 = QRadioButton("Complete", self)
        radio_button_2 = QRadioButton("Complete", self)
        radio_button_3 = QRadioButton("Complete", self)

        # Create layouts for the main widget, status text, and radio buttons
        main_layout = QHBoxLayout(self)
        status_layout = QVBoxLayout()
        button_layout = QVBoxLayout()

        # Add the QLineEdit widgets to the status layout
        status_layout.addWidget(status_edit_1)
        status_layout.addWidget(status_edit_2)
        status_layout.addWidget(status_edit_3)

        # Add the QRadioButton widgets to the button layout
        button_layout.addWidget(radio_button_1)
        button_layout.addWidget(radio_button_2)
        button_layout.addWidget(radio_button_3)

        # Add the status layout and button layout to the main layout
        main_layout.addLayout(status_layout)
        main_layout.addLayout(button_layout)

        # Set the layout for the main widget
        self.setLayout(main_layout)


if __name__ == "__main__":
    app = QApplication([])
    window = StatusWidget()
    window.show()
    app.exec()
