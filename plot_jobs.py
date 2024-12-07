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
# Copyright (C) 2022-2024 C.S. Echt, under GNU General Public License

# Standard library imports
from signal import signal, SIGINT
from sys import platform, exit as sys_exit

# Local application imports
from plot_utils import (path_check,
                        vcheck,
                        reports,
                        utils,
                        constants as const)

# Third party imports (tk may not be included with some Python installations).
try:
    import matplotlib.backends.backend_tkagg as backend
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import pandas as pd
    import tkinter as tk

    from matplotlib import ticker
    from matplotlib.widgets import CheckButtons, Button
    from numpy import where, int64, float64, zeros

except (ImportError, ModuleNotFoundError) as import_err:
    sys_exit('*** One or more required Python packages were not found'
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

# manage_args() returns a 3-tuple (bool, bool, path), as set by command line or by default.
TEST_ARG, UTC_ARG, DATA_PATH = utils.manage_args()


class TaskDataFrame:
    """
    Set up the DataFrame used for plotting.
    Is called only as an inherited Class from PlotTasks.
    Methods:
         setup_df - Set up main dataframe from an E@H job_log text file.
         manage_bad_times - Interpolate missing time data.
         add_project_tags - Add columns of boolean flags for Project ID.
         add_hz_values - Add task base (parent) search frequencies.
         add_daily_counts - Add daily counts for each Project.
    """

    def __init__(self):
        self.jobs_df = pd.DataFrame()

        self.setup_df()
        self.add_project_tags()
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

        self.jobs_df = pd.read_table(filepath_or_buffer=DATA_PATH,
                                     engine='c',
                                     sep=' ',
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
        self.jobs_df['null_time'] = zeros(self.jobs_df.shape[0])
        self.jobs_df['null_Dcnt'] = zeros(self.jobs_df.shape[0])

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
                self.jobs_df[col_name] = self.jobs_df[col_name].interpolate()
                print(f'*** Heads up: some {col_name} values could not'
                      ' be read from the file and have been interpolated. ***\n'
                      f'Tasks with "bad" times:\n'
                      f'row # (starts at 0)\n'
                      f'{nanjobs_df}')

    def add_project_tags(self):
        """
        Add columns that boolean flag each task's associated Project.
        """

        self.jobs_df['is_all'] = True
        for project, regex in const.PROJECT_NAME_REGEX.items():
            self.jobs_df[f'is_{project}'] = where(
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
                                     .astype(float64))
        self.jobs_df['gwO3AS_freq'] = (self.jobs_df.task_name
                                       .str.extract(regex_gwo3_freq)
                                       .astype(float64))

    def add_daily_counts(self):
        """
        Add columns of daily reported task counts for each E@H Project.
        """

        # Use UTC or local timestamp column option for daily task counts;
        # UTC_ARG is boolean, defined from the --utc invocation argument (default: False).
        ts2use = 'utc_tstamp' if UTC_ARG else 'local_tstamp'

        # For clarity, const.PROJECTS names used here need to match those used in
        #   isplotted (dict), ischecked (dict), and const.CHKBOX_LABELS (tuple).
        # Idea to tally using groupby and transform, source:
        #   https://stackoverflow.com/questions/17709270/
        #      create-column-of-value-counts-in-pandas-dataframe
        for project in const.PROJECTS:
            try:
                self.jobs_df[f'{project}_Dcnt'] = (
                    self.jobs_df[ts2use].groupby(
                        self.jobs_df[ts2use].dt.floor('D')[self.jobs_df[f'is_{project}']]
                    ).transform('count')
                )
            except AttributeError:
                print(f'Warning: A timestamp in Project {project} was not'
                      ' recognized as a dt object by add_daily_counts().')


class PlotTasks(TaskDataFrame):
    """
    Set up and display Matplotlib Figure and pyplot Plots of task (job)
    data. The plotted Pandas dataframe is inherited from TaskDataFrame.
    Note that the only use of inheritance is to simply set up the
    dataframe and pass self.jobs_df to this PlotTasks class. This is
    done to avoid the need for global variables.
    Called from main().
    Methods: setup_window, setup_buttons, setup_plot_manager,
    format_legends, toggle_legends, setup_count_axes, setup_freq_axes,
    display_freq_plot_tip, reset_plots, plot_all, plot_fgrp5,
    plot_fgrpBG1, plot_fgrp_hz, plot_gw_O2, plot_gw_O3, plot_brp4,
    plot_brp7, plot_fgrpHz_X_t, plot_gwO3Hz_X_t, manage_plots.
    """

    # https://stackoverflow.com/questions/472000/usage-of-slots
    # https://towardsdatascience.com/understand-slots-in-python-e3081ef5196d
    __slots__ = (
        'fig', 'ax0', 'ax1',
        'checkbox', 'do_replot', 'legend_btn_on', 'time_stamp', 'plot_project',
        'chkbox_label_index', 'isplotted', 'text_bbox',
    )

    def __init__(self):
        super().__init__()

        self.checkbox = None
        self.do_replot = False
        self.legend_btn_on = True
        self.time_stamp = 'utc_tstamp' if UTC_ARG else 'local_tstamp'

        # These keys must match plot names in project_groups.CHKBOX_LABELS.
        # Dictionary pairs plot name to plot method.
        self.plot_project = {
            'all': self.plot_all,
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
        self.fig, (self.ax0, self.ax1) = plt.subplots(
            nrows=2,
            sharex='all',
            gridspec_kw={'height_ratios': [3, 1.2],
                         'left': 0.10,
                         'right': 0.85,
                         'bottom': 0.16,
                         'top': 0.92,
                         'hspace': 0.15,
                         },
        )

    def setup_widgets(self) -> None:
        """
        Set up the plot window, buttons, checkboxes, and axes.
        Called from main() at startup.
        Returns: None
        """
        self.setup_plot_manager()
        self.setup_window()
        self.setup_buttons()
        self.setup_count_axes()

    def setup_plot_manager(self) -> None:
        """
        Set up dictionaries to use as plotting conditional variables.
        Set up the plot selection checkbox.
        Plot 'all' as startup default.
        Called from setup_widgets().
        """
        for i, project in enumerate(const.CHKBOX_LABELS):
            self.chkbox_label_index[project] = i

        # Need to populate the isplotted dictionary with Project label names and
        #   their default checkbox boolean states.
        for project in const.CHKBOX_LABELS:
            self.isplotted[project] = False

        # Relative coordinates in Figure, 4-tuple (LEFT, BOTTOM, WIDTH, HEIGHT).
        ax_chkbox = plt.axes((0.86, 0.54, 0.13, 0.36), facecolor=const.LIGHT_GRAY)
        ax_chkbox.set_xlabel('Project plots',
                             fontsize='medium',
                             fontweight='bold')
        ax_chkbox.xaxis.set_label_position('top')

        # Need check boxes to control which data series to plot.
        # At startup, activate checkbox label 'all' so that all tasks
        #  are plotted by default via manage_plots().
        self.checkbox = CheckButtons(ax=ax_chkbox, labels=const.CHKBOX_LABELS)
        self.checkbox.on_clicked(self.manage_plots)
        self.checkbox.set_active(self.chkbox_label_index['all'])

    def setup_window(self) -> None:
        """
        A tkinter window for the figure canvas: makes the CheckButton
        actions for drawing plots more responsive.
        Called from setup_widgets().
        """

        # TEST_ARG is boolean, defined from the --test invocation argument (default: False).
        _title = 'Sample data' if TEST_ARG else 'E@H job_log data'

        # canvas_window is the Tk mainloop defined in main().
        canvas_window.title(_title)
        canvas_window.minsize(1000, 550)

        # Allow full resizing of plot, but only horizontally for toolbar.
        canvas_window.rowconfigure(0, weight=1)
        canvas_window.columnconfigure(0, weight=1)
        canvas_window.configure(bg=const.CBLIND_COLOR['blue'])
        canvas_window.protocol('WM_DELETE_WINDOW', lambda: utils.quit_gui(canvas_window))
        canvas_window.bind_all('<Escape>', lambda _: utils.quit_gui(canvas_window))
        canvas_window.bind('<Control-q>', lambda _: utils.quit_gui(canvas_window))

        canvas = backend.FigureCanvasTkAgg(self.fig, master=canvas_window)

        # Now display all widgets. Use pack(), not grid(), for consistent Toolbar behavior.
        canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
        toolbar = backend.NavigationToolbar2Tk(canvas, canvas_window)

        # Need to remove the useless subplots navigation button.
        # Source: https://stackoverflow.com/questions/59155873/
        #   how-to-remove-toolbar-button-from-navigationtoolbar2tk-figurecanvastkagg
        # The button id '4' happens to work for all OS platforms. May change in future!
        toolbar.children['!button4'].pack_forget()
        toolbar.update()

        # Because macOS tool icon images won't/don't render properly,
        #   need to provide text descriptions of toolbar button functions.
        if platform == 'darwin':
            tool_lbl = tk.Label(canvas_window,
                                text='Home Fwd Back | Pan  Zoom | Save',
                                font=('TkTooltipFont', 8))
            tool_lbl.grid(row=2, column=0,
                          padx=5, pady=(0, 5),
                          sticky=tk.W)

        # Need to have mpl_connect statement before any autoscale statements
        #  (in setup_count_axes).
        self.fig.canvas.mpl_connect(
            'pick_event',
            lambda _: reports.on_pick_report(event=_, dataframe=self.jobs_df))

    def setup_buttons(self) -> None:
        """
        Setup buttons to toggle legends and to display log counts.
        Buttons are aligned with the plot checkbox, ax_chkbox.
        Called from setup_widgets().
        """

        # Relative coordinates in Figure are (LEFT, BOTTOM, WIDTH, HEIGHT).
        # Buttons need a dummy reference, per documentation: "For the
        #   buttons to remain responsive you must keep a reference to
        #   this object." This prevents garbage collection.

        # Position legend toggle button just below plot checkboxes.
        ax_legendbtn = plt.axes((0.885, 0.44, 0.09, 0.06))
        lbtn = Button(ax_legendbtn,
                      'Legends',
                      hovercolor=const.CBLIND_COLOR['sky blue'],
                      )
        lbtn.on_clicked(self.toggle_legends)
        ax_legendbtn._button = lbtn  # Prevent garbage collection.

        # Position log tally button to bottom right.
        ax_statsbtn = plt.axes((0.9, 0.09, 0.07, 0.08))
        sbtn = Button(ax_statsbtn,
                      'Job log\ncounts',
                      hovercolor=const.CBLIND_COLOR['orange'],
                      )
        sbtn.on_clicked(lambda _: reports.joblog_report(self.jobs_df))
        ax_statsbtn._button = sbtn  # Prevent garbage collection.

        # Position About button to bottom right corner.
        ax_aboutbtn = plt.axes((0.9, 0.01, 0.07, 0.06))
        abtn = Button(ax_aboutbtn,
                      'About',
                      hovercolor=const.CBLIND_COLOR['orange'],
                      )
        abtn.on_clicked(reports.about_report)
        ax_aboutbtn._button = abtn  # Prevent garbage collection.

    def format_legends(self):
        legend_params = dict(ncol=1,
                             fontsize='x-small',
                             loc='upper right',
                             markerscale=const.SCALE,
                             edgecolor='black',
                             framealpha=0.4)
        self.ax0.legend(**legend_params)
        self.ax1.legend(**legend_params)

    def toggle_legends(self, event) -> None:
        """
        Show and hide plot legends. If plot has no legend, do nothing.

        Args:
            event: Implicit mouse click event.

        Returns: None
        """
        if self.ax0.get_legend():
            if self.legend_btn_on:
                self.ax0.get_legend().set_visible(False)
                self.ax1.get_legend().set_visible(False)
                self.legend_btn_on = False
            else:
                self.format_legends()
                self.ax0.get_legend().set_visible(True)
                self.legend_btn_on = True
                self.format_legends()

        self.fig.canvas.draw()  # Speeds up response.

        return event

    def setup_count_axes(self):
        """
        Used to set initial axes and rebuild axes components when plots
        and axes are cleared by reset_plots().
        Called from setup_widgets() and reset_plots().
        """

        # Need to reset plot axes in case setup_freq_axes() was called.
        self.ax1.set_visible(True)
        self.ax0.tick_params('x', labelbottom=False)

        # Default axis margins are 0.05 (5%) of data values.
        self.ax0.margins(0.02, 0.02)
        self.ax1.margins(0.02, 0.05)

        lbl_params = dict(fontsize='medium', fontweight='bold')

        self.ax0.set_ylabel('Task completion time', **lbl_params)

        if UTC_ARG:
            self.ax1.set_xlabel('Task reporting datetime (UTC)', **lbl_params)
        else:
            self.ax1.set_xlabel('Task reporting datetime', **lbl_params)

        self.ax1.set_ylabel('Tasks/day', **lbl_params)

        # Need to rotate and right-align the date labels to avoid crowding.
        for label in self.ax0.get_yticklabels(which='major'):
            label.set(rotation=30, fontsize='x-small')

        for label in self.ax1.get_xticklabels(which='major'):
            label.set(rotation=15, fontsize='small', horizontalalignment='right')

        for label in self.ax1.get_yticklabels(which='major'):
            label.set(fontsize='small')

        self.ax0.yaxis.set(major_formatter=mdates.DateFormatter('%H:%M:%S'),
                           major_locator=ticker.AutoLocator(),
                           minor_locator=ticker.AutoMinorLocator())

        self.ax1.yaxis.set_major_locator(ticker.MaxNLocator(nbins=6, integer=True))

        self.ax0.grid(True)
        self.ax1.grid(True)

        # Used by reports.on_pick_reports() with plot() parameter picker=True.
        self.ax0.xaxis.set_pickradius(const.PICK_RADIUS)
        self.ax0.yaxis.set_pickradius(const.PICK_RADIUS)

        # NOTE: autoscale methods have no visual effect when reset_plots() plots
        #  the full range datetimes from a job log, BUT enabling autoscale()
        #  allows set_pickradius() to work properly.
        self.ax0.autoscale()
        self.ax1.autoscale()

    def setup_freq_axes(self, t_limits: tuple):
        """
        Remove bottom axis and show tick labels (b/c when sharex=True,
        tick labels only show on bottom (self.ax1) plot).
        Called from plot_fgrpHz_X_t() and plot_gwO3Hz_X_t().

        :param t_limits: Constrain x-axis of task times from zero to
            maximum value, plus a small buffer.
        :return: None
        """

        self.ax1.set_visible(False)
        self.ax0.tick_params('x', labelbottom=True)

        # When data are not available for a plot, the t_limit tuple
        #  will be (0, nan) and so set_xlim() will raise
        #    ValueError: Axis limits cannot be NaN or Inf
        try:
            self.ax0.set_xlim(t_limits)
        except ValueError:
            pass

        # Need to FIX: the Home tool sets (remembers) axes range of the
        #  first selected freq vs time plot, instead of current
        #  freq vs time plot, but only when the Zoom tool has been used.
        lbl_params = dict(fontsize='medium', fontweight='bold')

        self.ax0.set_xlabel('Task completion time, sec', **lbl_params)
        self.ax0.set_ylabel('Task base frequency, Hz', **lbl_params)

        self.ax0.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
        self.ax0.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))

    def display_freq_plot_tip(self) -> None:
        """
        Display text in the plot window for the Hz vs. time plots.
        """

        # Need to clear any previous text boxes.
        for txt in self.fig.texts:
            txt.remove()

        # Position text box above Navigation toolbar.
        self.ax0.text(-0.1, -0.7,
                      "Tip: use the Zoom and Arrow tools to adjust the Hz range.\n",
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax0.transAxes,
                      bbox=self.text_bbox,
                      )

        self.fig.canvas.draw()

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
        self.ax0.clear()
        self.ax1.clear()

        self.setup_count_axes()

        plot_params = dict(visible=False, label='_leave blank')

        self.ax0.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.null_time,
                      **plot_params,
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.null_Dcnt,
                      **plot_params,
                      )

        for plot, _ in self.isplotted.items():
            self.isplotted[plot] = False

    def plot_all(self):
        p_label = 'all'
        self.ax0.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t,
                      const.STYLE['point'],
                      markersize=const.SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['blue'],
                      alpha=0.2,
                      picker=True,
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.all_Dcnt,
                      const.STYLE['square'],
                      markersize=const.DCNT_SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['blue'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_fgrp5(self):
        p_label = 'fgrp5'
        self.ax0.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      const.STYLE['tri_left'],
                      markersize=const.SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['bluish green'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df[f'{p_label}_Dcnt'],
                      const.STYLE['square'],
                      markersize=const.DCNT_SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['bluish green'],
                      alpha=0.4,
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_fgrpBG1(self):
        p_label = 'fgrpBG1'
        self.ax0.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      const.STYLE['tri_right'],
                      markersize=const.SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['vermilion'],
                      alpha=0.5,
                      picker=True,
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df[f'{p_label}_Dcnt'],
                      const.STYLE['square'],
                      markersize=const.DCNT_SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['vermilion'],
                      )

        self.format_legends()
        self.isplotted[p_label] = True

    def plot_fgrp_hz(self):
        """
        Plot of frequency (Hz) vs. datetime for all FGRP tasks (5 & G1).
        """

        self.reset_plots()
        p_label = 'fgrp_hz'

        self.ax0.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.fgrp_freq,
                      const.STYLE['tri_right'],
                      markersize=const.SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['vermilion'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.fgrp5_Dcnt,
                      const.STYLE['square'],
                      markersize=const.DCNT_SIZE,
                      label='fgrp5',
                      color=const.CBLIND_COLOR['black'],
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.fgrpBG1_Dcnt,
                      const.STYLE['square'],
                      markersize=const.DCNT_SIZE,
                      label=p_label,  # fgrpBG1 counts
                      color=const.CBLIND_COLOR['vermilion'],
                      )

        self.ax0.set_ylabel('Task base frequency, Hz',
                            fontsize='medium', fontweight='bold')
        self.ax0.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))

        self.format_legends()
        self.isplotted[p_label] = True

    def plot_gw_O2(self):
        p_label = 'gw_O2'
        self.ax0.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      const.STYLE['triangle_down'],
                      markersize=const.SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['orange'],
                      alpha=0.4,
                      picker=True,
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df[f'{p_label}_Dcnt'],
                      const.STYLE['square'],
                      markersize=const.DCNT_SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['orange'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_gw_O3(self):
        p_label = 'gw_O3'
        self.ax0.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      const.STYLE['thin_diamond'],
                      markersize=const.SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['sky blue'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df[f'{p_label}_Dcnt'],
                      const.STYLE['square'],
                      markersize=const.DCNT_SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['sky blue'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_brp4(self):
        p_label = 'brp4'
        self.ax0.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      const.STYLE['pentagon'],
                      markersize=const.SIZE,
                      label=p_label,  # 'BRP4 & BRP4G',
                      color=const.CBLIND_COLOR['reddish purple'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df[f'{p_label}_Dcnt'],
                      const.STYLE['square'],
                      markersize=const.DCNT_SIZE,
                      label=p_label,  # 'BRP4 & BRP4G',
                      color=const.CBLIND_COLOR['reddish purple'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_brp7(self):
        p_label = 'brp7'
        self.ax0.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df.elapsed_t.where(self.jobs_df[f'is_{p_label}']),
                      const.STYLE['diamond'],
                      markersize=const.SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['black'],
                      alpha=0.3,
                      picker=True,
                      )
        self.ax1.plot(self.jobs_df[self.time_stamp],
                      self.jobs_df[f'{p_label}_Dcnt'],
                      const.STYLE['square'],
                      markersize=const.DCNT_SIZE,
                      label=p_label,
                      color=const.CBLIND_COLOR['black'],
                      )
        self.format_legends()
        self.isplotted[p_label] = True

    def plot_fgrpHz_X_t(self):
        num_f = self.jobs_df.fgrp_freq.nunique()
        min_f = self.jobs_df.fgrp_freq.min()
        max_f = self.jobs_df.fgrp_freq.max()
        min_t = self.jobs_df.elapsed_sec[self.jobs_df.is_fgrp].min().astype(int64)
        max_t = self.jobs_df.elapsed_sec[self.jobs_df.is_fgrp].max().astype(int64)
        # Add a 2% margin to time axis upper limit.
        self.setup_freq_axes((0, max_t * 1.02))

        self.display_freq_plot_tip()

        # Position text below lower left corner of plot area.
        self.ax0.text(0.0, -0.15,
                      f'Frequencies, N: {num_f}\n'
                      f'Hz, min--max: {min_f}--{max_f}\n'
                      f'Time, min--max: {min_t}--{max_t}',
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax0.transAxes,
                      bbox=self.text_bbox,
                      )

        self.ax0.plot(self.jobs_df.elapsed_sec.where(self.jobs_df.is_fgrp),
                      self.jobs_df.fgrp_freq,
                      const.STYLE['tri_right'],
                      markersize=const.SIZE,
                      color=const.CBLIND_COLOR['vermilion'],
                      alpha=0.3,
                      picker=True,
                      )

        self.isplotted['fgrpHz_X_t'] = True

    def plot_gwO3Hz_X_t(self):
        num_f = self.jobs_df.gwO3AS_freq.nunique()
        min_f = self.jobs_df.gwO3AS_freq.min()
        max_f = self.jobs_df.gwO3AS_freq.max()
        min_t = self.jobs_df.elapsed_sec[self.jobs_df.is_gw_O3].min().astype(int64)
        max_t = self.jobs_df.elapsed_sec[self.jobs_df.is_gw_O3].max().astype(int64)

        # Add a 2% margin to time axis upper limit.
        self.setup_freq_axes((0, max_t * 1.02))

        self.display_freq_plot_tip()

        # Position text below lower left corner of axes.
        self.ax0.text(0.0, -0.15,
                      f'Frequencies, N: {num_f}\n'
                      f'Hz, min--max: {min_f}--{max_f}\n'
                      f'Time, min--max: {min_t}--{max_t}',
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax0.transAxes,
                      bbox=self.text_bbox,
                      )

        self.ax0.plot(self.jobs_df.elapsed_sec.where(self.jobs_df.is_gw_O3),
                      self.jobs_df.gwO3AS_freq,
                      const.STYLE['triangle_up'],
                      markersize=const.SIZE,
                      color=const.CBLIND_COLOR['sky blue'],
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
        labels_status = dict(zip(const.CHKBOX_LABELS, self.checkbox.get_status()))
        label_is_checked: bool = labels_status[clicked_label]
        num_tasks = sum(self.jobs_df[f'is_{const.CLICKED_PLOT[clicked_label]}'])

        def display_nodata_msg():
            """
            Post a notice if the selected Project data are not available.
            Toggle off (deactivate) the selected label's check box.
            """
            self.fig.text(0.5, 0.51,
                          f'There are no {clicked_label} data to plot.',
                          horizontalalignment='center',
                          verticalalignment='center',
                          transform=self.ax0.transAxes,
                          visible=True,
                          zorder=1)
            self.checkbox.set_active(self.chkbox_label_index[clicked_label])

            # Re-plot (retain) any "exclusive" data that may have been
            #  plotted when a no-data Project label was selected
            #  A weak hack, but it works. The entire method needs work.
            for _l, _s in labels_status.items():
                if _l in const.EXCLUSIVE_PLOTS and _s:
                    self.plot_project[_l]()

            self.fig.canvas.draw_idle()

        # Remove any prior text box from display_nodata_msg().
        if label_is_checked and self.fig.texts:
            self.fig.texts.clear()

        # NOTE: CANNOT have same plot points overlaid; that creates
        #  multiple on_pick_report() calls for the same task info.

        # Exclusive plots can be plotted only by themselves.
        for plot in const.EXCLUSIVE_PLOTS:
            if clicked_label == plot and label_is_checked:
                if num_tasks == 0:
                    display_nodata_msg()
                    return

                # Label was toggled on...
                # Need to uncheck other label_is_checked project labels.
                for lbl in const.CHKBOX_LABELS:
                    if (lbl != clicked_label and
                            (self.isplotted[lbl] or labels_status[lbl])):
                        self.checkbox.set_active(self.chkbox_label_index[lbl])

                self.fig.canvas.draw_idle()
                self.plot_project[clicked_label]()
                return

        # Inclusive plots can be plotted only with (on top of) each another.
        #  So, first, need to remove any current exclusive plot.
        if clicked_label in const.ALL_INCLUSIVE and label_is_checked:
            if num_tasks == 0:
                display_nodata_msg()
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
        for plot in const.EXCLUSIVE_PLOTS:
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
        for proj_label, status in labels_status.items():
            if status and proj_label in const.ALL_INCLUSIVE and not self.isplotted[proj_label]:
                self.plot_project[proj_label]()


def run_checks():
    """Program exits here if system platform or Python version check fails."""
    utils.check_platform()
    utils.manage_args()
    vcheck.minversion('3.7')
    vcheck.maxversion('3.12')


def main():
    """Main program entry point."""

    # Comment out if using PyInstaller to create an executable.
    #  PyInstaller for Windows will still need to run check_platform()
    #   for DPI Awareness scaling issues.
    run_checks()

    # Need an image to replace blank tk desktop icon.
    utils.set_icon(canvas_window)

    print(f'Data from {DATA_PATH} are loading. This may take a few seconds...\n')

    # This call will set up an inherited pd dataframe in TaskDataFrame,
    #  then plot 'all' tasks as specified in setup_plot_manager().
    #  After that, plots are managed by CheckButton states in manage_plots().
    PlotTasks().setup_widgets()

    print('The plot window is ready.')

    # Allow user to quit from the Terminal command line using Ctrl-C
    #  without the delay of waiting for tk event actions.
    # Source: https://stackoverflow.com/questions/39840815/
    #   exiting-a-tkinter-app-with-ctrl-c-and-catching-sigint
    # Keep polling the mainloop to check for the SIGINT signal, Ctrl-C.
    # Can comment out the following statements when using PyInstaller.
    signal(signalnum=SIGINT, handler=lambda x, y: utils.quit_gui(canvas_window))

    def tk_check(msec):
        canvas_window.after(msec, tk_check, msec)

    poll_ms = 500
    canvas_window.after(poll_ms, tk_check, poll_ms)


if __name__ == '__main__':
    # Need to use a tkinter window for the plot canvas so that CheckButton
    #  actions for plot filtering are more responsive.
    canvas_window = tk.Tk()
    main()
    canvas_window.mainloop()
