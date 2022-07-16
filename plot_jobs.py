#!/usr/bin/env python3
"""
plot_jobs.py uses Matplotlib to draw plots from data in Einstein@Home
BOINC client job log files. Task times vs datetime, task counts/day vs.
datetime, and task frequency (Hz) vs. task time (sec) can be plotted for
various E@H Projects recorded in a job log. A job log file can store
records of reported tasks for up to about three years of full-time work.

USAGE: From within the program's folder, use one of these commands,
       depending on your system:
            python plot_jobs.py
            ./plot_jobs.py
            python3 plot_jobs.py
Basic help: python plot_jobs.py --help
Information: python plot_jobs.py --about
Plot sample data: python plot_jobs.py --test
NOTE: Depending on your system, there may be a slight lag when switching
      between plots. Be patient and avoid the urge to clicking on things
      to speed things up. For the typical job log, hundreds of
      thousands to millions of data points will be plotted.

Using the navigation bar, plots can be zoomed-in, panned, restored to
previous views, and copied to PNG files.
When no navigation bar buttons are active, clicking on a cluster or
single data point shows task grp near the click coordinates.
The "Job log counts" button shows summary counts of all tasks, by Project.

The default configuration reads the job_log_einstein.phys.uwm.edu.txt
file in its default BOINC location. If you have changed the default
location, or want to plot data from an archived job_logs, then
enter a custom full file path in the provided plot_cfg.txt file.

Requires tkinter (tk/tcl), Python3.7+, Matplotlib, Pandas, and Numpy.
Developed in Python 3.8-3.9.

URL: https://github.com/csecht/plot-einstein-jobs
Development Status :: 1 - Alpha
Version: 0.0.8

Copyright: (c) 2022 Craig S. Echt under GNU General Public License.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see https://www.gnu.org/licenses/.
"""

# Copyright (c) 2022 C.S. Echt, under GNU General Public License

import argparse
import sys

from plot_utils import (path_check, vcheck, platform_check,
                        markers as mark,
                        project_groups as grp)

try:
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import matplotlib.style as mplstyle
    import pandas as pd
    from matplotlib import ticker
    from matplotlib.font_manager import FontProperties
    from matplotlib.widgets import CheckButtons, Button, RangeSlider
    from numpy import where
except (ImportError, ModuleNotFoundError) as err:
    print('One or more of the required Python packages were not found:\n'
          'Matplotlib, Pandas, Numpy.\n'
          'To install: from the current folder, run this command\n'
          'pip install -r requirements.txt\n'
          'Alternative command formats (system dependent):\n'
          'python -m pip install -r requirements.txt\n'
          'python3 -m pip install -r requirements.txt\n'
          'py -m pip install -r requirements.txt\n'
          f'Error msg: {err}')
    sys.exit(1)


