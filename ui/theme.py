import contextlib
import os
import re

from utils.settings import Settings

from PyQt6.QtWidgets import QApplication

settings = Settings()

UI_PATH = f"{os.getcwd()}/ui/"
STYLE_PATH = os.path.join(UI_PATH, "style", "style.qss")
THEME_PATH = os.path.join(UI_PATH, "themes", f"{settings.get_value('theme')}.css")

DEFAULT_ICON_PATH = "icons"
CURRENT_ICON_PATH = os.path.join(UI_PATH, DEFAULT_ICON_PATH).replace("\\", "/")

THEME_VARIABLES = {}


def parse_theme_css(theme_file: str):
    variables = {}
    with open(theme_file, "r", encoding="utf-8") as file:
        content = file.read()
        matches = re.findall(r"--([\w-]+):\s*([^;]+);", content)
        for name, value in matches:
            variables[name] = value.strip()
    return variables


def apply_theme_to_qss(qss_content, variables):
    def replacer(match):
        var_name = match.group(1)
        return variables.get(var_name, match.group(0))

    return re.sub(r"var\(--([\w-]+)\)", replacer, qss_content)


def theme_var(variable_name: str) -> str:
    global THEME_VARIABLES
    if not THEME_VARIABLES:
        THEME_VARIABLES = parse_theme_css(THEME_PATH)
    return THEME_VARIABLES.get(variable_name, None)


def set_theme(app: QApplication, theme: str):
    global THEME_VARIABLES

    with contextlib.suppress(TypeError):
        app.setStyle("fusion")

    THEME_VARIABLES = parse_theme_css(THEME_PATH)

    with open(STYLE_PATH, "r", encoding="utf-8") as style_sheet:
        qss_content = style_sheet.read().replace(DEFAULT_ICON_PATH, CURRENT_ICON_PATH)
        updated_qss = apply_theme_to_qss(qss_content, THEME_VARIABLES)

    app.setStyleSheet(updated_qss)
