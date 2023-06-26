from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget, QPushButton, QFormLayout


class UberButtonTabWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.tab_widget = QTabWidget()
        self.show_all_tab = QWidget()
        layout = QFormLayout(self.show_all_tab)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)  # Set alignment to top-left
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)  # Allow fields to grow
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)  # Set label alignment to left

        self.tab_widget.addTab(self.show_all_tab, "Show All")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

        self.buttons: list[QPushButton] = []

        self.tabs = {"Show All": []}  # Dictionary to store tabs and their buttons
        self.tab_widget.currentChanged.connect(self.update_tab_button_visibility)

    def add_tab(self, name):
        tab_container = QWidget()
        tab_widget = QWidget()
        layout = QFormLayout(tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)  # Set alignment to top-left
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)  # Allow fields to grow
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)  # Set label alignment to left
        tab_widget.setLayout(layout)
        tab_container_layout = QVBoxLayout(tab_container)
        tab_container_layout.addWidget(tab_widget)
        self.tab_widget.addTab(tab_container, name)

        self.tabs[name] = []  # Add tab with an empty list for buttons

        return layout

    def add_button_to_tab(self, tab_name, button_name):
        buttons = self.tabs.get(tab_name)
        if buttons is not None:
            button = QPushButton(button_name, checkable=True)
            buttons.append(button)  # Add button to the list
            self.buttons.append(button)

    def get_buttons(self, tab_name):
        buttons = self.tabs.get(tab_name)
        if buttons is not None:
            return buttons
        return []

    def update_tab_button_visibility(self, tab_index: int):
        tab_name = self.tab_widget.tabText(tab_index)
        buttons = self.tabs.get(tab_name)
        if tab_name == "Show All":
            layout = self.tab_widget.widget(tab_index).layout()
            for button in self.buttons:
                layout.addWidget(button)
                button.setVisible(True)
        else:
            if buttons is not None:
                layout = self.tab_widget.widget(tab_index).layout()
                for button in self.buttons:
                    if button in buttons:
                        layout.addWidget(button)
                        button.setVisible(True)
                    else:
                        button.setVisible(False)


if __name__ == "__main__":
    app = QApplication([])
    window = UberButtonTabWidget()

    tab1_layout = window.add_tab("Tab 1")
    tab2_layout = window.add_tab("Tab 2")

    window.add_button_to_tab("Tab 1", "Button 1")
    window.add_button_to_tab("Tab 1", "Button 2")
    window.add_button_to_tab("Tab 2", "Button 3")

    window.update_tab_button_visibility(0)

    window.show()
    app.exec()
