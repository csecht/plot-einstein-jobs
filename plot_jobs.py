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
      between plots, so be patient and avoid the urge to start clicking
      around to speed things up. For the typical job log, hundreds of
      thousands to millions of data points can be plotted.

Using the navigation bar, plots can be zoomed-in, panned, restored to
previous views, and copied to PNG files.
When no navigation bar buttons are active, clicking on a cluster or
single data point shows task names near the click coordinates.
The "Job lob counts" button shows summary counts of all tasks, by Project.

The default configuration reads the job_log_einstein.phys.uwm.edu.txt
file in its default BOINC location. If you have changed the default
location, or want to plot data from an archived job_logs, then
enter a custom full file path in the provided plot_cfg.txt file.

Requires tkinter (tk/tcl), Python3.7+, Matplotlib, Pandas, and Numpy.
Developed in Python 3.8-3.9.

URL: https://github.com/csecht/plot-einstein-jobs
Development Status :: 1 - Alpha
Version: 0.0.2

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

from plot_utils import path_check, vcheck, platform_check, mpl_markers

mmark = mpl_markers

try:
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    import matplotlib.style as mplstyle
    import pandas as pd
    from matplotlib import ticker
    from matplotlib.font_manager import FontProperties
    from matplotlib.widgets import CheckButtons, Button
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

MARKER_SIZE = 4
MRKR_SCALE = 1
DCNT_SIZE = 2
LIGHT_COLOR = '#cccccc'  # '#d9d9d9' X11 gray85; '#cccccc' X11 gray80
DARK_BG = '#333333'  # X11 gray20
PICK_RADIUS = 6

#  Variables used in manage_plots().
all_excluded = ('all', 'gw_series', 'gw_O3_freq', 'fgrpG1_freq')
gw_series_excluded = ('all', 'gw_O2', 'gw_O3', 'gw_O3_freq', 'fgrpG1_freq')
freq_excluded = ('all', 'fgrpG1', 'fgrp5', 'gw_O3', 'gw_O2', 'gw_series', 'brp4')
all_inclusive = ('fgrpG1', 'fgrp5', 'gw_O3', 'gw_O2', 'brp4')
gw_series_inclusive = ('fgrpG1', 'fgrp5', 'brp4', 'gw_series')
freq_inclusive = ('gw_O3_freq', 'fgrpG1_freq')

# Variables used as globals.
do_replot = False
legend_btn_on = True


# For clarity, Project names in chkbox_labels are also used in:
#   projects (tuple), proj2report (tuple), chkbox_labelid (dict),
#   plot_proj (dict), ischecked (dict), & isplotted (dict).
chkbox_labels = ('all', 'fgrpG1', 'fgrp5', 'gw_O3', 'gw_O2', 'gw_series',
                 'brp4', 'gw_O3_freq', 'fgrpG1_freq')

