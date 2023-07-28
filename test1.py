from PyQt6.QtWidgets import QApplication

from ui.generate_workorder_dialog import GenerateWorkorderDialog
from ui.theme import set_theme

if __name__ == "__main__":
    app = QApplication([])
    set_theme(app, theme="dark")
    window = GenerateWorkorderDialog()
    window.show()
    app.exec()
