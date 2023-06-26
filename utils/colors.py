import random
import colorsys


def generate_random_color():
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
    original_rgb = hex_to_rgb(color)
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


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_to_hex(red, green, blue):
    return "#{:02x}{:02x}{:02x}".format(int(red * 255), int(green * 255), int(blue * 255))


def interpolate_color(color1, color2, factor):
    return tuple(c1 * (1 - factor) + c2 * factor for c1, c2 in zip(color1, color2))


def get_random_color() -> str:
    return shift_color_towards_hue(generate_random_color(), 5 / 3)


for i in range(10):
    random_color = generate_random_color()  # Randomly generated color
    shifted_color = shift_color_towards_hue(random_color, 5 / 3)
    print(shifted_color)
