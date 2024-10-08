#!/usr/bin/env python3
"""
plot_jobs.py uses Matplotlib to draw plots from data in Einstein@Home
BOINC client job log files.

USAGE: python3 -m plot_jobs
For execution options, see the README file or use the --help command
line option: python3 -m plot_jobs --help

Plot types are:
    Task elapsed times vs reported datetime
    Task counts/day vs. reported datetime
    Task frequency (Hz) vs. reported datetime
    Task Hz vs. task time (sec)
Plots can be specified for various E@H Projects.
A job log file can store records of reported tasks for up to about three
years of full-time work. This can include hundreds of thousands to
millions of tasks.

NOTE: Depending on your system, there may be a slight lag when switching
      between plots. Be patient and avoid the urge to click on things
      to speed it up.

Using the navigation bar at the bottom of the plot window, plots can be
zoomed-in, panned, restored to previous views, and copied to PNG files.

When no navigation bar buttons are selected, clicking on a cluster or
single data point shows details of tasks nearest the click coordinates.

The "Job log counts" button tallies counts of all tasks, by Project.
The "About" button shows this plus version, author, Project URL,
copyright, and license.

The job_log_einstein.phys.uwm.edu.txt file is normally read from its
default BOINC location. If you have changed the default location, or
want to plot data from an archived job_log file, then enter a custom
full file path in the provided plot_cfg.txt file.

Requires Python3.7 or later (incl. tkinter (tk/tcl)) and the packages
Matplotlib, Pandas, and Numpy.
Developed in Python 3.8-3.9.
"""
# Copyright (C) 2022 C.S. Echt, under GNU General Public License

# Standard library imports
import sys
import numpy as np

# Local application imports
from plot_utils import (path_check, vcheck,
                        reports, utils,
                        markers as mark,
                        project_groups as grp)

# Third party imports (tk may not be included with some Python installations).
try:
    import matplotlib.backends.backend_tkagg as backend
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import pandas as pd
    import tkinter as tk

    from matplotlib import ticker
    from matplotlib.widgets import CheckButtons, Button, RangeSlider
    from numpy import where

except (ImportError, ModuleNotFoundError) as import_err:
    print('*** One or more required Python packages were not found'
          ' or need an update:\n'
          'Matplotlib, Numpy, Pandas, Pillow, tkinter (tk/tcl).\n\n'
          'To install: from the current folder, run this command'
          ' for the Python package installer (PIP):\n'
          '   python3 -m pip install -r requirements.txt\n\n'
          'Alternative command formats (system dependent):\n'
          '   py -m pip install -r requirements.txt (Windows)\n'
          '   pip install -r requirements.txt\n\n'
          'A package may already be installed, but needs an update;\n'
          '   this may be the case when the error message (below) is a bit cryptic\n'
          '   Example update command:\n'
          '   python3 -m pip install -U matplotlib\n\n'
          'On Linux, if tkinter is the problem, then you may need:\n'
          '   sudo apt-get install python3-tk\n'
          '   See also: https://tkdocs.com/tutorial/install.html \n\n'
          f'Error message:\n{import_err}')
    sys.exit(1)

# manage_args() returns a 3-tuple (bool, bool, path), as set on command line.
TEST_ARG, UTC_ARG, DATA_PATH = utils.manage_args()

# Suppress pylint warning where df columns are referenced by dot notation.
# pylint: disable=no-member