"""
USE THIS to extract subprojects:
gw_names_list = gw_series_df.task_name.to_list()
pattern = r'__O.+?_'
matches = [re.search(pattern, name).group() for name in gw_names_list if re.search(pattern, name)]
uniq_matches = sorted(set(matches))
gw_seriesects = [i.replace('_', '') for i in uniq_matches]
print('Num of GW sub-projects: ', len(gw_seriesects))
print('Subprojects: ', gw_seriesects)

FGRP#5 name structure: LATeah1089F_1128.0_3791580_0.0_0
grp_names_list = grp_df.task_name.to_list()
pattern = r'LATeah.+?_'
matches = [re.match(pattern, name).group() for name in grp_names_list if re.match(pattern, name)]
uniq_matches = sorted(set(matches))
grp_subprojects = [i.replace('_', '') for i in uniq_matches]
print('Num of GR sub-projects: ', len(grp_subprojects))
print('Subprojects: ', grp_subprojects)
Num of GR sub-projects:  360
  Five 0000-series categories;
  0000F is GRP#5 (Gamma Ray Pulsar Search #5)
Subprojects:  [
'LATeah0060F', 'LATeah1026F', 'LATeah1028F', 'LATeah1029F', 'LATeah1030F', 'LATeah1031F', 'LATeah1089F',
'LATeah1049L05', 'LATeah1049Lba', 'LATeah1049N', 'LATeah1049O', 'LATeah1049P', 'LATeah1049Q', 'LATeah1049R', 'LATeah1049S', 'LATeah1049T', 'LATeah1049U', 'LATeah1049V', 'LATeah1049W', 'LATeah1049X', 'LATeah1049Y', 'LATeah1049ZA', 'LATeah1049ZB', 'LATeah1049ZC', 'LATeah1049ZD', 'LATeah1049ZE', 'LATeah1049ZF', 'LATeah1049Z', 'LATeah1049a', 'LATeah1049aa', 'LATeah1049ab', 'LATeah1049ac', 'LATeah1049ad', 'LATeah1049ae', 'LATeah1049af', 'LATeah1049ag', 'LATeah1049b', 'LATeah1049c',
'LATeah1061L00', 'LATeah1061L01', 'LATeah1061L02', 'LATeah1061L03', 'LATeah1061L04', 'LATeah1061L05', 'LATeah1061L06', 'LATeah1061L07', 'LATeah1061L08', 'LATeah1061L09', 'LATeah1061L10', 'LATeah1061L11', 'LATeah1061L12', 'LATeah1061L13', 'LATeah1061L14', 'LATeah1061L15', 'LATeah1061L16', 'LATeah1062L00', 'LATeah1062L01', 'LATeah1062L02', 'LATeah1062L03', 'LATeah1062L04', 'LATeah1062L05', 'LATeah1062L06', 'LATeah1062L07', 'LATeah1062L08', 'LATeah1062L09', 'LATeah1062L10', 'LATeah1062L11', 'LATeah1062L12', 'LATeah1062L13', 'LATeah1062L14', 'LATeah1062L15', 'LATeah1062L16', 'LATeah1062L17', 'LATeah1062L18', 'LATeah1062L19', 'LATeah1062L20', 'LATeah1062L21', 'LATeah1062L22', 'LATeah1062L23', 'LATeah1062L24', 'LATeah1062L25', 'LATeah1062L26', 'LATeah1062L27', 'LATeah1062L28', 'LATeah1062L29', 'LATeah1062L30', 'LATeah1062L31', 'LATeah1062L32', 'LATeah1062L33', 'LATeah1062L34', 'LATeah1062L35', 'LATeah1062L36', 'LATeah1062L37', 'LATeah1062L38', 'LATeah1062L39', 'LATeah1062L40', 'LATeah1062L41', 'LATeah1063L00', 'LATeah1063L01',
'LATeah1063L02', 'LATeah1063L03', 'LATeah1063L04', 'LATeah1063L05', 'LATeah1063L06', 'LATeah1063L07', 'LATeah1063L08', 'LATeah1063L09', 'LATeah1063L10', 'LATeah1063L11', 'LATeah1063L12', 'LATeah1063L13', 'LATeah1063L14', 'LATeah1063L15', 'LATeah1063L16', 'LATeah1063L17', 'LATeah1063L18', 'LATeah1063L19', 'LATeah1063L20', 'LATeah1063L21', 'LATeah1063L22', 'LATeah1063L23', 'LATeah1063L26', 'LATeah1063L29', 'LATeah1063L30', 'LATeah1063L31', 'LATeah1063L32', 'LATeah1063L33', 'LATeah1063L37', 'LATeah1063L38', 'LATeah1063L39', 'LATeah1063L40', 'LATeah1063L41', 'LATeah1063L42', 'LATeah1063L43', 'LATeah1063L44', 'LATeah1063L45', 'LATeah1063L46', 'LATeah1063L47', 'LATeah1063L48', 'LATeah1063L49', 'LATeah1063L50', 'LATeah1063L51', 'LATeah1063L52', 'LATeah1063L53', 'LATeah1064L00', 'LATeah1064L01', 'LATeah1064L02', 'LATeah1064L03', 'LATeah1064L04', 'LATeah1064L05', 'LATeah1064L06', 'LATeah1064L07', 'LATeah1064L08', 'LATeah1064L09', 'LATeah1064L10', 'LATeah1064L11', 'LATeah1064L12', 'LATeah1064L13', 'LATeah1064L14', 'LATeah1064L15', 'LATeah1064L16', 'LATeah1064L17', 'LATeah1064L18', 'LATeah1064L19', 'LATeah1064L20', 'LATeah1064L22', 'LATeah1064L23', 'LATeah1064L24', 'LATeah1064L25', 'LATeah1064L26', 'LATeah1064L27', 'LATeah1064L28', 'LATeah1064L29',
'LATeah1064L31', 'LATeah1064L32', 'LATeah1064L33', 'LATeah1064L34', 'LATeah1064L37', 'LATeah1064L38', 'LATeah1064L39', 'LATeah1064L40', 'LATeah1064L41', 'LATeah1064L42', 'LATeah1064L43', 'LATeah1064L44', 'LATeah1064L45', 'LATeah1064L46', 'LATeah1064L47', 'LATeah1064L48', 'LATeah1064L49', 'LATeah1064L50', 'LATeah1064L51', 'LATeah1064L52', 'LATeah1064L53', 'LATeah1064L54', 'LATeah1064L55', 'LATeah1064L56', 'LATeah1064L57', 'LATeah1064L58', 'LATeah1064L59', 'LATeah1064L60', 'LATeah1064L61', 'LATeah1064L62', 'LATeah1065L00', 'LATeah1065L01', 'LATeah1065L02', 'LATeah1065L03', 'LATeah1065L04', 'LATeah1065L05', 'LATeah1065L06', 'LATeah1065L07', 'LATeah1065L08', 'LATeah1065L09', 'LATeah1065L10', 'LATeah1065L11', 'LATeah1065L12', 'LATeah1065L13', 'LATeah1065L14', 'LATeah1065L15', 'LATeah1065L16', 'LATeah1065L17', 'LATeah1065L18', 'LATeah1065L19', 'LATeah1065L20', 'LATeah1065L21', 'LATeah1065L22', 'LATeah1065L23', 'LATeah1065L24', 'LATeah1065L25', 'LATeah1065L26', 'LATeah1065L27', 'LATeah1065L30', 'LATeah1066L03', 'LATeah1066L05', 'LATeah1066L12', 'LATeah1066L15', 'LATeah1066L16', 'LATeah1066L17', 'LATeah1066L18', 'LATeah1066L19', 'LATeah1066L20', 'LATeah1066L21', 'LATeah1066L22', 'LATeah1066L23', 'LATeah1066L24', 'LATeah1066L25', 'LATeah1066L26',
'LATeah1066L27', 'LATeah1066L28', 'LATeah1066L29', 'LATeah1066L30', 'LATeah1066L31', 'LATeah1066L32', 'LATeah1066L33', 'LATeah1066L34', 'LATeah1066L35', 'LATeah1066L36', 'LATeah1066L37', 'LATeah1066L38', 'LATeah1066L39', 'LATeah1066L40', 'LATeah1066L41', 'LATeah1066L42', 'LATeah1066L43', 'LATeah1066L44', 'LATeah1066L45', 'LATeah1066L46', 'LATeah1066L47', 'LATeah1066L48', 'LATeah1066L49', 'LATeah1066L50', 'LATeah1066L51', 'LATeah1066L52', 'LATeah1066L53', 'LATeah1066L54', 'LATeah1066L55', 'LATeah1066L56', 'LATeah1066L57', 'LATeah1066L58', 'LATeah1066L59', 'LATeah1066L61', 'LATeah1066L62', 'LATeah1066L63', 'LATeah1066L64', 'LATeah1066L65', 'LATeah1066L66', 'LATeah1066L67', 'LATeah1066L68', 'LATeah1066L69', 'LATeah1066L70', 'LATeah1066L71', 'LATeah1066L72', 'LATeah1066L73', 'LATeah1066L74', 'LATeah1066L75', 'LATeah1066L76', 'LATeah1066L77', 'LATeah1066L78', 'LATeah1066L79', 'LATeah1066L80',
'LATeah2049Lae', 'LATeah2049Laf', 'LATeah2049Lag', 'LATeah2065L68aj', 'LATeah2065L68ak', 'LATeah2065L68al', 'LATeah2065L68am', 'LATeah2065L68an',
'LATeah3001L00', 'LATeah3001L01', 'LATeah3002L00', 'LATeah3002L01', 'LATeah3002L02', 'LATeah3002L03', 'LATeah3003L00', 'LATeah3003L01', 'LATeah3003L02', 'LATeah3004L01', 'LATeah3004L02', 'LATeah3004L03', 'LATeah3004L04', 'LATeah3004L05', 'LATeah3011L00', 'LATeah3011L01', 'LATeah3011L02', 'LATeah3011L03', 'LATeah3011L04', 'LATeah3011L05', 'LATeah3011L06', 'LATeah3011L07', 'LATeah3011L08', 'LATeah3011L09', 'LATeah3012L00', 'LATeah3012L01', 'LATeah3012L02', 'LATeah3012L03', 'LATeah3012L04', 'LATeah3012L05', 'LATeah3012L06', 'LATeah3012L07', 'LATeah3012L08', 'LATeah3012L09', 'LATeah3012L10', 'LATeah3012L11',
'LATeah4001L00', 'LATeah4011L00', 'LATeah4011L01', 'LATeah4011L02', 'LATeah4011L03', 'LATeah4011L04', 'LATeah4012L00', 'LATeah4012L01', 'LATeah4012L02', 'LATeah4012L03', 'LATeah4012L04', 'LATeah4013L00', 'LATeah4013L01', 'LATeah4013L02', 'LATeah4013L03', 'LATeah4013L04'
]
"""
# Num of unique GW sub-projects:  23
# contains() grabs first matches: O2MD1G = O2MD1Gn, O3AS1 = O3AS1a,
#  so add back the Underscore at end of original sub-proj to make the match unique.
gw_series = ('O2AS20-500', 'O2MD1C1', 'O2MD1C2', 'O2MD1G2', 'O2MD1G_',
             'O2MD1Gn', 'O2MD1S3', 'O2MDFG2_', 'O2MDFG2e', 'O2MDFG2f',
             'O2MDFG3_', 'O2MDFG3a', 'O2MDFS2', 'O2MDFS3_', 'O2MDFS3a',
             'O2MDFV2_', 'O2MDFV2e', 'O2MDFV2g', 'O2MDFV2h', 'O2MDFV2i',
             'O3AS1_', 'O3AS1a', 'O3ASE1')


