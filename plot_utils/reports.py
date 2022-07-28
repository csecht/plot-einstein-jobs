import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from plot_utils import markers as mark

# Copyright (C) 2021 C. Echt under GNU General Public License'


def view_report(title: str, text: str, minsize: tuple, scroll=False) -> None:
    """
    Create a TopLevel window for reports from Button callbacks.

    :param title: The window title string.
    :param text: The report text string.
    :param minsize: An integer tuple for window minsize (width, height).
    :param scroll: True creates scrollable text (default: False)
    :return: None
    """

    max_line = len(max(text.splitlines(), key=len))
    num_lines = text.count('\n')
    _w, _h = minsize

    report_win = tk.Toplevel()
    report_win.title(title)
    report_win.minsize(_w, _h)
    report_win.attributes('-topmost', True)

    if scroll:
        report_txt = ScrolledText(report_win, height=num_lines // 3)
    else:
        report_txt = tk.Text(report_win, height=num_lines)

    report_txt.config(width=max_line,
                      font='TkFixedFont',
                      bg=mark.DARK_GRAY,
                      fg=mark.LIGHT_GRAY,
                      insertbackground=mark.LIGHT_GRAY,
                      relief='groove', bd=4,
                      padx=15, pady=10, )

    report_txt.insert(tk.INSERT, text)
    report_txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
