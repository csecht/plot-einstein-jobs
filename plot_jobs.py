#!/usr/bin/env python3
"""plot_jobs.py uses Matplotlib to draw plots from data in Einstein@Home
BOINC client job log files. Task times vs datetime, task counts/day vs.
datetime, and task frequency (Hz) vs. task time (sec) can be plotted for
various E@H Projects recorded in a job log. A job log file can store
records of reported tasks for up to about three years of full-time work.

NOTE: Depending on your system, there may be a slight lag when switching
      between plots. Be patient and avoid the urge to click on things
      to speed it up. For the typical job log, hundreds of thousands to
      millions of data points can be plotted.

Using the navigation bar, plots can be zoomed-in, panned, restored to
previous views, and copied to PNG files.
When no navigation bar buttons are active, clicking on a cluster or
single data point shows details of tasks near the click coordinates.

The "Job log counts" button shows summary counts of all tasks, by Project.

The job_log_einstein.phys.uwm.edu.txt file is normally read from its
default BOINC location. If you have changed the default location, or
want to plot data from an archived job_log file, then enter a custom
full file path in the provided plot_cfg.txt file.

Requires Python3.7 or later, Matplotlib, Pandas, and Numpy.
Developed in Python 3.8-3.9.
"""
# Copyright (C) 2022 C.S. Echt, under GNU General Public License

# Standard library imports
import argparse
import sys

# Local application imports
import plot_utils
from plot_utils import path_check, markers as mark, project_groups as grp

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
    print('One or more of the required Python packages were not found:\n'
          'Matplotlib, Numpy, Pandas, Pillow, tkinter.\n'
          'To install: from the current folder, run this command\n'
          'pip install -r requirements.txt\n'
          'Alternative command formats (system dependent):\n'
          '   python -m pip install -r requirements.txt\n'
          '   python3 -m pip install -r requirements.txt\n'
          '   py -m pip install -r requirements.txt\n'
          'On Linux, if tkinter is the problem, then you may need:\n'
          '   sudo apt-get install python3-tk\n'
          '   See also: https://tkdocs.com/tutorial/install.html \n'
          f'Error msg: {import_err}')
    sys.exit(1)


