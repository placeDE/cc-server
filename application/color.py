from enum import Enum
from typing import Optional

from PIL import ImageColor


class Color(Enum):
    BURGUNDY = {"id": 0, "hex": "#6d001a"}
    DARK_RED = {"id": 1, "hex": "#be0039"}
    RED = {"id": 2, "hex": "#ff4500"}
    ORANGE = {"id": 3, "hex": "#ffa800"}
    YELLOW = {"id": 4, "hex": "#ffd635"}
    PALE_YELLOW = {"id": 5, "hex": "#fff8b8"}
    DARK_GREEN = {"id": 6, "hex": "#00a368"}
    GREEN = {"id": 7, "hex": "#00cc78"}
    LIGHT_GREEN = {"id": 8, "hex": "#7eed56"}
    DARK_TEAL = {"id": 9, "hex": "#00756f"}
    TEAL = {"id": 10, "hex": "#009eaa"}
    LIGHT_TEAL = {"id": 11, "hex": "#00ccc0"}
    DARK_BLUE = {"id": 12, "hex": "#2450a4"}
    BLUE = {"id": 13, "hex": "#3690ea"}
    LIGHT_BLUE = {"id": 14, "hex": "#51e9f4"}
    INDIGO = {"id": 15, "hex": "#493ac1"}
    PERIWINKLE = {"id": 16, "hex": "#6a5cff"}
    LAVENDER = {"id": 17, "hex": "#94b3ff"}
    DARK_PURPLE = {"id": 18, "hex": "#811e9f"}
    PURPLE = {"id": 19, "hex": "#b44ac0"}
    PALE_PURPLE = {"id": 20, "hex": "#e4abff"}
    MAGENTA = {"id": 21, "hex": "#de107f"}
    PINK = {"id": 22, "hex": "#ff3881"}
    LIGHT_PINK = {"id": 23, "hex": "#ff99aa"}
    DARK_BROWN = {"id": 24, "hex": "#6D482F"}
    BROWN = {"id": 25, "hex": "#9C6926"}
    BEIGE = {"id": 26, "hex": "#FFB470"}
    BLACK = {"id": 27, "hex": "#000000"}
    DARK_GRAY = {"id": 28, "hex": "#515252"}
    GRAY = {"id": 29, "hex": "#898D90"}
    LIGHT_GRAY = {"id": 30, "hex": "#D4D7D9"}
    WHITE = {"id": 31, "hex": "#ffffff"}


rgb_to_color = {}
conv_dict = {}

# generate rgb values for all colors
for color in Color:
    color.value["rgb"] = ImageColor.getcolor(color.value["hex"], "RGB")
    rgb_to_color.update({color.value["rgb"]: color})

"""
Returns the color object based on the given rgb tuple
"""


def get_matching_color(rgb) -> Optional[Color]:
    if (color := rgb_to_color.get(rgb)) is None:
        print("Color not found:", rgb)
        return None
    return color
    """for color in Color:
        if color.value["rgb"] == rgb:
            return color"""


"""
Returns the color object based on a given place color index
"""
"""
Returns the color object based on a given place color index
"""

"""
Returns the color object based on a given place color index
"""


def get_color_from_index(index) -> Optional[Color]:
    for color in Color:
        if color.value["id"] == index:
            return color
    return None


# Where has AI gotten us?
# This function was written in its entirety by GPT3, WTF
# def get_closest_color(r, g, b) -> Color:
#     min_distance = None
#     closest_color = None
#     for color in Color:
#         distance = (r - color.value["rgb"][0]) ** 2 + (g - color.value["rgb"][1]) ** 2 + (b - color.value["rgb"][2]) ** 2
#         if min_distance is None or distance < min_distance:
#             min_distance = distance
#             closest_color = color
#     return closest_color

"""
Get the closest color available on place to any color for converting any image to a template
"""


def get_closest_color(r, g, b) -> Color:
    return min(list(Color), key=lambda color: (r - color.value["rgb"][0]) ** 2 + (g - color.value["rgb"][1]) ** 2 + (
            b - color.value["rgb"][2]) ** 2)


def hex_to_rgb(h: str):
    if len(h) == 7:
        h = h[1:]
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    else:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hex_to_rgba(h: str, translucent: bool):
    if (h, int(translucent)) in conv_dict:
        return conv_dict.get((h, int(translucent)))
    if translucent:
        v = *hex_to_rgb(h), 80
    else:
        v = *hex_to_rgb(h), 255
    conv_dict.update({(h, int(translucent)): v})
    return v
