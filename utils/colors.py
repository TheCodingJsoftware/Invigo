import colorsys
import random

from colormap import hls2rgb, rgb2hex, rgb2hls

# pip install colormap
# pip install easydev


def hex_to_rgb(hex: str):
    """
    The function `hex_to_rgb` takes a hexadecimal color code as input and returns the corresponding RGB
    values as a tuple.

    Args:
      hex: The `hex` parameter is a string representing a hexadecimal color code.

    Returns:
      a tuple of three integers representing the RGB values of the given hexadecimal color code.
    """
    _hex = hex.lstrip("#")
    hlen = len(_hex)
    return tuple(int(_hex[i : i + hlen // 3], 16) for i in range(0, hlen, hlen // 3))


def adjust_color_lightness(r: float, g: float, b: float, factor: float) -> str:
    """
    The function adjusts the lightness of an RGB color by a given factor.

    Args:
      r: The parameter "r" represents the red component of the RGB color value. It should be an integer
    between 0 and 255.
      g: The parameter "g" represents the green component of the RGB color.
      b: The parameter "b" represents the blue component of the RGB color.
      factor: The factor parameter is a value between 0 and 1 that determines the amount by which the
    lightness of the color should be adjusted. A factor of 0 will result in a completely dark color,
    while a factor of 1 will keep the original color unchanged.

    Returns:
      a hexadecimal representation of the adjusted RGB color.
    """
    h, l, s = rgb2hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(min(l * factor, 1.0), 0.0)
    r, g, b = hls2rgb(h, l, s)
    return rgb2hex(int(r * 255), int(g * 255), int(b * 255))


def darken_color(hex_number: str, factor: float = 0.2) -> str:
    """
    The `darken_color` function takes a hexadecimal color code and a factor, and returns a darker
    version of the color by reducing its lightness.

    Args:
      hex_number (str): The hex_number parameter is a string representing a color in hexadecimal format.
    For example, "#FF0000" represents the color red.
      factor (float): The `factor` parameter is a float value that determines how much to darken the
    color. It is a value between 0 and 1, where 0 means no darkening and 1 means fully darkened. The
    default value is 0.2, which means the color will be dark

    Returns:
      a string representing a darkened color in hexadecimal format.
    """
    r, g, b = hex_to_rgb(hex_number)  # hex to rgb format
    return adjust_color_lightness(r, g, b, 1 - factor)


def lighten_color(hex_number: str, factor: float = 0.9) -> str:
    """
    The `lighten_color` function takes a hexadecimal color code and a factor, and returns a lighter
    version of the color by adjusting its lightness.

    Args:
      hex_number (str): A string representing a hexadecimal color code.
      factor (float): The factor parameter is a float value that determines how much to lighten the
    color. A factor of 1.0 will keep the color unchanged, a factor less than 1.0 will lighten the color,
    and a factor greater than 1.0 will darken the color. The default value for

    Returns:
      a string representing a hex color code.
    """
    r, g, b = hex_to_rgb(hex_number)  # hex to rgb format
    return adjust_color_lightness(r, g, b, factor)


def generate_random_color():
    """
    The function generates a random RGB color code that has distinct values for red, green, and blue
    components.

    Returns:
      The function `generate_random_color()` returns a randomly generated color in the form of a
    hexadecimal string.
    """
    while True:
        color = [random.randint(0, 255) for _ in range(3)]  # Generate random RGB values

        # Check if the color components are within the acceptable range
        if (
            abs(color[0] - color[1]) >= 10  # Red and green difference
            and abs(color[0] - color[2]) >= 10  # Red and blue difference
            and abs(color[1] - color[2]) >= 10  # Green and blue difference
        ):
            return "#{:02x}{:02x}{:02x}".format(*color)


def shift_color_towards_hue(color, target_hue):
    """
    The function `shift_color_towards_hue` takes a color in hexadecimal format and a target hue value,
    and returns a new color that is shifted towards the target hue.

    Args:
      color: The color parameter is a hexadecimal color code representing the original color.
      target_hue: The target_hue parameter is the desired hue value that you want to shift the color
    towards. Hue values range from 0 to 1, where 0 represents red, 0.33 represents green, and 0.67
    represents blue.

    Returns:
      the shifted color as a hexadecimal string.
    """

    def _hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))

    original_rgb = _hex_to_rgb(color)
    original_hsv = colorsys.rgb_to_hsv(*original_rgb)

    # Gray scale test
    r, g, b = original_rgb
    if abs(r - g) <= 10 and abs(r - b) <= 10 and abs(g - b) <= 10:
        # If the original color is a shade of gray, return the original color as it is
        return color

    target_rgb = colorsys.hsv_to_rgb(target_hue, original_hsv[1], original_hsv[2])

    interpolated_rgb = interpolate_color(original_rgb, target_rgb, 0.5)  # Adjust the interpolation factor as desired

    shifted_color = rgb_to_hex(*interpolated_rgb)
    return shifted_color


def rgb_to_hex(red, green, blue):
    """
    The function `rgb_to_hex` converts RGB values to a hexadecimal color code.

    Args:
      red: The red parameter represents the intensity of the red color component in the RGB color model.
    It is a decimal value between 0 and 1, where 0 represents no red and 1 represents maximum intensity
    of red.
      green: The "green" parameter represents the intensity of the green color in the RGB color model.
    It is a value between 0 and 1, where 0 represents no green and 1 represents full intensity green.
      blue: The blue parameter represents the intensity of the blue color in the RGB color model. It is
    a value between 0 and 1, where 0 represents no blue and 1 represents maximum intensity of blue.

    Returns:
      a hexadecimal representation of the RGB values provided.
    """
    return "#{:02x}{:02x}{:02x}".format(int(red * 255), int(green * 255), int(blue * 255))


def interpolate_color(color1, color2, factor):
    """
    The function `interpolate_color` takes two colors and a factor, and returns a new color that is a
    linear interpolation between the two input colors.

    Args:
      color1: The first color, represented as a tuple of RGB values.
      color2: The second color to interpolate towards.
      factor: The factor parameter determines the weight of each color in the interpolation. A factor of
    0 will result in color1, a factor of 1 will result in color2, and a factor between 0 and 1 will
    result in a blend of the two colors.

    Returns:
      a tuple that represents the interpolated color between color1 and color2.
    """
    return tuple(c1 * (1 - factor) + c2 * factor for c1, c2 in zip(color1, color2))


def get_random_color() -> str:
    """
    The function `get_random_color()` generates a random color and then shifts it towards the hue by
    5/3.

    Returns:
      a string, which represents a random color.
    """
    return shift_color_towards_hue(generate_random_color(), 5 / 3)