# Variables used in job_log_counts() and log_proj_counts().
proj2report = ('all', 'fgrpG1', 'fgrp5', 'gw_O3', 'gw_O2', 'brp4',)
proj_totals = []
proj_daily_means = []
proj_days = []


# ######################### START set up Pandas dataframe. ####################

def setup_df(do_test=False):
    """
    Set up the Pandas DataFrame of task data read from a text file.
    Called from if __name__ == "__main__".

    :param do_test: True when --test argument used; default False.
    :return: None
    """
    global all_tasks

    """
    job_log_einstein.phys.uwm.edu.txt structure of records:
    1654865994 ue 916.720025 ct 340.770200 fe 144000000000000 nm h1_0681.20_O3aC01Cl1In0__O3AS1a_681.50Hz_19188_1 et 1283.553196 es 0
    """

    """ 
    Can check for NaN values with:
    print('Any null values?', all_tasks.isnull().values.any())  # -> True
    print("Sum of null timestamps:", all_tasks['time_stamp'].isnull().sum())
    print("Sum of ALL nulls:", all_tasks.isnull().sum()).sum())
    """

    # For all numerical data in job_log, use this:
    # joblog_col_idx = 0, 2, 4, 6, 8, 10  # All reported data
    # headers = ('time_stamp', 'est_sec', 'cpu_sec', 'est_flops', 'task_name', 'task_t')
    # time_col = ('time_stamp', 'est_sec', 'cpu_sec', 'task_t')
    # Only need job log data of interest to plot:
    joblog_col_idx = 0, 8, 10
    headers = ('time_stamp', 'task_name', 'task_t')

    if not do_test:
        plotdata = path_check.set_datapath()
    else:
        plotdata = path_check.set_datapath(True)

    print(f'Data from {plotdata} are loading. This may take a few seconds...')

    all_tasks = pd.read_table(plotdata,
                              sep=' ',
                              header=None,
                              usecols=joblog_col_idx,
                              names=headers,
                              )

    # Need to replace NaN values with usable data.
    #   Assumes read_table of job_log file will produce NaN ONLY for timestamp.
    all_tasks.time_stamp.interpolate(inplace=True)

    # Need to retain original elapsed time seconds values for correlations.
    #   Not sure whether floats as sec.ns or integers are better:
    all_tasks['task_sec'] = all_tasks.task_t.astype(int)

    #  Need to convert times to datetimes for efficient plotting.
    time_col = ('time_stamp', 'task_t')
    for col in time_col:
        all_tasks[col] = pd.to_datetime(all_tasks[col], unit=mmark.MARKER_STYLE['square'],
                                        infer_datetime_format=True)

    # Null column data used to visually reset_plots().
    all_tasks['null_time'] = pd.to_datetime(0.0, unit=mmark.MARKER_STYLE['square'])
    all_tasks['null_Dcnt'] = 0

    # Need columns that flag each task's Project and sub-Project.
    all_tasks['is_all'] = where(all_tasks.task_name, True, False)
    all_tasks['is_gw'] = where(all_tasks.task_name.str.startswith('h1_'), True, False)
    all_tasks['is_gw_O2'] = where(all_tasks.task_name.str.contains('_O2'), True, False)
    all_tasks['is_gw_O3'] = where(all_tasks.task_name.str.contains('_O3'), True, False)
    all_tasks['is_fgrp'] = where(all_tasks.task_name.str.startswith('LATeah'), True, False)
    all_tasks['is_fgrp5'] = where(all_tasks.task_name.str.contains(r'LATeah\d{4}F'), True, False)
    all_tasks['is_fgrpG1'] = where(all_tasks.task_name.str.contains(r'LATeah\d{4}L|LATeah1049'), True,
                                   False)
    all_tasks['is_brp4'] = where(all_tasks.task_name.str.startswith('p'), True, False)

    # Add columns of search frequencies, parsed from the task names,
    """
    Expected task names to match the regex for base frequency:
    FGRP task: 'LATeah4013L03_988.0_0_0.0_9010205_1'
    GW task: 'h1_0681.20_O3aC01Cl1In0__O3AS1a_681.50Hz_19188_1'
    """
    # pattern_gw_freq = r'h1_[0]?(\d+\.\d+)_?'  # Ignore leading 0 in capture.
    # pattern_gw_freq = r'h1.*_(\d+\.\d{2})Hz_'  # Capture highest freq, not base freq.
    pattern_gw_freq = r'h1_(\d+\.\d+)_?'  # Capture the base/parent freq.
    pattern_fgrpg1_freq = r'LATeah.*?_(\d+\.\d+)_?'
    all_tasks['gw_freq'] = (all_tasks.task_name
                            .str.extract(pattern_gw_freq).astype(float))
    all_tasks['fgrpG1_freq'] = (all_tasks.task_name
                                .str.extract(pattern_fgrpg1_freq).astype(float)
                                .where(all_tasks.is_fgrpG1))

    # from scipy.stats import kendalltau, pearsonr, spearmanr
    # print('Spearman - fgrpG freq to task time:',
    #       all_tasks.fgrpG1_freq.corr(
    #           all_tasks.task_sec.where(all_tasks.is_fgrpG1), method="spearman"))
    # print('Spearman - GW O3 freq to task time:',
    #       all_tasks.gw_freq.where(all_tasks.is_gw_O3).corr(
    #           all_tasks.task_sec.where(all_tasks.is_gw_O3), method="spearman"))

    """Idea to tally using groupby and transform from:
       https://stackoverflow.com/questions/17709270/
       create-column-of-value-counts-in-pandas-dataframe
    """
    # Make dict of daily task counts (Dcnt) for each Project and sub-Project.
    # NOTE: gw times are not plotted (use O2 + O3), but gw_Dcnt is used in plot_gw_series()
    # For clarity, Project names here are those used in:
    #   proj2report (tuple), isplotted (dict), and chkbox_labels (tuple).
    projects = ('all', 'gw', 'gw_O2', 'gw_O3', 'fgrp', 'fgrp5', 'fgrpG1', 'brp4',)
    daily_counts = {}
    for _proj in projects:
        is_name = f'is_{_proj}'
        daily_counts[f'{_proj}_Dcnt'] = (
            all_tasks.time_stamp
            .groupby(all_tasks.time_stamp.dt.floor('D')
                     .where(all_tasks[is_name]))
            .transform('count')
        )

    # Add columns to all_tasks df of daily counts for each Project and sub-Project.
    #  Note that _Dcnt column values are returned as floats (counts of Booleans), not integers.
    for _proj, _ in daily_counts.items():
        all_tasks[_proj] = daily_counts[_proj]

    for series in gw_series:
        is_ser = f'is_{series}'
        all_tasks[is_ser] = where(all_tasks.task_name.str.contains(series),
                                  True, False)

    # with pd.option_context('display.width', 300,
    #                        'display.max_colwidth', None,
    #                        'display.max_columns', None,
    #                        'display.max_rows', 25,  # None,
    #                        #'display.min_rows', 100,
    #                        # 'display.precision', 3,
    #                        'display.expand_frame_repr', True,
    #                        ):
        # print(all_tasks['gw_freq'][all_tasks['gw_freq'] > 100].values[0:1000])
        # print(all_tasks)
        # print(all_tasks.columns.values.tolist())
        # print(all_tasks.shape)
        # print(all_tasks.size)