class TaskDataFrame:
    """
    Set up the DataFrame used for plotting.
    Is called only as an inherited Class from PlotTasks.
    Methods:
         setup_df - Set up main dataframe from an E@H job_log text file.
         manage_bad_times - Interpolate missing time data.
         add_proj_tags - Add columns of boolean flags for Project ID.
         add_hz_values - Add task base (parent) search frequencies.
         add_daily_counts - Add daily counts for each Project.
    """

    def __init__(self):
        self.jobs_df = pd.DataFrame()

        self.setup_df()
        self.add_proj_tags()
        self.add_hz_values()
        self.add_daily_counts()

    def setup_df(self):
        """
        Set up the Pandas DataFrame of task data read from an E@H job_log
        text file.

        :return: None
        """

        # The record structure in job_log_einstein.phys.uwm.edu.txt:
        # 1654865994 ue 916.720025 ct 340.770200 fe 144000000000000 nm h1_0681.20_O3aC01Cl1In0__O3AS1a_681.50Hz_19188_1 et 1283.553196 es 0

        # To include all numerical data in job_log, use this:
        # joblog_col_index = 0, 2, 4, 6, 8, 10  # All reported data
        # names = ('utc_tstamp', 'est_sec', 'cpu_sec', 'est_flops', 'task_name', 'elapsed_t')
        # Note that utc_tstamp is UTC Epoch time in seconds.

        # Job log data of current interest:
        job_col_index = [0, 8, 10]
        names = ('utc_tstamp', 'task_name', 'elapsed_t')

        # The DATA_PATH text file path is from if __name__ == "__main__".
        self.jobs_df = pd.read_table(filepath_or_buffer=DATA_PATH,
                                     engine='c',
                                     delim_whitespace=True,
                                     header=None,
                                     usecols=job_col_index,
                                     names=names,
                                     )

        # Need to replace any NaN times from file with interpolated time values.
        self.manage_bad_times()

        # Need to retain original elapsed time as seconds to plot Hz x task time.
        self.jobs_df['elapsed_sec'] = self.jobs_df.elapsed_t

        # Need to create local timestamp from UTC timestamp (float, int, or NaN).
        self.jobs_df['local_tstamp'] = self.jobs_df.utc_tstamp + utils.utc_offset_sec()

        # For plot axis tick readability, convert Epoch timestamps and
        #   task times (int, float, NaN) to np.datetime64 dtype.
        # Doing this dtype conversion AFTER the UTC-to-local adjustment
        #   results in a much faster launch of the plot window.
        for col in ('utc_tstamp', 'local_tstamp', 'elapsed_t'):
            try:
                self.jobs_df[col] = pd.to_datetime(self.jobs_df[col], unit='s')
            except ValueError:
                print(f'Warning: A {col} value could not be converted'
                      ' to a pd datetime object by setup_df().\n')

        # Use zero-value data columns to visually clear plots in
        #   reset_plots(). Needed when use mpl_connect event picker.
        self.jobs_df['null_time'] = np.zeros(self.jobs_df.shape[0])
        self.jobs_df['null_Dcnt'] = np.zeros(self.jobs_df.shape[0])

    def manage_bad_times(self) -> None:
        """
        Report and interpolate timestamp and elapsed time values that are
        interpreted from file as NaN or are otherwise non-numeric.

        :return: None
        """

        # Clean up data: force to NaN any non-numeric time values read from file.
        # NOTE: If no times are NaN, then series dtype is numpy.int64,
        #   but if any NaN present, then series dtype is numpy.float64.
        for ser in ('utc_tstamp', 'elapsed_t'):
            self.jobs_df[ser] = pd.to_numeric(self.jobs_df[ser], errors='coerce')

        for col_name in ('utc_tstamp', 'elapsed_t'):
            if self.jobs_df[col_name].isna().sum() > 0:
                nanjobs_df = self.jobs_df[self.jobs_df[col_name].isna()]
                self.jobs_df[col_name].interpolate(method='linear', inplace=True)
                print(f'*** Heads up: some {col_name} values could not'
                      ' be read from the file and have been interpolated. ***\n'
                      f'Tasks with "bad" times:\n'
                      f'row # (starts at 0)\n'
                      f'{nanjobs_df}')

    def add_proj_tags(self):
        """
        Add columns that boolean flag each task's associated Project.
        """

        self.jobs_df['is_all'] = True
        for proj, regex in grp.PROJ_NAME_REGEX.items():
            self.jobs_df[f'is_{proj}'] = where(
                self.jobs_df.task_name.str.contains(regex), True, False)

    def add_hz_values(self):
        """
        Add columns of search frequencies, parsed from the task name.
        Regex for base frequency will match these task name structures:
        FGRP task: 'LATeah4013L03_988.0_0_0.0_9010205_1'
        GW task: 'h1_0681.20_O3aC01Cl1In0__O3AS1a_681.50Hz_19188_1'
        """
        regex_fgrp_freq = r'LATeah.*?_(\d+)'
        # regex_gw_hifreq = r'h1.*_(\d+\.\d{2})Hz_'  # Capture highest freq, not base freq.
        regex_gwo3_freq = r'h1_(\d+\.\d+)_.+__O3'  # Capture the base/parent freq.
        self.jobs_df['fgrp_freq'] = (self.jobs_df.task_name
                                     .str.extract(regex_fgrp_freq)
                                     .astype(np.float64))
        self.jobs_df['gwO3AS_freq'] = (self.jobs_df.task_name
                                       .str.extract(regex_gwo3_freq)
                                       .astype(np.float64))

    def add_daily_counts(self):
        """
        Add columns of daily reported task counts for each E@H Project.
        """

        # Use UTC or local timestamp column option for daily task counts;
        #   --utc is an optional command line argument; UTC_ARG is defined
        #   in if __name__ == "__main__"
        ts2use = 'utc_tstamp' if UTC_ARG else 'local_tstamp'

        # For clarity, grp.PROJECTS names used here need to match those used in
        #   isplotted (dict), ischecked (dict), and grp.CHKBOX_LABELS (tuple).
        # Idea to tally using groupby and transform, source:
        #   https://stackoverflow.com/questions/17709270/
        #      create-column-of-value-counts-in-pandas-dataframe
        for proj in grp.PROJECTS:
            try:
                self.jobs_df[f'{proj}_Dcnt'] = (
                    self.jobs_df[ts2use]
                    .groupby(self.jobs_df[ts2use]
                             .dt.floor('D')
                             .where(self.jobs_df[f'is_{proj}']))
                    .transform('count')
                )
            except AttributeError:
                print(f'Warning: A timestamp in Project {proj} was not'
                      ' recognized as a dt object by add_daily_counts().')


