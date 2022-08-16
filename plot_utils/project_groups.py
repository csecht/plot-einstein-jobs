"""
Matching Project and series names for checkbox labels, and dict keys,
used in various plot_utils modules.
"""

# Names used here must match keys in PlotTasks.plot_proj dictionary.
PROJECTS = ('all', 'fgrp5', 'fgrpG1', 'gw_O2', 'gw_O3', 'brp4', 'brp7')

CHKBOX_LABELS = ('all', 'fgrp5', 'fgrpG1', 'fgrp_hz', 'gw_O3', 'gw_O2',
                 'brp4', 'brp7', 'grG1hz_X_t', 'gwO3hz_X_t')

EXCLUSIVE_PLOTS = ('all', 'fgrp_hz', 'grG1hz_X_t', 'gwO3hz_X_t')

ALL_EXCLUDED = ('all', 'fgrp_hz', 'grG1hz_X_t', 'gwO3hz_X_t')

ALL_INCLUSIVE = ('fgrp5', 'fgrpG1', 'gw_O3', 'gw_O2', 'brp4', 'brp7')

# Dict used in PlotTasks.add_proj_id to fill in is_<project> columns
#   in the main DataFrame.
PROJ_NAME_REGEX = {
    'fgrp5': r'LATeah\d{4}F',
    'fgrpG1': r'LATeah\d{4}L|LATeah1049',
    'gw_O2': '_O2',
    'gw_O3': '_O3',
    'brp4': r'^p',
    'brp7': r'^M22',
}

# Dict used in PlotTasks.project_label() to match checkbox CHKBOX_LABELS to
#  is_<project> columns in the main DataFrame.
PROJECT_LABEL = {
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
