"""
Matching Project and series names for checkbox labels, and dict keys,
used in various plot_utils modules.
"""

PROJECTS = ('all', 'fgrp5', 'fgrpG1', 'gw_O2', 'gw_O3', 'brp4', 'brp7')

PROJ_TO_REPORT = ('all', 'fgrp5', 'fgrpG1', 'gw_O3', 'gw_O2', 'brp4', 'brp7')

# Names used here must match keys in PlotTasks.plot_proj dictionary.
CHKBOX_LABELS = ('all', 'fgrp5', 'fgrpG1', 'fgrp_hz', 'gw_O3', 'gw_O2',
                 'brp4', 'brp7', 'grG1hz_X_t', 'gwO3hz_X_t')

EXCLUSIVE_PLOTS = ('all', 'fgrp_hz', 'grG1hz_X_t', 'gwO3hz_X_t')

ALL_EXCLUDED = ('all', 'fgrp_hz', 'grG1hz_X_t', 'gwO3hz_X_t')

ALL_INCLUSIVE = ('fgrp5', 'fgrpG1', 'gw_O3', 'gw_O2', 'brp4', 'brp7')

# Dict used in PlotTasks.is_project() to match checkbox CHKBOX_LABELS to
#  is_<project> columns in the main DataFrame.
IS_PROJECT = {
    'all': 'all',
    'fgrpG1': 'fgrpG1',
    'fgrp_hz': 'fgrpG1',
    'fgrp5': 'fgrp5',
    'gw_O3': 'gw_O3',
    'gw_O2': 'gw_O2',
    'brp4': 'brp4',
    'brp7': 'brp7',
    'grG1hz_X_t': 'fgrpG1',
    'gwO3hz_X_t': 'gw_O3',
}
