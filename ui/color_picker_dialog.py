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
import sys

from PyQt6 import uic
from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent
from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow

from ui.theme import set_theme


class ColorPicker(QDialog):

    colorChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(ColorPicker, self).__init__(*args, **kwargs)
        uic.loadUi("ui/color_picker_dialog.ui", self)

        # Extract Initial Color out of kwargs
        rgb = kwargs.pop("rgb", None)
        hsv = kwargs.pop("hsv", None)
        _hex = kwargs.pop("hex", None)

        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
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

        if rgb:
            self.setRGB(rgb)
        elif hsv:
            self.setHSV(hsv)
        elif _hex:
            self.setHex(_hex)
        else:
            self.setRGB((0, 0, 0))
        self.load_theme()
        self.setStyleSheet("QWidget{background-color: none;} QFrame{border-radius:5px;}")

    ## Main Functions ##
    def getHSV(self, hrange=100, svrange=100):
        """
        This function returns the HSV (hue, saturation, value) values of a given color with a specified
        range for hue and saturation/value.

        Args:
          hrange: The range of values for the hue component of the color in the returned HSV tuple. It
        is a percentage value, where 100% represents the full range of 0-360 degrees for hue. So if
        hrange is set to 50, the returned hue value will be in the range of. Defaults to 100
          svrange: svrange stands for saturation and value range. It is a parameter that determines the
        maximum range of saturation and value values that can be returned by the function. The value is
        expressed as a percentage, with 100% being the maximum possible value. Defaults to 100

        Returns:
          A tuple containing the hue, saturation, and value of the color converted to the specified
        range. The hue is scaled to the range of 0 to hrange, and the saturation and value are scaled to
        the range of 0 to svrange.
        """
        h, s, v = self.color
        return (h * (hrange / 100.0), s * (svrange / 100.0), v * (svrange / 100.0))

    def getRGB(self, range=255):
        """
        This function takes in RGB values as text inputs, converts them to a range between 0 and 255,
        and returns them as a tuple.

        Args:
          range: The "range" parameter is a value that determines the maximum value of each color
        channel in the returned RGB tuple. By default, it is set to 255, which is the maximum value for
        an 8-bit color channel. If you set it to a different value, the RGB values will be. Defaults to
        255

        Returns:
          A tuple containing the RGB values of the color represented by the red, green, and blue text
        inputs, scaled to a range specified by the optional argument "range".
        """
        r, g, b = self.i(self.red.text()), self.i(self.green.text()), self.i(self.blue.text())
        return (r * (range / 255.0), g * (range / 255.0), b * (range / 255.0))

    def getHex(self, ht=False):
        """
        This function takes RGB values as input and returns a hexadecimal color code, with an optional
        '#' symbol.

        Args:
          ht: ht is a boolean parameter that stands for "hash tag". If ht is True, the function returns
        the RGB color code in the format of a CSS hex color code with a hash tag (#) prefix. If ht is
        False, the function returns the RGB color code without the hash tag prefix. Defaults to False

        Returns:
          The function `getHex()` returns a hexadecimal color code string in the format `#RRGGBB` or
        `RRGGBB` depending on the value of the `ht` parameter. The color code is obtained by converting
        the RGB values of a color input (taken from `red`, `green`, and `blue` text fields) to
        hexadecimal using the `rgb2hex()` method
        """
        rgb = (self.i(self.red.text()), self.i(self.green.text()), self.i(self.blue.text()))
        return f"#{self.rgb2hex(rgb)}" if ht else self.rgb2hex(rgb)

    def getColorName(self) -> str:
        return self.lineEdit_color_name.text()

    ## Update Functions ##
    def hsvChanged(self):
        """
        This function updates the color values and visual representation based on changes to the HSV
        color selector.
        """
        h, s, v = (100 - self.hue_selector.y() / 1.85, (self.selector.x() + 6) / 2.0, (194 - self.selector.y()) / 2.0)
        r, g, b = self.hsv2rgb(h, s, v)
        self.color = (h, s, v)
        self._setRGB((r, g, b))
        self._setHex(self.hsv2hex(self.color))
        self.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")
        self.color_view.setStyleSheet(f"border-radius: 5px;background-color: qlineargradient(x1:1, x2:0, stop:0 hsl({h}%,100%,50%), stop:1 #fff);")
        self.colorChanged.emit()

    def rgbChanged(self):
        """
        This function converts RGB values to HSV, sets the color and hex values, updates the color
        visualization, and emits a signal for color change.
        """
        r, g, b = self.i(self.red.text()), self.i(self.green.text()), self.i(self.blue.text())
        self.color = self.rgb2hsv(r, g, b)
        self._setHSV(self.color)
        self._setHex(self.rgb2hex((r, g, b)))
        self.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")
        self.colorChanged.emit()

    def hexChanged(self):
        """
        This function converts a hexadecimal color code to its corresponding RGB and HSV values, sets
        the color values, updates the color visualization, and emits a signal for color change.
        """
        _hex = self.hex.text()
        r, g, b = self.hex2rgb(_hex)
        self.color = self.hex2hsv(_hex)
        self._setHSV(self.color)
        self._setRGB(self.hex2rgb(_hex))
        self.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")
        self.colorChanged.emit()

    ## internal setting functions ##
    def _setRGB(self, c):
        """
        This function sets the values of red, green, and blue components of a color in a GUI.

        Args:
          c: c is a tuple containing three integers representing the values for red, green, and blue
        color channels.
        """
        r, g, b = c
        self.red.setText(str(self.i(r)))
        self.green.setText(str(self.i(g)))
        self.blue.setText(str(self.i(b)))

    def _setHSV(self, c):
        """
        This function sets the hue, color view, and selector position based on the given HSV color.

        Args:
          c: The parameter "c" is a tuple containing three values representing the HSV (hue, saturation,
        value) color model. The first value (c[0]) represents the hue, which is a value between 0 and
        360 degrees. The second value (c[1]) represents the saturation,
        """
        self.hue_selector.move(7, int((100 - c[0]) * 1.85))
        self.color_view.setStyleSheet(f"border-radius: 5px;background-color: qlineargradient(x1:1, x2:0, stop:0 hsl({c[0]}%,100%,50%), stop:1 #fff);")
        self.selector.move(int(c[1] * 2 - 6), int((200 - c[2] * 2) - 6))

    def _setHex(self, c):
        """
        This function sets the text of a widget called "hex" to the value of the input parameter "c".

        Args:
          c: The parameter "c" is a string representing a hexadecimal value that will be set as the text
        of a widget called "hex".
        """
        self.hex.setText(c)

    ## external setting functions ##
    def setRGB(self, c):
        """
        This function sets the RGB value of an object and triggers a notification that the RGB value has
        changed.

        Args:
          c: The parameter "c" is a color value that is being passed to the "setRGB" method. It is used
        to set the RGB (Red, Green, Blue) values of an object. The exact format of the color value may
        depend on the implementation of the method and the programming language being
        """
        self._setRGB(c)
        self.rgbChanged()

    def setHSV(self, c):
        """
        This function sets the HSV color value and triggers a change event.

        Args:
          c: The parameter "c" is likely a tuple or list containing three values representing the hue,
        saturation, and value (brightness) of a color in the HSV (hue, saturation, value) color space.
        This method sets the HSV values of an object to the values in the "c" parameter and
        """
        self._setHSV(c)
        self.hsvChanged()

    def setHex(self, c):
        """
        This function sets a hexadecimal value and triggers a hexChanged event.

        Args:
          c: The parameter "c" is likely a hexadecimal color code that is being passed to the method
        "setHex" as an argument. The method then sets the value of the color to the provided hexadecimal
        value and triggers the "hexChanged" event.
        """
        self._setHex(c)
        self.hexChanged()

    ## Color Utility ##
    def hsv2rgb(self, h_or_color, s=0, v=0):
        """
        This function converts a color from HSV color space to RGB color space.

        Args:
          h_or_color: This parameter can either be a float representing the hue value in degrees
        (0-360), or a tuple containing the hue, saturation, and value values (all floats between 0-100).
          s: The saturation value in the HSV color model. It represents the intensity or purity of the
        color. A value of 0 means the color is completely unsaturated (gray), while a value of 100 means
        the color is fully saturated. Defaults to 0
          v: The "v" parameter stands for "value" and represents the brightness of the color. It is a
        value between 0 and 100, where 0 is completely black and 100 is the brightest possible color.
        Defaults to 0

        Returns:
          the RGB color values obtained by converting the input HSV color values to RGB using the
        colorsys module, and then clamping the RGB values to the range of 0-255 using the clampRGB
        method.
        """
        if type(h_or_color).__name__ == "tuple":
            h, s, v = h_or_color
        else:
            h = h_or_color
        r, g, b = colorsys.hsv_to_rgb(h / 100.0, s / 100.0, v / 100.0)
        return self.clampRGB((r * 255, g * 255, b * 255))

    def rgb2hsv(self, r_or_color, g=0, b=0):
        """
        This function converts an RGB color value to its corresponding HSV color value.

        Args:
          r_or_color: This parameter can either be a single value representing the red component of an
        RGB color or a tuple containing all three RGB components (red, green, and blue).
          g: The parameter "g" represents the green component of an RGB color. It is an optional
        parameter with a default value of 0, which means that if it is not provided, it will default to
        0. Defaults to 0
          b: The parameter "b" represents the blue component of an RGB color. It is used in the rgb2hsv
        function to convert an RGB color to its corresponding HSV color values. Defaults to 0

        Returns:
          A tuple containing the hue, saturation, and value (brightness) values in the HSV color space,
        with each value multiplied by 100.
        """
        if type(r_or_color).__name__ == "tuple":
            r, g, b = r_or_color
        else:
            r = r_or_color
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        return (h * 100, s * 100, v * 100)

    def hex2rgb(self, _hex):
        """
        This function converts a hexadecimal color code to its corresponding RGB values.

        Args:
          _hex: _hex is a string parameter representing a hexadecimal color code.

        Returns:
          The function `hex2rgb` returns a tuple of three integers representing the red, green, and blue
        values of a given hexadecimal color code.
        """
        if len(_hex) < 6:
            _hex += "0" * (6 - len(_hex))
        elif len(_hex) > 6:
            _hex = _hex[:6]
        return tuple(int(_hex[i : i + 2], 16) for i in (0, 2, 4))

    def rgb2hex(self, r_or_color, g=0, b=0):
        """
        This function converts RGB values to hexadecimal color code.

        Args:
          r_or_color: This parameter can be either an integer representing the red value of the RGB
        color or a tuple containing the RGB values.
          g: The parameter "g" represents the green component of an RGB color. It has a default value of
        0, which means that if it is not provided as an argument when calling the function, it will be
        assumed to be 0. Defaults to 0
          b: The parameter "b" represents the blue component of an RGB color. It is used in the function
        to convert an RGB color to its corresponding hexadecimal representation. Defaults to 0

        Returns:
          a string that represents the hexadecimal value of the RGB color passed as input.
        """
        if type(r_or_color).__name__ == "tuple":
            r, g, b = r_or_color
        else:
            r = r_or_color
        return "%02x%02x%02x" % (int(r), int(g), int(b))

    def hex2hsv(self, hex):
        """
        This function converts a hexadecimal color code to its corresponding HSV color values.

        Args:
          hex: The hex parameter is a string representing a hexadecimal color code. It is used as input
        to convert the color from hex format to HSV format.

        Returns:
          The function `hex2hsv` is returning the result of calling the `rgb2hsv` function with the
        argument being the result of calling the `hex2rgb` function with the `hex` argument passed to
        the `hex2hsv` function.
        """
        return self.rgb2hsv(self.hex2rgb(hex))

    def hsv2hex(self, h_or_color, s=0, v=0):
        """
        This function converts a given HSV color or tuple to its corresponding hexadecimal value.

        Args:
          h_or_color: This parameter can either be a float representing the hue value in the range of 0
        to 1, or a tuple containing three values representing the hue, saturation, and value in the same
        range.
          s: s stands for saturation in the HSV (Hue, Saturation, Value) color model. It determines the
        intensity or purity of the color. A saturation value of 0 means the color is completely gray,
        while a value of 1 means the color is fully saturated and appears vivid. Defaults to 0
          v: The "v" parameter in the function represents the value or brightness component of the HSV
        (hue, saturation, value) color model. It determines how bright or dark the color is. The value
        ranges from 0 to 1, with 0 being completely black and 1 being the brightest possible. Defaults
        to 0

        Returns:
          a hexadecimal color code converted from an input in the HSV (hue, saturation, value) color
        space. The input can be either a tuple of (hue, saturation, value) values or just the hue value,
        with saturation and value set to default values of 0. The function first converts the input from
        HSV to RGB color space using the hsv2rgb() function, and
        """
        if type(h_or_color).__name__ == "tuple":
            h, s, v = h_or_color
        else:
            h = h_or_color
        return self.rgb2hex(self.hsv2rgb(h, s, v))

    # selector move function
    def moveSVSelector(self, event):
        """
        This function moves a selector and updates the HSV values based on the position of a mouse
        event.

        Args:
          event: The event parameter is an object that represents the event that triggered the function.
        In this case, it is a mouse event.

        Returns:
          If the event button is not the left mouse button, the function returns nothing (i.e., None).
        """
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
        """
        This function moves a hue selector based on the position of a mouse event and updates the HSV
        values.

        Args:
          event: The event parameter is an object that represents a user action or system event, such as
        a mouse click or a key press. It contains information about the event, such as the type of
        event, the position of the mouse cursor, and any keys that were pressed. In this case, the
        function is
        """
        if event.buttons() == Qt.MouseButton.LeftButton:
            pos = event.position().y() - 9
            pos = max(pos, 0)
            pos = min(pos, 185)
            self.hue_selector.move(QPoint(9, int(pos)))
            self.hsvChanged()

    def i(self, text):
        """
        The function takes a string as input and tries to convert it to an integer, returning 0 if it
        fails.

        Args:
          text: The text parameter is a string that represents a number that we want to convert to an
        integer.

        Returns:
          If the input `text` can be converted to an integer, the function will return the integer value
        of `text`. If `text` cannot be converted to an integer, the function will return 0.
        """
        try:
            return int(text)
        except Exception:
            return 0

    def clampRGB(self, rgb):
        """
        The function clamps the RGB values to be within the range of 0 to 255 and sets any values less
        than 0.0001 to 0.

        Args:
          rgb: The parameter `rgb` is a tuple containing three values representing the red, green, and
        blue components of a color in the RGB color model. The values are typically integers ranging
        from 0 to 255, but in this function they are treated as floats. The function clamps the values
        to ensure

        Returns:
          a tuple of three values representing the clamped RGB values.
        """
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

    def load_theme(self) -> None:
        """
        It loads the stylesheet.qss file from the theme folder
        """
        set_theme(self, theme="dark")