# Need to work up metrics here so there is less delay when "Log counts" button is used.
# Need Project names here to be same as those used in:
#   projects (tuple), isplotted (dict), and chkbox_labels (tuple).
def log_proj_counts():
    for p in proj2report:
        is_p = f'is_{p}'
        proj_totals.append(all_tasks[is_p].sum())

        p_dcnt = f'{p}_Dcnt'

        proj_days.append(len((all_tasks[p_dcnt]
                              .groupby(all_tasks.time_stamp.dt.date
                                       .where(all_tasks[p_dcnt].notnull()))
                              .unique())))
        # proj_daily_means.append(int((all_tasks[p_Dcnt]
        #                             .groupby(all_tasks.time_stamp.dt.date
        #                                      .where(all_tasks[p_Dcnt].notnull()))
        #                             .count().mean())))
        if proj_totals[-1] != 0:
            proj_daily_means.append(round((proj_totals[-1] / proj_days[-1]), 1))
        else:  # There is no Project p in the job log.
            proj_daily_means.append(0)


# #############################################################################
# Dataframe is made, now SET UP PLOTS. ########################################

"""To list all available styles, use:
print(plt.style.available)
"""
mplstyle.use(('seaborn-colorblind', 'fast'))

fig, (ax1, ax2) = plt.subplots(2, figsize=(9.5, 5),
                               sharex='all',
                               gridspec_kw={'height_ratios': [3, 1],
                                            'left': 0.11,
                                            'right': 0.85,
                                            'bottom': 0.16,
                                            'top': 0.92,
                                            'hspace': 0.15
                                            },
                               )


def setup_title(do_test=False):
    """
    Specify in the Figure title which data are plotted, those from the
    sample data file, plot_utils.testdata.txt, or the user's job log
    file. Called from if __name__ == "__main__".

    :param do_test: True when --test argument used; default False.
    :return: None
    """
    if do_test:
        title = 'Sample data'
    else:
        title = 'E@H job_log data'

    fig.suptitle(title,
                 fontsize=14, fontweight='bold',
                 color=LIGHT_COLOR)


