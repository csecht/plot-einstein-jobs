"""
Matching Project and series names for checkbox labels, and dict keys,
used in various plot_jobs.py modules.
Names used here must match keys in PlotTasks.plot_proj dictionary.
"""

PROJECTS = ('all', 'gw', 'gw_O2', 'gw_O3', 'fgrp', 'fgrp5', 'fgrpG1', 'brp4', 'brp7')

PROJ_TO_REPORT = ('all', 'fgrpG1', 'fgrp5', 'gw_O3', 'gw_O2', 'brp4', 'brp7')

ALL_EXCLUDED = ('all', 'gw_series', 'gw_O3_freq', 'fgrpG1_freq')

GW_SERIES_EXCLUDED = ('all', 'gw_O2', 'gw_O3', 'gw_O3_freq', 'fgrpG1_freq')

ALL_INCLUSIVE = ('fgrpG1', 'fgrp5', 'gw_O3', 'gw_O2', 'brp4', 'brp7')

GW_SERIES_INCLUSIVE = ('fgrpG1', 'fgrp5', 'brp4', 'gw_series')

CHKBOX_LABELS = ('all', 'fgrpG1', 'fgrp5', 'gw_O3', 'gw_O2', 'gw_series',
                 'brp4', 'brp7', 'gw_O3_freq', 'fgrpG1_freq')

GW_SERIES = ('O2AS20-500', 'O2MD1C1', 'O2MD1C2', 'O2MD1G2', 'O2MD1G_',
             'O2MD1Gn', 'O2MD1S3', 'O2MDFG2_', 'O2MDFG2e', 'O2MDFG2f',
             'O2MDFG3_', 'O2MDFG3a', 'O2MDFS2', 'O2MDFS3_', 'O2MDFS3a',
             'O2MDFV2_', 'O2MDFV2e', 'O2MDFV2g', 'O2MDFV2h', 'O2MDFV2i',
             'O3AS1_', 'O3AS1a', 'O3ASE1',
             )

IS_DATA = {
          'all': 'all',
          'fgrpG1': 'fgrpG1',
          'fgrp5': 'fgrp5',
          'gw_O3': 'gw_O3',
          'gw_O2': 'gw_O2',
          'gw_series': 'gw',
          'brp4': 'brp4',
          'brp7': 'brp7',
          'gw_O3_freq': 'gw_O3',
          'fgrpG1_freq': 'fgrpG1',
}
