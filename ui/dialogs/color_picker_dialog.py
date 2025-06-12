# ------------------------------------- #
#                                       #
# Modern Color Picker by Tom F.         #
# Edited by GiorgosXou for Qt6 Support. #
# Modified by JareBear                  #
#                                       #
# Version 1.3                           #
# made with Qt Creator & PyQt5          #
#                                       #
# ------------------------------------- #

import colorsys

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog

from ui.dialogs.color_picker_dialog_UI import Ui_ColorPicker
from utils import colors


class ColorPicker(QDialog, Ui_ColorPicker):
    colorChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Extract Initial Color out of kwargs
        rgb = kwargs.pop("rgb", None)
        hsv = kwargs.pop("hsv", None)
        _hex = kwargs.pop("hex", None)

        # Connect update functions
        self.hue.mouseMoveEvent = self.moveHueSelector
        self.hue.mousePressEvent = self.moveHueSelector
        self.red.textEdited.connect(self.rgbChanged)
        self.green.textEdited.connect(self.rgbChanged)
        self.blue.textEdited.connect(self.rgbChanged)
        self.hex.textEdited.connect(self.hexChanged)
        self.red.setVisible(False)
        self.blue.setVisible(False)
        self.green.setVisible(False)
        self.lbl_red.setVisible(False)
        self.lbl_blue.setVisible(False)
        self.lbl_green.setVisible(False)

        # Connect selector moving function
        self.black_overlay.mouseMoveEvent = self.moveSVSelector
        self.black_overlay.mousePressEvent = self.moveSVSelector

        self.comboBox_colors_ral.addItems(list(colors.colors_ral.keys()))
        self.comboBox_colors_ral.currentTextChanged.connect(
            self.quick_ral_colors_changed
        )

        if rgb:
            self.setRGB(rgb)
        elif hsv:
            self.setHSV(hsv)
        elif _hex:
            self.setHex(_hex)
        else:
            self.setRGB((0, 0, 0))
        self.setStyleSheet(
            "QWidget{background-color: none;} QFrame{border-radius:5px;}"
        )

    def quick_ral_colors_changed(self):
        self.setHex(
            colors.colors_ral[self.comboBox_colors_ral.currentText()]["hex"]
            .lower()
            .replace("#", "")
        )
        self.lineEdit_color_name.setText(
            colors.colors_ral[self.comboBox_colors_ral.currentText()]["name"]
        )

    ## Main Functions ##
    def getHSV(self, hrange=100, svrange=100):
        h, s, v = self.color
        return (h * (hrange / 100.0), s * (svrange / 100.0), v * (svrange / 100.0))

    def getRGB(self, range=255):
        r, g, b = (
            self.i(self.red.text()),
            self.i(self.green.text()),
            self.i(self.blue.text()),
        )
        return (r * (range / 255.0), g * (range / 255.0), b * (range / 255.0))

    def getHex(self, ht=False):
        rgb = (
            self.i(self.red.text()),
            self.i(self.green.text()),
            self.i(self.blue.text()),
        )
        return f"#{self.rgb2hex(rgb)}" if ht else self.rgb2hex(rgb)

    def getColorName(self) -> str:
        return self.lineEdit_color_name.text()

    ## Update Functions ##
    def hsvChanged(self):
        h, s, v = (
            100 - self.hue_selector.y() / 1.85,
            (self.selector.x() + 6) / 2.0,
            (194 - self.selector.y()) / 2.0,
        )
        r, g, b = self.hsv2rgb(h, s, v)
        self.color = (h, s, v)
        self._setRGB((r, g, b))
        self._setHex(self.hsv2hex(self.color))
        self.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")
        self.color_view.setStyleSheet(
            f"border-radius: 5px;background-color: qlineargradient(x1:1, x2:0, stop:0 hsl({h}%,100%,50%), stop:1 #fff);"
        )
        self.colorChanged.emit()

    def rgbChanged(self):
        r, g, b = (
            self.i(self.red.text()),
            self.i(self.green.text()),
            self.i(self.blue.text()),
        )
        self.color = self.rgb2hsv(r, g, b)
        self._setHSV(self.color)
        self._setHex(self.rgb2hex((r, g, b)))
        self.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")
        self.colorChanged.emit()

    def hexChanged(self):
        _hex = self.hex.text()
        r, g, b = self.hex2rgb(_hex)
        self.color = self.hex2hsv(_hex)
        self._setHSV(self.color)
        self._setRGB(self.hex2rgb(_hex))
        self.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")
        self.colorChanged.emit()

    ## internal setting functions ##
    def _setRGB(self, c):
        r, g, b = c
        self.red.setText(str(self.i(r)))
        self.green.setText(str(self.i(g)))
        self.blue.setText(str(self.i(b)))

    def _setHSV(self, c):
        self.hue_selector.move(7, int((100 - c[0]) * 1.85))
        self.color_view.setStyleSheet(
            f"border-radius: 5px;background-color: qlineargradient(x1:1, x2:0, stop:0 hsl({c[0]}%,100%,50%), stop:1 #fff);"
        )
        self.selector.move(int(c[1] * 2 - 6), int((200 - c[2] * 2) - 6))

    def _setHex(self, c):
        self.hex.setText(c)

    ## external setting functions ##
    def setRGB(self, c):
        self._setRGB(c)
        self.rgbChanged()

    def setHSV(self, c):
        self._setHSV(c)
        self.hsvChanged()

    def setHex(self, c):
        self._setHex(c)
        self.hexChanged()

    ## Color Utility ##
    def hsv2rgb(self, h_or_color, s=0, v=0):
        if type(h_or_color).__name__ == "tuple":
            h, s, v = h_or_color
        else:
            h = h_or_color
        r, g, b = colorsys.hsv_to_rgb(h / 100.0, s / 100.0, v / 100.0)
        return self.clampRGB((r * 255, g * 255, b * 255))

    def rgb2hsv(self, r_or_color, g=0, b=0):
        if type(r_or_color).__name__ == "tuple":
            r, g, b = r_or_color
        else:
            r = r_or_color
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        return (h * 100, s * 100, v * 100)

    def hex2rgb(self, _hex):
        if len(_hex) < 6:
            _hex += "0" * (6 - len(_hex))
        elif len(_hex) > 6:
            _hex = _hex[:6]
        return tuple(int(_hex[i : i + 2], 16) for i in (0, 2, 4))

    def rgb2hex(self, r_or_color, g=0, b=0):
        if type(r_or_color).__name__ == "tuple":
            r, g, b = r_or_color
        else:
            r = r_or_color
        return "%02x%02x%02x" % (int(r), int(g), int(b))

    def hex2hsv(self, hex):
        return self.rgb2hsv(self.hex2rgb(hex))

    def hsv2hex(self, h_or_color, s=0, v=0):
        if type(h_or_color).__name__ == "tuple":
            h, s, v = h_or_color
        else:
            h = h_or_color
        return self.rgb2hex(self.hsv2rgb(h, s, v))

    # selector move function
    def moveSVSelector(self, event):
        if event.buttons() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        if pos.x() < 0:
            pos.setX(0)
        if pos.y() < 0:
            pos.setY(0)
        if pos.x() > 200:
            pos.setX(200)
        if pos.y() > 200:
            pos.setY(200)
        self.selector.move(int(pos.x() - 6), int(pos.y() - 6))
        self.hsvChanged()

    def moveHueSelector(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            pos = event.position().y() - 9
            pos = max(pos, 0)
            pos = min(pos, 185)
            self.hue_selector.move(QPoint(9, int(pos)))
            self.hsvChanged()

    def i(self, text):
        try:
            return int(text)
        except Exception:
            return 0

    def clampRGB(self, rgb):
        r, g, b = rgb
        if r < 0.0001:
            r = 0
        if g < 0.0001:
            g = 0
        if b < 0.0001:
            b = 0
        r = min(r, 255)
        g = min(g, 255)
        b = min(b, 255)
        return (r, g, b)