class TaskDataFrame:
    """
    Set up the DataFrame used for plotting.
    Is called only as an inherited Class from PlotTasks.
    Methods: setup_df, count_log_projects
    """

    def __init__(self):
        self.tasks_df = pd.DataFrame()

        # The do_test parameter is set as a cmd line argument.

        # Variables used for reporting in joblog_report() and
        #   count_log_projects().
        self.proj_totals = []
        self.proj_daily_means = []
        self.proj_days = []
        self.total_jobs = 0

        self.setup_df()
        self.count_log_projects()

    def setup_df(self):
        """
        Set up the Pandas DataFrame of task data read from an E@H job_log
        text file.

        job_log_einstein.phys.uwm.edu.txt, structure of records:
        1654865994 ue 916.720025 ct 340.770200 fe 144000000000000 nm h1_0681.20_O3aC01Cl1In0__O3AS1a_681.50Hz_19188_1 et 1283.553196 es 0

        :return: None
        """

        # Developer note: Can check for presence NaN values with:
        # print('Any null values?', self.tasks_df.isnull().values.any())  # -> True
        # print("Sum of null timestamps:", self.tasks_df['time_stamp'].isnull().sum())
        # print("Sum of ALL nulls:", self.tasks_df.isnull().sum()).sum())

        # To include all numerical data in job_log, use this:
        # joblog_col_idx = 0, 2, 4, 6, 8, 10  # All reported data
        # headers = ('time_stamp', 'est_sec', 'cpu_sec', 'est_flops', 'task_name', 'task_t')
        # time_col = ('time_stamp', 'est_sec', 'cpu_sec', 'task_t')
        # Only need job log data of interest to plot:
        joblog_col_idx = 0, 8, 10
        headers = ('time_stamp', 'task_name', 'task_t')

        # The datapath path is defined in if __name__ == "__main__".
        self.tasks_df = pd.read_table(datapath,
                                      sep=' ',
                                      header=None,
                                      usecols=joblog_col_idx,
                                      names=headers,
                                      )

        # Need to replace NaN values with usable data.
        #   Assumes read_table of job_log file will produce NaN ONLY for timestamp.
        self.tasks_df.time_stamp.interpolate(inplace=True)

        # Need to retain original elapsed time seconds values for correlations.
        #   Not sure whether floats as sec.ns or integers are better:
        self.tasks_df['task_sec'] = self.tasks_df.task_t.astype(int)

        #  Need to convert times to datetimes for efficient plotting.
        time_colmn = ('time_stamp', 'task_t')
        for col in time_colmn:
            self.tasks_df[col] = pd.to_datetime(self.tasks_df[col],
                                                unit='s',
                                                infer_datetime_format=True)

        # Null column data used to visually reset_plots().
        self.tasks_df['null_time'] = pd.to_datetime(0.0, unit='s')
        self.tasks_df['null_Dcnt'] = 0

        # Need columns that flag each task's Project and sub-Project.
        self.tasks_df['is_all'] = where(
            self.tasks_df.task_name, True, False)
        self.tasks_df['is_gw'] = where(
            self.tasks_df.task_name.str.startswith('h1_'), True, False)
        self.tasks_df['is_gw_O2'] = where(
            self.tasks_df.task_name.str.contains('_O2'), True, False)
        self.tasks_df['is_gw_O3'] = where(
            self.tasks_df.task_name.str.contains('_O3'), True, False)
        self.tasks_df['is_fgrp'] = where(
            self.tasks_df.task_name.str.startswith('LATeah'), True,  False)
        self.tasks_df['is_fgrp5'] = where(
            self.tasks_df.task_name.str.contains(r'LATeah\d{4}F'), True, False)
        self.tasks_df['is_fgrpG1'] = where(
            self.tasks_df.task_name.str.contains(r'LATeah\d{4}L|LATeah1049'), True, False)
        self.tasks_df['is_brp4'] = where(
            self.tasks_df.task_name.str.startswith('p'), True, False)

        for series in grp.GW_SERIES:
            is_ser = f'is_{series}'
            self.tasks_df[is_ser] = where(
                self.tasks_df.task_name.str.contains(series), True, False)

        # Add columns of search frequencies, parsed from the task name.
        """
        Regex for base frequency will match these task name structures:
        FGRP task: 'LATeah4013L03_988.0_0_0.0_9010205_1'
        GW task: 'h1_0681.20_O3aC01Cl1In0__O3AS1a_681.50Hz_19188_1'
        """
        # pattern_gw_freq = r'h1_[0]?(\d+\.\d+)_?'  # Ignore leading 0 in capture.
        # pattern_gw_freq = r'h1.*_(\d+\.\d{2})Hz_'  # Capture highest freq, not base freq.
        pattern_gw_freq = r'h1_(\d+\.\d+)_?'  # Capture the base/parent freq.
        pattern_fgrpg1_freq = r'LATeah.*?_(\d+)'
        self.tasks_df['gw_freq'] = (self.tasks_df.task_name
                                    .str.extract(pattern_gw_freq).astype(float))
        self.tasks_df['fgrpG1_freq'] = (self.tasks_df.task_name
                                        .str.extract(pattern_fgrpg1_freq).astype(float)
                                        .where(self.tasks_df.is_fgrpG1))

        """
        Idea to tally using groupby and transform, source:
        https://stackoverflow.com/questions/17709270/
        create-column-of-value-counts-in-pandas-dataframe
        """
        # Make dict of daily task counts (Dcnt) for each Project and sub-Project.
        # NOTE: gw times are not plotted (use O2 + O3), but gw_Dcnt is used in
        #   plot_gw_series().
        # For clarity, Project names here are those used in:
        #   PROJ_TO_REPORT (tuple), isplotted (dict), and chkbox_labels (tuple).
        daily_counts = {}
        for _proj in grp.PROJECTS:
            is_proj = f'is_{_proj}'
            daily_counts[f'{_proj}_Dcnt'] = (
                self.tasks_df.time_stamp
                    .groupby(self.tasks_df.time_stamp.dt.floor('D')
                             .where(self.tasks_df[is_proj]))
                    .transform('count')
            )

        # Add columns to tasks_df of daily counts for each Project and sub-Project.
        #  Note that _Dcnt column values are returned as floats (counts of Booleans), not integers.
        for _proj, _ in daily_counts.items():
            self.tasks_df[_proj] = daily_counts[_proj]

    # Need to work up metrics here so there is less delay when "Job log counts"
    #  button is used.
    def count_log_projects(self):
        """
        Tally task counts for individual Projects in job file.
        The appended lists are used for reporting in joblog_report().
        """

        for _p in grp.PROJ_TO_REPORT:
            is_p = f'is_{_p}'
            self.proj_totals.append(self.tasks_df[is_p].sum())

            p_dcnt = f'{_p}_Dcnt'

            self.proj_days.append(len((self.tasks_df[p_dcnt]
                                       .groupby(self.tasks_df.time_stamp.dt.date
                                                .where(self.tasks_df[p_dcnt].notnull()))
                                       .unique())))

            if self.proj_totals[-1] != 0:
                self.proj_daily_means.append(
                    round((self.proj_totals[-1] / self.proj_days[-1]), 1))
            else:  # There is no Project _p in the job log.
                self.proj_daily_means.append(0)

            # Need to count total tasks reported in case grp.PROJ_TO_REPORT
            #  misses any Projects. Any difference with self.proj_totals
            #  will be apparent in the job log count report (run from plot window).
            self.total_jobs = len(self.tasks_df.index)


