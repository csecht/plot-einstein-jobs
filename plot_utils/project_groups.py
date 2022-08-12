"""
Matching Project and series names for checkbox labels, and dict keys,
used in various plot_utils modules.
"""

PROJECTS = ('all', 'fgrp', 'fgrp5', 'fgrpG1', 'gw', 'gw_O2', 'gw_O3', 'brp4', 'brp7')

PROJ_TO_REPORT = ('all', 'fgrp5', 'fgrpG1', 'gw_O3', 'gw_O2', 'brp4', 'brp7')

# Names used here must match keys in PlotTasks.plot_proj dictionary.
CHKBOX_LABELS = ('all', 'fgrp5', 'fgrpG1', 'fgrp_hz', 'gw_O3', 'gw_O2', 'gw_series',
                 'brp4', 'brp7', 'grG1hz_X_t', 'gwO3hz_X_t')

EXCLUSIVE_PLOTS = ('all', 'fgrp_hz', 'grG1hz_X_t', 'gwO3hz_X_t')

ALL_EXCLUDED = ('all', 'fgrp_hz', 'grG1hz_X_t', 'gwO3hz_X_t', 'gw_series')

GW_SERIES_EXCLUDED = ('all', 'fgrp_hz', 'grG1hz_X_t', 'gwO3hz_X_t', 'gw_O2', 'gw_O3')

ALL_INCLUSIVE = ('fgrp5', 'fgrpG1', 'gw_O3', 'gw_O2', 'brp4', 'brp7')

GW_SERIES_INCLUSIVE = ('fgrp5', 'fgrpG1', 'brp4', 'gw_series')

GW_SERIES = ('O2AS20-500', 'O2MD1C1', 'O2MD1C2', 'O2MD1G2', 'O2MD1G_',
             'O2MD1Gn', 'O2MD1S3', 'O2MDFG2_', 'O2MDFG2e', 'O2MDFG2f',
             'O2MDFG3_', 'O2MDFG3a', 'O2MDFS2', 'O2MDFS3_', 'O2MDFS3a',
             'O2MDFV2_', 'O2MDFV2e', 'O2MDFV2g', 'O2MDFV2h', 'O2MDFV2i',
             'O3AS1_', 'O3AS1a', 'O3ASE1',
             )

# Dict used in PlotTasks.is_project() to match checkbox CHKBOX_LABELS to
#  is_<project> columns in the main DataFrame.
IS_PROJECT = {
    'all': 'all',
    'fgrpG1': 'fgrpG1',
    'fgrp_hz': 'fgrpG1',
    'fgrp5': 'fgrp5',
    'gw_O3': 'gw_O3',
    'gw_O2': 'gw_O2',
    'gw_series': 'gw',
    'brp4': 'brp4',
    'brp7': 'brp7',
    'grG1hz_X_t': 'fgrpG1',
    'gwO3hz_X_t': 'gw_O3',
}