def on_pick(event):
    """
    Click on plot area to show nearby task info in new figure and in
    Terminal or Command Line. Template source:
     https://matplotlib.org/stable/users/explain/event_handling.html
     Used in conjunction with mpl_connect().

    :param event: Implicit mouse event, left or right button click, on
    area of plotted line markers. No event is triggered when a toolbar
    a navigation tool (pan or zoom) is active.
    :return: None
    """

    n = len(event.ind)  # VertexSelector(line), in lines.py
    if not n:
        print('event.ind is undefined')
        return event

    limit = 6  # Limit tasks from total in PICK_RADIUS.,
    task_info_list = ["Date | name | completion time"]
    for dataidx in event.ind:
        if limit > 0:
            task_info_list.append(
                f'{all_tasks.loc[dataidx].time_stamp.date()} | '
                f'{all_tasks.loc[dataidx].task_name} | '
                f'{all_tasks.loc[dataidx].task_t.time()}')
        limit -= 1

    # Need to print results to Terminal to provide a cut-and-paste
    #   record of picks.
    print('\n'.join(map(str, task_info_list)))

    # Make new window with text box, one window for each click.
    textfig = plt.figure(figsize=(6, 2))
    textax = textfig.add_subplot()
    textfig.suptitle('Tasks near clicked area, up to 6:')
    textax.axis('off')
    # textax.set_transform(textax.transAxes)

    textax.text(-0.12, 0.0,
                '\n\n'.join(map(str, task_info_list)),
                fontsize=8,
                bbox=dict(facecolor='orange',
                          alpha=0.4,
                          boxstyle='round'),
                transform=textax.transAxes,
                )

    plt.show()
    return event


# Need to have mpl_connect statement before any autoscale statements AND
#  need to have ax.autoscale(True) set for picker radius to work.
fig.canvas.mpl_connect('pick_event', on_pick)


def format_legends():
    ax1.legend(fontsize='x-small', ncol=2,
               loc='upper right',  # loc='best' takes time
               markerscale=MRKR_SCALE,
               edgecolor='black',
               framealpha=0.4,
               )
    ax2.legend(fontsize='x-small', ncol=2,
               loc='upper right',  # loc='best' takes time
               markerscale=MRKR_SCALE,
               edgecolor='black',
               framealpha=0.4,
               )


def toggle_legends(event):
    """
    Show/hide plot legends.

    :param event: Implicit mouse click event.
    :return:  None
    """
    global legend_btn_on

    if legend_btn_on:
        ax1.get_legend().set_visible(False)
        # In case viewing frequency plots where ax2 is hidden:
        if ax2.get_legend():
            ax2.get_legend().set_visible(False)
        legend_btn_on = False
    else:
        ax1.get_legend().set_visible(True)
        if ax2.get_legend():
            ax2.get_legend().set_visible(True)
        legend_btn_on = True

    fig.canvas.draw_idle()  # Speeds up response.

    return event


def joblog_counts(event):
    """
    Post statistical metrics of data in the job_log.
    Called from "Counts" button in Figure.

    :param event: Implicit mouse click event.
    :return:  None
    """

    stats_title = 'Report for all tasks in E@H job log'

    _results = tuple(zip(proj2report, proj_totals, proj_daily_means, proj_days))
    num_days = len(pd.to_datetime(all_tasks.time_stamp).dt.date.unique())

    _report = (f'Task counts for the past {num_days} days:\n\n'
               f'{"Project".ljust(6)} {"Total".rjust(10)}'
               f' {"per Day".rjust(9)} {"Days".rjust(8)}\n'
               )
    for proj_tup in _results:
        _proj, p_tot, p_dmean, p_days = proj_tup
        _report = _report + (f'{_proj.ljust(6)} {str(p_tot).rjust(10)}'
                             f' {str(p_dmean).rjust(9)} {str(p_days).rjust(8)}\n'
                             )

    print(stats_title)
    print(_report)

    statfig = plt.figure(figsize=(4.5, 2.5))
    statax = statfig.add_subplot()
    statfig.suptitle(stats_title)
    statax.axis('off')
    statax.set_transform(statax.transAxes)

    _font = FontProperties()
    _font.set_family('monospace')
    # font.set_name('Times New Roman')
    # font.set_style('italic')

    statax.text(0.0, 0.0,
                _report,
                fontproperties=_font,
                bbox=dict(facecolor='orange', alpha=0.4,
                          boxstyle='round'),
                transform=statax.transAxes,
                )

    plt.show()
    return event


def setup_buttons():
    # Relative coordinates in Figure are (LEFT, BOTTOM, WIDTH, HEIGHT).
    # Position button just below plot checkboxes.
    ax_legendbtn = plt.axes((0.885, 0.5, 0.09, 0.06))
    lbtn = Button(ax_legendbtn, 'Legends', color=LIGHT_COLOR, hovercolor='orange')
    lbtn.on_clicked(toggle_legends)
    # Dummy reference, per documentation: "For the buttons to remain responsive
    #   you must keep a reference to this object."
    ax_legendbtn._button = lbtn

    #  Relative coordinates in Figure, as 4-tuple, are (LEFT, BOTTOM, WIDTH, HEIGHT)
    ax_statsbtn = plt.axes((0.885, 0.02, 0.09, 0.08))  # Position: bottom right corner.
    sbtn = Button(ax_statsbtn, 'Job log\ncounts', color=LIGHT_COLOR, hovercolor='orange')
    sbtn.on_clicked(joblog_counts)
    ax_statsbtn._button = sbtn

    # These are in alignment with the plot selector checkbox, ax_chkbox:
    #  ax_chkbox = plt.axes((0.885, 0.6, 0.111, 0.3), facecolor=LIGHT_COLOR, )
    # and fitted to the figsize(9, 5) and subplot axes, ax1 & ax2, gridspec_kw:
    #                                                   'left': 0.11,
    #                                                   'right': 0.855,
    #                                                   'bottom': 0.16,
    #                                                   'top': 0.92,


