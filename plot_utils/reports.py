"""
Summary reporting functions for job_log plot data.
Functions:
about_report - Display program and Project information.
joblog_report - Display and print statistical metrics job_log data.
number_since - Number of tasks for a Project since a given date.
on_pick_report -  Display task details for tasks near clicked coordinates.
view_report - Create the toplevel window to display report text.
"""
# Copyright (C) 2022 C.S. Echt under GNU General Public License'

# Standard library imports
import re
from pathlib import Path
from sys import exit

# Third party imports.
#   tkinter may not be installed in all Python distributions,
try:
    import pandas as pd
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText

except (ImportError, ModuleNotFoundError) as import_err:
    print('*** One or more required Python packages were not found'
          ' or need an update:\n'
          'Pandas, tkinter (tk/tcl).\n\n'
          'To install: from the current folder, run this command'
          ' for the Python package installer (PIP):\n'
          '   python3 -m pip install -r requirements.txt\n\n'
          'Alternative command formats (system dependent):\n'
          '   py -m pip install -r requirements.txt (Windows)\n'
          '   pip install -r requirements.txt\n\n'
          'A package may already be installed, but needs an update;\n'
          '   this may be the case when the error message (below) is a bit cryptic\n'
          '   Example update command:\n'
          '   python3 -m pip install -U pandas\n\n'
          'On Linux, if tkinter is the problem, then try:\n'
          '   sudo apt-get install python3-tk\n'
          '   See also: https://tkdocs.com/tutorial/install.html \n\n'
          f'Error message:\n{import_err}')
    exit(1)

# Local application imports
# __main__ and plot_utils are used with the --about option to access
#   __doc__ and __init__.py constants and custom dunders.
from __main__ import __doc__
import plot_utils
from plot_utils import (path_check,
                        utils,
                        markers as mark,
                        project_groups as grp)

# This exception handler is to avoid an AttributeError when reports.py
#   is, on an off-chance, run as "__main__", and ensures that Python
#   returns the usual, "Process finished with exit code 0".
# The timestamp column name strings here must match those set for
#   self.time_stamp in PlotTasks __init__.
# manage_args() returns a 2-tuple of booleans.
try:
    TIME_STAMP = 'utc_tstamp' if utils.manage_args()[1] else 'local_tstamp'
except AttributeError:
    pass


def about_text() -> str:
    """
    Informational text for --about execution argument and GUI About cmd.
    """

    return (f'{__doc__}\n'
            f'{"Author:".ljust(13)}{plot_utils.__author__}\n'
            f'{"Version:".ljust(13)}{plot_utils.__version__}\n'
            f'{"Status:".ljust(13)}{plot_utils.__status__}\n'
            f'{"URL:".ljust(13)}{plot_utils.URL}\n'
            f'{plot_utils.__copyright__}'
            f'{plot_utils.__license__}\n')


