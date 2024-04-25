import colorsys
import random

from colormap import hls2rgb, rgb2hex, rgb2hls

# pip install colormap
# pip install easydev


def hex_to_rgb(hex: str):
    _hex = hex.lstrip("#")
    hlen = len(_hex)
    return tuple(int(_hex[i : i + hlen // 3], 16) for i in range(0, hlen, hlen // 3))


def adjust_color_lightness(r: float, g: float, b: float, factor: float) -> str:
    h, l, s = rgb2hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(min(l * factor, 1.0), 0.0)
    r, g, b = hls2rgb(h, l, s)
    return rgb2hex(int(r * 255), int(g * 255), int(b * 255))


def darken_color(hex_number: str, factor: float = 0.2) -> str:
    r, g, b = hex_to_rgb(hex_number)  # hex to rgb format
    return adjust_color_lightness(r, g, b, 1 - factor)


def lighten_color(hex_number: str, factor: float = 0.9) -> str:
    r, g, b = hex_to_rgb(hex_number)  # hex to rgb format
    return adjust_color_lightness(r, g, b, factor)


def generate_random_color():
    while True:
        color = [random.randint(0, 255) for _ in range(3)]  # Generate random RGB values

        # Check if the color components are within the acceptable range
        if abs(color[0] - color[1]) >= 10 and abs(color[0] - color[2]) >= 10 and abs(color[1] - color[2]) >= 10:  # Red and green difference  # Red and blue difference  # Green and blue difference
            return "#{:02x}{:02x}{:02x}".format(*color)


def shift_color_towards_hue(color, target_hue):
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
    return "#{:02x}{:02x}{:02x}".format(int(red * 255), int(green * 255), int(blue * 255))


def interpolate_color(color1, color2, factor):
    return tuple(c1 * (1 - factor) + c2 * factor for c1, c2 in zip(color1, color2))


def darken_color(hex_color: str) -> str:
    # Remove the '#' character and convert to RGB values
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))

    # Generate a random darkness value between -65 and -45
    darkness = random.randint(-65, -50)

    # Adjust the RGB values to make the color darker
    r = max(r + darkness, 0)
    g = max(g + darkness, 0)
    b = max(b + darkness, 0)

    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def get_random_color() -> str:
    return darken_color(shift_color_towards_hue(generate_random_color(), 5 / 3))