def setup_count_axes():
    """
    Used to rebuild axes components when plots and axes are cleared by
    reset_plots().
    """
    # ax1.xaxis.axis_date()
    # ax1.yaxis.axis_date()

    # Need to reset plot axes in case setup_freq_axes() was called.
    ax2.set_visible(True)
    ax1.tick_params('x', labelbottom=False)

    ax1.set_ylabel('Task completion time',
                   fontsize='medium', fontweight='bold')

    ax2.set_xlabel('Task reporting datetime',
                   # 'format: [y-m], [y-m-date], [m-date hr], [date h:sec]',
                   fontsize='medium', fontweight='bold')
    ax2.set_ylabel('Tasks/day',
                   fontsize='medium', fontweight='bold')

    # Need to set the Tasks/day axis label in a static position.
    ax2.yaxis.set_label_coords(-0.1, 0.55)

    # ax1.set(xticklabels=['']) # hides labels, but only with sharex=False

    # Need to rotate and right-align the date labels to avoid crowding.
    for label in ax1.get_yticklabels(which='major'):
        label.set(rotation=30, fontsize='small')

    for label in ax2.get_xticklabels(which='major'):
        label.set(rotation=15, fontsize='small', horizontalalignment='right')

    for label in ax2.get_yticklabels(which='major'):
        label.set(fontsize='small')

    ax1.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    ax1.yaxis.set_major_locator(ticker.AutoLocator())
    ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    # ax2.yaxis.get_major_locator().set_params(integer=True)
    ax2.yaxis.set_major_locator(ticker.AutoLocator())
    ax2.yaxis.set_minor_locator(ticker.AutoMinorLocator())

    fig.set_facecolor(DARK_BG)

    ax1.set_facecolor(LIGHT_COLOR)
    ax1.yaxis.label.set_color(LIGHT_COLOR)
    ax1.xaxis.label.set_color(LIGHT_COLOR)

    ax1.tick_params(colors=LIGHT_COLOR, which='both')

    ax2.set_facecolor(LIGHT_COLOR)
    ax2.yaxis.label.set_color(LIGHT_COLOR)
    ax2.xaxis.label.set_color(LIGHT_COLOR)
    ax2.tick_params(colors=LIGHT_COLOR, which='both')

    ax1.grid(True)
    ax2.grid(True)

    # NOTE: autoscale methods have no visual effect when reset_plots() plots
    #  the full range datetimes from a job lob, BUT enabling autoscale
    #  does allow the picker radius to work properly.
    ax1.autoscale(True)
    ax2.autoscale(True)


def setup_freq_axes(t_limits: tuple):
    # Need to remove bottom axis and show tick lables (b/c when sharex=True,
    #   tick labels only show on bottom (ax2) plot).
    ax2.set_visible(False)
    ax1.tick_params('x', labelbottom=True)

    ax1.set_xlim(t_limits)

    ax1.set_xlabel('Task completion time, sec',
                   fontsize='medium', fontweight='bold')

    ax1.set_ylabel('Task base frequency, Hz',
                   fontsize='medium', fontweight='bold')

    ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))

    ax1.xaxis.set_major_locator(ticker.AutoLocator())
    ax1.xaxis.set_minor_locator(ticker.AutoMinorLocator())

    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.2f'))

    ax1.yaxis.set_major_locator(ticker.AutoLocator())
    ax1.yaxis.set_minor_locator(ticker.AutoMinorLocator())


setup_buttons()
setup_count_axes()

chkbox_labelid = {}
for i, proj in enumerate(chkbox_labels):
    chkbox_labelid[proj] = i

isplotted = {}
for proj in chkbox_labels:
    isplotted[proj] = False

"""
chkbox_labelid = {
    'all': 0,
    'fgrpG1': 1,
    'fgrp5': 2,
    'gw_O3': 3,
    'gw_O2': 4,
    'gw_series': 5,
    'brp4': 6,
    'gw_O3_freq': 7,
    'fgrpG1_freq': 8,
}

isplotted = {
    'all': False,
    'fgrpG1': False,
    'fgrp5': False,
    'gw_O3': False,
    'gw_O2': False,
    'gw_series': False,
    'brp4': False,
    'gw_O3_freq': False,
    'fgrpG1_freq': False,
}"""


def reset_plots():
    """
    Clear plots. axis labels, ticks, formats, legends, etc.
    Clears plotted data by setting all data values to zero.
    Useful to avoid stacking plots, which messes up on_pick() display of
    nearby task info. Note that with this the full x-axis datetime range
    in job lob is always plotted; therefore, the methods ax.relim()
    ax.autoscale_view() and ax.autoscale() have no effect on individual
    data plots.
    Called from manage_plots().
    """
    global all_tasks
    ax1.clear()
    ax2.clear()

    setup_count_axes()

    ax1.plot(all_tasks.time_stamp,
             all_tasks.null_time,
             visible=False,
             label='_leave blank',
             )
    ax2.plot(all_tasks.time_stamp,
             all_tasks.null_Dcnt,
             visible=False,
             label='_leave blank',
             )

    for plot, _ in isplotted.items():
        isplotted[plot] = False


def plot_all():
    ax1.plot(all_tasks.time_stamp,
             all_tasks.task_t,
             mmark.MARKER_STYLE['point'],
             markersize=MARKER_SIZE,
             label='all',
             color=mmark.CBLIND_COLOR['blue'],
             picker=PICK_RADIUS,
             )
    ax2.plot(all_tasks.time_stamp,
             all_tasks.all_Dcnt,
             mmark.MARKER_STYLE['square'],
             markersize=DCNT_SIZE,
             label='all',
             color=mmark.CBLIND_COLOR['blue'],
             )
    format_legends()
    isplotted['all'] = True


def plot_gw_O2():
    ax1.plot(all_tasks.time_stamp,
             all_tasks.task_t.where(all_tasks.is_gw_O2),
             mmark.MARKER_STYLE['triangle_down'],
             markersize=MARKER_SIZE,
             label='gw_O2MD1',
             color=mmark.CBLIND_COLOR['orange'],
             alpha=0.5,
             picker=PICK_RADIUS,
             )
    ax2.plot(all_tasks.time_stamp,
             all_tasks.gw_O2_Dcnt,
             mmark.MARKER_STYLE['square'],
             markersize=DCNT_SIZE,
             label='gw_O2MD1',
             color=mmark.CBLIND_COLOR['orange'],
             )
    format_legends()
    isplotted['gw_O2'] = True


