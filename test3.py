import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

class MultiToolBox(QWidget):
    def __init__(self):
        super().__init__()

        self.widgets = []
        self.buttons = []

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

    def addTab(self, widget_text, button_text):
        widget = QLabel(widget_text)
        button = QPushButton(button_text)
        button.clicked.connect(lambda checked, w=widget: self.toggle_widget_visibility(w))

        layout = QVBoxLayout()
        layout.addWidget(button)
        layout.addWidget(widget)

        self.buttons.append(button)
        self.widgets.append(widget)

        self.layout().addLayout(layout)

    def toggle_widget_visibility(self, widget):
        widget.setVisible(not widget.isVisible())

if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = MultiToolBox()
    main_window.addTab("Widget 1", "Hide/Show Widget 1")
    main_window.addTab("Widget 2", "Hide/Show Widget 2")
    main_window.addTab("Widget 3", "Hide/Show Widget 3")
    main_window.show()

    sys.exit(app.exec_())