def about_report(event) -> None:
    """
    Display program and Project information.
    Called from "About" button in Figure.

    :param event: Implicit mouse click event.
    :return: None
    """

    view_report(title=f'About {Path(__file__).name}',
                text=about_text(),
                minsize=(400, 220),
                scroll=True)

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
    p_tally = []

    for _p in grp.PROJECTS:
        is_p = f'is_{_p}'
        proj_totals.append(dataframe[is_p].sum())

        p_dcnt = f'{_p}_Dcnt'

        proj_days.append(len((dataframe[p_dcnt]
                              .groupby(dataframe[TIME_STAMP]
                                       .dt.date
                                       .where(dataframe[p_dcnt].notnull()))
                              .unique())))

        if proj_totals[-1] != 0:
            proj_daily_means.append(
                round((proj_totals[-1] / proj_days[-1]), 1))
        else:  # There is no Project _p in the job log.
            proj_daily_means.append(0)

    # Note: utils.manage_args()[0] returns the --test command line option as boolean.
    data_file = path_check.set_datapath(use_test_file=utils.manage_args()[0])

    _results = tuple(zip(
        grp.PROJECTS, proj_totals, proj_daily_means, proj_days))

    num_days = (len(pd.to_datetime(dataframe[TIME_STAMP])
                    .dt.date
                    .unique()))

    # Example report layout: note that 'all' and Projects total may differ.
    # /var/lib/boinc/job_log_einstein.phys.uwm.edu.txt
    #
    # Counts for 1242 days:
    #
    # Project       Total    per Day      Days
    # all          382561      308.0      1242
    # fgrp5           131        7.7        17
    # fgrpBG1      166155      174.2       954
    # gw_O2MD       86173      221.0       390
    # gw_O3AS      126263      350.7       360
    # brp4              0          0         0
    # brp7           2022       77.8        26
    # Listed Projects total: 380744
    _report = (f'{data_file}\n\n'
               f'Counts for {num_days} days:\n\n'
               f'{"Project".ljust(7)} {"Total".rjust(11)}'
               f' {"per Day".rjust(10)} {"Days".rjust(9)}\n'
               )

    for proj_tup in _results:
        proj, p_total, p_dmean, p_days = proj_tup
        _report = _report + (f'{proj.ljust(7)} {str(p_total).rjust(11)}'
                             f' {str(p_dmean).rjust(10)} {str(p_days).rjust(9)}\n'
                             )
        p_tally.append(p_total)

    # Report sum of known Projects; comparison to 'all' total tasks will show
    #   whether any Projects are missing from grp.PROJ_TO_REPORT.
    _report = _report + f'Listed Projects total: {sum(p_tally) - p_tally[0]}\n'

    view_report(title='Summary of tasks counts in...',
                text=_report, minsize=(400, 260))


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

    use_utc = True if TIME_STAMP == 'utc_tstamp' else False

    if use_utc:
        _header = ('Tasks nearest the selected point\n'
                   'UTC date   time     | task name | completion time (μs)')
    else:
        _header = ('Tasks nearest the selected point\n'
                   'Local date time     | task name | completion time (μs)')

    task_info_list = [_header]

    # VertexSelector(line), in matplotlib.lines; list of df indices included in
    #   set_pickradius().
    _n = len(event.ind)
    if not _n:
        print('event.ind is undefined')
        return event

    # Need to limit tasks from total included in set_pickradius(mark.PICK_RADIUS)
    #   from PlotTasks.setup_count_axes().
    report_limit = 6
    for dataidx in event.ind:
        if report_limit > 0:
            task_info_list.append(
                f'{dataframe.loc[dataidx][TIME_STAMP]} | '
                f'{dataframe.loc[dataidx].task_name} | '
                f'{dataframe.loc[dataidx].elapsed_t.time()}')
        report_limit -= 1

    # Add something special; count the number of tasks reported for
    #   a Project since the datetime timestamp of the nearest task.
    dt_since = dataframe.loc[event.ind[0]][TIME_STAMP]
    _name = dataframe.loc[event.ind[0]].task_name
    project = ''
    for proj, regex in grp.PROJ_NAME_REGEX.items():
        if re.search(regex, _name):
            project = proj

    num_since = number_since(dataframe, project, dt_since)
    task_info_list.append(
        f"The first selected task's Project is {project.upper()}.\n"
        f'Since {dt_since}, {num_since} tasks have been reported for that Project.\n'
    )

    _report = '\n\n'.join(map(str, task_info_list))

    # Display task info in Terminal and pop-up window.
    #   (_report string uses two newlines, but Terminal string needs only one.)
    print('\n'.join(map(str, task_info_list)))

    view_report(title='Task details (6 tasks maximum)',
                text=_report, minsize=(600, 300))
    return event


def number_since(dataframe: pd, proj: str, since_date: str) -> int:
    """
    Count how many tasks for a Project were run since a given date.
    Example: n = reports.number_since(self.jobs_df, 'brp7', '8/25/2022')
    Called from on_pick(), which passes this datetime string format:
    '2022-08-25 17:30:45'.

    :param dataframe: The pandas main dataframe of all job log data.
    :param proj: One of the plotted Projects listed in the module
     project_groups.PROJECTS, e.g. 'all', 'fgrp5', 'fgrpG1', 'gw_O2',
      'gw_O3', 'brp4', 'brp7'.
    :param since_date: Any common date string, e.g. '25/8/2022',
     'August 25, 2022', '25th of August, 2022', '25-08-2022'.
      Does not recognize Epoch time (seconds).

    :return: The count of Project tasks reported after the beginning of
     *since_date*.
    """
    since_dt = pd.to_datetime(since_date, infer_datetime_format=True)
    count_since = (dataframe[f'is_{proj}']
                   .where(dataframe[TIME_STAMP] >= since_dt)
                   ).sum()
    return count_since


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
