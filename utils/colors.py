import math
import random

from colormap import hls2rgb, rgb2hex, rgb2hls

# pip install colormap
# pip install easydev
# https://gist.github.com/mathebox/e0805f72e7db3269ec22

colors_ral: dict[str, dict[str, str]] = {
    "RAL 1000": {"hex": "#CCC58F", "name": "Green beige"},
    "RAL 1001": {"hex": "#D1BC8A", "name": "Beige"},
    "RAL 1002": {"hex": "#D2B773", "name": "Sand yellow"},
    "RAL 1003": {"hex": "#F7BA0B", "name": "Signal yellow"},
    "RAL 1004": {"hex": "#E2B007", "name": "Golden yellow"},
    "RAL 1005": {"hex": "#C89F04", "name": "Honey yellow"},
    "RAL 1006": {"hex": "#E1A100", "name": "Maize yellow"},
    "RAL 1007": {"hex": "#E79C00", "name": "Daffodil yellow"},
    "RAL 1011": {"hex": "#AF8A54", "name": "Brown beige"},
    "RAL 1012": {"hex": "#D9C022", "name": "Lemon yellow"},
    "RAL 1013": {"hex": "#E9E5CE", "name": "Oyster white"},
    "RAL 1014": {"hex": "#DFCEA1", "name": "Ivory"},
    "RAL 1015": {"hex": "#EADEBD", "name": "Light ivory"},
    "RAL 1016": {"hex": "#EAF044", "name": "Sulfur yellow"},
    "RAL 1017": {"hex": "#F4B752", "name": "Saffron yellow"},
    "RAL 1018": {"hex": "#F3E03B", "name": "Zinc yellow"},
    "RAL 1019": {"hex": "#A4957D", "name": "Grey beige"},
    "RAL 1020": {"hex": "#9A9464", "name": "Olive yellow"},
    "RAL 1021": {"hex": "#EEC900", "name": "Rape yellow"},
    "RAL 1023": {"hex": "#F0CA00", "name": "traffic yellow"},
    "RAL 1024": {"hex": "#B89C50", "name": "Ochre yellow"},
    "RAL 1026": {"hex": "#F5FF00", "name": "Luminous yellow"},
    "RAL 1027": {"hex": "#A38C15", "name": "Curry"},
    "RAL 1028": {"hex": "#FFAB00", "name": "Melon yellow"},
    "RAL 1032": {"hex": "#DDB20F", "name": "Broom yellow"},
    "RAL 1033": {"hex": "#FAAB21", "name": "Dahlia yellow"},
    "RAL 1034": {"hex": "#EDAB56", "name": "Pastel yellow"},
    "RAL 1035": {"hex": "#A29985", "name": "Pearl beige"},
    "RAL 1036": {"hex": "#927549", "name": "Pearl gold"},
    "RAL 1037": {"hex": "#EEA205", "name": "Sun yellow"},
    "RAL 2000": {"hex": "#DD7907", "name": "Yellow orange"},
    "RAL 2001": {"hex": "#BE4E20", "name": "Red orange"},
    "RAL 2002": {"hex": "#C63927", "name": "Vermillion"},
    "RAL 2003": {"hex": "#FA842B", "name": "Pastel orange"},
    "RAL 2004": {"hex": "#E75B12", "name": "Pure orange"},
    "RAL 2005": {"hex": "#FF2300", "name": "Luminous orange"},
    "RAL 2007": {"hex": "#FFA421", "name": "Luminous bright orange"},
    "RAL 2008": {"hex": "#F3752C", "name": "Bright red orange"},
    "RAL 2009": {"hex": "#E15501", "name": "traffic orange"},
    "RAL 2010": {"hex": "#D4652F", "name": "Signal orange"},
    "RAL 2011": {"hex": "#EC7C25", "name": "Deep orange"},
    "RAL 2012": {"hex": "#DB6A50", "name": "Salmon orange"},
    "RAL 2013": {"hex": "#954527", "name": "Pearl orange"},
    "RAL 3000": {"hex": "#AB2524", "name": "Flame red"},
    "RAL 3001": {"hex": "#A02128", "name": "Signal red"},
    "RAL 3002": {"hex": "#A1232B", "name": "Carmine red"},
    "RAL 3003": {"hex": "#8D1D2C", "name": "Ruby red"},
    "RAL 3004": {"hex": "#701F29", "name": "Purple red"},
    "RAL 3005": {"hex": "#5E2028", "name": "Wine red"},
    "RAL 3007": {"hex": "#402225", "name": "Black red"},
    "RAL 3009": {"hex": "#703731", "name": "Oxide red"},
    "RAL 3011": {"hex": "#7E292C", "name": "Brown red"},
    "RAL 3012": {"hex": "#CB8D73", "name": "Beige red"},
    "RAL 3013": {"hex": "#9C322E", "name": "Tomato red"},
    "RAL 3014": {"hex": "#D47479", "name": "Antique pink"},
    "RAL 3015": {"hex": "#E1A6AD", "name": "Light pink"},
    "RAL 3016": {"hex": "#AC4034", "name": "Coral red"},
    "RAL 3017": {"hex": "#D3545F", "name": "Rose"},
    "RAL 3018": {"hex": "#D14152", "name": "Strawberry red"},
    "RAL 3020": {"hex": "#C1121C", "name": "traffic red"},
    "RAL 3022": {"hex": "#D56D56", "name": "Salmon pink"},
    "RAL 3024": {"hex": "#F70000", "name": "Luminous red"},
    "RAL 3026": {"hex": "#FF0000", "name": "Luminous bright red"},
    "RAL 3027": {"hex": "#B42041", "name": "Raspberry red"},
    "RAL 3028": {"hex": "#E72512", "name": "Pure red"},
    "RAL 3031": {"hex": "#AC323B", "name": "Orient red"},
    "RAL 3032": {"hex": "#711521", "name": "Pearl ruby red"},
    "RAL 3033": {"hex": "#B24C43", "name": "Pearl pink"},
    "RAL 4001": {"hex": "#8A5A83", "name": "Red lilac"},
    "RAL 4002": {"hex": "#933D50", "name": "Red violet"},
    "RAL 4003": {"hex": "#D15B8F", "name": "Heather violet"},
    "RAL 4004": {"hex": "#691639", "name": "Claret violet"},
    "RAL 4005": {"hex": "#83639D", "name": "Blue lilac"},
    "RAL 4006": {"hex": "#992572", "name": "Traffic purple"},
    "RAL 4007": {"hex": "#4A203B", "name": "Purple violet"},
    "RAL 4008": {"hex": "#904684", "name": "Signal violet"},
    "RAL 4009": {"hex": "#A38995", "name": "Pastel violet"},
    "RAL 4010": {"hex": "#C63678", "name": "Telemagenta"},
    "RAL 4011": {"hex": "#8773A1", "name": "Pearl violet"},
    "RAL 4012": {"hex": "#6B6880", "name": "Pearl blackberry"},
    "RAL 5000": {"hex": "#384C70", "name": "Violet blue"},
    "RAL 5001": {"hex": "#1F4764", "name": "Green blue"},
    "RAL 5002": {"hex": "#2B2C7C", "name": "Ultramarine blue"},
    "RAL 5003": {"hex": "#2A3756", "name": "Sapphire blue"},
    "RAL 5004": {"hex": "#1D1F2A", "name": "Black blue"},
    "RAL 5005": {"hex": "#154889", "name": "Signal blue"},
    "RAL 5007": {"hex": "#41678D", "name": "Brilliant blue"},
    "RAL 5008": {"hex": "#313C48", "name": "Grey blue"},
    "RAL 5009": {"hex": "#2E5978", "name": "Azure blue"},
    "RAL 5010": {"hex": "#13447C", "name": "Gentian blue"},
    "RAL 5011": {"hex": "#232C3F", "name": "Steel blue"},
    "RAL 5012": {"hex": "#3481B8", "name": "Light blue"},
    "RAL 5013": {"hex": "#232D53", "name": "Cobalt blue"},
    "RAL 5014": {"hex": "#6C7C98", "name": "Pigeon blue"},
    "RAL 5015": {"hex": "#2874B2", "name": "Sky blue"},
    "RAL 5017": {"hex": "#0E518D", "name": "Traffic blue"},
    "RAL 5018": {"hex": "#21888F", "name": "Turquoise blue"},
    "RAL 5019": {"hex": "#1A5784", "name": "Capri blue"},
    "RAL 5020": {"hex": "#0B4151", "name": "Ocean blue"},
    "RAL 5021": {"hex": "#07737A", "name": "Water blue"},
    "RAL 5022": {"hex": "#2F2A5A", "name": "Night blue"},
    "RAL 5023": {"hex": "#4D668E", "name": "Distant blue"},
    "RAL 5024": {"hex": "#6A93B0", "name": "Pastel blue"},
    "RAL 5025": {"hex": "#296478", "name": "Pearl Gentian blue"},
    "RAL 5026": {"hex": "#102C54", "name": "Pearl night blue"},
    "RAL 6000": {"hex": "#327662", "name": "Patina green"},
    "RAL 6001": {"hex": "#28713E", "name": "Emerald green"},
    "RAL 6002": {"hex": "#276235", "name": "Leaf green"},
    "RAL 6003": {"hex": "#4B573E", "name": "Olive Green"},
    "RAL 6004": {"hex": "#0E4243", "name": "Blue green"},
    "RAL 6005": {"hex": "#0F4336", "name": "Moss green"},
    "RAL 6006": {"hex": "#40433B", "name": "Grey olive"},
    "RAL 6007": {"hex": "#283424", "name": "Bottle green"},
    "RAL 6008": {"hex": "#35382E", "name": "Brown green"},
    "RAL 6009": {"hex": "#26392F", "name": "Fir green"},
    "RAL 6010": {"hex": "#3E753B", "name": "Grass green"},
    "RAL 6011": {"hex": "#68825B", "name": "Reseda green"},
    "RAL 6012": {"hex": "#31403D", "name": "Black green"},
    "RAL 6013": {"hex": "#797C5A", "name": "Reed green"},
    "RAL 6014": {"hex": "#444337", "name": "Yellow olive"},
    "RAL 6015": {"hex": "#3D403A", "name": "Black olive"},
    "RAL 6016": {"hex": "#026A52", "name": "Turquoise green"},
    "RAL 6017": {"hex": "#468641", "name": "May green"},
    "RAL 6018": {"hex": "#48A43F", "name": "Yellow green"},
    "RAL 6019": {"hex": "#B7D9B1", "name": "pastel green"},
    "RAL 6020": {"hex": "#354733", "name": "Chrome green"},
    "RAL 6021": {"hex": "#86A47C", "name": "Pale green"},
    "RAL 6022": {"hex": "#3E3C32", "name": "Brown olive"},
    "RAL 6024": {"hex": "#008754", "name": "Traffic green"},
    "RAL 6025": {"hex": "#53753C", "name": "Fern green"},
    "RAL 6026": {"hex": "#005D52", "name": "Opal green"},
    "RAL 6027": {"hex": "#81C0BB", "name": "Light green"},
    "RAL 6028": {"hex": "#2D5546", "name": "Pine green"},
    "RAL 6029": {"hex": "#007243", "name": "Mint green"},
    "RAL 6032": {"hex": "#0F8558", "name": "Signal green"},
    "RAL 6033": {"hex": "#478A84", "name": "Mint turquoise"},
    "RAL 6034": {"hex": "#7FB0B2", "name": "Pastel turquoise"},
    "RAL 6035": {"hex": "#1B542C", "name": "Pearl green"},
    "RAL 6036": {"hex": "#005D4C", "name": "Pearl opal green"},
    "RAL 6037": {"hex": "#25E712", "name": "Pure green"},
    "RAL 6038": {"hex": "#00F700", "name": "Luminous green"},
    "RAL 7000": {"hex": "#7E8B92", "name": "Squirrel grey"},
    "RAL 7001": {"hex": "#8F999F", "name": "Silver grey"},
    "RAL 7002": {"hex": "#817F68", "name": "Olive grey"},
    "RAL 7003": {"hex": "#7A7B6D", "name": "Moss grey"},
    "RAL 7004": {"hex": "#9EA0A1", "name": "Signal grey"},
    "RAL 7005": {"hex": "#6B716F", "name": "Mouse grey"},
    "RAL 7006": {"hex": "#756F61", "name": "Beige grey"},
    "RAL 7008": {"hex": "#746643", "name": "Khaki grey"},
    "RAL 7009": {"hex": "#5B6259", "name": "Green grey"},
    "RAL 7010": {"hex": "#575D57", "name": "Tarpaulin grey"},
    "RAL 7011": {"hex": "#555D61", "name": "Iron grey"},
    "RAL 7012": {"hex": "#596163", "name": "Basalt grey"},
    "RAL 7013": {"hex": "#555548", "name": "Brown-grey also"},
    "RAL 7015": {"hex": "#51565C", "name": "Slate grey"},
    "RAL 7016": {"hex": "#373F43", "name": "Anthracite grey"},
    "RAL 7021": {"hex": "#2E3234", "name": "Black grey"},
    "RAL 7022": {"hex": "#4B4D46", "name": "Umbra grey"},
    "RAL 7023": {"hex": "#818479", "name": "Concrete grey"},
    "RAL 7024": {"hex": "#474A50", "name": "Graphite grey"},
    "RAL 7026": {"hex": "#374447", "name": "Granite grey"},
    "RAL 7030": {"hex": "#939388", "name": "Stone grey"},
    "RAL 7031": {"hex": "#5D6970", "name": "Blue grey"},
    "RAL 7032": {"hex": "#B9B9A8", "name": "Pebble grey"},
    "RAL 7033": {"hex": "#818979", "name": "Cement grey"},
    "RAL 7034": {"hex": "#939176", "name": "Yellow grey"},
    "RAL 7035": {"hex": "#CBD0CC", "name": "Light grey"},
    "RAL 7036": {"hex": "#9A9697", "name": "Platinum grey"},
    "RAL 7037": {"hex": "#7C7F7E", "name": "Dusty grey"},
    "RAL 7038": {"hex": "#B4B8B0", "name": "Agate grey"},
    "RAL 7039": {"hex": "#6B695F", "name": "Quartz grey"},
    "RAL 7040": {"hex": "#9DA3A6", "name": "Window grey"},
    "RAL 7042": {"hex": "#8F9695", "name": "Traffic grey A"},
    "RAL 7043": {"hex": "#4E5451", "name": "Traffic grey B"},
    "RAL 7044": {"hex": "#BDBDB2", "name": "Silk grey"},
    "RAL 7045": {"hex": "#91969A", "name": "Telegrey 1"},
    "RAL 7046": {"hex": "#82898E", "name": "Telegrey 2"},
    "RAL 7047": {"hex": "#CFD0CF", "name": "Telegrey 4"},
    "RAL 7048": {"hex": "#888175", "name": "Pearl mouse grey"},
    "RAL 8000": {"hex": "#887142", "name": "Green brown"},
    "RAL 8001": {"hex": "#9C6B30", "name": "Ochre brown"},
    "RAL 8002": {"hex": "#7B5141", "name": "Signal brown"},
    "RAL 8003": {"hex": "#80542F", "name": "Clay brown"},
    "RAL 8004": {"hex": "#8F4E35", "name": "Copper brown"},
    "RAL 8007": {"hex": "#6F4A2F", "name": "Fawn brown"},
    "RAL 8008": {"hex": "#6F4F28", "name": "Olive brown"},
    "RAL 8011": {"hex": "#5A3A29", "name": "Nut brown"},
    "RAL 8012": {"hex": "#673831", "name": "Red brown"},
    "RAL 8014": {"hex": "#49392D", "name": "Sepia brown"},
    "RAL 8015": {"hex": "#633A34", "name": "Chestnut brown"},
    "RAL 8016": {"hex": "#4C2F26", "name": "Mahogany brown"},
    "RAL 8017": {"hex": "#44322D", "name": "Chocolate brown"},
    "RAL 8019": {"hex": "#3F3A3A", "name": "Grey brown"},
    "RAL 8022": {"hex": "#211F20", "name": "Black brown"},
    "RAL 8023": {"hex": "#A65E2F", "name": "Orange brown"},
    "RAL 8024": {"hex": "#79553C", "name": "Beige brown"},
    "RAL 8025": {"hex": "#755C49", "name": "Pale brown"},
    "RAL 8028": {"hex": "#4E3B31", "name": "Terra brown"},
    "RAL 8029": {"hex": "#763C28", "name": "Pearl copper"},
    "RAL 9001": {"hex": "#FDF4E3", "name": "Cream"},
    "RAL 9002": {"hex": "#E7EBDA", "name": "Grey white"},
    "RAL 9003": {"hex": "#F4F4F4", "name": "Signal white"},
    "RAL 9004": {"hex": "#282828", "name": "Signal black"},
    "RAL 9005": {"hex": "#0A0A0A", "name": "Jet black"},
    "RAL 9006": {"hex": "#A5A5A5", "name": "White aluminum"},
    "RAL 9007": {"hex": "#8F8F8F", "name": "Grey aluminum"},
    "RAL 9010": {"hex": "#FFFFFF", "name": "Pure white"},
    "RAL 9011": {"hex": "#1C1C1C", "name": "Graphite black"},
    "RAL 9016": {"hex": "#F6F6F6", "name": "Traffic white"},
    "RAL 9017": {"hex": "#1E1E1E", "name": "Traffic black"},
    "RAL 9018": {"hex": "#D7D7D7", "name": "Papyrus white"},
    "RAL 9022": {"hex": "#9C9C9C", "name": "Pearl light grey"},
    "RAL 9023": {"hex": "#828282", "name": "Pearl dark grey"},
}


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


