import builtins
import sys

from PyQt6.QtWidgets import QApplication

from config.environments import Environment
from ui.icons import Icons
from ui.theme import set_theme
from ui.windows.main_window import MainWindow

# if Environment.APP_ENV == "development":
#     from rich import print as rich_print

#     builtins.print = rich_print


def main():
    app = QApplication(sys.argv)

    set_theme(app, theme="dark")

    Icons.load_icons()

    mainwindow = MainWindow()
    mainwindow.show()

    app.exec()


if __name__ == "__main__":
    main()
