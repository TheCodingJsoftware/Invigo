import contextlib
import os

THEME_PATH = f"{os.getcwd()}/ui/"

STYLE_SHEET_PATH_DICT = {"dark": os.path.join(THEME_PATH, "dark_theme.qss")}

DEFAULT_ICON_PATH = "icons"
CURRENT_ICON_PATH = os.path.join(THEME_PATH, DEFAULT_ICON_PATH).replace("\\", "/")


def set_theme(app, theme):
    with contextlib.suppress(TypeError):
        app.setStyle("fusion")

    with open(STYLE_SHEET_PATH_DICT[theme], "r", encoding="utf-8") as style_sheet:
        app.setStyleSheet(style_sheet.read().replace(DEFAULT_ICON_PATH, CURRENT_ICON_PATH))
