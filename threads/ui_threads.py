from PyQt5.QtCore import QThread

from utils.json_file import JsonFile

settings_file = JsonFile(file_name="settings")


class ProcessItemSelectedThread(QThread):
    """This class is a QThread that emits a signal when it's done processing a list of items"""

    def __init__(self, QObjects: dict, highlight_color: str, selected_item) -> None:
        """
        A constructor for the class.

        Args:
          QObjects (dict): dict = {'QObject1': QObject1, 'QObject2': QObject2, 'QObject3': QObject3}
          highlight_color (str): str = The color to highlight the selected item with.
          selected_item: The item that was selected in the list
        """
        QThread.__init__(self)
        self.QObjects: dict = QObjects
        self.highlight_color: str = highlight_color
        self.selected_item = selected_item
        self.theme: str = (
            "dark" if settings_file.get_value(item_name="dark_mode") else "light"
        )

    def run(self) -> None:
        """
        It's a function that changes the background color of a QComboBox widget and a QSpinBox widget
        when the QComboBox widget is clicked
        """
        for item in list(self.QObjects.keys()):
            spin_current_quantity = self.QObjects[item]["current_quantity"]
            if item.currentText() == self.selected_item:
                if self.highlight_color == "#3daee9":
                    item.setStyleSheet(
                        f"background-color: {self.highlight_color}; border: 1px solid {self.highlight_color};"
                    )
                    if spin_current_quantity.value() <= 0:
                        spin_current_quantity.setStyleSheet(
                            "background-color: #1d2023; color: red"
                        )
                    else:
                        spin_current_quantity.setStyleSheet(
                            "background-color: #1d2023; color: white"
                        )
                else:
                    if spin_current_quantity.value() <= 0:
                        spin_current_quantity.setStyleSheet(
                            f"background-color: {self.highlight_color}; border: 1px solid {self.highlight_color}; color: red"
                        )
                    else:
                        spin_current_quantity.setStyleSheet(
                            f"background-color: {self.highlight_color}; border: 1px solid {self.highlight_color}; color: white"
                        )
                    self.highlight_color = "#3daee9"
            elif self.theme == "dark":
                if self.highlight_color == "#3daee9":
                    item.setStyleSheet("background-color: #1d2023")
                if spin_current_quantity.value() <= 0:
                    spin_current_quantity.setStyleSheet(
                        "background-color: #1d2023; color: red"
                    )

                else:
                    spin_current_quantity.setStyleSheet(
                        "background-color: #1d2023; color: white"
                    )

            else:
                if self.highlight_color == "#3daee9":
                    item.setStyleSheet("background-color: #eff0f1")
                if spin_current_quantity.value() <= 0:
                    spin_current_quantity.setStyleSheet(
                        "background-color: #eff0f1; color: red"
                    )
                else:
                    spin_current_quantity.setStyleSheet(
                        "background-color: #eff0f1; color: white"
                    )


class SetStyleSheetThread(QThread):
    """This class is a QThread that sets the stylesheet of a QWidget"""

    def __init__(self, QObject: object, stylesheet: str) -> None:
        """
        A constructor for the class.

        Args:
          QObject (object): The object you want to apply the stylesheet to.
          stylesheet (str): The stylesheet you want to apply to the QObject
        """
        QThread.__init__(self)
        self.QObject: object = object
        self.stylesheet: str = stylesheet

    def run(self) -> None:
        """
        It sets the stylesheet of the QObject to the stylesheet that was passed in
        """
        self.QObject.setStyleSheet(self.stylesheet)