def plot_gw_O3():
    ax1.plot(all_tasks.time_stamp,
             all_tasks.task_t.where(all_tasks.is_gw_O3),
             mmark.MARKER_STYLE['triangle_up'],
             markersize=MARKER_SIZE,
             label='gw_O3AS',
             color=mmark.CBLIND_COLOR['sky blue'],
             alpha=0.5,
             picker=PICK_RADIUS,
             )
    ax2.plot(all_tasks.time_stamp,
             all_tasks.gw_O3_Dcnt,
             mmark.MARKER_STYLE['square'],
             markersize=DCNT_SIZE,
             label='gw_O3AS',
             color=mmark.CBLIND_COLOR['sky blue'],
             )
    format_legends()
    isplotted['gw_O3'] = True


def plot_fgrp5():
    ax1.plot(all_tasks.time_stamp,
             all_tasks.task_t.where(all_tasks.is_fgrp5),
             mmark.MARKER_STYLE['tri_left'],
             markersize=MARKER_SIZE,
             label='fgrp5',
             color=mmark.CBLIND_COLOR['bluish green'],
             alpha=0.5,
             picker=PICK_RADIUS,
             )
    ax2.plot(all_tasks.time_stamp,
             all_tasks.fgrp5_Dcnt,
             mmark.MARKER_STYLE['square'],
             markersize=DCNT_SIZE,
             label='fgrp5',
             color=mmark.CBLIND_COLOR['bluish green'],
             alpha=0.5,
             picker=PICK_RADIUS,
             )
    format_legends()
    isplotted['fgrp5'] = True


def plot_fgrpG1():
    ax1.plot(all_tasks.time_stamp,
             all_tasks.task_t.where(all_tasks.is_fgrpG1),
             mmark.MARKER_STYLE['tri_right'],
             markersize=MARKER_SIZE,
             label='FGRBPG1',
             color=mmark.CBLIND_COLOR['vermilion'],
             alpha=0.5,
             picker=PICK_RADIUS,
             )
    ax2.plot(all_tasks.time_stamp,
             all_tasks.fgrpG1_Dcnt,
             mmark.MARKER_STYLE['square'],
             markersize=DCNT_SIZE,
             label='FGRBPG1',
             color=mmark.CBLIND_COLOR['vermilion'],
             )
    format_legends()
    isplotted['fgrpG1'] = True


def plot_brp4():
    ax1.plot(all_tasks.time_stamp,
             all_tasks.task_t.where(all_tasks.is_brp4),
             mmark.MARKER_STYLE['pentagon'],
             markersize=MARKER_SIZE,
             label='BRP4 & BRP4G',
             color=mmark.CBLIND_COLOR['reddish purple'],
             alpha=0.5,
             picker=PICK_RADIUS,
             )
    ax2.plot(all_tasks.time_stamp,
             all_tasks.brp4_Dcnt,
             mmark.MARKER_STYLE['square'],
             markersize=DCNT_SIZE,
             label='BRP4 & BRP4G',
             color=mmark.CBLIND_COLOR['reddish purple'],
             )
    format_legends()
    isplotted['brp4'] = True


def plot_gw_series():
    for subproj in gw_series:
        is_subproj = f'is_{subproj}'

        ax1.plot(all_tasks.time_stamp,
                 all_tasks.task_t.where(all_tasks[is_subproj]),
                 mmark.next_marker(),
                 label=subproj,
                 markersize=MARKER_SIZE,
                 alpha=0.4,
                 picker=True,
                 pickradius=PICK_RADIUS,
                 )

    ax2.plot(all_tasks.time_stamp,
             all_tasks.gw_Dcnt,
             mmark.MARKER_STYLE['square'],
             label='All GW',
             markersize=DCNT_SIZE,
             )
    format_legends()
    isplotted['gw_series'] = True


def plot_fgrpG1_txf():
    num_freq = all_tasks.fgrpG1_freq.nunique()
    min_f = all_tasks.fgrpG1_freq.min()
    max_f = all_tasks.fgrpG1_freq.max()
    min_t = all_tasks.task_sec.where(all_tasks.is_fgrpG1).min()
    max_t = all_tasks.task_sec.where(all_tasks.is_fgrpG1).max()

    setup_freq_axes((0, max_t + 20))

    ax1.text(0.0, -0.15,  # Below lower left corner of axes.
             f'# frequencies: {num_freq}\n'
             f'Freq. min--max: {min_f}--{max_f}\n'
             f'T, min--max: {min_t}--{max_t}',
             style='italic',
             fontsize=6,
             verticalalignment='top',
             transform=ax1.transAxes,
             bbox=dict(facecolor='white',
                       alpha=0.6,
                       boxstyle='round'),
             )

    ax1.plot(all_tasks.task_sec.where(all_tasks.is_fgrpG1),
             all_tasks.fgrpG1_freq,
             mmark.MARKER_STYLE['point'],
             markersize=MARKER_SIZE,
             label='FGRPG1 f vs. task t',
             color=mmark.CBLIND_COLOR['orange'],
             alpha=0.3,  # Higher alpha for zoom-in, lower for zoom-out.
             picker=PICK_RADIUS,
             )

    ax1.legend(fontsize='x-small', ncol=2,
               loc='upper right',
               markerscale=MRKR_SCALE,
               edgecolor='black',
               framealpha=0.4,
               )
    isplotted['fgrpG1_freq'] = True


def plot_gw_O3_txf():
    num_freq = all_tasks.gw_freq.where(all_tasks.is_gw_O3).nunique()
    min_f = all_tasks.gw_freq.where(all_tasks.is_gw_O3).min()
    max_f = all_tasks.gw_freq.where(all_tasks.is_gw_O3).max()
    min_t = all_tasks.task_sec.where(all_tasks.is_gw_O3).min()
    max_t = all_tasks.task_sec.where(all_tasks.is_gw_O3).max()

    setup_freq_axes((0, max_t + 20))

    ax1.text(0.0, -0.15,  # Below lower left corner of axes.
             f'# frequencies: {num_freq}\n'
             f'Freq. min--max: {min_f}--{max_f}\n'
             f'T, min--max: {min_t}--{max_t}',
             style='italic',
             fontsize=6,
             verticalalignment='top',
             transform=ax1.transAxes,
             bbox=dict(facecolor='white',
                       alpha=0.6,
                       boxstyle='round'),
             )

    # NOTE that there is not a separate df column for O3 freq.
    ax1.plot(all_tasks.task_sec.where(all_tasks.is_gw_O3),
             all_tasks.gw_freq.where(all_tasks.is_gw_O3),
             mmark.MARKER_STYLE['point'],
             markersize=MARKER_SIZE,
             label='GW O3 f vs. task t',
             color=mmark.CBLIND_COLOR['blue'],
             alpha=0.3,  # Better to increase alpha for zoom-in, lower for zoom-out.
             picker=PICK_RADIUS,
             )

    ax1.legend(fontsize='x-small', ncol=2,
               loc='upper right',
               markerscale=MRKR_SCALE,
               edgecolor='black',
               framealpha=0.4,
               )

    isplotted['gw_O3_freq'] = True