def manage_args() -> bool:
    """Allow handling of command line arguments.

    :return: True if --_test argument used (default: False).
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('--about',
                        help='Provide description, version, GNU license',
                        action='store_true',
                        default=False)
    parser.add_argument('--test',
                        help='Plot _test data instead of your job_log data.',
                        action='store_true',
                        default=False,
                        )

    args = parser.parse_args()

    if args.about:
        print(__doc__)
        print('Author:', plot_utils.__author__)
        print('Version:', plot_utils.__version__)
        print('Status:', plot_utils.__dev_status__)
        print('URL', plot_utils.URL)
        print(plot_utils.__copyright__)
        print(plot_utils.LICENSE)
        sys.exit(0)

    return args.test


def quit_gui(keybind=None) -> None:
    """
    Error-free and informative exit from the program.
    Called from widget or keybindings.
    Explicitly closes all Matplotlib objects and their parent tk window
    when the user closes the plot window with the system's built-in
    close window icon ("X") or key command. This is required to cleanly
    exit and close the tk thread running Matplotlib.

    :param keybind: Implicit event passed from bind().
    """

    print('\n*** User quit the program. ***\n')

    # pylint: disable=broad-except
    try:
        plt.close('all')
        canvas_window.update_idletasks()
        canvas_window.after(200)
        canvas_window.destroy()
    except Exception as err:
        print(f'An error occurred: {err}')
        sys.exit('Program exit with unexpected condition.')

    return keybind


class TaskDataFrame:
    """
    Set up the DataFrame used for plotting.
    Is called only as an inherited Class from PlotTasks.
    Methods: setup_df, count_log_projects
    """

    # https://stackoverflow.com/questions/472000/usage-of-slots
    # https://towardsdatascience.com/understand-slots-in-python-e3081ef5196d
    __slots__ = ('tasks_df', 'proj_totals', 'proj_daily_means',
                 'proj_days', 'total_jobs')

    def __init__(self):
        self.tasks_df = pd.DataFrame()

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

        :return: None
        """

        # job_log_einstein.phys.uwm.edu.txt, structure of records:
        # 1654865994 ue 916.720025 ct 340.770200 fe 144000000000000 nm h1_0681.20_O3aC01Cl1In0__O3AS1a_681.50Hz_19188_1 et 1283.553196 es 0

        # To include all numerical data in space-delimited job_log, use this:
        # joblog_col_index = 0, 2, 4, 6, 8, 10  # All reported data
        # headers = ('time_stamp', 'est_sec', 'cpu_sec', 'est_flops', 'task_name', 'task_t')
        # time_col = ('time_stamp', 'est_sec', 'cpu_sec', 'task_t')
        # Job log data of current interest:
        joblog_col_index = 0, 8, 10
        _headers = ('time_stamp', 'task_name', 'task_t')

        # The datapath path is defined in if __name__ == "__main__".
        self.tasks_df = pd.read_table(datapath,
                                      sep=' ',
                                      header=None,
                                      usecols=joblog_col_index,
                                      names=_headers,
                                      )

        # Developer note: Can check for presence NaN values with:
        # print('Any null values?', self.tasks_df.isnull().values.any())  # -> True
        # print("Sum of null timestamps:", self.tasks_df['time_stamp'].isnull().sum())
        # print("Sum of ALL nulls:", self.tasks_df.isnull().sum()).sum())
        # Need to replace NaN values with usable data.
        #   Assumes read_table of job_log file will produce NaN ONLY for timestamp.
        self.tasks_df.time_stamp.interpolate(inplace=True)

        # Need to retain original elapsed time as integer seconds for
        #   plotting frequency data:
        self.tasks_df['task_sec'] = self.tasks_df.task_t.astype(int)

        #  Need to convert times to datetimes for efficient plotting.
        time_colmn = ('time_stamp', 'task_t')
        for col in time_colmn:
            self.tasks_df[col] = pd.to_datetime(self.tasks_df[col],
                                                unit='s',
                                                infer_datetime_format=True)

        # Zero data columns are used to visually clear plots in reset_plots().
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
            self.tasks_df.task_name.str.startswith('LATeah'), True, False)
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
    data from the inherited DataFrame.
    The plotted Pandas dataframe is inherited from TaskDataFrame.
    Methods: setup_window, setup_title, setup_buttons, setup_plot_manager,
        on_pick, format_legends, toggle_legends, joblog_report,
        setup_count_axes, setup_freq_axes, reset_plots, plot_all,
        plot_gw_O2, plot_gw_O3, plot_fgrp5, plot_fgrpG1, plot_brp4
        plot_gw_series, plot_fgrpG1_freq, plot_gw_O3_freq, manage_plots.
    """

    # https://stackoverflow.com/questions/472000/usage-of-slots
    # https://towardsdatascience.com/understand-slots-in-python-e3081ef5196d
    __slots__ = (  # Module function attributes
        'import_err', 'manage_args', 'quit_qui',
        # __main__ attributes
        'do_test', 'datapath', 'img', 'canvas_window',
        # Instance attributes
        '_test',
        'marker_size', 'marker_scale', 'dcnt_size', 'pick_radius',
        'light_gray', 'dark_gray',
        'fig', 'ax1', 'ax2',
        'checkbox', 'do_replot', 'legend_btn_on', 'plot_proj',
        'chkbox_labelid', 'isplotted', 'freq_bbox', 'ax_slider',
    )

    def __init__(self, _test):
        super().__init__()

        # The _test parameter is set from an invocation argument.
        self._test = _test

        self.marker_size = 4
        self.marker_scale = 1
        self.dcnt_size = 2
        self.pick_radius = 6

        # Matplotlib does not recognize tkinter X11 color names.
        self.light_gray = '#cccccc'  # '#d9d9d9' X11 gray85; '#cccccc' X11 gray80
        self.dark_gray = '#404040'  # '#404040' X11 gray25, '#333333' X11 gray20, '#4d4d4d' X11 gray30

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

        self.freq_bbox = dict(facecolor='white',
                              edgecolor='grey',
                              boxstyle='round',
                              )

        self.fig, (self.ax1, self.ax2) = plt.subplots(
            2,
            sharex='all',
            gridspec_kw={'height_ratios': [3, 1],
                         'left': 0.15,
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

        self.setup_window()
        self.setup_title()
        self.setup_buttons()
        self.setup_count_axes()

    def setup_window(self):
        """
        A tkinter window for the figure canvas that makes the
        CheckButton checkbox actions for plotting more responsive.
        """
        canvas_window.title('Plotting E@H tasks')
        canvas_window.minsize(850, 550)
        canvas_window.rowconfigure(0, weight=1)
        canvas_window.columnconfigure(0, weight=1)
        canvas_window.configure(bg='green')
        canvas_window.protocol('WM_DELETE_WINDOW', quit_gui)

        canvas_window.bind_all('<Escape>', quit_gui)
        canvas_window.bind('<Control-q>', quit_gui)

        canvas = backend.FigureCanvasTkAgg(self.fig, master=canvas_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

        toolbar = backend.NavigationToolbar2Tk(canvas, canvas_window)

        # Need to remove the subplots navigation button.
        # Source: https://stackoverflow.com/questions/59155873/
        #   how-to-remove-toolbar-button-from-navigationtoolbar2tk-figurecanvastkagg
        if sys.platform in 'linux, darwin':
            toolbar.children['!button4'].pack_forget()
        else:  # is Windows
            toolbar.children['!button6'].pack_forget()

        toolbar.update()

    def setup_title(self):
        """
        Specify in the Figure title which data are plotted, those from the
        sample data file, plot_utils.testdata.txt, or the user's job log
        file. Called from if __name__ == "__main__".
        self._test is inherited from TaskDataFrame(do_test) as boolean
        via call from if __name__ == "__main__".

        :return: None
        """
        if self._test:
            _title = 'Sample data'
        else:
            _title = 'E@H job_log data'

        self.fig.suptitle(_title,
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
                      color=self.light_gray,
                      hovercolor=mark.CBLIND_COLOR['orange'],
                      )
        lbtn.on_clicked(self.toggle_legends)

        # Dummy reference, per documentation: "For the buttons to remain
        #   responsive you must keep a reference to this object."
        ax_legendbtn._button = lbtn

        # Position log tally button to bottom right.
        ax_statsbtn = plt.axes((0.9, 0.09, 0.07, 0.08))
        sbtn = Button(ax_statsbtn,
                      'Job log\ncounts',
                      color=self.light_gray,
                      hovercolor=mark.CBLIND_COLOR['orange'],
                      )
        sbtn.on_clicked(self.joblog_report)
        ax_statsbtn._button = sbtn

        # Position About button to bottom right corner.
        ax_aboutbtn = plt.axes((0.9, 0.01, 0.07, 0.06))
        abtn = Button(ax_aboutbtn,
                      'About',
                      color='white',
                      hovercolor=mark.CBLIND_COLOR['sky blue'],
                      )

        def about(event):
            print('_____ ABOUT START _____')
            print(__doc__)
            print('Version:', plot_utils.__version__)
            print('Author:', plot_utils.__author__)
            print('URL:', plot_utils.URL)
            print(plot_utils.__copyright__)
            print(plot_utils.LICENSE)
            print('_____ ABOUT END _____')
            return event

        abtn.on_clicked(about)
        ax_aboutbtn._button = abtn

    def setup_slider(self, max_f: float):
        """
        Create a RangeSlider for real-time y-axis Hz range adjustments
        of *_freq plots.

        :param max_f: The plotted Project's maximum frequency value.
        """

        # Need to replace any prior slider bar with a new one to prevent
        #   stacking of bars.
        self.ax_slider.remove()

        # Add a 2% margin to the slider upper limit when frequency data are available.
        # When there are no plot data max_f will be NaA, so _test if Nan to
        #   avoid a ValueError for RangeSlider range when max_f is NaN.
        # https://towardsdatascience.com/5-methods-to-check-for-nan-values-in-in-python-3f21ddd17eed
        if max_f != max_f:
            max_limit = 1
        else:
            max_limit = max_f + max_f * 0.02

        # RangeSlider Coord: (LEFT, BOTTOM, WIDTH, HEIGHT).
        # self.ax_slider = plt.axes((0.11, 0.15, 0.60, 0.02)) # horiz
        self.ax_slider = plt.axes((0.05, 0.38, 0.01, 0.52))  # vert

        # Invert min/max values on vertical slider so max is on top.
        self.ax1.invert_yaxis()

        hz_slider = RangeSlider(self.ax_slider, "Hz range",
                                0, max_limit,
                                (0, max_limit),
                                valstep=2,
                                orientation='vertical',
                                color=mark.CBLIND_COLOR['yellow'],
                                handle_style={'size': 8,
                                              'facecolor': self.dark_gray,
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
                      bbox=self.freq_bbox,
                      )

        # Dummy reference, per documentation: "For the slider to remain
        #  responsive you must keep a reference to this object."
        self.ax_slider._slider = hz_slider

        def _update(val):
            """
            Live update of the plot's y-axis frequency range.

            :param val: Value implicitly passed to a callback by the
             RangeSlider as a tuple, (min, max).
            """

            self.ax1.set_ylim(val)

            self.fig.canvas.draw_idle()

        hz_slider.on_changed(_update)

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
        ax_chkbox = plt.axes((0.86, 0.6, 0.13, 0.3), facecolor=self.dark_gray)
        ax_chkbox.set_xlabel('Plots', fontsize='medium', fontweight='bold')
        ax_chkbox.xaxis.set_label_position('top')

        # Need check boxes to control which data to plot.
        # At startup, activate checkbox label 'all' so that all tasks
        #  are plotted by default via manage_plots().
        self.checkbox = CheckButtons(ax_chkbox, grp.CHKBOX_LABELS)
        for label in self.checkbox.labels:
            label.set_color('white')
            label.set_size(8)
        for _r in self.checkbox.rectangles:
            _r.set_width(0.08)
            _r.set_edgecolor(self.light_gray)
        for line in self.checkbox.lines:
            for artist in line:
                artist.set_linewidth(4)
                artist.set_color('yellow')

        self.checkbox.on_clicked(self.manage_plots)
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

        report_title = ('Tasks near selected point, up to 6:\n'
                        '      Date | name | completion time')

        _n = len(event.ind)  # VertexSelector(line), in lines.py
        if not _n:
            print('event.ind is undefined')
            return event

        limit = 6  # Limit tasks, from total in self.pick_radius

        task_info_list = [report_title]
        for dataidx in event.ind:
            if limit > 0:
                task_info_list.append(
                    f'{self.tasks_df.loc[dataidx].time_stamp.date()} | '
                    f'{self.tasks_df.loc[dataidx].task_name} | '
                    f'{self.tasks_df.loc[dataidx].task_t.time()}')
            limit -= 1

        _report = '\n\n'.join(map(str, task_info_list))

        # Display task info in Terminal and pop-up window.
        print('\n'.join(map(str, task_info_list)))

        # Make new window with text box; one window made for each click.
        taskwin = tk.Toplevel()
        taskwin.title('Task info')
        taskwin.minsize(600, 300)
        # taskwin.attributes('-topmost', True)

        max_line = len(max(_report.splitlines(), key=len))
        num_lines = _report.count('\n')

        tasktxt = tk.Text(taskwin, font='TkFixedFont',
                          width=max_line, height=num_lines,
                          bg=self.dark_gray, fg='white',
                          relief='groove', bd=4,
                          padx=15, pady=10,
                          )
        tasktxt.insert(1.0, _report)
        tasktxt.pack(fill=tk.BOTH, expand=True,
                     padx=5, pady=5,
                     )

        return event

    def format_legends(self):
        self.ax1.legend(fontsize='x-small', ncol=2,
                        loc='upper right',
                        markerscale=self.marker_scale,
                        edgecolor='black',
                        framealpha=0.5,
                        )
        self.ax2.legend(fontsize='x-small', ncol=2,
                        loc='upper right',
                        markerscale=self.marker_scale,
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

        report_title = 'Summary of tasks counts in...'

        data_file = path_check.set_datapath(do_test)

        _results = tuple(zip(
            grp.PROJ_TO_REPORT, self.proj_totals, self.proj_daily_means, self.proj_days))
        num_days = len(pd.to_datetime(self.tasks_df.time_stamp).dt.date.unique())

        _report = (f'{data_file}\n\n'
                   f'Total tasks in file: {self.total_jobs}\n'
                   f'Counts for the past {num_days} days:\n\n'
                   f'{"Project".ljust(6)} {"Total".rjust(10)}'
                   f' {"per Day".rjust(9)} {"Days".rjust(8)}\n'
                   )
        for proj_tup in _results:
            _proj, p_tot, p_dmean, p_days = proj_tup
            _report = _report + (f'{_proj.ljust(6)} {str(p_tot).rjust(10)}'
                                 f' {str(p_dmean).rjust(9)} {str(p_days).rjust(8)}\n'
                                 )

        # Print to terminal to give user the option to cut-and-paste.
        print(report_title, _report)

        # Make new window with text box; one window made for each click.
        statswin = tk.Toplevel()
        statswin.title(report_title)
        statswin.minsize(400, 220)
        # statswin.attributes('-topmost', True)

        max_line = len(max(_report.splitlines(), key=len))
        num_lines = _report.count('\n')

        statstxt = tk.Text(statswin, font='TkFixedFont',
                           width=max_line, height=num_lines,
                           bg=self.dark_gray, fg='white',
                           relief='groove', bd=4,
                           padx=15, pady=10,
                           )
        statstxt.insert(1.0, _report)
        statstxt.pack(fill=tk.BOTH, expand=True,
                      padx=5, pady=5,
                      )

        return event

    def setup_count_axes(self):
        """
        Used to set initial axes and rebuild axes components when plots
        and axes are cleared by reset_plots().
        """

        # self.ax1.xaxis.axis_date()  # No effect?
        # self.ax1.yaxis.axis_date()

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

        # When data are not available for a plot, the t_limit tuple
        #  will be (0, nan) and set_xlim() will raise
        #    ValueError: Axis limits cannot be NaN or Inf
        try:
            self.ax1.set_xlim(t_limits)
        except ValueError:
            pass

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

    def plot_gw_O2(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.task_t.where(self.tasks_df.is_gw_O2),
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
                      self.tasks_df.task_t.where(self.tasks_df.is_gw_O3),
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

    def plot_fgrp5(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.task_t.where(self.tasks_df.is_fgrp5),
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
                      self.tasks_df.task_t.where(self.tasks_df.is_fgrpG1),
                      mark.MARKER_STYLE['tri_right'],
                      markersize=self.marker_size,
                      label='FGRBPG1',
                      color=mark.CBLIND_COLOR['vermilion'],
                      alpha=0.3,
                      picker=self.pick_radius,
                      )
        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.fgrpG1_Dcnt,
                      mark.MARKER_STYLE['square'],
                      markersize=self.dcnt_size,
                      label='FGRBPG1',
                      color=mark.CBLIND_COLOR['vermilion'],
                      )
        self.format_legends()
        self.isplotted['fgrpG1'] = True

    def plot_brp4(self):
        self.ax1.plot(self.tasks_df.time_stamp,
                      self.tasks_df.task_t.where(self.tasks_df.is_brp4),
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

    def plot_gw_series(self):
        for subproj in grp.GW_SERIES:
            is_subproj = f'is_{subproj}'

            self.ax1.plot(self.tasks_df.time_stamp,
                          self.tasks_df.task_t.where(self.tasks_df[is_subproj]),
                          mark.next_marker(),
                          label=subproj,
                          markersize=self.marker_size,
                          alpha=0.3,
                          picker=True,
                          pickradius=self.pick_radius,
                          )

        self.ax2.plot(self.tasks_df.time_stamp,
                      self.tasks_df.gw_Dcnt,
                      mark.MARKER_STYLE['square'],
                      label='All GW',
                      markersize=self.dcnt_size,
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

        # Position text below lower left corner of plot area.
        self.ax1.text(0.0, -0.15,
                      f'Frequencies, N: {num_freq}\n'
                      f'Hz, min--max: {min_f}--{max_f}\n'
                      f'Time, min--max: {min_t}--{max_t}',
                      style='italic',
                      fontsize=6,
                      verticalalignment='top',
                      transform=self.ax1.transAxes,
                      bbox=self.freq_bbox,
                      )

        self.ax1.plot(self.tasks_df.task_sec.where(self.tasks_df.is_fgrpG1),
                      self.tasks_df.fgrpG1_freq,
                      mark.MARKER_STYLE['point'],
                      markersize=self.marker_size,
                      color=mark.CBLIND_COLOR['blue'],
                      alpha=0.3,
                      picker=self.pick_radius,
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
                      bbox=self.freq_bbox,
                      )

        # NOTE that there is not a separate df column for O3 freq.
        self.ax1.plot(self.tasks_df.task_sec.where(self.tasks_df.is_gw_O3),
                      self.tasks_df.gw_freq.where(self.tasks_df.is_gw_O3),
                      mark.MARKER_STYLE['point'],
                      markersize=self.marker_size,
                      color=mark.CBLIND_COLOR['blue'],
                      alpha=0.3,
                      picker=self.pick_radius,
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

        elif not ischecked[clicked_label]:

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

        elif not ischecked[clicked_label]:

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

    # System platform and version checks are run in plot_utils __init__.py
    #   Program exits if checks fail.

    do_test = manage_args()  # Function returns boolean.

    if not do_test:
        datapath = path_check.set_datapath()
    else:
        datapath = path_check.set_datapath('do test')

    print(f'Data from {datapath} are loading. This may take a few seconds...')

    # Need to use a tkinter window for the plot canvas so that the
    #   CheckButton actions for plot management are more responsive.
    canvas_window = tk.Tk()

    # This call will set up an inherited pd dataframe in TaskDataFrame,
    #  then plot 'all' tasks as specified in setup_plot_manager().
    #  After that, plots are managed by CheckButton states in manage_plots().
    PlotTasks(do_test).setup_plot_manager()

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
