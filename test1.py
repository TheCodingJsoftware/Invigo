from PyQt6.QtWidgets import QApplication

from ui.select_timeline_dialog import SelectTimeLineDialog
from ui.theme import set_theme

if __name__ == "__main__":
    app = QApplication([])
    set_theme(app, theme="dark")
    window = SelectTimeLineDialog()
    window.show()
    app.exec()