#  Relative coordinates in Figure, in 4-tuple: (LEFT, BOTTOM, WIDTH, HEIGHT)
ax_chkbox = plt.axes((0.86, 0.6, 0.13, 0.3), facecolor=LIGHT_COLOR, )
checkbox = CheckButtons(ax_chkbox, chkbox_labels)

# These keys need to match the chkbox_labels:
# ('all', 'fgrpG1', 'fgrp5', 'gw_O3', 'gw_O2', 'gw_series',
#    'brp4', 'gw_O3_freq', 'fgrpG1_freq')
plot_proj = {
    'all': plot_all,
    'fgrpG1': plot_fgrpG1,
    'fgrp5': plot_fgrp5,
    'gw_O3': plot_gw_O3,
    'gw_O2': plot_gw_O2,
    'gw_series': plot_gw_series,
    'brp4': plot_brp4,
    'gw_O3_freq': plot_gw_O3_txf,
    'fgrpG1_freq': plot_fgrpG1_txf,
}


def manage_plots(clicked_label):
    """
    Conditions determining which columns, defined by selected checkbox
    labels, to plot and which other columns are inclusive and exclusive
    for co-plotting. Called from the checkbox.on_clicked() method.

    :param clicked_label: Implicit event that returns the label name
      selected in the checkbox. Labels are defined in chkbox_labels.
    :return: None
    """
    global do_replot

    #  NOTE: CANNOT have same plot points overlaid. That creates multiple
    #    on_pick() calls of windows for the same task info text.

    # NOTE: with checkbox.eventson = True (default),
    #   all proj button clicks trigger this manage_plots() callback
    #   (all conditions are evaluated with every click).

    # ischecked key is project label, value is True/False check status.
    ischecked = dict(zip(chkbox_labels, checkbox.get_status()))

    # Note: ischecked and isplotted dictionary values are boolean.
    if clicked_label == 'all' and ischecked[clicked_label]:

        # Was toggled on...
        # Need to uncheck all other checked project labels.
        for _label in chkbox_labels:
            if _label != clicked_label and (isplotted[_label] or ischecked[_label]):
                ischecked[_label] = False
                # Toggle off all excluded plots.
                checkbox.set_active(chkbox_labelid[_label])
                # Set a flag to avoid multiple resets.
                do_replot = True

        if do_replot:
            reset_plots()
            do_replot = False

        plot_all()

    elif not ischecked[clicked_label]:
        reset_plots()

    if clicked_label in all_inclusive and ischecked[clicked_label]:
        for _plot in all_excluded:
            if isplotted[_plot] or ischecked[_plot]:
                isplotted[_plot] = False
                checkbox.set_active(chkbox_labelid[_plot])
                do_replot = True

        if do_replot:
            reset_plots()
            do_replot = False

        for _proj, status in ischecked.items():
            if status and _proj in all_inclusive and not isplotted[_proj]:
                plot_proj[_proj]()

    elif clicked_label in all_inclusive and not ischecked[clicked_label]:

        # Was toggled off, so remove all plots,
        #   then replot only inclusive checked ones.
        reset_plots()
        for _proj, status in ischecked.items():
            if _proj in all_inclusive and status:
                plot_proj[_proj]()
            if _proj == 'gw_series' and status:
                plot_gw_series()

    if clicked_label == 'gw_series' and ischecked[clicked_label]:

        # Uncheck excluded checkbox labels if plotted.
        for excluded in gw_series_excluded:
            if isplotted[excluded] or ischecked[excluded]:
                checkbox.set_active(chkbox_labelid[excluded])

        for _proj, status in ischecked.items():
            if status and _proj in gw_series_inclusive and not isplotted[_proj]:
                plot_proj[_proj]()

    elif clicked_label == 'gw_series' and not ischecked[clicked_label]:

        # Was toggled off, so need to remove gw_series plot,
        # but not others. Reset all, then replot the others.
        reset_plots()
        for _proj, status in ischecked.items():
            if status and _proj in gw_series_inclusive:
                plot_proj[_proj]()

    if clicked_label == 'fgrpG1_freq' and ischecked[clicked_label]:

        # Was toggled on...
        # Need to uncheck all other checked project labels.
        for _label in chkbox_labels:
            if _label != clicked_label and (isplotted[_label] or ischecked[_label]):
                checkbox.set_active(chkbox_labelid[_label])
                do_replot = True

        if do_replot:
            reset_plots()
            do_replot = False

        plot_proj[clicked_label]()

    if clicked_label == 'gw_O3_freq' and ischecked[clicked_label]:
        for _label in chkbox_labels:
            if _label != clicked_label and (isplotted[_label] or ischecked[_label]):
                ischecked[_label] = False
                checkbox.set_active(chkbox_labelid[_label])
                do_replot = True

        if do_replot:
            reset_plots()
            do_replot = False

        plot_proj[clicked_label]()

    fig.canvas.draw_idle()


checkbox.on_clicked(manage_plots)


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

    # Program will exit here if checks fail.
    platform_check.check_platform()
    vcheck.minversion('3.7')

    setup_df(args.test)

    # Make call here to speed up count button response.
    log_proj_counts()

    setup_title(args.test)

    # At startup, set the checkbox to 'all'; all tasks are plotted via
    #  manage_plots() run from the checkbox.on_clicked(manage_plots)
    #  statement.
    checkbox.set_active(chkbox_labelid['all'])

    print('The plot window is ready.')

    try:
        plt.show()
    except KeyboardInterrupt:
        print('\n*** User quit the program ***\n')
        plt.close('all')
