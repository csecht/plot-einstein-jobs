"""Constants and functions for marker styles and colors."""

from itertools import cycle

SIZE = 4  # Plotted Line2D vertex marker size.
SCALE = 1  # Adjust legend marker icon as factor of marker_size.
DCNT_SIZE = 2  # Task daily count marker size.
PICK_RADIUS = 6  # Radius used by set_pickradius for reports.on_pick_report().

"""
Line and marker styles:
================    ===============================
character           description
================    ===============================
   -                solid line style
   --               dashed line style
   -.               dash-dot line style
   :                dotted line style
   .                point marker
   ,                pixel marker
   o                circle marker
   v                triangle_down marker
   ^                triangle_up marker
   <                triangle_left marker
   >                triangle_right marker
   1                tri_down marker
   2                tri_up marker
   3                tri_left marker
   4                tri_right marker
   s                square marker
   p                pentagon marker
   *                star marker
   h                hexagon1 marker
   H                hexagon2 marker
   +                plus marker
   x                x marker
   D                diamond marker
   d                thin_diamond marker
   |                vline marker
   _                hline marker
================    ===============================

filled_markers = ('o', 'v', '^', '<', '>', '8', 's', 'p', '*', 'h', 'H',
                  'D', 'd', 'P', 'X')
"""

STYLE = {
    'solid line': '-',
    'dashed line': '--',
    'dash-dot line': '-.',
    'dotted line': ':',
    'point': '.',
    'pixel': ':',
    'circle': 'o',
    'triangle_down': 'v',
    'triangle_up': '^',
    'triangle_left': '<',
    'triangle_right': '>',
    'tri_down': '1',
    'tri_up': '2',
    'tri_left': '3',
    'tri_right': '4',
    'square': 's',
    'pentagon': 'p',
    'star': '*',
    'hexagon1': 'h',
    'hexagon2': 'H',
    'plus': '+',
    'x': 'x',
    'diamond': 'D',
    'thin_diamond': 'd',
    'vline': '|',
    'hline': '_',
}

"""
Colorblind color pallet source:
  Wong, B. Points of view: Color blindness. Nat Methods 8, 441 (2011).
  https://doi.org/10.1038/nmeth.1618
Hex values source: https://www.rgbtohex.net/
See also: https://matplotlib.org/stable/tutorials/colors/colormaps.html
"""
CBLIND_COLOR = {
    'blue': '#0072B2',
    'orange': '#E69F00',
    'sky blue': '#56B4E9',
    'bluish green': '#009E73',
    'vermilion': '#D55E00',
    'reddish purple': '#CC79A7',
    'yellow': '#F0E442',
    'black': 'black',
    'white': 'white',
}

# Need hexcodes b/c Matplotlib does not recognize tkinter X11 grayscale color names.
LIGHT_GRAY = '#d9d9d9'  # '#d9d9d9' X11 gray85 (close to 'lightgray'); '#cccccc' X11 gray80
DARK_GRAY = '#404040'  # '#404040' X11 gray25, '#333333' X11 gray20, '#4d4d4d' X11 gray30

# Source: https://medium.com/@masnun/infinitely-cycling-through-a-list-in-python-ef37e9df100
markers = ['.', 'o', '*', '+', 'x', 'v', '^', '<', '>', '1', '2',
           '3', '4', '8', 's', 'p', 'P', 'h', 'H', 'X', 'D', 'd']
markers_cycle = cycle(markers)


def next_marker() -> iter:

    return next(markers_cycle)
