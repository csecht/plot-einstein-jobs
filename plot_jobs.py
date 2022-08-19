#!/usr/bin/env python3
"""plot_jobs.py uses Matplotlib to draw plots from data in Einstein@Home
BOINC client job log files.

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

# Local application imports
from plot_utils import (path_check, reports, utils,
                        markers as mark,
                        project_groups as grp)

# Third party imports (tk may not be included with some Python installations).
try:
    import matplotlib.backends.backend_tkagg as backend
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import matplotlib.style as mplstyle
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


class TaskDataFrame:
    """
    Set up the DataFrame used for plotting.
    Is called only as an inherited Class from PlotTasks.
    Methods:
         setup_df - Set up main dataframe from an E@H job_log text file.
         manage_bad_times - Interpolate missing time data.
         add_proj_id - Add columns of boolean flags for Project ID.
         add_frequencies - Add task base (parent) search frequencies.
         add_daily_counts - Add daily counts for each Project.
    """

    def __init__(self):
        self.tasks_df = pd.DataFrame()

        self.setup_df()
        self.add_proj_id()
        self.add_frequencies()
        self.add_daily_counts()

    def setup_df(self):
        """
        Set up the Pandas DataFrame of task data read from an E@H job_log
        text file.

        :return: None
        """

        # job_log_einstein.phys.uwm.edu.txt, structure of records:
        # 1654865994 ue 916.720025 ct 340.770200 fe 144000000000000 nm h1_0681.20_O3aC01Cl1In0__O3AS1a_681.50Hz_19188_1 et 1283.553196 es 0

        # To include all numerical data in space-delimited job_log, use this:
        # joblog_col_index = 0, 2, 4, 6, 8, 10  # All reported data
        # names = ('time_stamp', 'est_sec', 'cpu_sec', 'est_flops', 'task_name', 'elapsed_t')
        # time_names = ('time_stamp', 'est_sec', 'cpu_sec', 'elapsed_t')

        # Job log data of current interest:
        joblog_col_index = 0, 8, 10
        names = ('time_stamp', 'task_name', 'elapsed_t')

        # The datapath path is defined in if __name__ == "__main__".
        self.tasks_df = pd.read_table(data_path,
                                      engine='c',
                                      delim_whitespace=True,
                                      header=None,
                                      usecols=joblog_col_index,
                                      names=names,
                                      )

        # Need to replace NaN time data with interpolated time values.
        self.manage_bad_times()

        # Need to retain original elapsed time as seconds to plot Hz x time:
        self.tasks_df['elapsed_sec'] = self.tasks_df.elapsed_t

        #  Need to convert time seconds (int or float) to datetimes for
        #    plot axis tick readability.
        time_colmn = ('time_stamp', 'elapsed_t')
        for col in time_colmn:
            self.tasks_df[col] = pd.to_datetime(self.tasks_df[col],
                                                unit='s',
                                                infer_datetime_format=True)

        # Zero data columns are used to visually clear plots in reset_plots().
        self.tasks_df['null_time'] = pd.to_datetime(0.0, unit='s')
        self.tasks_df['null_Dcnt'] = 0.0

    def manage_bad_times(self) -> None:
        """
        Report and interpolate timestamp and elapsed time values that are
        interpreted from file as NaN.

        :return: None
        """
        # NOTE: If no times are NaN, then column dtype is numpy.int64,
        #   but if any NaN present, then column dtype is numpy.float64.
        ts_nan_sum = self.tasks_df.time_stamp.isna().sum()
        et_nan_sum = self.tasks_df.elapsed_t.isna().sum()
        time_and_nansum = (('time_stamp', ts_nan_sum),
                           ('elapsed_t', et_nan_sum))

        for tup in time_and_nansum:
            if tup[1] > 0:
                list_missing = self.tasks_df[self.tasks_df['time_stamp'].isna()]
                self.tasks_df.time_stamp.interpolate(
                    method='linear', inplace=True)
                print(f'*** Heads up: {tup[1]} {tup[0]} values could not'
                      ' be read from the file and have been interpolated. ***\n'
                      f'Tasks with "bad" times in the file:\nrow #\n{list_missing}')

    def add_proj_id(self):
        """
        Add columns that boolean flag each task's associated Project.
        """

        self.tasks_df['is_all'] = True
        for _proj, _regex in grp.PROJ_NAME_REGEX.items():
            is_proj = f'is_{_proj}'
            self.tasks_df[is_proj] = where(
                self.tasks_df.task_name.str.contains(_regex), True, False)

    def add_frequencies(self):
        """
        Add columns of search frequencies, parsed from the task name.
        Regex for base frequency will match these task name structures:
        FGRP task: 'LATeah4013L03_988.0_0_0.0_9010205_1'
        GW task: 'h1_0681.20_O3aC01Cl1In0__O3AS1a_681.50Hz_19188_1'
        """
        regex_fgrp_freq = r'LATeah.*?_(\d+)'
        # pattern_gw_freq = r'h1.*_(\d+\.\d{2})Hz_'  # Capture highest freq, not base freq.
        regex_gwo3_freq = r'h1_(\d+\.\d+)_.+__O3'  # Capture the base/parent freq.
        self.tasks_df['fgrp_freq'] = (self.tasks_df.task_name
                                      .str.extract(regex_fgrp_freq).astype('float64'))
        self.tasks_df['gwO3_freq'] = (self.tasks_df.task_name
                                      .str.extract(regex_gwo3_freq).astype('float64'))

    def add_daily_counts(self):
        """
        Add columns of daily reported task counts for each E@H Project.
        """

        #  Idea to tally using groupby and transform, source:
        #         https://stackoverflow.com/questions/17709270/
        #           create-column-of-value-counts-in-pandas-dataframe

        # For clarity, PROJECTS names used here need to match those used
        #   in isplotted (dict) and chkbox_labels (tuple).
        for _proj in grp.PROJECTS:
            self.tasks_df[f'{_proj}_Dcnt'] = (
                self.tasks_df.time_stamp
                    .groupby(self.tasks_df.time_stamp.dt.floor('D')
                             .where(self.tasks_df[f'is_{_proj}']))
                    .transform('count')
            )


class PlotTasks(TaskDataFrame):
    """
    Set up and display Matplotlib Figure and pyplot Plots of task (job)
    data.
    The plotted Pandas dataframe is inherited from TaskDataFrame.
    Called only from if __name__ == "__main__".
    Methods: setup_window, setup_title, setup_buttons, setup_slider,
        setup_plot_manager, format_legends, toggle_legends, on_pick_report,
        joblog_report, about_report, setup_count_axes, setup_freq_axes,
        reset_plots, plot_all, plot_gw_O2, plot_gw_O3, plot_fgrp5,
        plot_fgrpG1, plot_brp4, plot_gw_series, plot_fgrpHz_X_t,
        plot_gwO3Hz_X_t, manage_plots.
    """

    # https://stackoverflow.com/questions/472000/usage-of-slots
    # https://towardsdatascience.com/understand-slots-in-python-e3081ef5196d
    __slots__ = (
        'marker_size', 'marker_scale', 'dcnt_size', 'pick_radius',
        'fig', 'ax1', 'ax2',
        'checkbox', 'do_replot', 'legend_btn_on', 'plot_proj',
        'chkbox_labelid', 'isplotted', 'text_bbox', 'ax_slider',
    )

    def __init__(self):
        super().__init__()

        self.marker_size = 4
        self.marker_scale = 1
        self.dcnt_size = 2
        self.pick_radius = 6

        self.checkbox = None
        self.do_replot = False
        self.legend_btn_on = True

        # These keys must match CHKBOX_LABELS in project_groups.py.
        # Dictionary pairs plot name to plot method.
        self.plot_proj = {
            'all': self.plot_all,
            'fgrp5': self.plot_fgrp5,
            'fgrpG1': self.plot_fgrpG1,
            'fgrp_hz': self.plot_fgrp_hz,
            'gw_O3': self.plot_gw_O3,
            'gw_O2': self.plot_gw_O2,
            'brp4': self.plot_brp4,
            'brp7': self.plot_brp7,
            'gwO3Hz_X_t': self.plot_gwO3Hz_X_t,
            'fgrpHz_X_t': self.plot_fgrpHz_X_t,
        }

        self.chkbox_labelid = {}
        self.isplotted = {}

        # Establish the style for text fancy boxes.
        self.text_bbox = dict(facecolor='white',
                              edgecolor='grey',
                              boxstyle='round4',
                              pad=0.7,
                              )

        # Make the Figure and Axes objects; establish geometry of axes.
        self.fig, (self.ax1, self.ax2) = plt.subplots(
            2,
            sharex='all',
            gridspec_kw={'height_ratios': [3, 1],
                         'left': 0.15,
                         'right': 0.85,
                         'bottom': 0.16,
                         'top': 0.92,
                         'hspace': 0.15,
                         },
        )

        mplstyle.use(('seaborn-colorblind', 'fast'))

        # Need to have mpl_connect statement before any autoscale statements AND
        #  need to have ax.autoscale() set for picker radius to work.
        self.fig.canvas.mpl_connect(
            'pick_event', lambda _: reports.on_pick_report(_, self.tasks_df))

        # Slider used in *_Hz plots to set Hz ranges; initialize here
        #  so that it can be removed/redrawn with each *_Hz plot call
        #  and hidden for all other plots.
        self.ax_slider = plt.axes()

        self.setup_window()
        self.setup_buttons()
        self.setup_count_axes()

    def setup_window(self) -> None:
        """
        A tkinter window for the figure canvas: makes the CheckButton
        actions for drawing plots more responsive.
        """

        # test_arg is boolean, defined in if __name__ == "__main__" from
        #   the --test invocation argument (default: False).
        if test_arg:
            _title = 'Sample data'
        else:
            _title = 'E@H job_log data'

        # canvas_window is the Tk object defined in if __name__ == "__main__".
        canvas_window.title(_title)
        canvas_window.minsize(850, 550)

        # Allow full resizing of plot, but only horizontally for toolbar.
        canvas_window.rowconfigure(0, weight=1)
        canvas_window.columnconfigure(0, weight=1)
        canvas_window.configure(bg=mark.CBLIND_COLOR['blue'])
        canvas_window.protocol('WM_DELETE_WINDOW', lambda: utils.quit_gui(canvas_window))
        canvas_window.bind_all('<Escape>', lambda _: utils.quit_gui(canvas_window))
        canvas_window.bind('<Control-q>', lambda _: utils.quit_gui(canvas_window))

        canvas = backend.FigureCanvasTkAgg(self.fig, master=canvas_window)

        toolbar = backend.NavigationToolbar2Tk(canvas, canvas_window)

        # Need to remove the subplots navigation button.
        # Source: https://stackoverflow.com/questions/59155873/
        #   how-to-remove-toolbar-button-from-navigationtoolbar2tk-figurecanvastkagg
        toolbar.children['!button4'].pack_forget()

        # Now display all widgets.
        # NOTE: toolbar must be gridded before canvas to prevent
        #   FigureCanvasTkAgg from preempting window geometry with pack().
        toolbar.grid(row=1, column=0,
                     padx=5, pady=(0, 5),  # Put a border around toolbar.
                     sticky=tk.NSEW,
                     )
        canvas.get_tk_widget().grid(row=0, column=0,
                                    ipady=10, ipadx=10,
                                    padx=5, pady=5,  # Put a border around plot.
                                    sticky=tk.NSEW,
                                    )
        # Because macOS tool icon images won't render properly,
        #   need to provide text descriptions of tool button functions.
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
        sbtn.on_clicked(lambda _: reports.joblog_report(self.tasks_df))
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
        of *_freq plots.

        :param max_f: The plotted Project's maximum frequency value.
        """

        # Need to replace any prior slider bar with a new one to prevent
        #   stacking of bars.
        self.ax_slider.remove()

        # Add a 2% margin to the slider upper limit when frequency data are available.
        # When there are no plot data, max_f will be NaN, so use some NaN magic
        #   to test that and avoid a ValueError for RangeSlider max range.
        # https://towardsdatascience.com/5-methods-to-check-for-nan-values-in-in-python-3f21ddd17eed
        if max_f != max_f:  # Will be True if max_f is NaN.
            max_limit = 1
        else:
            max_limit = max_f * 1.02

        # RangeSlider Coord: (LEFT, BOTTOM, WIDTH, HEIGHT).
        self.ax_slider = plt.axes((0.05, 0.38, 0.01, 0.52))  # vert

        # Invert min/max values on vertical slider so max is on top.
        plt.gca().invert_yaxis()

        hz_slider = RangeSlider(self.ax_slider, "Hz range",
                                0, max_limit,
                                (0, max_limit),
                                valstep=2,
                                orientation='vertical',
                                color=mark.CBLIND_COLOR['yellow'],
                                handle_style={'size': 8, }
                                )

        # Position text box above Navigation toolbar.
        self.ax1.text(-0.19, -0.6,
                      ("Range slider and Navigation bar tools may conflict.\n"
                       "If so, then toggle the plot's checkbox to reset."),
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax1.transAxes,
                      bbox=self.text_bbox,
                      )
        self.ax_slider._slider = hz_slider  # Prevent garbage collection.

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
            self.chkbox_labelid[proj] = i

        for proj in grp.CHKBOX_LABELS:
            self.isplotted[proj] = False

        # Relative coordinates in Figure, 4-tuple (LEFT, BOTTOM, WIDTH, HEIGHT)
        ax_chkbox = plt.axes((0.86, 0.54, 0.13, 0.36), facecolor=mark.DARK_GRAY)
        ax_chkbox.set_xlabel('Plots',
                             fontsize='medium',
                             fontweight='bold')
        ax_chkbox.xaxis.set_label_position('top')

        # Need check boxes to control which data series to plot.
        # At startup, activate checkbox label 'all' so that all tasks
        #  are plotted by default via manage_plots().
        self.checkbox = CheckButtons(ax_chkbox, grp.CHKBOX_LABELS)
        for label in self.checkbox.labels:
            label.set_color('white')
            label.set_size(8)
        for _r in self.checkbox.rectangles:
            _r.set_width(0.08)
            _r.set_edgecolor(mark.LIGHT_GRAY)
        for line in self.checkbox.lines:
            for artist in line:
                artist.set_linewidth(4)
                artist.set_color('yellow')

        self.checkbox.on_clicked(self.manage_plots)
        self.checkbox.set_active(self.chkbox_labelid['all'])

    def format_legends(self):
        self.ax1.legend(ncol=2,
                        fontsize='x-small',
                        loc='upper right',
                        markerscale=self.marker_scale,
                        edgecolor='black',
                        framealpha=0.5,
                        )
        self.ax2.legend(ncol=2,
                        fontsize='x-small',
                        loc='upper right',
                        markerscale=self.marker_scale,
                        edgecolor='black',
                        framealpha=0.4,
                        )

    def toggle_legends(self, event) -> None:
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

    def setup_count_axes(self):
        """
        Used to set initial axes and rebuild axes components when plots
        and axes are cleared by reset_plots().
        """

        # Need to reset plot axes in case setup_freq_axes() was called.
        self.ax_slider.set_visible(False)
        self.ax2.set_visible(True)
        self.ax1.tick_params('x', labelbottom=False)

        # Default axis margins are 0.05 (5%) of data values.
        self.ax1.margins(0.02, 0.02)
        self.ax2.margins(0.02, 0.05)

        self.ax1.set_ylabel('Task completion time',
                            fontsize='medium',
                            fontweight='bold')
        self.ax2.set_xlabel('Task reporting datetime',
                            fontsize='medium',
                            fontweight='bold')
        self.ax2.set_ylabel('Tasks/day',
                            fontsize='medium',
                            fontweight='bold')

        # Need to set the Tasks/day axis label in a static position.
        self.ax2.yaxis.set_label_coords(-0.1, 0.55)

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

        self.ax2.yaxis.set_major_locator(ticker.MaxNLocator(nbins=6, integer=True))

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
        Called from plot_fgrpHz_X_t() and plot_gwO3Hz_X_t().

        :param t_limits: Constrain x-axis of task times from zero to
            maximum value, plus a small buffer.
        :return: None
        """

        self.ax2.set_visible(False)
        self.ax1.tick_params('x', labelbottom=True)

        # When data are not available for a plot, the t_limit tuple
        #  will be (0, nan) and set_xlim() will raise
        #    ValueError: Axis limits cannot be NaN or Inf
        try:
            self.ax1.set_xlim(t_limits)
        except ValueError:
            pass

        # Need to FIX: the Home tool sets (remembers) axes range of the
        #  first selected freq vs time plot, instead of current
        #  freq vs time plot, but only when the Zoom tool has been used.
        self.ax1.set_xlabel('Task completion time, sec',
                            fontsize='medium', fontweight='bold')

        self.ax1.set_ylabel('Task base frequency, Hz',
                            fontsize='medium', fontweight='bold')

        self.ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
        self.ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))

    def reset_plots(self):
        """
        Clear plots. axis labels, ticks, formats, legends, etc.
        Clears plotted data by setting all data values to zero and removing marks.
        Use to avoid stacking of plots, which affects on_pick_report() display of
        nearby task info. Note that, with this, the full x-axis datetime range
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

    def clicked_plot(self, clicked_label: str) -> None:
        """
        When there are no data to plot for a clicked plot label, post a
        message in the plot area. Called from manage_plots().

        :param clicked_label: The checked checkbox data series label.
        """

        # Need to first clear any prior no-data text message.
        for txt in self.fig.texts:
            txt.set_visible(False)

        # When a project series has no data, its is_<project> df column
        #  has no True values and therefore sums to zero (False).
        #  The CLICKED_PLOT dict pairs grp.CHKBOX_LABELS to grp.PROJECTS strings.
        if not sum(self.tasks_df[f'is_{grp.CLICKED_PLOT[clicked_label]}']):
            self.fig.text(0.5, 0.51,
                          f'There are no {clicked_label} data to plot.',
                          horizontalalignment='center',
                          verticalalignment='center',
                          transform=self.ax1.transAxes)

    def plot_all(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.elapsed_t,
                      mark.MARKER_STYLE['point'],
                      markersize=self.marker_size,
                      label='all',
                      color=mark.CBLIND_COLOR['blue'],
                      alpha=0.2,
                      picker=self.pick_radius,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.all_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.dcnt_size,
                      label='all',
                      color=mark.CBLIND_COLOR['blue'],
                      )
        self.format_legends()
        self.isplotted['all'] = True

    def plot_fgrp5(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.elapsed_t.where(self.tasks_df.is_fgrp5),
                      mark.MARKER_STYLE['tri_left'],
                      markersize=self.marker_size,
                      label='fgrp5',
                      color=mark.CBLIND_COLOR['bluish green'],
                      alpha=0.3,
                      picker=self.pick_radius,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.fgrp5_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.dcnt_size,
                      label='fgrp5',
                      color=mark.CBLIND_COLOR['bluish green'],
                      alpha=0.4,
                      picker=self.pick_radius,
                      )
        self.format_legends()
        self.isplotted['fgrp5'] = True

    def plot_fgrpG1(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.elapsed_t.where(self.tasks_df.is_fgrpG1),
                      mark.MARKER_STYLE['tri_right'],
                      markersize=self.marker_size,
                      label='fgrpG1',
                      color=mark.CBLIND_COLOR['vermilion'],
                      alpha=0.3,
                      picker=self.pick_radius,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.fgrpG1_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.dcnt_size,
                      label='fgrpG1',
                      color=mark.CBLIND_COLOR['vermilion'],
                      )

        self.format_legends()
        self.isplotted['fgrpG1'] = True

    def plot_fgrp_hz(self):
        """
        Plot of frequency (Hz) vs. datetime for all FGRP tasks (5 + G1).
        """

        self.reset_plots()

        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.fgrp_freq,
                      mark.MARKER_STYLE['tri_right'],
                      markersize=self.marker_size,
                      label='fgrp_hz',
                      color=mark.CBLIND_COLOR['vermilion'],
                      alpha=0.3,
                      picker=self.pick_radius,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df[['fgrpG1_Dcnt', 'fgrp5_Dcnt']].sum(axis=1),
                      mark.MARKER_STYLE['square'],
                      markersize=self.dcnt_size,
                      label='fgrp5 & fgrpG1',
                      color=mark.CBLIND_COLOR['vermilion'],
                      )

        self.ax1.set_ylabel('Task base frequency, Hz',
                            fontsize='medium', fontweight='bold')
        self.ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))

        self.format_legends()
        self.isplotted['fgrp_hz'] = True

    def plot_gw_O2(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.elapsed_t.where(self.tasks_df.is_gw_O2),
                      mark.MARKER_STYLE['triangle_down'],
                      markersize=self.marker_size,
                      label='gw_O2MD1',
                      color=mark.CBLIND_COLOR['orange'],
                      alpha=0.4,
                      picker=self.pick_radius,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.gw_O2_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.dcnt_size,
                      label='gw_O2MD1',
                      color=mark.CBLIND_COLOR['orange'],
                      )
        self.format_legends()
        self.isplotted['gw_O2'] = True

    def plot_gw_O3(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.elapsed_t.where(self.tasks_df.is_gw_O3),
                      mark.MARKER_STYLE['triangle_up'],
                      markersize=self.marker_size,
                      label='gw_O3AS',
                      color=mark.CBLIND_COLOR['sky blue'],
                      alpha=0.3,
                      picker=self.pick_radius,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.gw_O3_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.dcnt_size,
                      label='gw_O3AS',
                      color=mark.CBLIND_COLOR['sky blue'],
                      )
        self.format_legends()
        self.isplotted['gw_O3'] = True

    def plot_brp4(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.elapsed_t.where(self.tasks_df.is_brp4),
                      mark.MARKER_STYLE['pentagon'],
                      markersize=self.marker_size,
                      label='BRP4 & BRP4G',
                      color=mark.CBLIND_COLOR['reddish purple'],
                      alpha=0.3,
                      picker=self.pick_radius,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.brp4_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.dcnt_size,
                      label='BRP4 & BRP4G',
                      color=mark.CBLIND_COLOR['reddish purple'],
                      )
        self.format_legends()
        self.isplotted['brp4'] = True

    def plot_brp7(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.elapsed_t.where(self.tasks_df.is_brp7),
                      mark.MARKER_STYLE['diamond'],
                      markersize=self.marker_size,
                      label='BRP7',
                      color=mark.CBLIND_COLOR['yellow'],
                      alpha=0.5,
                      picker=self.pick_radius,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.brp7_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.dcnt_size,
                      label='BRP7',
                      color=mark.CBLIND_COLOR['yellow'],
                      )
        self.format_legends()
        self.isplotted['brp7'] = True

    def plot_fgrpHz_X_t(self):
        num_f = self.tasks_df.fgrp_freq.nunique()
        min_f = self.tasks_df.fgrp_freq.min()
        max_f = self.tasks_df.fgrp_freq.max()
        min_t = self.tasks_df.elapsed_sec.where(
            self.tasks_df.is_fgrp).min().astype('int64')
        max_t = self.tasks_df.elapsed_sec.where(
            self.tasks_df.is_fgrp).max().astype('int64')

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

        self.ax1.plot(self.tasks_df.elapsed_sec.where(self.tasks_df.is_fgrp),
                      self.tasks_df.fgrp_freq,
                      mark.MARKER_STYLE['tri_right'],
                      markersize=self.marker_size,
                      color=mark.CBLIND_COLOR['vermilion'],
                      alpha=0.3,
                      picker=self.pick_radius,
                      )

        self.isplotted['fgrpHz_X_t'] = True

    def plot_gwO3Hz_X_t(self):
        num_f = self.tasks_df.gwO3_freq.nunique()
        min_f = self.tasks_df.gwO3_freq.min()
        max_f = self.tasks_df.gwO3_freq.max()
        min_t = self.tasks_df.elapsed_sec.where(
            self.tasks_df.is_gw_O3).min().astype('int64')
        max_t = self.tasks_df.elapsed_sec.where(
            self.tasks_df.is_gw_O3).max().astype('int64')

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

        # NOTE that there is not a separate df column for O3 freq.
        self.ax1.plot(self.tasks_df.elapsed_sec.where(self.tasks_df.is_gw_O3),
                      self.tasks_df.gwO3_freq,
                      mark.MARKER_STYLE['triangle_up'],
                      markersize=self.marker_size,
                      color=mark.CBLIND_COLOR['sky blue'],
                      alpha=0.3,
                      picker=self.pick_radius,
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

        #  NOTE: CANNOT have same plot points overlaid. That creates
        #    multiple on_pick_report() calls for the same task info.

        # NOTE: with checkbox.eventson = True (default),
        #   all proj button clicks trigger this manage_plots() callback
        #   (all conditions are evaluated with every click).

        # ischecked key is project label, value is True/False check status.
        # Note: ischecked and self.isplotted dictionary values are boolean.
        ischecked = dict(zip(grp.CHKBOX_LABELS, self.checkbox.get_status()))

        # Exclusive plots can only be plotted by themselves.
        for _plot in grp.EXCLUSIVE_PLOTS:
            if clicked_label == _plot and ischecked[clicked_label]:

                # Need to post notice if selected data are not available.
                self.clicked_plot(clicked_label)

                # Was toggled on...
                # Need to uncheck other checked project labels.
                for _l in grp.CHKBOX_LABELS:
                    if _l != clicked_label and (self.isplotted[_l] or ischecked[_l]):
                        self.checkbox.set_active(self.chkbox_labelid[_l])

                self.plot_proj[clicked_label]()

        # Inclusive plots can be plotted with each another.
        if clicked_label in grp.ALL_INCLUSIVE and ischecked[clicked_label]:
            self.clicked_plot(clicked_label)

            for _plot in grp.ALL_EXCLUDED:
                if self.isplotted[_plot] or ischecked[_plot]:
                    self.isplotted[_plot] = False
                    self.checkbox.set_active(self.chkbox_labelid[_plot])
                    self.do_replot = True

            if self.do_replot:
                self.reset_plots()
                self.do_replot = False

            for _proj, status in ischecked.items():
                if status and (_proj in grp.ALL_INCLUSIVE) and not self.isplotted[_proj]:
                    self.plot_proj[_proj]()

        elif not ischecked[clicked_label]:

            # Was toggled off, so remove all plots,
            #   then replot only inclusive checked ones.
            self.reset_plots()
            for _proj, status in ischecked.items():
                if _proj in grp.ALL_INCLUSIVE and status:
                    self.plot_proj[_proj]()
                # if _proj == 'gw_series' and status:
                #     self.plot_gw_series()

        self.fig.canvas.draw_idle()


if __name__ == "__main__":

    # System platform and version checks are run in plot_utils __init__.py
    #   Program exits if checks fail.

    test_arg = utils.manage_args()  # Module returns a boolean.

    if not test_arg:
        data_path = path_check.set_datapath()
    else:
        data_path = path_check.set_datapath(use_test_file=True)

    print(f'Data from {data_path} are loading. This may take a few seconds...')

    # Need to use a tkinter window for the plot canvas so that the
    #   CheckButton actions for plot management are more responsive.
    canvas_window = tk.Tk()

    # This call will set up an inherited pd dataframe in TaskDataFrame,
    #  then plot 'all' tasks as specified in setup_plot_manager().
    #  After that, plots are managed by CheckButton states in manage_plots().
    PlotTasks().setup_plot_manager()

    print('The plot window is ready.')

    # Need an image to replace blank tk desktop icon.
    img = tk.PhotoImage(
        file='images/desktop_icon.png')
    canvas_window.iconphoto(True, img)

    try:
        canvas_window.mainloop()
    except KeyboardInterrupt:
        print('\n*** User quit the program ***\n')
    except Exception as unk:
        print(f'An error occurred: {unk}')
        sys.exit('Program exit with unexpected condition.')
