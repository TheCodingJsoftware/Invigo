
import os
from PyQt5 import QtGui

THEME_PATH = os.getcwd() + "/ui/"

STYLE_SHEET_PATH_DICT = {
    'dark': os.path.join(THEME_PATH, 'dark_theme.css')
}

DEFAULT_ICON_PATH = 'icons'
CURRENT_ICON_PATH = os.path.join(THEME_PATH, DEFAULT_ICON_PATH).replace('\\', '/')

def set_theme(app, theme: str = 'default') -> None:
    ''' This function use to set theme for "QApplication", support for "PySide2" and "PyQt5"
    '''
    # Get the name of the library that the app object belongs to
    lib_name = app.__module__.split('.')[0]

    # Import the QtGui module from the library with the name stored in lib_name
    # QtGui = __import__(lib_name).QtGui

    # Check if the theme is set to 'dark'
    if theme == 'dark':
        # Set the application style to 'Fusion'
        try:
            app.setStyle('fusion')
        except TypeError:
            pass

        # Create a palette with dark colors
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor(44, 44, 44))
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(246, 246, 246))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(29, 29, 29))
        palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
        palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(0, 0, 0))
        palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(210, 210, 210))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(210, 218, 218))
        palette.setColor(QtGui.QPalette.Button, QtGui.QColor(44, 44, 44))
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(210, 210, 210))
        palette.setColor(QtGui.QPalette.BrightText, QtGui.QColor(246, 0, 0))
        palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(110, 120, 125, 127))
        # Apply the dark palette to the application
        app.setPalette(palette)

        # set dark theme style sheet
        with open(STYLE_SHEET_PATH_DICT[theme], 'r') as style_sheet:
            app.setStyleSheet(style_sheet.read().replace(DEFAULT_ICON_PATH, CURRENT_ICON_PATH))
    
    # Check if the theme is set to 'default'
    elif theme == 'default':
        # Set the application style to an empty string, which resets it to the default style
        app.setStyle(str())

        # Reset the application palette to the default palette
        app.setPalette(QtGui.QPalette())