def rgb_to_hex(red, green, blue):
    return "#{:02x}{:02x}{:02x}".format(int(red), int(green), int(blue))


def rgb_to_hsv(r, g, b):
    r = float(r)
    g = float(g)
    b = float(b)
    high = max(r, g, b)
    low = min(r, g, b)
    h, s, v = high, high, high

    d = high - low
    s = 0 if high == 0 else d / high

    if high == low:
        h = 0.0
    else:
        h = {
            r: (g - b) / d + (6 if g < b else 0),
            g: (b - r) / d + 2,
            b: (r - g) / d + 4,
        }[high]
        h /= 6

    return h, s, v


def hsv_to_rgb(h, s, v):
    i = math.floor(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    r, g, b = [
        (v, t, p),
        (q, v, p),
        (p, v, t),
        (p, q, v),
        (t, p, v),
        (v, p, q),
    ][int(i % 6)]

    return r, g, b


def rgb_to_hsl(r, g, b):
    r = float(r)
    g = float(g)
    b = float(b)
    high = max(r, g, b)
    low = min(r, g, b)
    h, s, v = ((high + low) / 2,) * 3

    if high == low:
        h = 0.0
        s = 0.0
    else:
        d = high - low
        s = d / (2 - high - low) if l > 0.5 else d / (high + low)
        h = {
            r: (g - b) / d + (6 if g < b else 0),
            g: (b - r) / d + 2,
            b: (r - g) / d + 4,
        }[high]
        h /= 6

    return h, s, v


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def saturate(value):
    return clamp(value, 0.0, 1.0)


def hue_to_rgb(h):
    r = abs(h * 6.0 - 3.0) - 1.0
    g = 2.0 - abs(h * 6.0 - 2.0)
    b = 2.0 - abs(h * 6.0 - 4.0)
    return saturate(r), saturate(g), saturate(b)


def hsl_to_rgb(h, s, l):
    r, g, b = hue_to_rgb(h)
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    r = (r - 0.5) * c + l
    g = (g - 0.5) * c + l
    b = (b - 0.5) * c + l
    return r, g, b


def hsv_to_hsl(h, s, v):
    l = 0.5 * v * (2 - s)
    s = v * s / (1 - math.fabs(2 * l - 1))
    return h, s, l


def hsl_to_hsv(h, s, l):
    v = (2 * l + s * (1 - math.fabs(2 * l - 1))) / 2
    s = 2 * (v - l) / v
    return h, s, v


def hsl_to_hex(h, s, l):
    r, g, b = hsl_to_rgb(h, s, l)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def interpolate_color(color1, color2, factor):
    return tuple(c1 * (1 - factor) + c2 * factor for c1, c2 in zip(color1, color2))


def get_random_color() -> str:
    return hsl_to_hex(
        random.randint(0, 360) / 360,
        random.randint(25, 75) / 100,
        random.randint(15, 50) / 100,
    )


def get_contrast_text_color(hex_color: str) -> str:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    return "black" if luminance > 0.5 else "white"