class PlotTasks(TaskDataFrame):
    """
    Set up and display Matplotlib Figure and pyplot Plots of task (job)
    data from an E@H job log file.
    The plotted Pandas dataframe is inherited from TaskDataFrame.
    Methods: setup_title, setup_buttons, setup_plot_manager, on_pick,
       format_legends, toggle_legends, joblog_report, setup_count_axes,
       setup_freq_axes, reset_plots, plot_all, plot_gw_O2, plot_gw_O3,
       plot_fgrp5, plot_fgrpG1, plot_brp4, plot_gw_series,
       plot_fgrpG1_freq, plot_gw_O3_freq, manage_plots.
    """

    MARKER_SIZE = 4
    MARKER_SCALE = 1
    DCNT_SIZE = 2
    PICK_RADIUS = 6
    LIGHT_GRAY = '#cccccc'  # '#d9d9d9' X11 gray85; '#cccccc' X11 gray80
    DARK_GRAY = '#333333'  # X11 gray20

    def __init__(self, do_test):
        super().__init__()

        # The do_test parameter may be set as a cmd line argument.
        self.do_test = do_test

        self.checkbox = None
        self.do_replot = False
        self.legend_btn_on = True

        # These keys must match grp.CHKBOX_LABELS in project_groups.py.
        self.plot_proj = {
            'all': self.plot_all,
            'fgrpG1': self.plot_fgrpG1,
            'fgrp5': self.plot_fgrp5,
            'gw_O3': self.plot_gw_O3,
            'gw_O2': self.plot_gw_O2,
            'gw_series': self.plot_gw_series,
            'brp4': self.plot_brp4,
            'gw_O3_freq': self.plot_gw_O3_freq,
            'fgrpG1_freq': self.plot_fgrpG1_freq,
        }

        self.chkbox_labelid = {}
        self.isplotted = {}

        self.bbox_freq = dict(facecolor='white',
                              edgecolor='grey',
                              boxstyle='round',
                              )

        self.fig, (self.ax1, self.ax2) = plt.subplots(
            2,
            figsize=(9.5, 5),
            sharex='all',
            gridspec_kw={'height_ratios': [3, 1],
                         # 'left': 0.11,  # When use horiz Hz slider
                         'left': 0.15,  # When use vertical Hz slider
                         'right': 0.85,
                         'bottom': 0.16,
                         'top': 0.92,
                         'hspace': 0.15
                         },
        )

        mplstyle.use(('seaborn-colorblind', 'fast'))

        # Need to have mpl_connect statement before any autoscale statements AND
        #  need to have ax.autoscale() set for picker radius to work.
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)

        # Slider used in *_freq plots to set Hz ranges; initialize here
        #  so that it can be removed/redrawn with each *_freq plot call
        #  and hidden for all other plots.
        self.ax_slider = plt.axes()

        self.setup_title()
        self.setup_buttons()
        self.setup_count_axes()

    def setup_title(self):
        """
        Specify in the Figure title which data are plotted, those from the
        sample data file, plot_utils.testdata.txt, or the user's job log
        file. Called from if __name__ == "__main__".
        self.do_test is inherited from TaskDataFrame(args.test)
        via call in if __name__ == "__main__".

        :return: None
        """
        if self.do_test:
            title = 'Sample data'
        else:
            title = 'E@H job_log data'

        self.fig.suptitle(title,
                          fontsize=14,
                          fontweight='bold',
                          )

    def setup_buttons(self):
        """
        Setup buttons to toggle legends and to display log counts.
        Buttons are aligned with the plots' checkbox, ax_chkbox.
        """

        # Relative coordinates in Figure are (LEFT, BOTTOM, WIDTH, HEIGHT).
        # Position legend toggle button just below plot checkboxes.
        ax_legendbtn = plt.axes((0.885, 0.5, 0.09, 0.06))
        lbtn = Button(ax_legendbtn,
                      'Legends',
                      color=self.LIGHT_GRAY,
                      hovercolor='orange',
                      )
        lbtn.on_clicked(self.toggle_legends)

        # Dummy reference, per documentation: "For the buttons to remain
        #   responsive you must keep a reference to this object."
        ax_legendbtn._button = lbtn

        # Position log tally display button to bottom right corner of window.
        ax_statsbtn = plt.axes((0.885, 0.02, 0.09, 0.08))
        sbtn = Button(ax_statsbtn,
                      'Job log\ncounts',
                      color=self.LIGHT_GRAY,
                      hovercolor='orange',
                      )
        sbtn.on_clicked(self.joblog_report)
        ax_statsbtn._button = sbtn

    def setup_slider(self, max_f: float):
        """
        Create a RangeSlider for real-time y-axis Hz range adjustments
        of *_freq plots.

        :param max_f: The plotted Project's maximum frequency value.
        """

        # Need to replace any prior slider bar with a new one to prevent
        #   stacking of bars.
        self.ax_slider.remove()

        # Add a 2% margin to the slider upper limit.
        max_limit = max_f + max_f * 0.02

        # RangeSlider Coord: (LEFT, BOTTOM, WIDTH, HEIGHT).
        # self.ax_slider = plt.axes((0.11, 0.15, 0.60, 0.02)) # horiz
        self.ax_slider = plt.axes((0.05, 0.38, 0.01, 0.52)) # vert

        # Invert min/max values on vertical slider so max is on top.
        plt.gca().invert_yaxis()

        hz_slider = RangeSlider(self.ax_slider, "Hz range",
                                0, max_limit,
                                (0, max_limit),
                                valstep=2,
                                orientation='vertical',
                                color=mark.CBLIND_COLOR['yellow'],
                                handle_style={'size': 8,
                                              'facecolor': self.DARK_GRAY,
                                              }
                                )

        # Position text box above Navigation toolbar.
        self.ax1.text(-0.19, -0.6,
                      ("Range slider and Navigation bar tools may conflict.\n"
                       "If so, then toggle the plot's checkbox to reset."),
                      style='italic',
                      fontsize=8,
                      verticalalignment='top',
                      transform=self.ax1.transAxes,
                      bbox=self.bbox_freq,
                      )

        # Dummy reference, per documentation: "For the slider to remain
        #  responsive you must keep a reference to this object."
        self.ax_slider._slider = hz_slider

        def update(val):
            """
            Live update of the plot's y-axis frequency range.

            :param val: Value implicitly passed to a callback by the
             RangeSlider as a tuple, (min, max).
            """

            self.ax1.set_ylim(val)

            self.fig.canvas.draw_idle()

        hz_slider.on_changed(update)

    def setup_plot_manager(self):
        """
        Set up dictionaries to use as plotting conditional variables.
        Set up the plot selection checkbox.
        Plot 'all' as startup default.
        """
        for i, proj in enumerate(grp.CHKBOX_LABELS):
            self.chkbox_labelid[proj] = i

        for proj in grp.CHKBOX_LABELS:
            self.isplotted[proj] = False

        #  Relative coordinates in Figure, in 4-tuple: (LEFT, BOTTOM, WIDTH, HEIGHT)
        ax_chkbox = plt.axes((0.86, 0.6, 0.13, 0.3), facecolor=self.LIGHT_GRAY)

        # checkbox is used in manage_plots() and in if __name__ == "__main__".
        self.checkbox = CheckButtons(ax_chkbox, grp.CHKBOX_LABELS)

        self.checkbox.on_clicked(self.manage_plots)

        # At startup, activate checkbox label 'all' so that all tasks
        #  are plotted by default (via manage_plots() called from the
        #  on_clicked() statement).
        self.checkbox.set_active(self.chkbox_labelid['all'])

    def on_pick(self, event):
        """
        Click on plot area to show nearby task info in new figure and in
        Terminal or Command Line. Template source:
        https://matplotlib.org/stable/users/explain/event_handling.html
        Used in conjunction with mpl_connect().

        :param event: Implicit mouse event, left or right button click, on
        area of plotted markers. No event is triggered when a toolbar
        a navigation tool (pan or zoom) is active.
        :return: None
        """

        _n = len(event.ind)  # VertexSelector(line), in lines.py
        if not _n:
            print('event.ind is undefined')
            return event

        limit = 6  # Limit tasks from total in self.PICK_RADIUS.,
        task_info_list = ["Date | name | completion time"]
        for dataidx in event.ind:
            if limit > 0:
                task_info_list.append(
                    f'{self.tasks_df.loc[dataidx].time_stamp.date()} | '
                    f'{self.tasks_df.loc[dataidx].task_name} | '
                    f'{self.tasks_df.loc[dataidx].task_t.time()}')
            limit -= 1

        # Need to print results to Terminal to provide user with the
        #   option to cut-and-paste selected task info.
        print('\n'.join(map(str, task_info_list)))

        # Make new window with text box; one window made for each click.
        textfig = plt.figure(figsize=(6, 2))
        textax = textfig.add_subplot()

        textfig.suptitle('Tasks near clicked area, up to 6:')

        textax.axis('off')

        textax.text(-0.12, 0.0,
                    '\n\n'.join(map(str, task_info_list)),
                    fontsize=8,
                    bbox=dict(facecolor='orange',
                              alpha=0.4,
                              boxstyle='round',
                              ),
                    transform=textax.transAxes,
                    )

        plt.show()
        return event

    def format_legends(self):
        self.ax1.legend(fontsize='x-small', ncol=2,
                        loc='upper right',
                        markerscale=self.MARKER_SCALE,
                        edgecolor='black',
                        framealpha=0.5,
                        )
        self.ax2.legend(fontsize='x-small', ncol=2,
                        loc='upper right',
                        markerscale=self.MARKER_SCALE,
                        edgecolor='black',
                        framealpha=0.4,
                        )

    def toggle_legends(self, event):
        """
        Show/hide plot legends. If plot has no legend, do nothing.

        :param event: Implicit mouse click event.
        :return:  None
        """

        if self.ax1.get_legend():
            if self.legend_btn_on:
                self.ax1.get_legend().set_visible(False)
                # In case viewing frequency plots where self.ax2 is hidden:
                if self.ax2.get_legend():
                    self.ax2.get_legend().set_visible(False)
                self.legend_btn_on = False
            else:
                self.ax1.get_legend().set_visible(True)
                if self.ax2.get_legend():
                    self.ax2.get_legend().set_visible(True)
                self.legend_btn_on = True

            self.fig.canvas.draw_idle()  # Speeds up response.

        return event

    def joblog_report(self, event):
        """
        Display and print statistical metrics job_log data.
        Called from "Job log counts" button in Figure.

        :param event: Implicit mouse click event.
        :return:  None
        """

        stats_title = (f'Summary of all tasks in\n'
                       f'{path_check.set_datapath(args.test)}')

        _results = tuple(zip(
            grp.PROJ_TO_REPORT, self.proj_totals, self.proj_daily_means, self.proj_days))
        num_days = len(pd.to_datetime(self.tasks_df.time_stamp).dt.date.unique())

        _report = (f'Total tasks in file: {self.total_jobs}\n'
                   f'Task counts for the past {num_days} days:\n\n'
                   f'{"Project".ljust(6)} {"Total".rjust(10)}'
                   f' {"per Day".rjust(9)} {"Days".rjust(8)}\n'
                   )
        for proj_tup in _results:
            _proj, p_tot, p_dmean, p_days = proj_tup
            _report = _report + (f'{_proj.ljust(6)} {str(p_tot).rjust(10)}'
                                 f' {str(p_dmean).rjust(9)} {str(p_days).rjust(8)}\n'
                                 )

        # Print to terminal to give user the option to cut-and-paste.
        print(stats_title)
        print(_report)

        statfig = plt.figure(figsize=(5, 2.5),
                             facecolor=self.DARK_GRAY,
                             )
        statax = statfig.add_subplot()
        statfig.suptitle(stats_title, color=self.LIGHT_GRAY)
        statax.axis('off')

        statax.text(0.0, 0.0,
                    _report,
                    color=self.LIGHT_GRAY,
                    fontproperties=FontProperties(family='monospace'),
                    transform=statax.transAxes,
                    )

        plt.show()
        return event

    def setup_count_axes(self):
        """
        Used to rebuild axes components when plots and axes are cleared by
        reset_plots().
        """

        # Need to reset plot axes in case setup_freq_axes() was called.
        self.ax_slider.set_visible(False)
        self.ax2.set_visible(True)
        self.ax1.tick_params('x', labelbottom=False)

        # Default axis margins are 0.05 (5%) of data values.
        self.ax1.margins(0.02, 0.02)
        self.ax2.margins(0.02, 0.05)

        self.ax1.set_ylabel('Task completion time',
                            fontsize='medium', fontweight='bold')

        self.ax2.set_xlabel('Task reporting datetime',
                            # 'format: [y-m], [y-m-date], [m-date hr], [date h:sec]',
                            fontsize='medium', fontweight='bold')
        self.ax2.set_ylabel('Tasks/day',
                            fontsize='medium', fontweight='bold')

        # Need to set the Tasks/day axis label in a static position.
        self.ax2.yaxis.set_label_coords(-0.1, 0.55)

        # self.ax1.set(xticklabels=['']) # hides labels, but only with sharex=False

        # Need to rotate and right-align the date labels to avoid crowding.
        for label in self.ax1.get_yticklabels(which='major'):
            label.set(rotation=30, fontsize='x-small')

        for label in self.ax2.get_xticklabels(which='major'):
            label.set(rotation=15, fontsize='small', horizontalalignment='right')

        for label in self.ax2.get_yticklabels(which='major'):
            label.set(fontsize='small')

        self.ax1.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

        self.ax1.yaxis.set_major_locator(ticker.AutoLocator())
        self.ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())

        self.ax2.yaxis.set_major_locator(ticker.AutoLocator())
        self.ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator())

        self.ax1.grid(True)
        self.ax2.grid(True)

        # NOTE: autoscale methods have no visual effect when reset_plots() plots
        #  the full range datetimes from a job lob, BUT enabling autoscale
        #  allows the picker radius to work properly.
        self.ax1.autoscale()
        self.ax2.autoscale()

    def setup_freq_axes(self, t_limits: tuple):
        """
        Remove bottom axis and show tick labels (b/c when sharex=True,
        tick labels only show on bottom (self.ax2) plot).
        Called from plot_fgrpG1_freq() and plot_gw_O3_freq().

        :param t_limits: Constrain x-axis of task times to from
            zero to max value plus a small buffer.
        :return: None
        """
        #
        self.ax2.set_visible(False)
        self.ax1.tick_params('x', labelbottom=True)

        self.ax1.set_xlim(t_limits)

        self.ax1.set_xlabel('Task completion time, sec',
                            fontsize='medium', fontweight='bold')

        self.ax1.set_ylabel('Task base frequency, Hz',
                            fontsize='medium', fontweight='bold')

        self.ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))

        self.ax1.xaxis.set_major_locator(ticker.AutoLocator())
        self.ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator())

        self.ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))

        self.ax1.yaxis.set_major_locator(ticker.AutoLocator())
        self.ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    def reset_plots(self):
        """
        Clear plots. axis labels, ticks, formats, legends, etc.
        Clears plotted data by setting all data values to zero and removing marks.
        Use to avoid stacking of plots, which affects on_pick() display of
        nearby task info. Note that with this the full x-axis datetime range
        in job lob is always plotted; therefore, the methods ax.relim()
        ax.autoscale_view() and ax.autoscale() have no effect on individual
        data plots.
        Called from manage_plots().
        """
        self.ax1.clear()
        self.ax2.clear()

        self.setup_count_axes()

        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.null_time,
                      visible=False,
                      label='_leave blank',
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.null_Dcnt,
                      visible=False,
                      label='_leave blank',
                      )

        for plot, _ in self.isplotted.items():
            self.isplotted[plot] = False

    def plot_all(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.task_t,
                      mark.MARKER_STYLE['point'],
                      markersize=self.MARKER_SIZE,
                      label='all',
                      color=mark.CBLIND_COLOR['blue'],
                      alpha=0.3,
                      picker=self.PICK_RADIUS,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.all_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.DCNT_SIZE,
                      label='all',
                      color=mark.CBLIND_COLOR['blue'],
                      )
        self.format_legends()
        self.isplotted['all'] = True

    def plot_gw_O2(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.task_t.where(self.tasks_df.is_gw_O2),
                      mark.MARKER_STYLE['triangle_down'],
                      markersize=self.MARKER_SIZE,
                      label='gw_O2MD1',
                      color=mark.CBLIND_COLOR['orange'],
                      alpha=0.4,
                      picker=self.PICK_RADIUS,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.gw_O2_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.DCNT_SIZE,
                      label='gw_O2MD1',
                      color=mark.CBLIND_COLOR['orange'],
                      )
        self.format_legends()
        self.isplotted['gw_O2'] = True

    def plot_gw_O3(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.task_t.where(self.tasks_df.is_gw_O3),
                      mark.MARKER_STYLE['triangle_up'],
                      markersize=self.MARKER_SIZE,
                      label='gw_O3AS',
                      color=mark.CBLIND_COLOR['sky blue'],
                      alpha=0.3,
                      picker=self.PICK_RADIUS,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.gw_O3_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.DCNT_SIZE,
                      label='gw_O3AS',
                      color=mark.CBLIND_COLOR['sky blue'],
                      )
        self.format_legends()
        self.isplotted['gw_O3'] = True

    def plot_fgrp5(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.task_t.where(self.tasks_df.is_fgrp5),
                      mark.MARKER_STYLE['tri_left'],
                      markersize=self.MARKER_SIZE,
                      label='fgrp5',
                      color=mark.CBLIND_COLOR['bluish green'],
                      alpha=0.3,
                      picker=self.PICK_RADIUS,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.fgrp5_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.DCNT_SIZE,
                      label='fgrp5',
                      color=mark.CBLIND_COLOR['bluish green'],
                      alpha=0.4,
                      picker=self.PICK_RADIUS,
                      )
        self.format_legends()
        self.isplotted['fgrp5'] = True

    def plot_fgrpG1(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.task_t.where(self.tasks_df.is_fgrpG1),
                      mark.MARKER_STYLE['tri_right'],
                      markersize=self.MARKER_SIZE,
                      label='FGRBPG1',
                      color=mark.CBLIND_COLOR['vermilion'],
                      alpha=0.3,
                      picker=self.PICK_RADIUS,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.fgrpG1_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.DCNT_SIZE,
                      label='FGRBPG1',
                      color=mark.CBLIND_COLOR['vermilion'],
                      )
        self.format_legends()
        self.isplotted['fgrpG1'] = True

    def plot_brp4(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.task_t.where(self.tasks_df.is_brp4),
                      mark.MARKER_STYLE['pentagon'],
                      markersize=self.MARKER_SIZE,
                      label='BRP4 & BRP4G',
                      color=mark.CBLIND_COLOR['reddish purple'],
                      alpha=0.3,
                      picker=self.PICK_RADIUS,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.brp4_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.DCNT_SIZE,
                      label='BRP4 & BRP4G',
                      color=mark.CBLIND_COLOR['reddish purple'],
                      )
        self.format_legends()
        self.isplotted['brp4'] = True

    def plot_gw_series(self):
        for subproj in grp.GW_SERIES:
            is_subproj = f'is_{subproj}'

            self.ax1.plot(self.tasks_df.time_stamp,
                          self.tasks_df.task_t.where(self.tasks_df[is_subproj]),
                          mark.next_marker(),
                          label=subproj,
                          markersize=self.MARKER_SIZE,
                          alpha=0.3,
                          picker=True,
                          pickradius=self.PICK_RADIUS,
                          )

        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.gw_Dcnt,
                      mark.MARKER_STYLE['square'],
                      label='All GW',
                      markersize=self.DCNT_SIZE,
                      )
        self.format_legends()
        self.isplotted['gw_series'] = True

    def plot_fgrpG1_freq(self):
        num_freq = self.tasks_df.fgrpG1_freq.nunique()
        min_f = self.tasks_df.fgrpG1_freq.min()
        max_f = self.tasks_df.fgrpG1_freq.max()
        min_t = self.tasks_df.task_sec.where(self.tasks_df.is_fgrpG1).min()
        max_t = self.tasks_df.task_sec.where(self.tasks_df.is_fgrpG1).max()

        # Add a 2% margin to time axis upper limit.
        self.setup_freq_axes((0, max_t + (max_t * 0.02)))

        self.setup_slider(max_f)

        # Position text below lower left corner of axes.
        self.ax1.text(0.0, -0.15,
                      f'Frequencies, N: {num_freq}\n'
                      f'Hz, min--max: {min_f}--{max_f}\n'
                      f'Time, min--max: {min_t}--{max_t}',
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax1.transAxes,
                      bbox=self.bbox_freq,
                      )

        self.ax1.plot(self.tasks_df.task_sec.where(self.tasks_df.is_fgrpG1),
                      self.tasks_df.fgrpG1_freq,
                      mark.MARKER_STYLE['point'],
                      markersize=self.MARKER_SIZE,
                      color=mark.CBLIND_COLOR['blue'],
                      alpha=0.3,
                      picker=self.PICK_RADIUS,
                      )

        self.isplotted['fgrpG1_freq'] = True

    def plot_gw_O3_freq(self):
        num_freq = self.tasks_df.gw_freq.where(self.tasks_df.is_gw_O3).nunique()
        min_f = self.tasks_df.gw_freq.where(self.tasks_df.is_gw_O3).min()
        max_f = self.tasks_df.gw_freq.where(self.tasks_df.is_gw_O3).max()
        min_t = self.tasks_df.task_sec.where(self.tasks_df.is_gw_O3).min()
        max_t = self.tasks_df.task_sec.where(self.tasks_df.is_gw_O3).max()

        # Add a 2% margin to time axis upper limit.
        self.setup_freq_axes((0, max_t + (max_t * 0.02)))

        self.setup_slider(max_f)

        # Position text below lower left corner of axes.
        self.ax1.text(0.0, -0.15,
                      f'Frequencies, N: {num_freq}\n'
                      f'Hz, min--max: {min_f}--{max_f}\n'
                      f'Time, min--max: {min_t}--{max_t}',
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax1.transAxes,
                      bbox=self.bbox_freq,
                      )

        # NOTE that there is not a separate df column for O3 freq.
        self.ax1.plot(self.tasks_df.task_sec.where(self.tasks_df.is_gw_O3),
                      self.tasks_df.gw_freq.where(self.tasks_df.is_gw_O3),
                      mark.MARKER_STYLE['point'],
                      markersize=self.MARKER_SIZE,
                      color=mark.CBLIND_COLOR['blue'],
                      alpha=0.3,
                      picker=self.PICK_RADIUS,
                      )

        self.isplotted['gw_O3_freq'] = True

    def manage_plots(self, clicked_label):
        """
        Conditions determining which columns, defined by selected checkbox
        labels, to plot and which other columns are inclusive and exclusive
        for co-plotting. Called from the checkbox.on_clicked() method.

        :param clicked_label: Implicit event that returns the label name
          selected in the checkbox. Labels are defined in chkbox_labels.
        :return: None
        """

        #  NOTE: CANNOT have same plot points overlaid. That creates multiple
        #    on_pick() calls of windows for the same task info text.

        # NOTE: with checkbox.eventson = True (default),
        #   all proj button clicks trigger this manage_plots() callback
        #   (all conditions are evaluated with every click).

        # ischecked key is project label, value is True/False check status.
        ischecked = dict(zip(grp.CHKBOX_LABELS, self.checkbox.get_status()))

        # Note: ischecked and self.isplotted dictionary values are boolean.
        if clicked_label == 'all' and ischecked[clicked_label]:

            # Was toggled on...
            # Need to uncheck all others project labels.
            for _label in grp.CHKBOX_LABELS:
                if _label != clicked_label and (self.isplotted[_label] or ischecked[_label]):
                    ischecked[_label] = False
                    # Toggle off all excluded plots.
                    self.checkbox.set_active(self.chkbox_labelid[_label])
                    # Set a flag to avoid multiple resets.
                    self.do_replot = True

            if self.do_replot:
                self.reset_plots()
                self.do_replot = False

            self.plot_all()

        elif not ischecked[clicked_label]:
            self.reset_plots()

        if clicked_label in grp.ALL_INCLUSIVE and ischecked[clicked_label]:
            for _plot in grp.ALL_EXCLUDED:
                if self.isplotted[_plot] or ischecked[_plot]:
                    self.isplotted[_plot] = False
                    self.checkbox.set_active(self.chkbox_labelid[_plot])
                    self.do_replot = True

            if self.do_replot:
                self.reset_plots()
                self.do_replot = False

            for _proj, status in ischecked.items():
                if status and _proj in grp.ALL_INCLUSIVE and not self.isplotted[_proj]:
                    self.plot_proj[_proj]()

        elif clicked_label in grp.ALL_INCLUSIVE and not ischecked[clicked_label]:

            # Was toggled off, so remove all plots,
            #   then replot only inclusive checked ones.
            self.reset_plots()
            for _proj, status in ischecked.items():
                if _proj in grp.ALL_INCLUSIVE and status:
                    self.plot_proj[_proj]()
                if _proj == 'gw_series' and status:
                    self.plot_gw_series()

        if clicked_label == 'gw_series' and ischecked[clicked_label]:

            # Uncheck excluded checkbox labels if plotted.
            for excluded in grp.GW_SERIES_EXCLUDED:
                if self.isplotted[excluded] or ischecked[excluded]:
                    self.checkbox.set_active(self.chkbox_labelid[excluded])

            for _proj, status in ischecked.items():
                if status and _proj in grp.GW_SERIES_INCLUSIVE and not self.isplotted[_proj]:
                    self.plot_proj[_proj]()

        elif clicked_label == 'gw_series' and not ischecked[clicked_label]:

            # Was toggled off, so need to remove gw_series plot,
            # but not others. Reset all, then replot the others.
            self.reset_plots()
            for _proj, status in ischecked.items():
                if status and _proj in grp.GW_SERIES_INCLUSIVE:
                    self.plot_proj[_proj]()

        if clicked_label == 'fgrpG1_freq' and ischecked[clicked_label]:

            # Was toggled on...
            # Need to uncheck all other checked project labels.
            for _label in grp.CHKBOX_LABELS:
                if _label != clicked_label and (self.isplotted[_label] or ischecked[_label]):
                    self.checkbox.set_active(self.chkbox_labelid[_label])
                    self.do_replot = True

            if self.do_replot:
                self.reset_plots()
                self.do_replot = False

            self.plot_proj[clicked_label]()

        if clicked_label == 'gw_O3_freq' and ischecked[clicked_label]:
            for _label in grp.CHKBOX_LABELS:
                if _label != clicked_label and (self.isplotted[_label] or ischecked[_label]):
                    ischecked[_label] = False
                    self.checkbox.set_active(self.chkbox_labelid[_label])
                    self.do_replot = True

            if self.do_replot:
                self.reset_plots()
                self.do_replot = False

            self.plot_proj[clicked_label]()

        self.fig.canvas.draw_idle()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--about',
                        help='Provide description, version, GNU license',
                        action='store_true',
                        default=False)
    parser.add_argument('--test',
                        help='Plot test data instead of your job_log data.',
                        action='store_true',
                        default=False,
                        )
    # parser.add_argument('--logpath',
    #                     help='Enter path to alternate job_log file.',
    #                     )
    args = parser.parse_args()

    if args.about:
        print(__doc__)
        sys.exit(0)

    # Program will exit if any check fails.
    platform_check.check_platform()
    vcheck.minversion('3.7')

    if not args.test:
        datapath = path_check.set_datapath()
    else:
        datapath = path_check.set_datapath('do test')

    print(f'Data from {datapath} are loading. This may take a few seconds...')

    # This call will set up an inherited pd dataframe in TaskDataFrame,
    #  then plot 'all' tasks as specified in setup_plot_manager(). After that,
    #  plots are managed by checkbox label states via manage_plots().
    PlotTasks(args.test).setup_plot_manager()

    print('The plot window is ready.')

    try:
        plt.show()
    except KeyboardInterrupt:
        print('\n*** User quit the program ***\n')
        plt.close('all')
