from itertools import cycle


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

MARKER_STYLE = {
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
# Source: https://medium.com/@masnun/infinitely-cycling-through-a-list-in-python-ef37e9df100
markers = ['.', 'o', '*', '+', 'x', 'v', '^', '<', '>', '1', '2',
           '3', '4', '8', 's', 'p', 'P', 'h', 'H', 'X', 'D', 'd']
markers_cycle = cycle(markers)


def next_marker():

    return next(markers_cycle)