class PlotTasks(TaskDataFrame):
    """
    Set up and display Matplotlib Figure and pyplot Plots of task (job)
    data.
    The plotted Pandas dataframe is inherited from TaskDataFrame.
    Called only from if __name__ == "__main__".
    Methods: setup_window, setup_buttons, setup_slider, setup_plot_manager,
     format_legends, toggle_legends, setup_count_axes, setup_freq_axes,
      reset_plots, plot_all, plot_fgrp5, plot_fgrpBG1, plot_fgrp_hz,
       plot_gw_O2, plot_gw_O3, plot_brp4, plot_brp7, plot_fgrpHz_X_t,
        plot_gwO3Hz_X_t, manage_plots.
    """

    # https://stackoverflow.com/questions/472000/usage-of-slots
    # https://towardsdatascience.com/understand-slots-in-python-e3081ef5196d
    __slots__ = (
        'fig', 'ax1', 'ax2',
        'checkbox', 'do_replot', 'legend_btn_on', 'time_stamp', 'plot_proj',
        'chkbox_label_index', 'isplotted', 'text_bbox', 'hz_slider',
    )

    def __init__(self):
        super().__init__()

        self.checkbox = None
        self.do_replot = False
        self.legend_btn_on = True
        self.time_stamp = 'utc_tstamp' if UTC_ARG else 'local_tstamp'

        # These keys must match plot names in project_groups.CHKBOX_LABELS.
        # Dictionary pairs plot name to plot method.
        self.plot_proj = {'all': self.plot_all,
                          'fgrp5': self.plot_fgrp5,
                          'fgrpBG1': self.plot_fgrpBG1,
                          'fgrp_hz': self.plot_fgrp_hz,
                          'gw_O2': self.plot_gw_O2,
                          'gw_O3': self.plot_gw_O3,
                          'brp4': self.plot_brp4,
                          'brp7': self.plot_brp7,
                          'gwO3Hz_X_t': self.plot_gwO3Hz_X_t,
                          'fgrpHz_X_t': self.plot_fgrpHz_X_t
                          }

        self.chkbox_label_index: dict = {}
        self.isplotted: dict = {}

        # Establish the style for text fancy boxes.
        self.text_bbox = {'facecolor': 'white',
                          'edgecolor': 'grey',
                          'boxstyle': 'round4',
                          'pad': 0.7,
                          }

        # 'bmh' style: from Baysean Methods for Hackers; looks nice for this data.
        #  http://camdavidsonpilon.github.io/Probabilistic-Programming-and-Bayesian-Methods-for-Hackers/
        #  'fast', see: https://matplotlib.org/stable/users/explain/performance.html
        # Statement order relative to subplots assignment affects bg color & initial plot.
        plt.style.use(('bmh', 'fast'))

        # Make the Figure and Axes objects; establish geometry of axes.
        self.fig, (self.ax1, self.ax2) = plt.subplots(
            nrows=2,
            sharex='all',
            gridspec_kw={'height_ratios': [3, 1.2],
                         'left': 0.15,
                         'right': 0.85,
                         'bottom': 0.16,
                         'top': 0.92,
                         'hspace': 0.15,
                         },
        )

        # Need to have mpl_connect statement before any autoscale statements AND
        #  need to have ax.autoscale() set for set_pickradius() to work.
        self.fig.canvas.mpl_connect(
            'pick_event', lambda _: reports.on_pick_report(_, self.jobs_df))

        # Slider used in *_Hz plots to set Hz ranges; attribute here
        #  so that it can be removed/redrawn with each *_Hz plot call
        #  and hidden for all other plots.
        self.hz_slider = plt.axes()

        self.setup_window()
        self.setup_buttons()
        self.setup_count_axes()

    def setup_window(self) -> None:
        """
        A tkinter window for the figure canvas: makes the CheckButton
        actions for drawing plots more responsive.
        """

        # TEST_ARG is boolean, defined in if __name__ == "__main__" from
        #   the --test invocation argument (default: False).
        _title = 'Sample data' if TEST_ARG else 'E@H job_log data'

        # canvas_window is the Tk mainloop defined in if __name__ == "__main__".
        canvas_window.title(_title)
        canvas_window.minsize(1000, 550)


        # Allow full resizing of plot, but only horizontally for toolbar.
        canvas_window.rowconfigure(0, weight=1)
        canvas_window.columnconfigure(0, weight=1)
        canvas_window.configure(bg=mark.CBLIND_COLOR['blue'])
        canvas_window.protocol('WM_DELETE_WINDOW', lambda: utils.quit_gui(canvas_window))
        canvas_window.bind_all('<Escape>', lambda _: utils.quit_gui(canvas_window))
        canvas_window.bind('<Control-q>', lambda _: utils.quit_gui(canvas_window))

        canvas = backend.FigureCanvasTkAgg(self.fig, master=canvas_window)

        toolbar = backend.NavigationToolbar2Tk(canvas, canvas_window)

        # Need to remove the useless subplots navigation button.
        # Source: https://stackoverflow.com/questions/59155873/
        #   how-to-remove-toolbar-button-from-navigationtoolbar2tk-figurecanvastkagg
        # The button id '4' happens to work for all OS platforms. May change in future!
        toolbar.children['!button4'].pack_forget()

        # Now display all widgets.
        # NOTE: toolbar must be gridded BEFORE canvas to prevent
        #   FigureCanvasTkAgg from preempting window geometry with its pack().
        toolbar.grid(row=1, column=0,
                     padx=5, pady=(0, 5),  # Put a border around toolbar.
                     sticky=tk.NSEW,
                     )
        canvas.get_tk_widget().grid(row=0, column=0,
                                    ipady=10, ipadx=10,
                                    padx=5, pady=5,  # Put a border around plot.
                                    sticky=tk.NSEW,
                                    )
        # Because macOS tool icon images won't/don't render properly,
        #   need to provide text descriptions of toolbar button functions.
        if sys.platform == 'darwin':
            tool_lbl = tk.Label(canvas_window,
                                text='Home Fwd Back | Pan  Zoom | Save',
                                font=('TkTooltipFont', 8))
            tool_lbl.grid(row=2, column=0,
                          padx=5, pady=(0, 5),
                          sticky=tk.W)

    def setup_buttons(self) -> None:
        """
        Setup buttons to toggle legends and to display log counts.
        Buttons are aligned with the plot checkbox, ax_chkbox.
        """

        # Relative coordinates in Figure are (LEFT, BOTTOM, WIDTH, HEIGHT).
        # Buttons need a dummy reference, per documentation: "For the
        #   buttons to remain responsive you must keep a reference to
        #   this object." This prevents garbage collection.

        # Position legend toggle button just below plot checkboxes.
        ax_legendbtn = plt.axes((0.885, 0.44, 0.09, 0.06))
        lbtn = Button(ax_legendbtn,
                      'Legends',
                      hovercolor=mark.CBLIND_COLOR['sky blue'],
                      )
        lbtn.on_clicked(self.toggle_legends)
        ax_legendbtn._button = lbtn  # Prevent garbage collection.

        # Position log tally button to bottom right.
        ax_statsbtn = plt.axes((0.9, 0.09, 0.07, 0.08))
        sbtn = Button(ax_statsbtn,
                      'Job log\ncounts',
                      hovercolor=mark.CBLIND_COLOR['orange'],
                      )
        sbtn.on_clicked(lambda _: reports.joblog_report(self.jobs_df))
        ax_statsbtn._button = sbtn  # Prevent garbage collection.

        # Position About button to bottom right corner.
        ax_aboutbtn = plt.axes((0.9, 0.01, 0.07, 0.06))
        abtn = Button(ax_aboutbtn,
                      'About',
                      hovercolor=mark.CBLIND_COLOR['orange'],
                      )
        abtn.on_clicked(reports.about_report)
        ax_aboutbtn._button = abtn  # Prevent garbage collection.

    def setup_slider(self, max_f: float) -> None:
        """
        Create a RangeSlider for real-time y-axis Hz range adjustments
        of *_freq plots. Also create usage text box.

        :param max_f: The plotted Project's maximum frequency value.
        """

        # Need to replace any prior slider bar with a new one to prevent
        #   stacking of bars.
        self.hz_slider.remove()

        # Add a 2% margin to the slider upper limit when frequency data are available.
        # When there are no plot data, max_f will be NaN, so use some NaN magic
        #   to test that and avoid a ValueError for RangeSlider max range by
        #   assigning it a limit of 1.
        # https://towardsdatascience.com/
        #   5-methods-to-check-for-nan-values-in-in-python-3f21ddd17eed
        max_limit = 1 if max_f != max_f else max_f * 1.02

        # RangeSlider relative Figure coord: (LEFT, BOTTOM, WIDTH, HEIGHT).
        self.hz_slider = plt.axes((0.05, 0.38, 0.01, 0.52))  # vert

        # Invert min/max values on vertical slider so max is on top.
        plt.gca().invert_yaxis()

        hz_slider = RangeSlider(ax=self.hz_slider,
                                label="Hz range",
                                valmin=0,
                                valmax=max_limit,
                                valstep=2,
                                orientation='vertical',
                                color=mark.CBLIND_COLOR['blue'],
                                handle_style={'size': 8, }
                                )

        # Position text box above Navigation toolbar.
        self.ax1.text(-0.19, -0.7,
                      ("Range slider and Navigation bar tools may conflict.\n"
                       "If so, then toggle the plot's checkbox to reset."),
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax1.transAxes,
                      bbox=self.text_bbox,
                      )
        self.hz_slider._slider = hz_slider  # Prevent garbage collection.

        def _update(val):
            """
            Live update of the plot's y-axis frequency range.

            :param val: Value implicitly passed to a callback by the
             RangeSlider as a tuple, (min, max).
            """

            self.ax1.set_ylim(val)

            self.fig.canvas.draw_idle()

        hz_slider.on_changed(_update)

    def setup_plot_manager(self) -> None:
        """
        Set up dictionaries to use as plotting conditional variables.
        Set up the plot selection checkbox.
        Plot 'all' as startup default.
        """
        for i, proj in enumerate(grp.CHKBOX_LABELS):
            self.chkbox_label_index[proj] = i

        # Need to populate the isplotted dictionary with Project label names and
        #   their default checkbox boolean states.
        for proj in grp.CHKBOX_LABELS:
            self.isplotted[proj] = False

        # Relative coordinates in Figure, 4-tuple (LEFT, BOTTOM, WIDTH, HEIGHT).
        ax_chkbox = plt.axes((0.86, 0.54, 0.13, 0.36), facecolor=mark.LIGHT_GRAY)
        ax_chkbox.set_xlabel('Project plots',
                             fontsize='medium',
                             fontweight='bold')
        ax_chkbox.xaxis.set_label_position('top')

        # Need check boxes to control which data series to plot.
        # At startup, activate checkbox label 'all' so that all tasks
        #  are plotted by default via manage_plots().
        self.checkbox = CheckButtons(ax=ax_chkbox, labels=grp.CHKBOX_LABELS)
        self.checkbox.on_clicked(self.manage_plots)
        self.checkbox.set_active(self.chkbox_label_index['all'])

    def format_legends(self):
        legend_params = dict(ncol=1,
                             fontsize='x-small',
                             loc='upper right',
                             markerscale=mark.SCALE,
                             edgecolor='black',
                             framealpha=0.4)
        self.ax1.legend(**legend_params)
        self.ax2.legend(**legend_params)

    def toggle_legends(self, event) -> None:
        """
        Show and hide plot legends. If plot has no legend, do nothing.

        Args:
            event: Implicit mouse click event.

        Returns: None
        """
        if self.ax1.get_legend():
            if self.legend_btn_on:
                self.ax1.get_legend().set_visible(False)
                self.ax2.get_legend().set_visible(False)
                self.legend_btn_on = False
            else:
                self.format_legends()
                self.ax1.get_legend().set_visible(True)
                self.legend_btn_on = True
                self.format_legends()

        self.fig.canvas.draw()  # Speeds up response.

        return event

    def setup_count_axes(self):
        """
        Used to set initial axes and rebuild axes components when plots
        and axes are cleared by reset_plots().
        """

        # Need to reset plot axes in case setup_freq_axes() was called.
        self.hz_slider.set_visible(False)
        self.ax2.set_visible(True)
        self.ax1.tick_params('x', labelbottom=False)

        # Default axis margins are 0.05 (5%) of data values.
        self.ax1.margins(0.02, 0.02)
        self.ax2.margins(0.02, 0.05)

        lbl_params = dict(fontsize='medium', fontweight='bold')

        self.ax1.set_ylabel('Task completion time', **lbl_params)

        if UTC_ARG:
            self.ax2.set_xlabel('Task reporting datetime (UTC)', **lbl_params)
        else:
            self.ax2.set_xlabel('Task reporting datetime', **lbl_params)

        self.ax2.set_ylabel('Tasks/day', **lbl_params)

        # Need to set the Tasks/day axis label in a static position.
        self.ax2.yaxis.set_label_coords(-0.1, 0.55)

        # Need to rotate and right-align the date labels to avoid crowding.
        for label in self.ax1.get_yticklabels(which='major'):
            label.set(rotation=30, fontsize='x-small')

        for label in self.ax2.get_xticklabels(which='major'):
            label.set(rotation=15, fontsize='small', horizontalalignment='right')

        for label in self.ax2.get_yticklabels(which='major'):
            label.set(fontsize='small')

        self.ax1.yaxis.set(major_formatter=mdates.DateFormatter('%H:%M:%S'),
                           major_locator=ticker.AutoLocator(),
                           minor_locator=ticker.AutoMinorLocator())

        self.ax2.yaxis.set_major_locator(ticker.MaxNLocator(nbins=6, integer=True))

        self.ax1.grid(True)
        self.ax2.grid(True)

        # Used by reports.on_pick_reports() with plot() parameter picker=True.
        self.ax1.xaxis.set_pickradius(mark.PICK_RADIUS)
        self.ax1.yaxis.set_pickradius(mark.PICK_RADIUS)

        # NOTE: autoscale methods have no visual effect when reset_plots() plots
        #  the full range datetimes from a job log, BUT enabling autoscale()
        #  allows set_pickradius() to work properly.
        self.ax1.autoscale()
        self.ax2.autoscale()

    def setup_freq_axes(self, t_limits: tuple):
        """
        Remove bottom axis and show tick labels (b/c when sharex=True,
        tick labels only show on bottom (self.ax2) plot).
        Called from plot_fgrpHz_X_t() and plot_gwO3Hz_X_t().

        :param t_limits: Constrain x-axis of task times from zero to
            maximum value, plus a small buffer.
        :return: None
        """

        self.ax2.set_visible(False)
        self.ax1.tick_params('x', labelbottom=True)

        # When data are not available for a plot, the t_limit tuple
        #  will be (0, nan) and so set_xlim() will raise
        #    ValueError: Axis limits cannot be NaN or Inf
        try:
            self.ax1.set_xlim(t_limits)
        except ValueError:
            pass

        # Need to FIX: the Home tool sets (remembers) axes range of the
        #  first selected freq vs time plot, instead of current
        #  freq vs time plot, but only when the Zoom tool has been used.
        lbl_params = dict(fontsize='medium', fontweight='bold')

        self.ax1.set_xlabel('Task completion time, sec', **lbl_params)
        self.ax1.set_ylabel('Task base frequency, Hz', **lbl_params)

        self.ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
        self.ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))

    def reset_plots(self):
        """
        Clear plots, axis labels, ticks, formats, legends, sliders, etc.
        Clears plotted data by setting all data values to zero and
        removing marks. Use to avoid stacking of plots, which affects
        on_pick_report() display of nearby task info. Note that, with
        this, the full x-axis datetime range in job lob is always
        plotted; therefore, the methods ax.relim(), ax.autoscale_view(),
        and ax.autoscale() have no effect on individual plots.
        Called from manage_plots().
        """
        self.ax1.clear()
        self.ax2.clear()

        self.setup_count_axes()

        plot_params = dict(visible=False, label='_leave blank')

        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.null_time,
                      **plot_params,
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.null_Dcnt,
                      **plot_params,
                      )

        for plot, _ in self.isplotted.items():
            self.isplotted[plot] = False

    def plot_all(self):
        p_label = 'all'
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t,
                      mark.STYLE['point'],
                      markersize=mark.SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['blue'],
                      alpha=0.2,
                      picker=True,
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.all_Dcnt,
                      mark.STYLE['square'],
                      markersize=mark.DCNT_SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['blue'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_fgrp5(self):
        p_label = 'fgrp5'
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      mark.STYLE['tri_left'],
                      markersize=mark.SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['bluish green'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.fgrp5_Dcnt,
                      mark.STYLE['square'],
                      markersize=mark.DCNT_SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['bluish green'],
                      alpha=0.4,
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_fgrpBG1(self):
        p_label = 'fgrpBG1'
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      mark.STYLE['tri_right'],
                      markersize=mark.SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['vermilion'],
                      alpha=0.5,
                      picker=True,
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.fgrpBG1_Dcnt,
                      mark.STYLE['square'],
                      markersize=mark.DCNT_SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['vermilion'],
                      )

        self.format_legends()
        self.isplotted[p_label] = True

    def plot_fgrp_hz(self):
        """
        Plot of frequency (Hz) vs. datetime for all FGRP tasks (5 & G1).
        """

        self.reset_plots()
        p_label = 'fgrp_hz'

        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.fgrp_freq,
                      mark.STYLE['tri_right'],
                      markersize=mark.SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['vermilion'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.fgrp5_Dcnt,
                      mark.STYLE['square'],
                      markersize=mark.DCNT_SIZE,
                      label='fgrp5',
                      color=mark.CBLIND_COLOR['black'],
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.fgrpBG1_Dcnt,
                      mark.STYLE['square'],
                      markersize=mark.DCNT_SIZE,
                      label=p_label,  # fgrpBG1 counts
                      color=mark.CBLIND_COLOR['vermilion'],
                      )

        self.ax1.set_ylabel('Task base frequency, Hz',
                            fontsize='medium', fontweight='bold')
        self.ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))

        self.format_legends()
        self.isplotted[p_label] = True

    def plot_gw_O2(self):
        p_label = 'gw_O2'
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      mark.STYLE['triangle_down'],
                      markersize=mark.SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['orange'],
                      alpha=0.4,
                      picker=True,
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.gw_O2_Dcnt,
                      mark.STYLE['square'],
                      markersize=mark.DCNT_SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['orange'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_gw_O3(self):
        p_label = 'gw_O3'
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      mark.STYLE['thin_diamond'],
                      markersize=mark.SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['sky blue'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.gw_O3_Dcnt,
                      mark.STYLE['square'],
                      markersize=mark.DCNT_SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['sky blue'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_brp4(self):
        p_label = 'brp4'
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      mark.STYLE['pentagon'],
                      markersize=mark.SIZE,
                      label=p_label,  # 'BRP4 & BRP4G',
                      color=mark.CBLIND_COLOR['reddish purple'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.brp4_Dcnt,
                      mark.STYLE['square'],
                      markersize=mark.DCNT_SIZE,
                      label=p_label,  # 'BRP4 & BRP4G',
                      color=mark.CBLIND_COLOR['reddish purple'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_brp7(self):
        p_label = 'brp7'
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      mark.STYLE['diamond'],
                      markersize=mark.SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['black'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax2.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.brp7_Dcnt,
                      mark.STYLE['square'],
                      markersize=mark.DCNT_SIZE,
                      label=p_label,
                      color=mark.CBLIND_COLOR['black'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_fgrpHz_X_t(self):
        num_f = self.jobs_df.fgrp_freq.nunique()
        min_f = self.jobs_df.fgrp_freq.min()
        max_f = self.jobs_df.fgrp_freq.max()
        min_t = self.jobs_df.elapsed_sec.where(
            self.jobs_df.is_fgrp).min().astype(np.int64)
        max_t = self.jobs_df.elapsed_sec.where(
            self.jobs_df.is_fgrp).max().astype(np.int64)

        # Add a 2% margin to time axis upper limit.
        self.setup_freq_axes((0, max_t * 1.02))

        self.setup_slider(max_f)

        # Position text below lower left corner of plot area.
        self.ax1.text(0.0, -0.15,
                      f'Frequencies, N: {num_f}\n'
                      f'Hz, min--max: {min_f}--{max_f}\n'
                      f'Time, min--max: {min_t}--{max_t}',
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax1.transAxes,
                      bbox=self.text_bbox,
                      )

        self.ax1.plot(self.jobs_df.elapsed_sec.where(self.jobs_df.is_fgrp),
                      self.jobs_df.fgrp_freq,
                      mark.STYLE['tri_right'],
                      markersize=mark.SIZE,
                      color=mark.CBLIND_COLOR['vermilion'],
                      alpha=0.3,
                      picker=True,
                      )

        self.isplotted['fgrpHz_X_t'] = True

    def plot_gwO3Hz_X_t(self):
        num_f = self.jobs_df.gwO3AS_freq.nunique()
        min_f = self.jobs_df.gwO3AS_freq.min()
        max_f = self.jobs_df.gwO3AS_freq.max()
        min_t = self.jobs_df.elapsed_sec.where(
            self.jobs_df.is_gw_O3).min().astype(np.int64)
        max_t = self.jobs_df.elapsed_sec.where(
            self.jobs_df.is_gw_O3).max().astype(np.int64)

        # Add a 2% margin to time axis upper limit.
        self.setup_freq_axes((0, max_t * 1.02))

        self.setup_slider(max_f)

        # Position text below lower left corner of axes.
        self.ax1.text(0.0, -0.15,
                      f'Frequencies, N: {num_f}\n'
                      f'Hz, min--max: {min_f}--{max_f}\n'
                      f'Time, min--max: {min_t}--{max_t}',
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax1.transAxes,
                      bbox=self.text_bbox,
                      )

        self.ax1.plot(self.jobs_df.elapsed_sec.where(self.jobs_df.is_gw_O3),
                      self.jobs_df.gwO3AS_freq,
                      mark.STYLE['triangle_up'],
                      markersize=mark.SIZE,
                      color=mark.CBLIND_COLOR['sky blue'],
                      alpha=0.3,
                      picker=True,
                      )

        self.isplotted['gw_O3_freq'] = True

    def manage_plots(self, clicked_label: str) -> None:
        """
        Conditions determining which plot functions, selected from
        checkbox labels, to plot, either with each other or solo.
        Called from checkbox.on_clicked() callback.

        :param clicked_label: Implicit event that returns the label name
          selected from the checkbox CheckButton widget.
        :return: None
        """

        # NOTE: with checkbox.eventson = True (default), every checkbox
        #  click calls this method.

        # labels_status key is Project name, value is current check status.
        labels_status = dict(zip(grp.CHKBOX_LABELS, self.checkbox.get_status()))
        label_is_checked: bool = labels_status[clicked_label]
        num_tasks = sum(self.jobs_df[f'is_{grp.CLICKED_PLOT[clicked_label]}'])

        def post_nodata_msg():
            """
            Post a notice if the selected Project data are not available.
            Toggle off (deactivate) the selected label's check box.
            """
            self.fig.text(0.5, 0.51,
                          f'There are no {clicked_label} data to plot.',
                          horizontalalignment='center',
                          verticalalignment='center',
                          transform=self.ax1.transAxes,
                          visible=True,
                          zorder=1)
            self.checkbox.set_active(self.chkbox_label_index[clicked_label])

            # Re-plot (retain) any "exclusive" data that may have been
            #  plotted when a no-data Project label was selected
            #  A weak hack, but it works. The entire method needs work.
            for _l, _s in labels_status.items():
                if _l in grp.EXCLUSIVE_PLOTS and _s:
                    self.plot_proj[_l]()

            self.fig.canvas.draw_idle()

        # Remove any prior text box from post_nodata_msg().
        if label_is_checked and self.fig.texts:
            self.fig.texts.clear()

        # NOTE: CANNOT have same plot points overlaid; that creates
        #  multiple on_pick_report() calls for the same task info.

        # Exclusive plots can be plotted only by themselves.
        for plot in grp.EXCLUSIVE_PLOTS:
            if clicked_label == plot and label_is_checked:
                if num_tasks == 0:
                    post_nodata_msg()
                    return

                # Label was toggled on...
                # Need to uncheck other label_is_checked project labels.
                for lbl in grp.CHKBOX_LABELS:
                    if (lbl != clicked_label and
                            (self.isplotted[lbl] or labels_status[lbl])):
                        self.checkbox.set_active(self.chkbox_label_index[lbl])

                self.fig.canvas.draw_idle()
                self.plot_proj[clicked_label]()
                return

        # Inclusive plots can be plotted only with (on top of) each another.
        #  So, first, need to remove any current exclusive plot.
        if clicked_label in grp.ALL_INCLUSIVE and label_is_checked:
            if num_tasks == 0:
                post_nodata_msg()
                return

            self.reset_exclusive_plots(labels_status)
            self.plot_inclusive_plots(labels_status)
        elif not label_is_checked:

            # A checkbox was toggled off, so remove all plots,
            #   then replot the other existing inclusive plots.
            self.reset_plots()
            self.plot_inclusive_plots(labels_status)

        self.fig.canvas.draw_idle()

    def reset_exclusive_plots(self, labels_status) -> None:
        """
        Reset exclusive plots to an unchecked state when different plot
        is checked.
        Called from manage_plots(). Calls reset_plots().
        Args:
            labels_status:  A dictionary of Project names and their
            checked status.

        Returns: None

        """
        for plot in grp.EXCLUSIVE_PLOTS:
            if self.isplotted[plot] or labels_status[plot]:
                self.isplotted[plot] = False
                self.checkbox.set_active(self.chkbox_label_index[plot])
        self.reset_plots()

    def plot_inclusive_plots(self, labels_status) -> None:
        """
        Plot inclusive plots, which can be plotted with each other.
        Called from manage_plots().
        Args:
            labels_status:  A dictionary of Project names and their
            checked status.

        Returns: None

        """
        for proj, status in labels_status.items():
            if status and proj in grp.ALL_INCLUSIVE and not self.isplotted[proj]:
                self.plot_proj[proj]()

def run_checks():
    """Program exits here if system platform or Python version check fails."""
    utils.check_platform()
    vcheck.minversion('3.7')


def main():
    """Main program entry point."""

    # Developer: Custom handlers for unexpected system and tkinter exceptions.
    # Uncomment to test the program's exception handling.
    # sys.excepthook = utils.handle_exception
    # canvas_window.report_callback_exception = utils.handle_exception

    # Need an image to replace blank tk desktop icon.
    #   Set correct path to the local 'images' directory and icon file.
    try:
        icon_path = path_check.valid_path_to('images/desktop_icon.png')
        icon = tk.PhotoImage(file=icon_path)
        canvas_window.iconphoto(True, icon)
    except tk.TclError as msg:
        print('Cannot display program icon,'
              ' so it will be left blank or tk default.')
        print(f'tk error message: {msg}\n')

    try:
        print(f'Data from {DATA_PATH} are loading. This may take a few seconds...\n')

        # This call will set up an inherited pd dataframe in TaskDataFrame,
        #  then plot 'all' tasks as specified in setup_plot_manager().
        #  After that, plots are managed by CheckButton states in manage_plots().
        PlotTasks().setup_plot_manager()
        print('The plot window is ready.')

        canvas_window.mainloop()
    except KeyboardInterrupt:
        print("\n*** User quit the program from Terminal/Console ***\n")

if __name__ == '__main__':

    # Comment out if using PyInstaller to create an executable.
    run_checks()

    # Need to use a tkinter window for the plot canvas so that CheckButton
    #   actions for plotting are more responsive.
    canvas_window = tk.Tk()
    main()
