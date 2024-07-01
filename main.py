import sys
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import set_theme


def main():
    app = QApplication(sys.argv)

    set_theme(app, theme="dark")

    mainwindow = MainWindow()
    mainwindow.show()

    app.exec()


if __name__ == "__main__":
    main()
