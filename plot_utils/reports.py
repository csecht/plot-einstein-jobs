"""
Summary reporting functions for job_log plot data.
Functions:
about_report - Display program and Project information.
joblog_report - Display and print statistical metrics job_log data.
on_pick_report -  Display task details for tasks near clicked coordinates.
view_report - Create the toplevel window to display report text.
"""
# Copyright (C) 2022 C.S. Echt under GNU General Public License'

import __main__

# Standard library imports
import tkinter as tk
from pathlib import Path
from tkinter.scrolledtext import ScrolledText

# Third party imports.
import pandas as pd

# Local application imports
import plot_utils
from plot_utils import (markers as mark,
                        path_check,
                        project_groups as grp)


def about_report(event) -> None:
    """
    Display program and Project information.
    Called from "About" button in Figure.

    :param event: Implicit mouse click event.
    :return: None
    """

    _report = (f'{__main__.__doc__}\n'
               f'{"Version:".ljust(9)} {plot_utils.__version__}\n'
               f'{"Author:".ljust(9)} {plot_utils.__author__}\n'
               f'{"URL:".ljust(9)} {plot_utils.URL}\n'
               f'{plot_utils.__copyright__}\n'
               f'{plot_utils.LICENSE}\n'
               )

    view_report(title=f'About {Path(__file__).name}',
                text=_report, minsize=(400, 220), scroll=True)
    return event


def joblog_report(dataframe: pd) -> None:
    """
    Display and print statistical metrics job_log data.
    Called from "Job log counts" button in Figure.

    :param dataframe: The pandas main dataframe of all job log data.
    :return:  None
    """

    proj_totals = []
    proj_daily_means = []
    proj_days = []
    total_jobs = 0

    for _p in grp.PROJ_TO_REPORT:
        is_p = f'is_{_p}'
        proj_totals.append(dataframe[is_p].sum())

        p_dcnt = f'{_p}_Dcnt'

        proj_days.append(len((dataframe[p_dcnt]
                              .groupby(dataframe.time_stamp.dt.date
                                       .where(dataframe[p_dcnt].notnull()))
                              .unique())))

        if proj_totals[-1] != 0:
            proj_daily_means.append(
                round((proj_totals[-1] / proj_days[-1]), 1))
        else:  # There is no Project _p in the job log.
            proj_daily_means.append(0)

        # Need to count total tasks reported in case grp.PROJ_TO_REPORT
        #  misses any Projects. Any difference with proj_totals
        #  will be apparent in the job log count report (run from plot window).
        total_jobs = len(dataframe.index)

    data_file = path_check.set_datapath(use_test_file=__main__.test_arg)

    _results = tuple(zip(
        grp.PROJ_TO_REPORT, proj_totals, proj_daily_means, proj_days))
    num_days = len(pd.to_datetime(dataframe.time_stamp).dt.date.unique())

    _report = (f'{data_file}\n\n'
               f'Total tasks in file: {total_jobs}\n'
               f'Counts for the past {num_days} days:\n\n'
               f'{"Project".ljust(6)} {"Total".rjust(10)}'
               f' {"per Day".rjust(9)} {"Days".rjust(8)}\n'
               )
    for proj_tup in _results:
        _proj, p_tot, p_dmean, p_days = proj_tup
        _report = _report + (f'{_proj.ljust(6)} {str(p_tot).rjust(10)}'
                             f' {str(p_dmean).rjust(9)} {str(p_days).rjust(8)}\n'
                             )

    view_report(title='Summary of tasks counts in...',
                text=_report, minsize=(400, 260))
    # return event


def on_pick_report(event, dataframe: pd) -> None:
    """
    Click on plot area to show nearby task info in new figure and in
    Terminal or Command Line. Template source:
    https://matplotlib.org/stable/users/explain/event_handling.html
    Used in conjunction with mpl_connect().

    :param event: Implicit mouse event, left or right button click, on
    area of plotted markers. No event is triggered when a toolbar
    a navigation tool (pan or zoom) is active.
    :param dataframe: The pandas main dataframe of all job log data.
    :return: None
    """

    _header = ('Tasks nearest the selected point\n'
               '      Date | name | completion time')

    _n = len(event.ind)  # VertexSelector(line), in lines.py
    if not _n:
        print('event.ind is undefined')
        return event

    _limit = 6  # Limit tasks, from total in self.pick_radius

    task_info_list = [_header]
    for dataidx in event.ind:
        if _limit > 0:
            task_info_list.append(
                f'{dataframe.loc[dataidx].time_stamp.date()} | '
                f'{dataframe.loc[dataidx].task_name} | '
                f'{dataframe.loc[dataidx].task_t.time()}')
        _limit -= 1

    _report = '\n\n'.join(map(str, task_info_list))

    # Display task info in Terminal and pop-up window.
    print('\n'.join(map(str, task_info_list)))

    view_report(title='Task details (max 6)',
                text=_report, minsize=(600, 300))
    # return event


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
