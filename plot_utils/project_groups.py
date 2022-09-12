"""
Matching Project and series names for checkbox labels, and dict keys,
used in various plot_utils modules.
"""

# Names used here must match keys in PlotTasks.plot_proj dictionary.
PROJECTS = ('all', 'fgrp5', 'fgrpBG1', 'gw_O2MD', 'gw_O3AS', 'brp4', 'brp7')

CHKBOX_LABELS = ('all', 'fgrp5', 'fgrpBG1', 'fgrp_hz', 'gw_O3AS', 'gw_O2MD',
                 'brp4', 'brp7', 'fgrpHz_X_t', 'gwO3Hz_X_t')

EXCLUSIVE_PLOTS = ('all', 'fgrp_hz', 'fgrpHz_X_t', 'gwO3Hz_X_t')

ALL_EXCLUDED = ('all', 'fgrp_hz', 'fgrpHz_X_t', 'gwO3Hz_X_t')

ALL_INCLUSIVE = ('fgrp5', 'fgrpBG1', 'gw_O2MD', 'gw_O3AS', 'brp4', 'brp7')

# Dict used in PlotTasks.add_proj_tags to fill in is_<project> columns
#   in the main DataFrame.
PROJ_NAME_REGEX = {
    'fgrp': 'LATeah',
    'fgrp5': r'LATeah\d{4}F',
    'fgrpBG1': r'LATeah\d{4}L|LATeah1049',
    'gw_O2MD': '_O2MD',
    'gw_O3AS': '_O3AS',
    'brp4': r'^p',
    'brp7': r'^M22',
}

# Dict used in PlotTasks.clicked_plot() to match checkbox CHKBOX_LABELS to
#  is_<project> columns in the main DataFrame. Provides naming flexibility.
CLICKED_PLOT = {
    'all': 'all',
    'fgrp': 'fgrp',
    'fgrpBG1': 'fgrpBG1',
    'fgrp5': 'fgrp5',
    'fgrp_hz': 'fgrp',
    'gw_O3AS': 'gw_O3AS',
    'gw_O2MD': 'gw_O2MD',
    'brp4': 'brp4',
    'brp7': 'brp7',
    'fgrpHz_X_t': 'fgrp',
    'gwO3Hz_X_t': 'gw_O3AS',
}
