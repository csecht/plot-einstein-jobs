import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from plot_utils import markers as mark


def view_report(_title: str, _text: str, _minsize: tuple, scroll=False) -> None:
    """
    Create a TopLevel window for reports from Button callbacks.

    :param _title: The window title string.
    :param _text: The report text string.
    :param _minsize: An integer tuple for window minsize (width, height).
    :param scroll: True creates scrollable text (default: False)
    :return: None
    """

    max_line = len(max(_text.splitlines(), key=len))
    num_lines = _text.count('\n')
    _w, _h = _minsize

    report_win = tk.Toplevel()
    report_win.title(_title)
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

    report_txt.insert(tk.INSERT, _text)
    report_txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
